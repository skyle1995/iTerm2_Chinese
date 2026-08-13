#!/usr/bin/env python3
"""
Build verified translation memory from iTerm2 3.6.6.

all_translations.json maps {nib: {"idx.key": zh}} for iTerm2 3.6.6.
english_366.json maps {nib: {"idx.key": en}} extracted from real 3.6.6 nibs.
Join them -> {en: zh} translation memory, string-based (index-shift safe).
"""

import json
import os

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open('/tmp/english_366.json') as f:
    en366 = json.load(f)
with open(PROJ + '/all_translations.json') as f:
    trans = json.load(f)

tm = {}
joined = 0
skipped_no_en = 0
conflicts = 0
for nib, entries in trans.items():
    en_strings = en366.get(nib, {})
    for key, zh in entries.items():
        en = en_strings.get(key)
        if not en:
            skipped_no_en += 1
            continue
        joined += 1
        if en in tm and tm[en] != zh:
            conflicts += 1
            continue
        tm[en] = zh

with open('/tmp/tm.json', 'w') as f:
    json.dump(tm, f, ensure_ascii=False, indent=1)

print(f"TM entries: {len(tm)}")
print(f"Joined: {joined}, no-english-found: {skipped_no_en}, conflicts: {conflicts}")
