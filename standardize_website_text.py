#!/usr/bin/env python3
"""
Kerne Website Text Size Standardization Script
Searches through key pages and replaces non-standard text sizes with approved scale.

Approved Text Sizes (from project_state.md):
- text-xs = 11px
- text-s = 14px
- text-m = 16px
- text-l = 18px
- text-xl = 30px

This script targets:
- Home page (page.tsx)
- Terminal page (terminal/page.tsx)
- About page (about/page.tsx)
- Transparency page (transparency/page.tsx)
- Onboarding/Institutional page (institutional/page.tsx)
"""

import re
import os
from pathlib import Path

# Define the files to process (pages + components)
TARGET_FILES = [
    # Pages
    "frontend/src/app/page.tsx",
    "frontend/src/app/terminal/page.tsx",
    "frontend/src/app/about/page.tsx",
    "frontend/src/app/transparency/page.tsx",
    "frontend/src/app/institutional/page.tsx",
    # Components used on these pages
    "frontend/src/components/VaultInteraction.tsx",
    "frontend/src/components/AssetComposition.tsx",
    "frontend/src/components/BacktestedPerformance.tsx",
    "frontend/src/components/KerneExplained.tsx",
    "frontend/src/components/PerformanceChart.tsx",
    "frontend/src/components/ETHComparisonChart.tsx",
    "frontend/src/components/Navbar.tsx",
    "frontend/src/components/Footer.tsx",
    "frontend/src/components/WalletConnectButton.tsx",
    "frontend/src/components/WalletDropdown.tsx",
    "frontend/src/components/WalletModal.tsx",
]

# Mapping of non-standard text sizes to standard sizes
TEXT_SIZE_REPLACEMENTS = {
    # Common Tailwind defaults that should be replaced
    r'\btext-sm\b': 'text-s',      # 14px -> text-s
    r'\btext-base\b': 'text-m',    # 16px -> text-m
    r'\btext-lg\b': 'text-l',      # 18px -> text-l
    
    # Larger sizes that should be text-xl (30px)
    r'\btext-2xl\b': 'text-xl',    # Usually for display text
    r'\btext-3xl\b': 'text-xl',
    r'\btext-4xl\b': 'text-xl',
    
    # Custom pixel sizes (common patterns)
    r'\btext-\[10px\]\b': 'text-xs',   # 10px -> 11px (text-xs)
    r'\btext-\[11px\]\b': 'text-xs',   # 11px exact
    r'\btext-\[12px\]\b': 'text-xs',   # 12px -> 11px (text-xs)
    r'\btext-\[13px\]\b': 'text-s',    # 13px -> 14px (text-s)
    r'\btext-\[14px\]\b': 'text-s',    # 14px exact
    r'\btext-\[15px\]\b': 'text-m',    # 15px -> 16px (text-m)
    r'\btext-\[16px\]\b': 'text-m',    # 16px exact
    r'\btext-\[17px\]\b': 'text-l',    # 17px -> 18px (text-l)
    r'\btext-\[18px\]\b': 'text-l',    # 18px exact
    r'\btext-\[20px\]\b': 'text-l',    # 20px -> 18px (text-l)
    r'\btext-\[24px\]\b': 'text-xl',   # 24px -> 30px (text-xl)
    r'\btext-\[30px\]\b': 'text-xl',   # 30px exact
}

# Colors to note (from project_state.md) - for reference only
APPROVED_COLORS = {
    'Green': '#37d097',
    'Dark Green': '#0d8c70',
    'Teal': '#19b097',
    'Lightest Grey': '#d4dce1',
    'Light Grey': '#aab9be',
    'Grey': '#444a4f',
    'Dark Grey': '#22252a',
    'Black': '#000000',
    'White': '#ffffff',
}

def find_non_standard_text_sizes(content, filename):
    """Find all non-standard text size classes in the content."""
    issues = []
    
    # Pattern to match text-* classes (excluding our approved ones)
    approved_pattern = r'\b(text-xs|text-s|text-m|text-l|text-xl)\b'
    text_class_pattern = r'\btext-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl|\[[^\]]+\])\b'
    
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        # Find all text-* classes
        matches = re.finditer(text_class_pattern, line)
        for match in matches:
            text_class = match.group(0)
            # Check if it's NOT one of our approved sizes
            if not re.match(approved_pattern, text_class):
                issues.append({
                    'file': filename,
                    'line': line_num,
                    'class': text_class,
                    'context': line.strip()[:80]  # First 80 chars of line
                })
    
    return issues

def replace_text_sizes(content):
    """Replace non-standard text sizes with standard ones."""
    modified_content = content
    replacements_made = []
    
    for pattern, replacement in TEXT_SIZE_REPLACEMENTS.items():
        # Find all matches before replacing
        matches = list(re.finditer(pattern, modified_content))
        if matches:
            replacements_made.append((pattern, replacement, len(matches)))
            modified_content = re.sub(pattern, replacement, modified_content)
    
    return modified_content, replacements_made

def process_file(filepath):
    """Process a single file."""
    print(f"\n{'='*80}")
    print(f"Processing: {filepath}")
    print('='*80)
    
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        return False
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Find issues before replacement
    issues = find_non_standard_text_sizes(original_content, filepath)
    
    if not issues:
        print(f"[OK] No non-standard text sizes found!")
        return True
    
    print(f"\n[*] Found {len(issues)} non-standard text size(s):")
    for issue in issues[:10]:  # Show first 10
        print(f"  Line {issue['line']}: {issue['class']}")
        print(f"    Context: {issue['context']}")
    
    if len(issues) > 10:
        print(f"  ... and {len(issues) - 10} more")
    
    # Apply replacements
    modified_content, replacements = replace_text_sizes(original_content)
    
    if replacements:
        print(f"\n[FIX] Replacements made:")
        for pattern, replacement, count in replacements:
            print(f"  {pattern} -> {replacement} ({count} occurrences)")
        
        # Write the modified content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"\n[OK] File updated successfully!")
        return True
    else:
        print(f"\n[!] No replacements possible (issues may need manual review)")
        return False

def main():
    """Main execution function."""
    print("="*80)
    print("KERNE WEBSITE TEXT SIZE STANDARDIZATION")
    print("="*80)
    print("\nApproved Text Sizes:")
    print("  text-xs  = 11px")
    print("  text-s   = 14px")
    print("  text-m   = 16px")
    print("  text-l   = 18px")
    print("  text-xl  = 30px")
    print("\nNote: Headers (h1-h4) should inherit from globals.css")
    print("      This script only targets body text classes.")
    
    print("\n" + "="*80)
    print("APPROVED COLOR PALETTE (for reference):")
    print("="*80)
    for color_name, hex_value in APPROVED_COLORS.items():
        print(f"  {color_name:20s} {hex_value}")
    
    files_processed = 0
    files_modified = 0
    
    for filepath in TARGET_FILES:
        if process_file(filepath):
            files_processed += 1
            # Count as modified if file exists
            if os.path.exists(filepath):
                files_modified += 1
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Files processed: {files_processed}/{len(TARGET_FILES)}")
    print(f"Files modified: {files_modified}")
    print("\n[OK] Standardization complete!")
    print("\nNext steps:")
    print("  1. Review changes with git diff")
    print("  2. Test pages in browser")
    print("  3. Commit changes with: git commit -m '[YYYY-MM-DD] design: Standardized text sizes across key pages'")
    print("  4. Push to mahone/m-vercel: git push mahone main")

if __name__ == "__main__":
    main()