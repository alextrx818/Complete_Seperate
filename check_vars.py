import ast, sys

def check_undefined_vars(filepath):
    src = open(filepath).read()
    tree = ast.parse(src)
    undefined_vars = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            locals_defined = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    locals_defined.add(n.id)
            
            for n in ast.walk(node):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in locals_defined and n.id not in globals() and n.id != 'self':
                    undefined_vars.append((node.name, n.id, n.lineno))
    
    print('Potentially undefined variables in functions:')
    for func, var, line in undefined_vars:
        print(f'Function {func}, Variable {var}, Line {line}')

if __name__ == "__main__":
    check_undefined_vars("orchestrate_complete.py")
