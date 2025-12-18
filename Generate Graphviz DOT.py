from pycparser import c_ast, parse_file

class CallGraphBuilder(c_ast.NodeVisitor):
    def __init__(self):
        self.call_graph = {}
        self.current_function = None
    
    def visit_FuncDef(self, node):
        self.current_function = node.decl.name
        self.call_graph[self.current_function] = []
        self.generic_visit(node)
        self.current_function = None
    
    def visit_FuncCall(self, node):
        if self.current_function and hasattr(node.name, 'name'):
            called_func = node.name.name
            if called_func not in self.call_graph[self.current_function]:
                self.call_graph[self.current_function].append(called_func)
        self.generic_visit(node)
    
    def to_graphviz(self):
        lines = ['digraph CallGraph {', '    rankdir=TB;']
        for func, calls in self.call_graph.items():
            for called in calls:
                lines.append(f'    "{func}" -> "{called}";')
        lines.append('}')
        return '\n'.join(lines)

# Parse and generate
ast = parse_file('source_code/process_a.c', use_cpp=True)
builder = CallGraphBuilder()
builder.visit(ast)

# Save DOT file
with open('call_graph.dot', 'w') as f:
    f.write(builder.to_graphviz())

print("Graphviz DOT file generated: call_graph.dot")
print("\nTo create image: dot -Tpng call_graph.dot -o call_graph.png")
