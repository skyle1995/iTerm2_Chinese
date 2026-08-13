#!/usr/bin/env python3
"""Merge terminal context-menu (right-click menu) translations into
translations_merged.json. Idempotent: skips keys already present.
Also validates template entries (placeholder count must match)."""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT = os.path.join(HERE, 'translations_merged.json')

# Strings built at runtime by iTermTextViewContextMenuHelper.m /
# PseudoTerminal.m / PTYTextView+ARC.m / iTermContextMenuUtilities.m
# (iTerm2 v3.6.11 sources). Wording follows the nib-layer translations
# where the same strings appear in the main menu.
ADDITIONS = {
    # ---- 主右键菜单:拷贝/粘贴/选择 ----
    "Paste": "粘贴",
    "Select All": "全选",
    "Send Selection": "发送所选内容",
    "Save Selection as Snippet": "将所选内容存储为片段",
    "Clear Buffer": "清除缓冲区",
    "Annotate Selection": "为所选内容添加注释",
    "Reveal Annotation": "显示注释",
    # ---- 会话操作 ----
    "Edit Session...": "编辑会话…",          # 源码用三个点,与词典中省略号版并存
    "Toggle Broadcasting Input": "切换广播输入",
    "Stop Coprocess": "停止协处理",
    "Restart": "重新启动",
    # ---- 拆分/移动/交换 ----
    "Split Pane Vertically": "垂直拆分窗格",
    "Split Pane Horizontally": "水平拆分窗格",
    "Move Session to Split Pane": "将会话移动到拆分窗格",
    "Swap With Session…": "与会话交换…",
    # ---- 选区动作 ----
    "Open Selection as URL": "将所选内容作为 URL 打开",
    "Open URL in Vertical Split Pane": "在垂直拆分窗格中打开 URL",
    "Open URL in Horizontal Split Pane": "在水平拆分窗格中打开 URL",
    "Quick Look Link": "快速查看链接",
    "Search the Web for Selection": "在网络上搜索所选内容",
    "Send Email to Selected Address": "向所选地址发送邮件",
    # ---- 下载 ----
    "Download with scp": "使用 scp 下载",
    "Download using SSH Integration": "使用 SSH 集成下载",
    "Download with scp from %@": "使用 scp 从 %@ 下载",
    "Download using SSH Integration from %@": "使用 SSH 集成从 %@ 下载",
    # ---- 图片/文件右键菜单 ----
    "Save File As…": "文件另存为…",
    "Copy File": "拷贝文件",
    "Open File": "打开文件",
    "Inspect": "检查",
    "Save Image As…": "图像另存为…",
    "Copy Image": "拷贝图像",
    "Open Image": "打开图像",
    "Resume Animating": "继续播放动画",
    "Stop Animating": "停止播放动画",
    # ---- 选区替换 ----
    "Replace with Pretty-Printed JSON": "替换为格式化 JSON",
    "Replace with Base64-Decoded Value": "替换为 Base64 解码值",
    "Replace with Base64-Encoded Value": "替换为 Base64 编码值",
    # ---- 终端状态子菜单(与主菜单 nib 层措辞一致) ----
    "Alternate Screen": "备用屏幕",
    "Focus Reporting": "焦点报告",
    "Mouse Reporting": "鼠标报告",
    "Paste Bracketing": "粘贴括号模式",
    "Application Cursor": "应用程序光标",
    "Application Keypad": "应用程序键盘",
    "Standard Key Reporting Mode": "标准按键报告模式",
    "modifyOtherKeys Mode 1": "modifyOtherKeys 模式 1",
    "modifyOtherKeys Mode 2": "modifyOtherKeys 模式 2",
    "CSI u Mode": "CSI u 模式",
    "Raw Key Reporting Mode": "原始按键报告模式",
    "Disambiguate Escape": "消歧义 Escape",
    "Report All Event Types": "报告所有事件类型",
    "Report Alternate Keys": "报告替代按键",
    "Report All Keys as Escape Codes": "将所有按键报告为转义码",
    "Report Associated Text": "报告关联文本",
    "Literal Controls": "字面控制字符",
    "Emulation Level": "仿真级别",
    # ---- 命令信息弹出菜单(模板) ----
    "Command: %@": "命令：%@",
    "Directory: %@": "目录：%@",
    "Return code: %d": "返回码：%@",
    "Running time: %d:%02d:%02d": "运行时长：%@:%@:%@",
    "Running time: %d:%02d.%03d": "运行时长：%@:%@.%@",
    # ---- 拷贝提示 toast ----
    "Copied": "已拷贝",
    "Command Copied": "已拷贝命令",
    "Output Copied": "已拷贝输出",
    # ---- 选区换算菜单(iTermContextMenuUtilities) ----
    "Copy Base64-Decoded": "拷贝 Base64 解码结果",
    "Copy Base64-Encoded": "拷贝 Base64 编码结果",
    "Base64: %@": "Base64：%@",
    "Big-Endian int32: %@": "大端 int32：%@",
    "Little-Endian int32: %@": "小端 int32：%@",
    "Big-Endian int64: %@": "大端 int64：%@",
    "Little-Endian int64: %@": "小端 int64：%@",
    "%@ UTF-8 bytes: %@": "UTF-8 字节（%@ 个）：%@",
    "%@ hex bytes": "%@ 个十六进制字节",
    "Unix timestamp %@": "Unix 时间戳 %@",
    "“%@” = %@ = %@ (UTF-8)": "“%@” = %@ = %@（UTF-8）",
}

PLACEHOLDER = re.compile(r'%\d*\$?[@dlfuxs]')


def main():
    with open(DICT, encoding='utf-8') as f:
        trans = json.load(f)

    added = skipped = 0
    for k, v in ADDITIONS.items():
        if k in trans:
            print(f'  SKIP 已存在: {k!r} -> {trans[k]!r}')
            skipped += 1
            continue
        if '%' in k:
            nkey = len(PLACEHOLDER.findall(k))
            nval = v.count('%@')
            if nkey == 0 or nkey != nval:
                print(f'  ERR 占位符不匹配: {k!r} (键 {nkey} 个, 值 {nval} 个)')
                sys.exit(1)
        trans[k] = v
        added += 1

    with open(DICT, 'w', encoding='utf-8') as f:
        json.dump(trans, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'合并完成: 新增 {added} 条, 跳过 {skipped} 条, 词典共 {len(trans)} 条')


if __name__ == '__main__':
    main()
