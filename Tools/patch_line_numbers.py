"""
patch_line_numbers.py
Restores "line" capture using the correct variable name per finding dict.

For each finding dict, reads the "element": str(VARNAME) line to determine
the correct variable name, then replaces "line": None with
getattr(VARNAME, 'sourceline', None).

Run from toolkit root: python patch_line_numbers.py
"""

import os
import re

CHECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checks')


def patch_file(filepath: str) -> tuple[bool, int]:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    count = 0
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for "line":   None,
        if re.search(r'"line"\s*:\s*None,', line):
            # Scan backward from this line to find "element": str(VARNAME)
            var_name = None
            for j in range(i - 1, max(i - 15, -1), -1):
                m = re.search(r'"element"\s*:\s*str\((\w+)\)', lines[j])
                if m:
                    var_name = m.group(1)
                    break

            if var_name:
                indent = re.match(r'( +)', line).group(1)
                new_line = f'{indent}"line":   getattr({var_name}, \'sourceline\', None),\n'
                result.append(new_line)
                modified = True
                count += 1
            else:
                # No element variable found — keep None (landmark-style findings)
                result.append(line)
        else:
            result.append(line)

        i += 1

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(result)
        return True, count

    return False, 0


def main():
    check_files = sorted([
        f for f in os.listdir(CHECKS_DIR)
        if f.endswith('.py') and f != '__init__.py'
    ])

    total_modified = 0
    total_patched = 0

    for filename in check_files:
        filepath = os.path.join(CHECKS_DIR, filename)
        modified, count = patch_file(filepath)
        if modified:
            print(f"  [OK] {filename} — {count} line(s) restored")
            total_modified += 1
            total_patched += count
        else:
            print(f"  [--] {filename} — no match")

    print(f"\nDone. {total_modified} files modified, {total_patched} line captures restored.")


if __name__ == '__main__':
    main()