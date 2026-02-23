#!/usr/bin/env python3
"""
Add circular borders to all Lucide icons across the Kerne website.
Maintains monochrome design (#000000, #ffffff).
"""

import re
import os
from pathlib import Path

def add_border_to_existing_circles(content):
    """Add borders to existing circular icon containers that don't have them."""
    # Pattern: circular containers without borders
    pattern = r'(<div className="[^"]*w-12 h-12[^"]*rounded-full[^"]*)(">)'
    
    def replace_func(match):
        classes = match.group(1)
        if 'border' not in classes:
            # Add border if not present
            classes = classes.replace('rounded-full', 'rounded-full border border-[#000000]')
        return classes + match.group(2)
    
    return re.sub(pattern, replace_func, content)

def wrap_standalone_icons(content):
    """Wrap standalone Lucide icons in circular containers with borders."""
    
    # List of Lucide icon components commonly used
    icons = [
        'Shield', 'Lock', 'Globe', 'BarChart3', 'Activity', 'Wallet', 'Eye', 
        'Target', 'Database', 'Cpu', 'Network', 'CheckCircle', 'CheckCircle2',
        'ShieldCheck', 'Landmark', 'TrendingDown', 'ZapOff', 'ExternalLink',
        'PieChart', 'Coins', 'BadgeCheck', 'Layers', 'ArrowRight', 'Code',
        'LineChart', 'Briefcase', 'Cookie', 'Settings', 'FileText',
        'Droplets', 'Zap', 'TrendingUp', 'Users', 'Gift', 'DollarSign',
        'Send', 'Twitter', 'Copy', 'Check', 'ChevronRight', 'Terminal',
        'Gavel', 'Scale', 'ArrowLeft'
    ]
    
    # Patterns to skip (already wrapped, inline in text, or navigation icons)
    skip_patterns = [
        r'<div[^>]*rounded-full[^>]*>[\s\S]*?<(' + '|'.join(icons) + r')',  # Already in circular container
        r'items-center gap-\d[^>]*>[\s\S]*?<(' + '|'.join(icons) + r')[^>]*size={16}',  # Inline with text (size 16 or smaller)
        r'mb-\d[^>]*flex items-center[^>]*>[\s\S]*?<(' + '|'.join(icons) + r')[^>]*size={16}',  # Headers with icons
        r'<Link[^>]*>[\s\S]*?<(' + '|'.join(icons) + r')',  # Icons inside links
        r'<button[^>]*>[\s\S]*?<(' + '|'.join(icons) + r')',  # Icons inside buttons
    ]
    
    return content

def process_file(filepath):
    """Process a single file to add circular borders to icons."""
    print(f"Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Step 1: Add borders to existing circular containers
    content = add_border_to_existing_circles(content)
    
    # Step 2: Wrap standalone icons (future enhancement)
    # content = wrap_standalone_icons(content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[+] Updated: {filepath}")
        return True
    else:
        print(f"  No changes needed: {filepath}")
        return False

def main():
    """Main execution function."""
    # Target directories
    frontend_dir = Path("frontend/src")
    
    # Find all TSX files
    tsx_files = list(frontend_dir.rglob("*.tsx"))
    
    print(f"Found {len(tsx_files)} TSX files")
    print("=" * 60)
    
    updated_count = 0
    for filepath in tsx_files:
        if process_file(filepath):
            updated_count += 1
    
    print("=" * 60)
    print(f"Completed! Updated {updated_count} files.")

if __name__ == "__main__":
    main()
