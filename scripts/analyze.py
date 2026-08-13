#!/usr/bin/env python3
"""
Compare patched nibs vs original English nibs:
1. Recover applied translation pairs (english -> chinese) where the old patch
   wrote Chinese. Save to /tmp/pairs.json as {"<nib>\x1f<idx.key>": {"en":..,"zh":..}}
2. List remaining untranslated user-visible English strings, deduplicated,
   sorted by frequency. Save to /tmp/untranslated.json
"""

import json
import re

with open('/tmp/patched_full.json') as f:
    patched = json.load(f)
with open('/tmp/english_full.json') as f:
    english = json.load(f)

CJK = re.compile(r'[一-鿿]')

pairs = {}
for nib, strings in patched.items():
    en_strings = english.get(nib, {})
    for key, val in strings.items():
        en_val = en_strings.get(key)
        if en_val is None or en_val == val:
            continue
        if CJK.search(val):
            pairs[nib + '\x1f' + key] = {'en': en_val, 'zh': val}

with open('/tmp/pairs.json', 'w') as f:
    json.dump(pairs, f, ensure_ascii=False, indent=1)

# --- remaining untranslated strings ---
# Heuristic filter for user-visible strings
SELECTOR = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:$')
def visible(s):
    if len(s) < 2 or len(s) > 120:
        return False
    if not any(c.isalpha() for c in s):
        return False
    if s.startswith('_') or s.startswith('NS') or s.startswith('IB'):
        return False
    if SELECTOR.match(s):
        return False
    if s.startswith('com.') or '://' in s or s.startswith('/'):
        return False
    # CamelCase single token without spaces, long -> likely identifier/class
    if ' ' not in s and re.match(r'^[A-Za-z][A-Za-z0-9]*$', s) and len(s) > 14:
        return False
    return True

untrans = {}
for nib, strings in english.items():
    for key, val in strings.items():
        if CJK.search(val):
            continue
        if not visible(val):
            continue
        untrans.setdefault(val, []).append(nib + '\x1f' + key)

# sort by occurrence count desc
sorted_untrans = dict(sorted(untrans.items(), key=lambda kv: -len(kv[1])))
with open('/tmp/untranslated.json', 'w') as f:
    json.dump(sorted_untrans, f, ensure_ascii=False, indent=1)

print(f"Recovered pairs: {len(pairs)}")
print(f"Unique untranslated visible strings: {len(sorted_untrans)}")
total_locs = sum(len(v) for v in sorted_untrans.values())
print(f"Total locations needing translation: {total_locs}")
