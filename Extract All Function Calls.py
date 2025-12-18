from pycparser import c_parser, c_ast, parse_file

class FunctionCallVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.calls = []
    
    def visit_FuncCall(self, node):
        if hasattr(node.name, 'name'):
            self.calls.append({
                'function': node.name.name,
                'line': node.coord.line if node.coord else None
            })
        self.generic_visit(node)

ast = parse_file('source_code/process_a.c', use_cpp=True)
visitor = FunctionCallVisitor()
visitor.visit(ast)

for call in visitor.calls:
    print(f"Call to {call['function']} at line {call['line']}")
```

**Output:**
```
Call to init_system at line 12
Call to move_read at line 28
Call to validate_input at line 30
Call to move_write at line 45
Call to log_error at line 50
