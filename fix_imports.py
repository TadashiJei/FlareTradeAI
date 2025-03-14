#!/usr/bin/env python3
"""
Import Fix Script for FlareTrade

This script fixes import statements in Python files to use relative imports
where appropriate, helping resolve module import issues in the codebase.
"""

import os
import re
import sys
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Determine package depth based on file path
    rel_path = Path(file_path).relative_to(Path(os.path.abspath(os.path.dirname(__file__))) / 'src')
    parts = rel_path.parts
    
    if len(parts) <= 1:
        # Files directly in src don't need changes
        return False
    
    # Current package
    current_package = parts[0]
    
    # Regular expression to find absolute imports from the same package
    pattern = rf'from\s+{current_package}\.([^\s]+)\s+import'
    
    # Calculate prefix for relative imports based on depth
    if len(parts) == 2:
        # File is at top level of package
        prefix = 'from . import'
        replacement = r'from .\1 import'
    else:
        # File is in subdirectory
        # Calculate how many parent dirs to go up
        levels = len(parts) - 2
        prefix = '.' * levels
        replacement = rf'from {prefix}.\1 import'
    
    # Replace absolute imports with relative imports
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed imports in {file_path}")
        return True
    return False

def scan_and_fix_imports(directory):
    """Scan directory and fix imports in Python files."""
    fixed_count = 0
    py_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    for file_path in py_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    return fixed_count

if __name__ == "__main__":
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    fixed_count = scan_and_fix_imports(src_dir)
    print(f"Fixed imports in {fixed_count} files")
