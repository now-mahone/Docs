#!/usr/bin/env python3
"""
Typography Audit Script for Kerne Website
Checks for non-compliant header and text sizing across all frontend files.

STANDARDS (from globals.css):
- Headers (h1, h2, h3, h4): Should have NO inline text-size classes
- Text sizes: text-xs (11px), text-s (14px), text-m (16px), text-l (18px), text-xl (30px)
- Non-compliant: text-base, text-sm, text-lg, text-2xl, text-3xl, text-4xl, etc.
"""

import re
import os
from pathlib import Path

# Define non-compliant patterns
NON_COMPLIANT_TEXT_SIZES = [
    'text-base',  # Should be text-m
    'text-sm',    # Should be text-s
    'text-lg',    # Should be text-l
    'text-2xl',   # Not in standard (unless display text)
    'text-3xl',   # Not in standard (unless display text)
    'text-4xl',   # Not in standard (unless display text)
    'text-5xl',   # Not in standard (unless display text)
    'text-6xl',   # Not in standard (unless display text)
    'text-7xl',   # Not in standard (unless display text)
]

# Pattern to find headers with inline text-size classes
HEADER_WITH_SIZE = re.compile(r'<(h[1-4])[^>]*\sclassName=["\']([^"\']*text-(?:xs|s|m|l|xl|base|sm|lg|2xl|3xl|4xl|5xl|6xl|7xl)[^"\']*)["\']')

# Pattern to find non-compliant text sizes
NON_COMPLIANT_PATTERN = re.compile(r'\btext-(?:base|sm|lg|2xl|3xl|4xl|5xl|6xl|7xl)\b')

def audit_file(filepath):
    """Audit a single file for typography issues."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for headers with inline text-size classes
        for match in HEADER_WITH_SIZE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            header_tag = match.group(1)
            class_name = match.group(2)
            
            # Extract just the text-size class from the full className
            size_match = re.search(r'text-(?:xs|s|m|l|xl|base|sm|lg|2xl|3xl|4xl|5xl|6xl|7xl)', class_name)
            if size_match:
                size_class = size_match.group(0)
                issues.append({
                    'type': 'HEADER_WITH_INLINE_SIZE',
                    'line': line_num,
                    'tag': header_tag,
                    'size': size_class,
                    'context': lines[line_num - 1].strip()[:100]
                })
        
        # Check for non-compliant text sizes
        for i, line in enumerate(lines, 1):
            for match in NON_COMPLIANT_PATTERN.finditer(line):
                size_class = match.group(0)
                issues.append({
                    'type': 'NON_COMPLIANT_TEXT_SIZE',
                    'line': i,
                    'size': size_class,
                    'context': line.strip()[:100]
                })
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return issues

def main():
    """Main audit function."""
    frontend_dir = Path('frontend/src')
    
    if not frontend_dir.exists():
        print("Error: frontend/src directory not found!")
        return
    
    print("=" * 80)
    print("KERNE TYPOGRAPHY AUDIT")
    print("=" * 80)
    print("\nSTANDARDS:")
    print("  Headers (h1-h4): NO inline text-size classes allowed")
    print("  Text sizes: text-xs, text-s, text-m, text-l, text-xl ONLY")
    print("  Non-compliant: text-base, text-sm, text-lg, text-2xl, text-3xl, etc.")
    print("\n" + "=" * 80 + "\n")
    
    # Find all TSX and CSS files
    files_to_audit = list(frontend_dir.rglob('*.tsx')) + list(frontend_dir.rglob('*.css'))
    
    total_issues = 0
    files_with_issues = 0
    
    for filepath in sorted(files_to_audit):
        issues = audit_file(filepath)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            
            print(f"\n[FILE] {filepath.relative_to(Path('frontend'))}")
            print("-" * 80)
            
            for issue in issues:
                if issue['type'] == 'HEADER_WITH_INLINE_SIZE':
                    print(f"  [!] Line {issue['line']}: <{issue['tag']}> has inline size '{issue['size']}'")
                    print(f"      Context: {issue['context']}")
                elif issue['type'] == 'NON_COMPLIANT_TEXT_SIZE':
                    print(f"  [!] Line {issue['line']}: Non-compliant text size '{issue['size']}'")
                    print(f"      Context: {issue['context']}")
    
    print("\n" + "=" * 80)
    print(f"\n[SUMMARY]")
    print(f"  Total files audited: {len(files_to_audit)}")
    print(f"  Files with issues: {files_with_issues}")
    print(f"  Total issues found: {total_issues}")
    
    if total_issues == 0:
        print("\n[OK] All typography is compliant with standards!")
    else:
        print(f"\n[ERROR] Found {total_issues} typography issues that need to be fixed.")
    
    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()