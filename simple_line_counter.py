"""
Simple Line Counter for Banking Communication System
Works reliably on Windows with clear output
"""

import os
from pathlib import Path

def count_lines(directory="."):
    """Count lines in all code files"""
    
    print("\n" + "="*60)
    print("BANKING COMMUNICATION SYSTEM - CODE ANALYSIS")
    print("="*60)
    
    # File extensions to count
    extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json', '.md', '.txt', '.env', '.yml', '.yaml']
    
    # Folders to skip
    skip_folders = {'venv', '.venv', 'env', '.git', '__pycache__', 'node_modules', '.pytest_cache', 'htmlcov'}
    
    total_lines = 0
    total_files = 0
    file_counts = {}
    extension_counts = {}
    
    # Walk through all files
    for root, dirs, files in os.walk(directory):
        # Remove folders we want to skip
        dirs[:] = [d for d in dirs if d not in skip_folders]
        
        for file in files:
            # Check if it's a code file
            ext = Path(file).suffix.lower()
            if ext in extensions:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        total_lines += lines
                        total_files += 1
                        
                        # Store file info
                        rel_path = os.path.relpath(filepath, directory)
                        file_counts[rel_path] = lines
                        
                        # Count by extension
                        if ext not in extension_counts:
                            extension_counts[ext] = {'files': 0, 'lines': 0}
                        extension_counts[ext]['files'] += 1
                        extension_counts[ext]['lines'] += lines
                        
                        print(f"  ✓ Found: {rel_path} ({lines} lines)")
                        
                except Exception as e:
                    print(f"  ✗ Couldn't read: {filepath} - {e}")
    
    # Print summary
    print("\n" + "-"*60)
    print("SUMMARY:")
    print("-"*60)
    print(f"\n📊 TOTAL: {total_lines:,} lines across {total_files} files\n")
    
    # By extension
    print("BY FILE TYPE:")
    for ext, data in sorted(extension_counts.items(), key=lambda x: x[1]['lines'], reverse=True):
        pct = (data['lines'] / total_lines * 100) if total_lines > 0 else 0
        print(f"  {ext:8} {data['files']:3} files  {data['lines']:6,} lines ({pct:5.1f}%)")
    
    # Top 10 largest files
    print("\nTOP 10 LARGEST FILES:")
    sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for filepath, lines in sorted_files:
        print(f"  {lines:5,} lines - {filepath}")
    
    # Customer-centric keyword search
    print("\n🎯 CUSTOMER-CENTRIC KEYWORDS FOUND:")
    keywords = ['customer', 'sentiment', 'emotion', 'empathy', 'feeling', 'experience', 
                'satisfaction', 'complaint', 'vulnerable', 'accessibility']
    keyword_counts = {k: 0 for k in keywords}
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_folders]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for keyword in keywords:
                            keyword_counts[keyword] += content.count(keyword)
                except:
                    pass
    
    for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  '{keyword}': {count} occurrences")
    
    print("\n" + "="*60)
    print(f"✨ Analysis Complete! Your system has {total_lines:,} lines of code")
    print("="*60 + "\n")
    
    return total_lines, total_files

if __name__ == "__main__":
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Analyzing: {os.path.abspath(directory)}")
    count_lines(directory)