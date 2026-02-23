#!/usr/bin/env python3
"""
Fix remaining text-sm instances to text-s for consistency
"""

import re
from pathlib import Path

def fix_text_sm_in_file(filepath):
    """Replace text-sm with text-s in a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace text-sm with text-s
    content = re.sub(r'\btext-sm\b', 'text-s', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    frontend_dir = Path('frontend/src/app')
    
    files_to_fix = [
        'yield/page.tsx',
        'prime/page.tsx',
        'partner/page.tsx',
        'page.tsx',
        'liquidity/page.tsx',
        'admin/page.tsx',
        'access/page.tsx'
    ]
    
    total_changed = 0
    
    for file_path in files_to_fix:
        full_path = frontend_dir / file_path
        if full_path.exists():
            if fix_text_sm_in_file(full_path):
                print(f"Fixed: {file_path}")
                total_changed += 1
    
    print(f"\nTotal files changed: {total_changed}")

if __name__ == '__main__':
    main()
