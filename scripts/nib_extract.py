#!/usr/bin/env python3
"""
Extract localizable strings from all iTerm2 .nib files.
Outputs JSON mapping of {nib_name: {object_id.key: string_value}}.
"""

import json
import sys
import os

from nibarchive import NIBArchiveParser, NIBValueType

# Properties that represent user-visible strings
LOCALIZABLE_KEYS = {
    'NSTitle', 'NSLabel', 'NSWindowTitle', 'NSPlaceholderString',
    'NSHeaderTitle', 'NSPrompt', 'NSMessage', 'NSInformativeText',
    'NSAlternateContents', 'NSToolTip',
}

# Also extract NS.bytes which contains all string content
ALWAYS_EXTRACT = {'NS.bytes'}

# Strings that are NOT user-visible (IBOutlet names, class names, etc.)
SKIP_PATTERNS = [
    '_', 'NS', 'IB', 'submenuAction:', '.', 'action', 'delegate',
]


def is_user_visible(key_name, value_str, class_name):
    """Determine if a string is likely user-visible UI text."""
    # Skip empty or very short
    if not value_str or len(value_str) < 2:
        return False
    # Skip if it looks like an internal identifier
    if value_str.startswith('_') or value_str.startswith('NS'):
        return False
    if ':' in value_str and value_str.endswith(':'):  # selectors like "performAction:"
        return False
    if value_str.startswith('IB') or value_str.startswith('iB'):
        return False
    # Skip class names
    if not ' ' in value_str and value_str[0].isupper() and any(c.isupper() for c in value_str[1:]) and not any(c == ' ' for c in value_str):
        # CamelCase without spaces - likely a class name, but check for common menu items
        simple_words = {'Bookmarks', 'Profiles', 'Services', 'Window', 'Terminal',
                       'Keyboard', 'Display', 'General', 'Appearance', 'Keys',
                       'Triggers', 'Console', 'Manage', 'Separator', 'Selection'}
        if value_str not in simple_words and len(value_str) > 15:
            return False
    # Skip image names
    if value_str.startswith('NSImage') or value_str.startswith('NSMenu'):
        return False
    # Must contain at least one letter
    if not any(c.isalpha() for c in value_str):
        return False
    return True


def extract_nib(nib_path):
    """Extract localizable strings from a single nib file."""
    parser = NIBArchiveParser()
    with open(nib_path, 'rb') as f:
        nib = parser.parse(f)

    strings = {}
    for obj_idx, obj in enumerate(nib.objects):
        cn = nib.class_names[obj.class_name_index].name
        vals_start = obj.values_index
        vals_count = obj.value_count

        for vi in range(vals_start, vals_start + vals_count):
            if vi >= len(nib.values):
                break
            val = nib.values[vi]
            key_name = nib.keys[val.key_index].name

            if val.type == NIBValueType.DATA and isinstance(val.data, bytes):
                try:
                    s = val.data.decode('utf-8').rstrip('\x00')
                except:
                    continue

                if is_user_visible(key_name, s, cn):
                    obj_key = f"{obj_idx}.{key_name}"
                    strings[obj_key] = s

    return strings


def main():
    iterm_resources = '/Applications/iTerm.app/Contents/Resources'
    nib_files = [f for f in os.listdir(iterm_resources) if f.endswith('.nib')]

    all_strings = {}
    total = 0

    for nib_name in sorted(nib_files):
        nib_path = os.path.join(iterm_resources, nib_name)
        try:
            strings = extract_nib(nib_path)
            if strings:
                all_strings[nib_name] = strings
                total += len(strings)
                print(f"  {nib_name}: {len(strings)} strings", file=sys.stderr)
        except Exception as e:
            print(f"  {nib_name}: ERROR - {e}", file=sys.stderr)

    print(f"\nTotal: {total} strings from {len(all_strings)} nib files", file=sys.stderr)

    # Output JSON
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_strings, f, ensure_ascii=False, indent=2)
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(json.dumps(all_strings, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
