#!/usr/bin/env python3
"""
Extract user-visible hardcoded strings from iTerm2 source.

Strategy:
1. Contextual extraction: string literals on lines containing UI API calls
   (menu items, titles, alerts, tooltips, labels...) — high precision.
2. Full extraction from known UI files (context menus, advanced settings).
3. Advanced settings descriptions parsed specially (category splitting like
   the app does at display time).

Output: /tmp/source_ui_strings.json  {string: [files]}
"""

import json
import os
import re

SRC = '/tmp/iterm2-src/sources'

OBJC_LIT = re.compile(r'@"((?:[^"\\]|\\.)*)"')
SWIFT_LIT = re.compile(r'(?<![A-Za-z0-9_#])"((?:[^"\\]|\\.)*)"')

UI_MARKERS = [
    'initWithTitle:', 'addItemWithTitle:', 'itemWithTitle:', 'setTitle:',
    'setStringValue:', 'messageText', 'informativeText', 'addButtonWithTitle',
    'setToolTip:', 'setLabel:', 'setPaletteLabel:', 'setPlaceholderString:',
    'windowWithTitle:', 'NSMenuItem(', 'title =', 'title:', '.title',
    'beginSheetModal', 'runModal', 'Text("', 'label:', 'NSButton(title',
    'placeholder =', 'helpText', 'setHeaderTitle', 'tabViewItem setLabel',
    'setLabel:', 'showAlert', 'alert', 'window.title',
]

# Files known to build UI in code
UI_FILES = {
    'PseudoTerminal.m',
    'iTermTextViewContextMenuHelper.m',
    'MainMenuMangler.swift',
    'iTermAdvancedSettingsModel.m',
    'PTYSession.m',
    'iTermStatusBar.m',
}

CJK = re.compile(r'[一-鿿]')


def unescape(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            mapping = {'n': '\n', 't': '\t', '"': '"', '\\': '\\', "'": "'", 'r': '\r'}
            out.append(mapping.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def plausible(s):
    if len(s) < 2 or len(s) > 140:
        return False
    if CJK.search(s):
        return False
    if not any(c.isalpha() for c in s):
        return False
    if s[0] in '_.~/@#' or s.startswith(('kPref', 'com.', 'http', 'NS', 'IB')):
        return False
    if '://' in s or '\t' in s:
        return False
    # pure identifier (no spaces, no punctuation other than ._-)
    if re.match(r'^[A-Za-z][A-Za-z0-9._-]*$', s) and ' ' not in s:
        # allow single CamelCase words only if short (menu titles like Profiles)
        if len(s) > 16 or s[0].islower():
            return False
    if s.endswith(':') and ' ' not in s and len(s) < 30 and re.match(r'^[a-zA-Z]+:', s):
        # selector-like or label-like? keep labels like "Command:" (has upper)
        if s[0].islower():
            return False
    return True


results = {}


def add(s, where):
    if not plausible(s):
        return
    results.setdefault(s, set()).add(where)


def process_file(path, force_all):
    fn = os.path.basename(path)
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return
    is_swift = fn.endswith('.swift')
    rx = SWIFT_LIT if is_swift else OBJC_LIT
    for lineno, line in enumerate(lines, 1):
        lits = OBJC_LIT.findall(line) if not is_swift else SWIFT_LIT.findall(line)
        if not lits:
            continue
        contextual = force_all or any(m in line for m in UI_MARKERS)
        if contextual:
            for lit in lits:
                add(unescape(lit), fn)


for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for fn in files:
        if not fn.endswith(('.m', '.swift')):
            continue
        path = os.path.join(root, fn)
        process_file(path, fn in UI_FILES)

# ---- Advanced settings: parse SECTION_ macros + DEFINE_* descriptions ----
adv_path = os.path.join(SRC, 'Settings', 'iTermAdvancedSettingsModel.m')
adv_text = open(adv_path, encoding='utf-8').read()
sections = dict(re.findall(r'#define\s+(SECTION_\w+)\s+@"([^"]*)"', adv_text))
adv_categories = set()
adv_names = []
for sec_macro, desc_lit in re.findall(
        r'(SECTION_\w+)\s*@"((?:[^"\\]|\\.)*)"', adv_text):
    prefix = sections.get(sec_macro, '')
    desc = unescape(desc_lit)
    full = prefix + desc
    colon = full.find(':')
    if colon >= 0:
        adv_categories.add(full[:colon])
        rest = full[colon + 2:]
    else:
        rest = full
    adv_names.append(rest)
    # the table shows first line; detail shows the rest
    if '\n' in rest:
        first, _, remainder = rest.partition('\n')
        adv_names.append(first)
        adv_names.append(remainder)

with open('/tmp/source_ui_strings.json', 'w') as f:
    json.dump({k: sorted(v) for k, v in sorted(results.items())}, f,
              ensure_ascii=False, indent=1)
with open('/tmp/adv_settings.json', 'w') as f:
    json.dump({'categories': sorted(adv_categories), 'names': adv_names}, f,
              ensure_ascii=False, indent=1)

print(f"UI string candidates: {len(results)}")
print(f"Advanced settings: {len(adv_names)} names, {len(adv_categories)} categories")
