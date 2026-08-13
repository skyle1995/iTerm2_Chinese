#!/usr/bin/env python3
"""
Build the final work list of user-visible English strings in iTerm2 3.6.11
that need translation, with strict noise filtering.

Inputs: /tmp/english_full.json (3.6.11 clean strings), /tmp/classnames.json
Optional TM: /tmp/tm.json ({"english": "chinese"}) from iTerm2 3.6.6 project.

Outputs:
  /tmp/worklist_manual.json  - {english: [locations]} needing fresh translation
  /tmp/worklist_tm.json      - {english: [locations]} covered by translation memory
"""

import json
import os
import re

with open('/tmp/english_full.json') as f:
    english = json.load(f)
classnames = set(json.load(open('/tmp/classnames.json')))
CJK = re.compile(r'[一-鿿]')

TM_PATH = '/tmp/tm.json'
tm = {}
if os.path.exists(TM_PATH):
    tm = json.load(open(TM_PATH))

SELECTOR = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:$')
LOWER_ID = re.compile(r'^[a-z].*')
FRAME = re.compile(r'^\{\{')
AX = re.compile(r'^AX[A-Z]')
PURE_TOKEN = re.compile(r'^[A-Za-z][A-Za-z0-9]*$')
FONTISH = re.compile(r'(Font|Mono|Regular|Bold|Italic|Medium|Light|Thin|Black|Oblique|Condensed|Powerline|Nerd|Pro|Book|Roman|For Powerline)$')


def noise(s):
    if len(s) < 2:
        return True
    if not any(c.isalpha() for c in s):
        return True
    if CJK.search(s):
        return True
    if s[0] in '_.~/':
        return True
    if s.startswith(('NS', 'IB', 'com.', 'dyn.', 'http')):
        return True
    if '://' in s or 'pasteboard type' in s:
        return True
    if SELECTOR.match(s):
        return True
    if LOWER_ID.match(s):          # IB outlets, identifiers, selectors
        return True
    if FRAME.match(s):             # NSRect / NSPoint strings
        return True
    if AX.match(s):                # accessibility identifiers
        return True
    if ' ' not in s:
        if '.' in s:               # dotted identifiers, domains
            return True
        if len(s) > 18:            # long single tokens
            return True
        if FONTISH.search(s):      # font face names
            return True
    if s in classnames:            # ObjC class names
        return True
    return False


manual = {}
covered = {}
for nib, strings in english.items():
    for key, val in strings.items():
        if noise(val):
            continue
        loc = nib + '\x1f' + key
        target = covered if val in tm else manual
        target.setdefault(val, []).append(loc)

manual = dict(sorted(manual.items(), key=lambda kv: (-len(kv[1]), kv[0])))
covered = dict(sorted(covered.items(), key=lambda kv: (-len(kv[1]), kv[0])))

with open('/tmp/worklist_manual.json', 'w') as f:
    json.dump(manual, f, ensure_ascii=False, indent=1)
with open('/tmp/worklist_tm.json', 'w') as f:
    json.dump(covered, f, ensure_ascii=False, indent=1)

print(f"Manual translation needed: {len(manual)} unique "
      f"({sum(len(v) for v in manual.values())} locations)")
print(f"TM covered: {len(covered)} unique "
      f"({sum(len(v) for v in covered.values())} locations)")
