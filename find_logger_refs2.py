import ast

def print_logger_references():
    with open("orchestrate_complete.py", "r") as file:
        src = file.read()
    
    tree = ast.parse(src)
    
    # Find the run_complete_pipeline function
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_complete_pipeline":
            # Find all logger references
            logger_refs = []
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Name) and subnode.id == "logger":
                    logger_refs.append((subnode.lineno, "Store" if isinstance(subnode.ctx, ast.Store) else "Load"))
            
            print(f"Found {len(logger_refs)} references to 'logger' in run_complete_pipeline:")
            for line, ctx in logger_refs:
                print(f"Line {line}: {ctx} context")

if __name__ == "__main__":
    print_logger_references()
