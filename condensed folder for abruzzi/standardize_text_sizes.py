#!/usr/bin/env python3
"""
Standardize all text sizes to use custom sizing system from globals.css
Based on the home page pattern established on 2026-01-22
"""

import re
from pathlib import Path

# Text size mapping: Tailwind default -> Custom size
TEXT_SIZE_MAPPINGS = {
    'text-sm': 'text-s',      # 14px (text-sm → text-s)
    'text-lg': 'text-l',      # 18px (text-lg → text-l)
    'text-base': 'text-m',    # 16px (text-base → text-m)
    # xs, xl already use custom names
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
    'frontend/src/app/about/page.tsx',
]

def update_text_sizes_in_file(filepath: Path) -> tuple[int, str]:
    """Update all text size references in a file. Returns (num_changes, content)"""
    content = filepath.read_text(encoding='utf-8')
    changes = 0
    
    # Replace each text size using word boundaries to avoid partial matches
    for old_size, new_size in TEXT_SIZE_MAPPINGS.items():
        # Use word boundary to match complete class names only
        pattern = re.compile(r'\b' + re.escape(old_size) + r'\b')
        matches = pattern.findall(content)
        if matches:
            content = pattern.sub(new_size, content)
            changes += len(matches)
    
    return changes, content

def main():
    """Update all pages to use custom text sizes"""
    root = Path(__file__).parent
    total_changes = 0
    
    print("Standardizing text sizes to custom system (xs, s, m, l, xl)...\n")
    
    for page_path in PAGES_TO_UPDATE:
        filepath = root / page_path
        if not filepath.exists():
            print(f"[!] {page_path} - NOT FOUND")
            continue
        
        changes, new_content = update_text_sizes_in_file(filepath)
        
        if changes > 0:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"[+] {page_path} - {changes} text size references updated")
            total_changes += changes
        else:
            print(f"[-] {page_path} - Already standardized")
    
    print(f"\n[DONE] {total_changes} total text size references updated across {len(PAGES_TO_UPDATE)} pages")

if __name__ == '__main__':
    main()
