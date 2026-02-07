#!/usr/bin/env python3
"""
Mobile Spacing Audit Script for Kerne Website
Identifies spacing inconsistencies across all pages
"""

import re
from pathlib import Path

# Define the issues to look for
SPACING_ISSUES = {
    "Hero Section Padding": {
        "pattern": r"pt-32 pb-48 md:pb-64",
        "should_be": "pt-24 md:pt-32 pb-32 md:pb-48",
        "reason": "Excessive mobile bottom padding creates large gaps"
    },
    "Negative Margin No Responsive": {
        "pattern": r"-mb-32(?!\s+md:)",
        "should_be": "-mb-16 md:-mb-32",
        "reason": "Negative margins too large on mobile, causing overlap"
    },
    "Hero Content Spacing Inconsistent": {
        "pattern": r"mb-16 lg:mb-32",
        "should_be": "mb-12 md:mb-24",
        "reason": "Should use md: breakpoint consistently, not lg:"
    },
    "Section Padding Issues": {
        "pattern": r"py-32(?!\s+md:|\s+lg:)",
        "should_be": "py-24 md:py-32",
        "reason": "Consider responsive padding for mobile"
    }
}

def audit_file(filepath):
    """Audit a single file for spacing issues"""
    issues_found = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    for issue_name, issue_data in SPACING_ISSUES.items():
        pattern = issue_data['pattern']
        matches = re.finditer(pattern, content)
        
        for match in matches:
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            line_content = lines[line_num - 1].strip()
            
            issues_found.append({
                'issue': issue_name,
                'line': line_num,
                'found': match.group(),
                'should_be': issue_data['should_be'],
                'reason': issue_data['reason'],
                'context': line_content[:100]
            })
    
    return issues_found

def main():
    # Pages to audit
    pages = [
        'frontend/src/app/page.tsx',
        'frontend/src/app/about/page.tsx',
        'frontend/src/app/transparency/page.tsx',
        'frontend/src/app/institutional/page.tsx',
    ]
    
    print("=" * 80)
    print("KERNE MOBILE SPACING AUDIT")
    print("=" * 80)
    print()
    
    total_issues = 0
    
    for page_path in pages:
        filepath = Path(page_path)
        if not filepath.exists():
            print(f"[WARNING] {page_path} not found")
            continue
        
        issues = audit_file(filepath)
        
        if issues:
            print(f"[FILE] {page_path}")
            print(f"   Found {len(issues)} spacing issue(s):")
            print()
            
            for issue in issues:
                print(f"   [X] Line {issue['line']}: {issue['issue']}")
                print(f"      Found: {issue['found']}")
                print(f"      Should be: {issue['should_be']}")
                print(f"      Reason: {issue['reason']}")
                print()
            
            total_issues += len(issues)
        else:
            print(f"[OK] {page_path} - No issues found")
            print()
    
    print("=" * 80)
    print(f"TOTAL ISSUES FOUND: {total_issues}")
    print("=" * 80)

if __name__ == "__main__":
    main()