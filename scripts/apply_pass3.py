#!/usr/bin/env python3
"""
Pass 3: patch strings missed by the original noise filter:
  - selector-looking labels (Directory:, Model:, ...)
  - lowercase-starting labels (seconds, rows, interval, ...)
  - font-face-looking words that are real UI (Regular, Light, Black)
  - dotted title (Preferences...)
  - shared title/identifier strings -> clone NSString so identifier keeps
    its English value (needed by MainMenuMangler icon lookup)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nibarchive import NIBArchiveParser, NIBValueType, NIBValue, NIBObject
from nib_patch import serialize_nib

RES = '/Applications/iTerm.app/Contents/Resources'

# nib -> {obj_index: translation}
PATCHES = {
    'AdvancedWorkingDirectoryWindow.nib': {
        36: '目录:',
    },
    'BulkCopyProfilePreferences.nib': {
        80: '网页',
    },
    'CommandInfoViewController.nib': {
        16: '命令:',
        89: '目录:',
        145: '输出:',
    },
    'FindView.nib': {28: '搜索'},
    'MiniFilterViewController.nib': {44: '搜索'},
    'MinimalFindView.nib': {29: '搜索'},
    'PreferencePanel.nib': {
        580: '目录:',
        940: '桌面 1', 942: '桌面 2', 944: '桌面 3', 946: '桌面 4',
        948: '桌面 5', 950: '桌面 6', 952: '桌面 7', 954: '桌面 8',
        956: '桌面 9',
        1519: '操作:',
        1544: '参数:',
        1583: '用力点按',
        1622: '修饰键:',
        1733: '参数:',
        1763: '标题:',
        1966: '前导键:',
        2312: '模型:',
        2600: 'API:',
        2608: '功能:',
        2612: 'URL:',
        2851: '性能:',
        2882: 'Bonjour:',
        2899: '许可:',
        2903: '插件:',
        2928: '超时:',
        2932: '秒',
        3071: '粘贴:',
        3083: '选择:',
        3087: '访问:',
        3091: '复制:',
        3115: '标题:',
        3123: '调整大小:',
        3162: '剪贴板:',
        3166: '暂停:',
        3174: '配置文件:',
        3178: '附加:',
        3191: '秒用于追赶',
        3337: '列 ×',
        3388: '行',
        3396: '屏幕:',
        3404: '桌面:',
        3412: '样式:',
        3426: '点高',
        3430: '点宽 ×',
        3458: '透明度:',
        3512: '模糊:',
        3529: '混合:',
        3581: '间隔',
        3866: '触发器:',
        4070: '时间戳:',
        4155: '每',
        4159: '杂项:',
        4174: '高度:',
        4195: '关闭时:',
        4201: '文件夹:',
        4208: '归档:',
        4212: '日志记录:',
        4220: '文件名:',
        4273: '常规',
        4283: '浅色',
        4301: '主题:',
        4324: '美化:',
        4353: '外观:',
        4363: '可见性:',
        4498: '隐私:',
        4524: '徽章:',
        4577: '标签:',
        4594: '图标:',
        4629: '命令:',
        4773: '名称:',
        5102: '环境:',
        5106: '通知:',
        5110: '响铃:',
        5122: '滚动:',
        5126: '历史记录:',
        5141: '搜索',
        5417: '焦点:',
        5421: '点击:',
        5508: '光标:',
        5579: '规范化:',
        5636: 'Unicode:',
        5652: '字体:',
        5670: '黑色',
        5870: '默认值:',
        5889: '链接:',
        5925: '编辑:',
        5990: '标签页:',
        5994: '模式:',
        6021: '下划线:',
        6041: '粗体:',
    },
    'SSHConfigurationWindow.nib': {
        18: 'SSH 集成',
    },
    'SpecialExceptionsWindowController.nib': {
        247: '至',
    },
    'iTermDependencyEditorWindowController.nib': {
        157: '脚本:',
    },
    'iTermEditKeyActionWindowController.nib': {
        47: '配置文件:',
        112: '操作:',
    },
    'iTermEditSnippetWindowController.nib': {
        100: '标题:',
        107: '标签:',
        111: '值:',
    },
    'iTermHotkeyPreferencesWindowController.nib': {
        234: '热键:',
    },
    'iTermPasswordManager.nib': {
        118: '密码:',
        125: '账户:',
    },
    'iTermPasteSpecialViewController.nib': {
        173: '为',
    },
    'iTermShellIntegrationWindowController.nib': {
        295: '将运行以下命令:\n\ncurl -L https://iterm2.com/shell_integration/install_shell_integration_and_utilities.sh | bash',
    },
    'iTermStatusBarSetupViewController.nib': {
        50: '字体:',
    },
    'iTermTipCardViewController.nib': {
        18: 'Shell 集成',
    },
}

# nib -> [(obj_index, translation)] where the NSString is shared between
# NSTitle and NSMenuItemIdentifier: clone the string for the title only.
SPLIT_PATCHES = {
    'MainMenu.nib': [
        (79, '设置...'),
        (210, '网页'),
    ],
}


def find_key_index(nib, name):
    for i, k in enumerate(nib.keys):
        if k.name == name:
            return i
    raise KeyError(name)


def find_class_index(nib, name):
    for i, c in enumerate(nib.class_names):
        if c.name == name:
            return i
    raise KeyError(name)


parser = NIBArchiveParser()

for nibname, patches in PATCHES.items():
    path = f'{RES}/{nibname}'
    with open(path, 'rb') as f:
        nib = parser.parse(f)
    n = 0
    for oi, zh in patches.items():
        o = nib.objects[oi]
        for i in range(o.value_count):
            v = nib.values[o.values_index + i]
            if isinstance(v.data, bytes):
                old = v.data.decode('utf-8', 'replace')
                v.data = zh.encode('utf-8')
                print(f'  {nibname}: obj {oi} {old!r} -> {zh!r}')
                n += 1
    with open(path, 'wb') as f:
        f.write(serialize_nib(nib))
    print(f'{nibname}: patched {n} strings')

for nibname, splits in SPLIT_PATCHES.items():
    path = f'{RES}/{nibname}'
    with open(path, 'rb') as f:
        nib = parser.parse(f)
    nsstr_ci = find_class_index(nib, 'NSString')
    bytes_ki = find_key_index(nib, 'NS.bytes')
    title_ki = find_key_index(nib, 'NSTitle')
    for oi, zh in splits:
        old = None
        for i in range(nib.objects[oi].value_count):
            v = nib.values[nib.objects[oi].values_index + i]
            if isinstance(v.data, bytes):
                old = v.data.decode('utf-8', 'replace')
        new_obj_index = len(nib.objects)
        nib.values.append(NIBValue(bytes_ki, NIBValueType.DATA, zh.encode('utf-8')))
        nib.objects.append(NIBObject(nsstr_ci, len(nib.values) - 1, 1))
        # redirect only NSTitle references to the clone
        redirected = 0
        for o2 in nib.objects:
            for i in range(o2.value_count):
                v = nib.values[o2.values_index + i]
                if (v.type == NIBValueType.OBJECT_REF and v.data == oi
                        and v.key_index == title_ki):
                    v.data = new_obj_index
                    redirected += 1
        print(f'  {nibname}: obj {oi} {old!r} -> title clone {new_obj_index} {zh!r} '
              f'(redirected {redirected} NSTitle refs; identifier unchanged)')
    with open(path, 'wb') as f:
        f.write(serialize_nib(nib))
    print(f'{nibname}: split-patched {len(splits)} strings')

print('pass3 done')
