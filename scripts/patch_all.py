#!/usr/bin/env python3
"""
Patch all iTerm2 .nib files with Chinese translations.
Reads translations from all_translations.json and patches each nib file.
"""

import json
import sys
import os
import shutil

sys.path.insert(0, '/tmp/nibenv/lib/python3.12/site-packages')

# Import our patcher
sys.path.insert(0, os.path.dirname(__file__))
from nib_patch import patch_nib

ITERM_RESOURCES = '/Applications/iTerm.app/Contents/Resources'
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, '.backup-nibs')
TRANS_FILE = os.path.join(PROJECT_DIR, 'all_translations.json')


def main():
    # Load translations
    with open(TRANS_FILE) as f:
        all_trans = json.load(f)

    print(f"Loaded translations for {len(all_trans)} nib files")
    print()

    # Backup and patch each nib
    os.makedirs(BACKUP_DIR, exist_ok=True)

    total_patched = 0
    errors = []

    for nib_name, translations in sorted(all_trans.items()):
        nib_path = os.path.join(ITERM_RESOURCES, nib_name)

        if not os.path.exists(nib_path):
            print(f"  SKIP {nib_name} (not found)")
            continue

        # Backup if not already backed up
        backup_path = os.path.join(BACKUP_DIR, nib_name)
        if not os.path.exists(backup_path):
            shutil.copy2(nib_path, backup_path)

        # Patch
        try:
            count = patch_nib(nib_path, translations, nib_path)
            total_patched += count
            print(f"  OK {nib_name}: {count} strings patched")
        except Exception as e:
            errors.append((nib_name, str(e)))
            # Restore from backup on error
            shutil.copy2(backup_path, nib_path)
            print(f"  ERR {nib_name}: {e}")

    print()
    print(f"Total: {total_patched} strings patched across {len(all_trans)} nibs")
    if errors:
        print(f"Errors: {len(errors)}")
        for name, err in errors:
            print(f"  {name}: {err}")

    # Re-sign
    print()
    print("Re-signing iTerm2...")
    os.system('codesign --force --deep --sign - /Applications/iTerm.app 2>/dev/null')
    print("Done! Restart iTerm2 to see changes.")


if __name__ == '__main__':
    main()
