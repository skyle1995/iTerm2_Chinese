#!/usr/bin/env python3
"""
Second pass: patch strings missed by the noise filter (lowercase-starting UI
text). Locates them in the clean baseline extraction and patches in place.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from nib_patch import patch_nib

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES = '/Applications/iTerm.app/Contents/Resources'

PASS2_KEYS = [
    'iTerm2 Help',
    'modifyOtherKeys Mode 1',
    'modifyOtherKeys Mode 2',
    'fn Function',
    'tmux Integration:',
    'fn key:',
    'tmux Dashboard',
    'macOS Keychain',
    'ex: 0x7f',
    'xxx lines, xxx bytes.',
    'iTerm2 integrates with the major LLM providers for various AI features. <a href="$3">Learn more here</a>.\n\niTerm2 is currently configured to use $4. You can change your AI provider in Settings > General > AI.\n\nBefore you can use this feature, you’ll need an API key. If you don’t already have one, you’ll need to <a href="$1">create an account</a> and <a href="$2">generate an API</a>. Then enter it below:',
]

manual = json.load(open(PROJ + '/manual_translations.json'))
english = json.load(open('/tmp/english_full.json'))

by_nib = {}
for nib, strings in english.items():
    for key, val in strings.items():
        if val in PASS2_KEYS and val in manual:
            by_nib.setdefault(nib, {})[key] = manual[val]

total = 0
for nib, trans in sorted(by_nib.items()):
    path = os.path.join(RESOURCES, nib)
    count = patch_nib(path, trans, path)
    total += count
    print(f"  OK {nib}: {count} strings patched")

print(f"Total: {total} strings patched")
