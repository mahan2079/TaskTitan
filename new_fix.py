"""
Find and fix references to 'week_start_date' in the codebase
"""

import os
import sys
import re

def find_and_fix_references():
    """Find and fix references to week_start_date in the codebase."""
    search_dir = "TaskTitan"
    if not os.path.isdir(search_dir):
        print(f"Error: Directory '{search_dir}' not found")
        return
    
    # Track files with matches
    files_with_matches = []
    
    # Walk through the directory
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if 'week_start_date' is in the content
                    if 'week_start_date' in content:
                        files_with_matches.append(file_path)
                        print(f"Found reference in: {file_path}")
                        
                        # Extract the lines with 'week_start_date'
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'week_start_date' in line:
                                print(f"  Line {i+1}: {line.strip()}")
                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    if not files_with_matches:
        print("No references to 'week_start_date' found.")
    else:
        print(f"\nFound {len(files_with_matches)} files with references to 'week_start_date'.")
        print("You may need to modify these files to fix the database schema issue.")

if __name__ == "__main__":
    find_and_fix_references() 