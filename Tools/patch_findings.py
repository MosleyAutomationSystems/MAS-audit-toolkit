"""
patch_findings_v2.py
Adds "line" and "parent" fields to every finding dict in all check modules.
Uses regex to match "url": url, at any indentation level.
Run from the toolkit root: python patch_findings_v2.py
"""

import os
import re

CHECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checks')


def patch_file(filepath: str) -> tuple[bool, int]:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already patched.
    if '"line":' in content or '"parent":' in content:
        return False, 0

    original = content

    # Match "url": url, with any indentation and any spacing around the colon.
    pattern = re.compile(r'( +)"url"\s*:\s*url,')

    def replacer(match):
        indent = match.group(1)
        return (
            f'{indent}"line":   getattr(element, \'sourceline\', None),\n'
            f'{indent}"parent": str(element.parent)[:80] if element.parent else "",\n'
            f'{indent}"url":      url,'
        )

    new_content, count = pattern.subn(replacer, content)

    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, count

    return False, 0


def main():
    check_files = [
        f for f in os.listdir(CHECKS_DIR)
        if f.endswith('.py') and f != '__init__.py'
    ]
    check_files.sort()

    total_modified = 0
    total_findings = 0

    for filename in check_files:
        filepath = os.path.join(CHECKS_DIR, filename)
        modified, count = patch_file(filepath)
        if modified:
            print(f"  [OK] {filename} — {count} finding(s) patched")
            total_modified += 1
            total_findings += count
        else:
            print(f"  [--] {filename} — skipped")

    print(f"\nDone. {total_modified} files modified, {total_findings} findings patched.")


if __name__ == '__main__':
    main()