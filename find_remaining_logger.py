#!/usr/bin/env python3
"""
Simple script to find remaining logger references in the run_complete_pipeline function
"""
import re
from pathlib import Path

def find_logger_references():
    with open(Path(__file__).parent / "orchestrate_complete.py", "r") as f:
        content = f.read()
    
    # Find the run_complete_pipeline function
    pattern = r'async def run_complete_pipeline\(\):(.*?)(?=\n\n# NOTE FOR AI BOT:|$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("Could not find run_complete_pipeline function")
        return
    
    function_code = match.group(1)
    
    # Find all logger references
    logger_refs = re.findall(r'\blogger\b', function_code)
    
    print(f"Found {len(logger_refs)} references to 'logger' in run_complete_pipeline")
    
    # Show code context for each reference
    for i, line in enumerate(function_code.split('\n')):
        if 'logger' in line:
            line_num = i + 1  # Adjust for 1-based line numbering
            print(f"Line {line_num}: {line.strip()}")

if __name__ == "__main__":
    find_logger_references()
