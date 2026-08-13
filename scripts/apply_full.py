#!/usr/bin/env python3
"""
Apply translations_3.6.11.json to the installed iTerm2 nibs.
Same patching logic as patch_all.py but uses the complete 3.6.11 translation.
Originals must already be backed up in .backup-nibs/ (verified before running).
"""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
from nib_patch import patch_nib

ITERM_RESOURCES = os.path.join(
    os.environ.get('ITERM_APP', '/Applications/iTerm.app'), 'Contents', 'Resources')
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, '.backup-nibs')
TRANS_FILE = os.path.join(PROJECT_DIR, 'translations_3.6.11.json')


def main():
    with open(TRANS_FILE) as f:
        all_trans = json.load(f)

    print(f"Loaded translations for {len(all_trans)} nib files")

    total_patched = 0
    errors = []

    for nib_name, translations in sorted(all_trans.items()):
        nib_path = os.path.join(ITERM_RESOURCES, nib_name)
        if not os.path.exists(nib_path):
            print(f"  SKIP {nib_name} (not found)")
            continue

        backup_path = os.path.join(BACKUP_DIR, nib_name)
        if not os.path.exists(backup_path):
            print(f"  ERR {nib_name}: no backup, refusing to patch")
            errors.append((nib_name, 'no backup'))
            continue

        try:
            count = patch_nib(nib_path, translations, nib_path)
            total_patched += count
            print(f"  OK {nib_name}: {count} strings patched")
        except Exception as e:
            errors.append((nib_name, str(e)))
            shutil.copy2(backup_path, nib_path)
            print(f"  ERR {nib_name}: {e} (restored from backup)")

    print()
    print(f"Total: {total_patched} strings patched across {len(all_trans)} nibs")
    if errors:
        print(f"Errors: {len(errors)}")
        for name, err in errors:
            print(f"  {name}: {err}")
        sys.exit(1)


if __name__ == '__main__':
    main()
