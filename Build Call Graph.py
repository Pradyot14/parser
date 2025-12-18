from pycparser import c_ast, parse_file
import json

class CallGraphBuilder(c_ast.NodeVisitor):
    def __init__(self):
        self.call_graph = {}  # {function: [called_functions]}
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

# Parse file
ast = parse_file('source_code/process_a.c', use_cpp=True)
builder = CallGraphBuilder()
builder.visit(ast)

# Print call graph
print("Call Graph:")
print("-" * 40)
for func, calls in builder.call_graph.items():
    print(f"{func}()")
    for called in calls:
        print(f"  └── {called}()")
```

**Output:**
```
Call Graph:
----------------------------------------
main()
  └── init_system()
  └── process_request()
  └── cleanup()
process_request()
  └── validate_input()
  └── move_read()
  └── process_data()
  └── move_write()
  └── log_info()
validate_input()
  └── check_bounds()
  └── log_error()
