#!/usr/bin/env python3
"""
Script to standardize border-radius values to rounded-sm throughout the Kerne frontend.
Converts rounded-md, rounded-lg, rounded-xl to rounded-sm.
Preserves rounded-full for circular elements like icons.
"""

import os
import re
from pathlib import Path

# Define the frontend directory
FRONTEND_DIR = Path("frontend/src")

# Border radius mappings (what to replace)
RADIUS_REPLACEMENTS = {
    r'\brounded-md\b': 'rounded-sm',
    r'\brounded-lg\b': 'rounded-sm',
    r'\brounded-xl\b': 'rounded-sm',
    r'\brounded-2xl\b': 'rounded-sm',
    r'\brounded-3xl\b': 'rounded-sm',
}

# Extensions to process
EXTENSIONS = ['.tsx', '.ts', '.jsx', '.js']

def should_process_file(file_path):
    """Check if file should be processed."""
    return file_path.suffix in EXTENSIONS and not file_path.name.startswith('.')

def process_file(file_path):
    """Process a single file and return number of replacements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        total_replacements = 0
        
        # Apply all replacements
        for pattern, replacement in RADIUS_REPLACEMENTS.items():
            content, count = re.subn(pattern, replacement, content)
            total_replacements += count
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return total_replacements
        
        return 0
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def main():
    """Main execution function."""
    print("=" * 80)
    print("KERNE BORDER RADIUS STANDARDIZATION SCRIPT")
    print("=" * 80)
    print(f"\nScanning directory: {FRONTEND_DIR}")
    print(f"\nReplacements to make:")
    for pattern, replacement in RADIUS_REPLACEMENTS.items():
        print(f"  {pattern} -> {replacement}")
    print(f"\nPreserving: rounded-full (for circular elements)")
    print("\n" + "=" * 80 + "\n")
    
    total_files_processed = 0
    total_replacements = 0
    files_modified = []
    
    # Walk through all files
    for root, dirs, files in os.walk(FRONTEND_DIR):
        # Skip node_modules and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        
        for file in files:
            file_path = Path(root) / file
            
            if should_process_file(file_path):
                replacements = process_file(file_path)
                if replacements > 0:
                    total_files_processed += 1
                    total_replacements += replacements
                    relative_path = file_path.relative_to(FRONTEND_DIR)
                    files_modified.append((relative_path, replacements))
                    print(f"[OK] {relative_path}: {replacements} replacement(s)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files modified: {total_files_processed}")
    print(f"Total replacements: {total_replacements}")
    
    if files_modified:
        print(f"\nModified files:")
        for file_path, count in sorted(files_modified):
            print(f"  - {file_path} ({count} changes)")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] Border radius standardization complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()