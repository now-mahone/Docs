#!/usr/bin/env python3
"""
Update all pages to monochrome color scheme (#000000 and #ffffff only)
Based on the home page pattern established on 2026-01-22
"""

import re
from pathlib import Path

# Color mapping: old -> new
COLOR_MAPPINGS = {
    # Brand colors -> Black
    '#4c7be7': '#000000',  # Brand Blue -> Black
    '#0d33ec': '#000000',  # Deep Blue -> Black
    '#37bf8d': '#000000',  # Mint -> Black
    '#0d8c61': '#000000',  # Success Green -> Black
    '#c41259': '#000000',  # Accent Pink -> Black
    
    # Grays/neutrals -> White or Black
    '#f9f9f4': '#ffffff',  # Off-white -> Pure White
    '#f1f1ed': '#000000',  # Light border -> Black border
    '#737581': '#000000',  # Muted text -> Black text
    '#191919': '#000000',  # Dark gray -> Black
    '#1f1f1f': '#000000',  # Dark gray -> Black
    
    # Muted colors -> White or Black
    '#edf2fd': '#ffffff',  # Muted Blue -> White
    '#ebf9f4': '#ffffff',  # Muted Green -> White
}

# Pages to update (excluding page.tsx which is already done)
PAGES_TO_UPDATE = [
    'frontend/src/app/transparency/page.tsx',
    'frontend/src/app/institutional/page.tsx',
    'frontend/src/app/referrals/page.tsx',
    'frontend/src/app/litepaper/page.tsx',
    'frontend/src/app/privacy/page.tsx',
    'frontend/src/app/terms/page.tsx',
    'frontend/src/app/cookies/page.tsx',
]

def update_colors_in_file(filepath: Path) -> tuple[int, str]:
    """Update all color references in a file. Returns (num_changes, content)"""
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    changes = 0
    
    # Replace each color
    for old_color, new_color in COLOR_MAPPINGS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(old_color), re.IGNORECASE)
        matches = pattern.findall(content)
        if matches:
            content = pattern.sub(new_color, content)
            changes += len(matches)
    
    # Update file header comment to add "Monochrome: 2026-01-22"
    if '// Created:' in content and 'Monochrome: 2026-01-22' not in content:
        content = re.sub(
            r'(// Created:.*?)(\n)',
            r'\1 | Monochrome: 2026-01-22\2',
            content,
            count=1
        )
    
    return changes, content

def main():
    """Update all pages to monochrome scheme"""
    root = Path(__file__).parent
    total_changes = 0
    
    print("Converting pages to monochrome color scheme (#000000 and #ffffff)...\n")
    
    for page_path in PAGES_TO_UPDATE:
        filepath = root / page_path
        if not filepath.exists():
            print(f"[!] {page_path} - NOT FOUND")
            continue
        
        changes, new_content = update_colors_in_file(filepath)
        
        if changes > 0:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"[+] {page_path} - {changes} color references updated")
            total_changes += changes
        else:
            print(f"[-] {page_path} - Already monochrome")
    
    print(f"\n[DONE] {total_changes} total color references updated across {len(PAGES_TO_UPDATE)} pages")

if __name__ == '__main__':
    main()
