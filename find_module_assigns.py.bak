import ast, pprint
tree = ast.parse(open("orchestrate_complete.py").read())
assigns = [n for n in tree.body if isinstance(n, ast.Assign)]
for n in assigns:
    if hasattr(n.targets[0], 'id'):
        print(f"{n.targets[0].id} at line {n.lineno}")
