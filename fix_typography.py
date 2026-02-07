#!/usr/bin/env python3
"""
Automated Typography Fix Script for Kerne Website
Fixes all non-compliant header and text sizing across the site.
"""

import re
import os
from pathlib import Path

def fix_file(filepath):
    """Fix typography issues in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix 1: Remove inline text-size classes from h1, h2, h3, h4 tags
        # Pattern: <h[1-4] className="...text-[size]..."
        content = re.sub(
            r'(<h[1-4]\s+className=["\'])([^"\']*?)\s*text-(?:xs|s|m|l|xl|base|sm|lg|2xl|3xl|4xl|5xl|6xl|7xl)\s*([^"\']*?)(["\'])',
            r'\1\2 \3\4',
            content
        )
        
        # Fix 2: Replace non-compliant text sizes in all other contexts
        # text-sm -> text-s
        content = re.sub(r'\btext-sm\b', 'text-s', content)
        
        # text-base -> text-m
        content = re.sub(r'\btext-base\b', 'text-m', content)
        
        # text-lg -> text-l
        content = re.sub(r'\btext-lg\b', 'text-l', content)
        
        # Clean up any double spaces that may have been created
        content = re.sub(r'className="([^"]*?)\s{2,}([^"]*?)"', r'className="\1 \2"', content)
        content = re.sub(r"className='([^']*?)\s{2,}([^']*?)'", r"className='\1 \2'", content)
        
        # Trim extra spaces in className
        content = re.sub(r'className="([^"]*?)\s+([^"]*?)"', lambda m: f'className="{m.group(1).strip()} {m.group(2).strip()}"', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main fix function."""
    frontend_dir = Path('frontend/src')
    
    if not frontend_dir.exists():
        print("Error: frontend/src directory not found!")
        return
    
    print("=" * 80)
    print("KERNE TYPOGRAPHY AUTO-FIX")
    print("=" * 80)
    print("\nFixing:")
    print("  1. Removing inline text-size classes from headers (h1-h4)")
    print("  2. Converting text-sm -> text-s")
    print("  3. Converting text-base -> text-m")
    print("  4. Converting text-lg -> text-l")
    print("\n" + "=" * 80 + "\n")
    
    # Find all TSX files (skip CSS as it has the definitions)
    files_to_fix = list(frontend_dir.rglob('*.tsx')) + list(frontend_dir.rglob('*.ts'))
    
    # Exclude certain files
    exclude_patterns = ['node_modules', '.next', 'dist', 'build']
    files_to_fix = [f for f in files_to_fix if not any(ex in str(f) for ex in exclude_patterns)]
    
    fixed_count = 0
    
    for filepath in sorted(files_to_fix):
        if fix_file(filepath):
            fixed_count += 1
            print(f"[FIXED] {filepath.relative_to(Path('frontend'))}")
    
    print("\n" + "=" * 80)
    print(f"\n[SUMMARY]")
    print(f"  Total files processed: {len(files_to_fix)}")
    print(f"  Files modified: {fixed_count}")
    
    if fixed_count > 0:
        print(f"\n[OK] Successfully fixed typography in {fixed_count} files!")
    else:
        print("\n[OK] No files needed fixing - all typography is compliant!")
    
    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()