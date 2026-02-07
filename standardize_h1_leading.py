#!/usr/bin/env python3
"""
Standardize h1 line-height to leading-[0.95]
"""

import re
from pathlib import Path

def fix_h1_leading_in_file(filepath):
    """Replace leading-[0.85] with leading-[0.95] in h1 tags"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace leading-[0.85] with leading-[0.95] in h1 tags
    content = re.sub(r'leading-\[0\.85\]', 'leading-[0.95]', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    frontend_dir = Path('frontend/src/app')
    
    # Files that have h1 with leading-[0.85]
    files_to_fix = [
        'about/page.tsx',
        'cookies/page.tsx',
        'institutional/page.tsx',
        'transparency/page.tsx'
    ]
    
    total_changed = 0
    
    for file_path in files_to_fix:
        full_path = frontend_dir / file_path
        if full_path.exists():
            if fix_h1_leading_in_file(full_path):
                print(f"Fixed: {file_path}")
                total_changed += 1
    
    print(f"\nTotal files changed: {total_changed}")

if __name__ == '__main__':
    main()
