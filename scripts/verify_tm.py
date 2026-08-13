#!/usr/bin/env python3
"""
Verify translation memory safety before applying:
1. Placeholder preservation: %@, %d, %lld, %1$@ ... must match between en/zh
2. List identity entries (en == zh)
3. Only check entries actually used by the 3.6.11 worklist
"""

import json
import re

tm = json.load(open('/tmp/tm.json'))
worklist = json.load(open('/tmp/worklist_tm.json'))

PLACEHOLDER = re.compile(r'%\d+\$[@diuoxXfFeEgGcspCSPaAF@]|%[@diuoxXfFeEgGcspCSPaAF]')

problems = []
identity = []
for en in worklist:
    zh = tm.get(en)
    if zh is None:
        continue
    if en == zh:
        identity.append(en)
        continue
    en_ph = sorted(PLACEHOLDER.findall(en))
    zh_ph = sorted(PLACEHOLDER.findall(zh))
    if en_ph != zh_ph:
        problems.append((en, zh, en_ph, zh_ph))

print(f"Used TM entries: {len(worklist)}")
print(f"Identity (untranslated on purpose): {len(identity)}")
print(f"Placeholder mismatches: {len(problems)}")
print()
for en, zh, ep, zp in problems:
    print(f"EN: {en!r}  ph={ep}")
    print(f"ZH: {zh!r}  ph={zp}")
    print()
