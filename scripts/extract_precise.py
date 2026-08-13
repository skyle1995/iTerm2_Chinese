#!/usr/bin/env python3
"""
Precise extraction: only string literals passed directly to UI APIs.
Handles multi-line calls by scanning full text with regex per API.
"""

import json
import os
import re

SRC = '/tmp/iterm2-src/sources'

# (name, regex) — capture the literal inside the API call
OBJC_APIS = [
    ('menuitem_init', r'initWithTitle:\s*@"((?:[^"\\]|\\.)*)"'),
    ('menu_add', r'addItemWithTitle:\s*@"((?:[^"\\]|\\.)*)"'),
    ('alert_button', r'addButtonWithTitle:\s*@"((?:[^"\\]|\\.)*)"'),
    ('msg_text', r'(?:set)?[Mm]essageText[:=]\s*@"((?:[^"\\]|\\.)*)"'),
    ('info_text', r'(?:set)?[Ii]nformativeText[:=]\s*@"((?:[^"\\]|\\.)*)"'),
    ('set_title', r'setTitle:\s*@"((?:[^"\\]|\\.)*)"'),
    ('win_title', r'windowWithTitle:\s*@"((?:[^"\\]|\\.)*)"'),
    ('tooltip', r'setToolTip:\s*@"((?:[^"\\]|\\.)*)"'),
    ('seg_label', r'setLabel:\s*@"((?:[^"\\]|\\.)*)"'),
    ('placeholder', r'setPlaceholderString:\s*@"((?:[^"\\]|\\.)*)"'),
    ('tab_label', r'setLabel:\s*@"((?:[^"\\]|\\.)*)"'),
    ('stringvalue', r'setStringValue:\s*@"((?:[^"\\]|\\.)*)"'),
    ('help', r'setHelp:\s*@"((?:[^"\\]|\\.)*)"'),
]
SWIFT_APIS = [
    ('menuitem_init', r'NSMenuItem\(\s*title:\s*"((?:[^"\\]|\\.)*)"'),
    ('title_assign', r'\.title\s*=\s*"((?:[^"\\]|\\.)*)"'),
    ('button_title', r'NSButton\(title:\s*"((?:[^"\\]|\\.)*)"'),
    ('msg_text', r'messageText\s*=\s*"((?:[^"\\]|\\.)*)"'),
    ('info_text', r'informativeText\s*=\s*"((?:[^"\\]|\\.)*)"'),
    ('alert_button', r'addButton\(withTitle:\s*"((?:[^"\\]|\\.)*)"'),
    ('win_title', r'window\.title\s*=\s*"((?:[^"\\]|\\.)*)"'),
    ('tooltip', r'toolTip\s*=\s*"((?:[^"\\]|\\.)*)"'),
    ('swiftui_text', r'Text\("((?:[^"\\]|\\.)*)"'),
    ('label_arg', r'label:\s*"((?:[^"\\]|\\.)*)"'),
]


def unescape(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            out.append({'n': '\n', 't': '\t', '"': '"', '\\': '\\',
                        "'": "'", 'r': '\r'}.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


results = {}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for fn in files:
        if fn.endswith('.m'):
            apis = OBJC_APIS
        elif fn.endswith('.swift'):
            apis = SWIFT_APIS
        else:
            continue
        path = os.path.join(root, fn)
        try:
            text = open(path, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        for api_name, rx in apis:
            for m in re.finditer(rx, text):
                s = unescape(m.group(1))
                if len(s) < 1:
                    continue
                results.setdefault(s, set()).add(fn)

with open('/tmp/precise_strings.json', 'w') as f:
    json.dump({k: sorted(v) for k, v in sorted(results.items())}, f,
              ensure_ascii=False, indent=1)
print(f"Precise UI strings: {len(results)}")
