import ast, pprint
src = open("orchestrate_complete.py").read()
tree = ast.parse(src)
for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=="run_complete_pipeline"]:
    refs = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id=="logger"]
    pprint.pprint([ (type(r).__name__, r.lineno) for r in refs ])
