#!/usr/bin/env python3
"""
Build the final iTerm2 3.6.11 translation file from:
  - TM-covered locations (worklist_tm.json + tm.json), skipping identity entries
  - Manual translations (worklist_manual.json + manual_translations.json)
  - Manual overrides win over TM.
Output format (repo-compatible): {nib: {"idx.key": "zh"}}
"""

import json
import os

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

tm = json.load(open('/tmp/tm.json'))
manual_trans = json.load(open(PROJ + '/manual_translations.json'))
worklist_tm = json.load(open('/tmp/worklist_tm.json'))
worklist_manual = json.load(open('/tmp/worklist_manual.json'))

final = {}
applied = 0
skipped_identity = 0
untranslated_manual = []


def add(loc, zh):
    global applied
    nib, key = loc.split('\x1f')
    final.setdefault(nib, {})[key] = zh
    applied += 1


for en, locs in worklist_tm.items():
    zh = manual_trans.get(en) or tm.get(en)
    if zh is None or zh == en:
        skipped_identity += len(locs)
        continue
    for loc in locs:
        add(loc, zh)

for en, locs in worklist_manual.items():
    zh = manual_trans.get(en)
    if zh is None:
        untranslated_manual.append(en)
        continue
    for loc in locs:
        add(loc, zh)

with open(PROJ + '/translations_3.6.11.json', 'w') as f:
    json.dump(final, f, ensure_ascii=False, indent=1)

print(f"Final entries: {applied} across {len(final)} nibs")
print(f"Skipped (identity/untranslated): {skipped_identity}")
print(f"Manual worklist left in English ({len(untranslated_manual)}):")
for s in untranslated_manual:
    print(f"  {s!r}")
