#!/usr/bin/env python3
"""Extract all NIBArchive class names from every .nib in a directory."""

import json
import os
import sys

from nibarchive import NIBArchiveParser


def main():
    nib_dir = sys.argv[1]
    out_path = sys.argv[2]
    names = set()
    for name in sorted(os.listdir(nib_dir)):
        if not name.endswith('.nib'):
            continue
        try:
            parser = NIBArchiveParser()
            with open(os.path.join(nib_dir, name), 'rb') as f:
                nib = parser.parse(f)
            for cn in nib.class_names:
                names.add(cn.name)
        except Exception as e:
            print(f"ERROR {name}: {e}", file=sys.stderr)
    with open(out_path, 'w') as f:
        json.dump(sorted(names), f, indent=1)
    print(f"{len(names)} class names -> {out_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
