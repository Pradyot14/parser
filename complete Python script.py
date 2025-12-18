"""
MOVE Middleware C Code Analyzer
Extracts function calls, MOVE operations, and generates reports
"""

from pycparser import c_ast, parse_file
import os
import json

# MOVE function classifications
MOVE_READ_FUNCS = ['move_read', 'move_get', 'move_fetch', 'move_load']
MOVE_WRITE_FUNCS = ['move_write', 'move_put', 'move_store', 'move_save']
MOVE_CREATE_FUNCS = ['move_create', 'move_open']
MOVE_DELETE_FUNCS = ['move_delete', 'move_remove', 'move_close']

ALL_MOVE_FUNCS = MOVE_READ_FUNCS + MOVE_WRITE_FUNCS + MOVE_CREATE_FUNCS + MOVE_DELETE_FUNCS


class MoveCodeAnalyzer(c_ast.NodeVisitor):
    """Analyzes C code for MOVE middleware operations"""
    
    def __init__(self, filename):
        self.filename = filename
        self.functions = {}  # {func_name: {calls: [], move_ops: []}}
        self.current_function = None
    
    def visit_FuncDef(self, node):
        """Visit function definition"""
        func_name = node.decl.name
        self.current_function = func_name
        self.functions[func_name] = {
            'line': node.coord.line if node.coord else None,
            'calls': [],
            'move_operations': []
        }
        self.generic_visit(node)
        self.current_function = None
    
    def visit_FuncCall(self, node):
        """Visit function call"""
        if not self.current_function:
            self.generic_visit(node)
            return
        
        if not hasattr(node.name, 'name'):
            self.generic_visit(node)
            return
        
        func_name = node.name.name
        line = node.coord.line if node.coord else None
        
        # Record all function calls
        call_info = {'function': func_name, 'line': line}
        if call_info not in self.functions[self.current_function]['calls']:
            self.functions[self.current_function]['calls'].append(call_info)
        
        # Check if it's a MOVE function
        if func_name in ALL_MOVE_FUNCS:
            move_op = self._extract_move_operation(node, func_name, line)
            self.functions[self.current_function]['move_operations'].append(move_op)
        
        self.generic_visit(node)
    
    def _extract_move_operation(self, node, func_name, line):
        """Extract details from MOVE function call"""
        # Determine operation type
        if func_name in MOVE_READ_FUNCS:
            op_type = 'READ'
        elif func_name in MOVE_WRITE_FUNCS:
            op_type = 'WRITE'
        elif func_name in MOVE_CREATE_FUNCS:
            op_type = 'CREATE'
        else:
            op_type = 'DELETE'
        
        # Extract filenum (first argument)
        filenum = 'unknown'
        if node.args and node.args.exprs:
            first_arg = node.args.exprs[0]
            if hasattr(first_arg, 'value'):
                filenum = first_arg.value
            elif hasattr(first_arg, 'name'):
                filenum = f"var:{first_arg.name}"
        
        return {
            'function': func_name,
            'operation': op_type,
            'filenum': filenum,
            'line': line
        }
    
    def get_call_graph(self):
        """Return call graph as dictionary"""
        return {func: [c['function'] for c in data['calls']] 
                for func, data in self.functions.items()}
    
    def get_move_operations(self):
        """Return all MOVE operations"""
        ops = []
        for func, data in self.functions.items():
            for op in data['move_operations']:
                ops.append({
                    'caller': func,
                    **op
                })
        return ops
    
    def get_file_access_summary(self):
        """Summarize which functions access which files"""
        summary = {}  # {filenum: {'read': [], 'write': [], ...}}
        
        for func, data in self.functions.items():
            for op in data['move_operations']:
                filenum = op['filenum']
                op_type = op['operation'].lower()
                
                if filenum not in summary:
                    summary[filenum] = {'create': [], 'read': [], 'write': [], 'delete': []}
                
                if func not in summary[filenum][op_type]:
                    summary[filenum][op_type].append(func)
        
        return summary
    
    def generate_report(self):
        """Generate analysis report as string"""
        lines = []
        lines.append(f"# Analysis Report: {self.filename}")
        lines.append(f"\n## Functions Found: {len(self.functions)}")
        
        for func, data in self.functions.items():
            lines.append(f"\n### {func}() [Line {data['line']}]")
            
            if data['calls']:
                lines.append("**Calls:**")
                for call in data['calls']:
                    lines.append(f"  - {call['function']}()")
            
            if data['move_operations']:
                lines.append("**MOVE Operations:**")
                for op in data['move_operations']:
                    lines.append(f"  - {op['operation']}: {op['function']}(filenum={op['filenum']})")
        
        # File access summary
        summary = self.get_file_access_summary()
        if summary:
            lines.append("\n## File Access Summary (CRUD)")
            lines.append("| File | CREATE | READ | UPDATE | DELETE |")
            lines.append("|------|--------|------|--------|--------|")
            for filenum, ops in summary.items():
                create = ', '.join(ops['create']) or '-'
                read = ', '.join(ops['read']) or '-'
                write = ', '.join(ops['write']) or '-'
                delete = ', '.join(ops['delete']) or '-'
                lines.append(f"| {filenum} | {create} | {read} | {write} | {delete} |")
        
        return '\n'.join(lines)
    
    def generate_graphviz(self):
        """Generate Graphviz DOT for call graph"""
        lines = ['digraph CallGraph {', '    rankdir=TB;', '    node [shape=rectangle];']
        
        # Add MOVE function nodes with different style
        lines.append('    // MOVE functions')
        for func in ALL_MOVE_FUNCS:
            lines.append(f'    "{func}" [shape=cylinder, style=filled, fillcolor=lightblue];')
        
        # Add edges
        lines.append('    // Call edges')
        for func, calls in self.get_call_graph().items():
            for called in calls:
                lines.append(f'    "{func}" -> "{called}";')
        
        lines.append('}')
        return '\n'.join(lines)


def analyze_file(filepath):
    """Analyze a single C file"""
    print(f"Analyzing: {filepath}")
    
    try:
        ast = parse_file(filepath, use_cpp=True,
                        cpp_args=['-E', '-I/usr/include', '-I./include'])
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    
    analyzer = MoveCodeAnalyzer(filepath)
    analyzer.visit(ast)
    
    return analyzer


def analyze_directory(dirpath, output_dir='analysis_output'):
    """Analyze all C files in directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    all_move_ops = []
    all_call_graphs = {}
    
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if file.endswith('.c'):
                filepath = os.path.join(root, file)
                analyzer = analyze_file(filepath)
                
                if analyzer:
                    # Save individual report
                    report_path = os.path.join(output_dir, f"{file}_analysis.md")
                    with open(report_path, 'w') as f:
                        f.write(analyzer.generate_report())
                    
                    # Save call graph
                    dot_path = os.path.join(output_dir, f"{file}_callgraph.dot")
                    with open(dot_path, 'w') as f:
                        f.write(analyzer.generate_graphviz())
                    
                    # Collect data
                    all_move_ops.extend(analyzer.get_move_operations())
                    all_call_graphs[file] = analyzer.get_call_graph()
    
    # Save combined data
    with open(os.path.join(output_dir, 'all_move_operations.json'), 'w') as f:
        json.dump(all_move_ops, f, indent=2)
    
    with open(os.path.join(output_dir, 'all_call_graphs.json'), 'w') as f:
        json.dump(all_call_graphs, f, indent=2)
    
    print(f"\nAnalysis complete. Results in: {output_dir}/")


# Main execution
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python move_analyzer.py <file.c or directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if os.path.isfile(target):
        analyzer = analyze_file(target)
        if analyzer:
            print("\n" + analyzer.generate_report())
    elif os.path.isdir(target):
        analyze_directory(target)
    else:
        print(f"Error: {target} not found")
