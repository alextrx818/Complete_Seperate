#!/usr/bin/env python3
"""
Logger AST Report - Analyzes Python files for logger usage patterns
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

class LoggerVisitor(ast.NodeVisitor):
    """Visitor that tracks logger initialization and usage."""
    
    def __init__(self):
        self.direct_getlogger_calls = []  # logging.getLogger calls
        self.custom_getlogger_calls = []  # get_logger calls
        self.logger_assignments = []      # logger = x assignments
        self.logger_usages = []           # logger.x() calls
        self.logger_shadowing = []        # Function-level logger assignments that shadow module loggers
        self.current_function = None
        self.module_loggers = set()       # Module-level logger variables
        
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
        
    def visit_AsyncFunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
        
    def visit_Call(self, node):
        # Check for logging.getLogger calls
        if (isinstance(node.func, ast.Attribute) and 
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'logging' and 
            node.func.attr == 'getLogger'):
            self.direct_getlogger_calls.append((node.lineno, self.current_function))
            
        # Check for get_logger calls
        elif (isinstance(node.func, ast.Name) and 
              node.func.id == 'get_logger'):
            self.custom_getlogger_calls.append((node.lineno, self.current_function))
            
        # Check for logger usages (logger.info, logger.debug, etc.)
        elif (isinstance(node.func, ast.Attribute) and 
              isinstance(node.func.value, ast.Name) and
              node.func.value.id == 'logger'):
            self.logger_usages.append((node.lineno, self.current_function, node.func.attr))
            
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        # Check for logger assignments
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'logger':
                if self.current_function:
                    # Check if this shadows a module-level logger
                    if 'logger' in self.module_loggers:
                        self.logger_shadowing.append((target.lineno, self.current_function))
                else:
                    # This is a module-level logger assignment
                    self.module_loggers.add('logger')
                
                self.logger_assignments.append((target.lineno, self.current_function))
        
        self.generic_visit(node)

def analyze_file(file_path: str) -> Dict:
    """Analyze a Python file for logger usage."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
            visitor = LoggerVisitor()
            visitor.visit(tree)
            
            return {
                'file': file_path,
                'direct_getlogger_calls': visitor.direct_getlogger_calls,
                'custom_getlogger_calls': visitor.custom_getlogger_calls,
                'logger_assignments': visitor.logger_assignments,
                'logger_usages': visitor.logger_usages,
                'logger_shadowing': visitor.logger_shadowing,
                'module_loggers': list(visitor.module_loggers)
            }
        except SyntaxError as e:
            return {
                'file': file_path,
                'error': f"Syntax error: {str(e)}"
            }
        except Exception as e:
            return {
                'file': file_path,
                'error': f"Error analyzing file: {str(e)}"
            }

def find_python_files(start_dir: str) -> List[str]:
    """Find all Python files in a directory structure."""
    python_files = []
    for root, _, files in os.walk(start_dir):
        # Skip virtual environment directories
        if 'sports_venv' in root.split(os.path.sep):
            continue
            
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to analyze logger usage in Python files."""
    # Use current directory if no argument is provided
    start_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    print(f"Analyzing Python files in {start_dir} for logger usage...")
    
    # Find all Python files
    python_files = find_python_files(start_dir)
    print(f"Found {len(python_files)} Python files")
    
    # Analyze each file
    results = []
    for file_path in python_files:
        results.append(analyze_file(file_path))
    
    # Summarize results
    total_direct_calls = sum(len(r.get('direct_getlogger_calls', [])) for r in results)
    total_custom_calls = sum(len(r.get('custom_getlogger_calls', [])) for r in results)
    total_shadowing = sum(len(r.get('logger_shadowing', [])) for r in results)
    
    print("\n=== SUMMARY ===")
    print(f"Total direct logging.getLogger calls: {total_direct_calls}")
    print(f"Total custom get_logger calls: {total_custom_calls}")
    print(f"Total instances of logger shadowing: {total_shadowing}")
    
    # Print files with logger shadowing (most serious issue)
    if total_shadowing > 0:
        print("\n=== FILES WITH LOGGER SHADOWING ===")
        for result in results:
            if result.get('logger_shadowing'):
                print(f"\n{result['file']}:")
                for line, func in result.get('logger_shadowing', []):
                    print(f"  Line {line}, Function {func}")
    
    # Print files with direct logging.getLogger calls (bypassing centralized logging)
    if total_direct_calls > 0:
        print("\n=== FILES WITH DIRECT logging.getLogger CALLS ===")
        for result in results:
            if result.get('direct_getlogger_calls'):
                print(f"\n{result['file']}:")
                for line, func in result.get('direct_getlogger_calls', []):
                    func_ctx = f" in function {func}" if func else " at module level"
                    print(f"  Line {line}{func_ctx}")
    
    # Print files with multiple logger assignments
    print("\n=== FILES WITH MULTIPLE LOGGER ASSIGNMENTS ===")
    for result in results:
        if len(result.get('logger_assignments', [])) > 1:
            print(f"\n{result['file']}:")
            for line, func in result.get('logger_assignments', []):
                func_ctx = f" in function {func}" if func else " at module level"
                print(f"  Line {line}{func_ctx}")
    
    # Special case analysis for orchestrate_complete.py (since we know it has issues)
    print("\n=== DETAILED ANALYSIS OF orchestrate_complete.py ===")
    for result in results:
        if result['file'].endswith('orchestrate_complete.py'):
            print(f"Module-level loggers: {result.get('module_loggers', [])}")
            print("\nLogger assignments:")
            for line, func in result.get('logger_assignments', []):
                func_ctx = f" in function {func}" if func else " at module level"
                print(f"  Line {line}{func_ctx}")
            
            print("\nLogger usages:")
            for line, func, method in result.get('logger_usages', []):
                func_ctx = f" in function {func}" if func else " at module level"
                print(f"  Line {line}{func_ctx}: logger.{method}")
            
            # Detect possible unbound local errors
            func_assignments = {}
            func_usages = {}
            
            for line, func in result.get('logger_assignments', []):
                if func:
                    func_assignments.setdefault(func, []).append(line)
            
            for line, func, _ in result.get('logger_usages', []):
                if func:
                    func_usages.setdefault(func, []).append(line)
            
            print("\nPotential UnboundLocalError detection:")
            for func, usage_lines in func_usages.items():
                if func in func_assignments:
                    first_assignment = min(func_assignments[func])
                    early_usages = [line for line in usage_lines if line < first_assignment]
                    if early_usages:
                        print(f"  Function {func} uses logger before assignment:")
                        print(f"    First assignment: line {first_assignment}")
                        print(f"    Earlier usages: {early_usages}")

if __name__ == "__main__":
    main()
