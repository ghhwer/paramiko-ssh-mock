#!/usr/bin/env python3
"""
Script to update README.md with coverage badge
"""

import re
import sys
from pathlib import Path


def update_readme_with_coverage():
    """Update README.md with coverage badge"""
    
    readme_path = Path("README.md")
    
    if not readme_path.exists():
        print("ERROR: README.md not found")
        return False
    
    # Read current README content
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Coverage badge markdown
    coverage_badge = "![Coverage](coverage.svg)"
    
    # Pattern to find the sponsor badge section
    sponsor_pattern = r'(\[\!\[.*\]\(https://img\.shields\.io/static/v1\?label=Sponsor.*\)\]\(https://github\.com/sponsors/ghhwer\))'
    
    # Pattern to find existing coverage badge
    existing_coverage_pattern = r'!\[Coverage\]\(coverage\.svg\)'
    
    # Remove existing coverage badge if it exists
    content = re.sub(existing_coverage_pattern, '', content)
    
    # Clean up any extra blank lines left from removing the badge
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Add coverage badge after sponsor badge
    if re.search(sponsor_pattern, content):
        # Add coverage badge after sponsor badge
        content = re.sub(sponsor_pattern, r'\1\n\n' + coverage_badge, content)
        print("Added coverage badge after sponsor badge")
    else:
        # If sponsor badge not found, add after the title
        title_pattern = r'(# Paramiko Mock\n)'
        if re.search(title_pattern, content):
            content = re.sub(title_pattern, r'\1\n\n' + coverage_badge + '\n', content)
            print("Added coverage badge after title")
        else:
            print("WARNING: Could not find appropriate place to add coverage badge")
            return False
    
    # Write updated README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("README.md updated successfully with coverage badge")
    return True


if __name__ == "__main__":
    success = update_readme_with_coverage()
    sys.exit(0 if success else 1)
