#!/usr/bin/env python3
"""
Full string extractor: dump EVERY DATA-bytes string from all .nib files in a
directory, keyed by object index + key name. No visibility filtering.

Usage: python3 full_extract.py <dir_with_nibs> <output.json>
Output: {nib_name: {"obj_idx.key_name": "string"}}
"""

import json
import os
import sys

from nibarchive import NIBArchiveParser, NIBValueType


def extract_nib(nib_path):
    parser = NIBArchiveParser()
    with open(nib_path, 'rb') as f:
        nib = parser.parse(f)

    strings = {}
    for obj_idx, obj in enumerate(nib.objects):
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
                except Exception:
                    continue
                if s:
                    strings[f"{obj_idx}.{key_name}"] = s
    return strings


def main():
    nib_dir = sys.argv[1]
    out_path = sys.argv[2]
    result = {}
    total = 0
    for name in sorted(os.listdir(nib_dir)):
        if not name.endswith('.nib'):
            continue
        path = os.path.join(nib_dir, name)
        try:
            strings = extract_nib(path)
            result[name] = strings
            total += len(strings)
        except Exception as e:
            print(f"ERROR {name}: {e}", file=sys.stderr)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"Extracted {total} strings from {len(result)} nibs -> {out_path}",
          file=sys.stderr)


if __name__ == '__main__':
    main()
