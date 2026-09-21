<div align="center">

# 🇨🇳 iTerm2 简体中文汉化补丁(双层方案)

[![License](https://img.shields.io/badge/license-GPLv2-blue)](LICENSE)
[![iTerm2](https://img.shields.io/badge/iTerm2-3.6.11-green)](https://iterm2.com/)
[![nib](https://img.shields.io/badge/nib_层-1421_条-blueviolet)](#-翻译覆盖范围)
[![Runtime](https://img.shields.io/badge/运行时词典-1543_条-orange)](#-翻译覆盖范围)
[![Platform](https://img.shields.io/badge/macOS-arm64_%2B_x86__64-lightgrey)](#-支持环境)

面向 **iTerm2 3.6.11** 的完整界面汉化补丁，与 [iTerm2 官方项目](https://github.com/gnachman/iTerm2) 无关

**双层方案**:NIBArchive 二进制补丁 + 运行时翻译 dylib 注入，
覆盖菜单栏、设置面板(含全部高级设置)、对话框、标签右键菜单、**终端内右键菜单**、通知等

</div>

---

## 📖 目录

- [✨ 方案概述](#-方案概述)
- [✅ 支持环境](#-支持环境)
- [🚀 安装](#-安装)
- [🗑️ 卸载](#️-卸载)
- [📊 翻译覆盖范围](#-翻译覆盖范围)
- [🔧 词典变更后重建 dylib](#-词典变更后重建-dylib)
- [⚠️ 已知限制](#️-已知限制)
- [📐 翻译原则](#-翻译原则)
- [📁 项目结构](#-项目结构)
- [🤖 AI / 开发者参考](#-ai--开发者参考)
- [🔒 安全说明](#-安全说明)
- [🙏 致谢](#-致谢)
- [📄 许可证](#-许可证)

## ✨ 方案概述

iTerm2 的界面文字分两类存放，单一手段无法覆盖，因此本项目分两层实现:

### 第一层:nib 静态补丁

窗口、设置面板等界面布局存放在 **NIBArchive** 二进制 nib 文件中。
本层解析 nib、替换其中的字符串数据并重新序列化(`scripts/nib_patch.py`):

1. 从官方 iTerm2 3.6.6 提取 nib 英文字符串
2. 与上游翻译记忆库 `all_translations.json`(70 组 / 2317 条)按索引对接，
   得到经校验的"英文 → 中文"记忆库
3. 按**字符串内容**(而非索引)匹配 3.6.11 的全部界面字符串
4. 记忆库未覆盖的字符串人工补译(`manual_translations.json`,28 条)
5. 校验占位符(`%@`、`%d` 等)一致后才应用

**产出**:`translations_3.6.11.json`(67 个 nib / 1421 条)

### 第二层:运行时翻译 dylib

大量文字**硬编码在程序代码里**(nib 补丁无法触及):高级设置全部 455 条、
标签右键菜单、终端内右键菜单(含「终端状态」子菜单、图片/文件菜单、命令信息弹窗)、
退出确认对话框、运行时动态生成的对话框等。本层用 Method Swizzling 在运行时
拦截 AppKit 的字符串设置方法并查表翻译:

- `iTermZhPatch.dylib` 经 `LC_LOAD_DYLIB` 注入主程序(`scripts/inject_dylib.py`，自研无三方依赖)，启动即加载
- 内嵌运行时词典 `translations_merged.json`(**1543 条**，含正则模板)
- 拦截点:`NSMenuItem / NSMenu / NSWindow / NSControl / NSCell / NSAlert /
  NSTabViewItem / NSToolbarItem / NSSegmentedControl` 的 `setTitle`、
  `setStringValue`、`setAttributedStringValue`、`setMessageText`、
  `addButtonWithTitle`、`setLabel`、`setToolTip`、`addItemWithTitle` 等
- 富文本按 run 翻译，保留各段原有字号(高级设置表中 8pt 分隔行 / 13pt 名称 /
  11pt 描述不再互相污染)
- 兼容 `itemWithTitle:`、`indexOfItemWithTitle:` 等按英文标题查找的内部调用，
  翻译后查找仍然有效
- 对 macOS 26 设置窗口右上搜索栏图标/文字不居中的上游缺陷
  (iTerm2 issue 12708)做了 cell 级垂直居中校正

> 两层配合后，界面文字基本实现 100% 中文。

## ✅ 支持环境

| 项 | 要求 |
|----|------|
| iTerm2 | **3.6.11**(已测试) |
| 系统 | macOS(实测 macOS 26 / Darwin 25.5.0) |
| 架构 | arm64 + x86_64(通用二进制) |
| 依赖 | Python 3(系统自带或 Homebrew)、clang(Xcode 命令行工具) |
| 权限 | 修改 `/Applications/iTerm.app` 需要管理员权限(脚本会提示 `sudo`) |

iTerm2 安装位置不是 `/Applications/iTerm.app` 时，用环境变量 `ITERM_APP` 指定:

```bash
ITERM_APP=/path/to/iTerm.app bash scripts/install.sh
```

## 🚀 安装

```bash
git clone https://hub.ifunx.com/skyle1995/iTerm2_Chinese.git
cd iTerm2_Chinese
bash scripts/install.sh
```

安装脚本自动完成 5 步:

1. 🐍 创建 Python 虚拟环境(`build/venv`)并安装 `nibarchive`
2. 💾 备份原始 nib 到 `.backup-nibs/`，应用第一层汉化补丁(出错自动恢复)
3. 🔨 由词典生成 shim 源码并构建通用 dylib(`build/iTermZhPatch.dylib`)
4. 💉 安装 dylib 并注入主程序(注入前备份为 `iTerm2.orig-backup`)
5. ✍️ ad-hoc 重签名(dylib + 主程序)

安装完成后**完全退出 iTerm2(`Command+Q`)再重新打开**即可看到中文界面。

> 说明:运行中的 iTerm2 在启动时就把 dylib 载入内存了，所以必须重启一次才生效。

## 🗑️ 卸载

```bash
bash scripts/uninstall.sh
```

脚本依次:恢复 nib 备份 → 删除 dylib → 恢复原始主程序(移除 `LC_LOAD_DYLIB` 注入)
→ ad-hoc 重签名。**`.backup-nibs/` 与 `iTerm2.orig-backup` 是卸载依赖，请勿删除。**

## 📊 翻译覆盖范围

<div align="center">

| 层 | 数据文件 | 规模 |
|----|----------|------|
| 第一层:nib 静态补丁 | `translations_3.6.11.json` | **67** 个 nib / **1421** 条 |
| 第二层:运行时词典 | `translations_merged.json` | **1543** 条(含正则模板) |
| 翻译记忆库(原料) | `all_translations.json` | 70 组 / 2317 条 |
| 人工补译 | `manual_translations.json` | 28 条 |

</div>

覆盖范围包括:

- 🍎 菜单栏(文件、编辑、视图、窗口等)
- ⚙️ 设置面板全部标签页，含**全部 455 条高级设置**
- 💬 对话框与提示信息、退出确认对话框
- 🖱️ 标签右键菜单、**终端内右键菜单**(含「终端状态」子菜单、图片/文件菜单、命令信息弹窗、拷贝 toast)
- 🔧 工具栏、⌨️ 快捷键设置
- 🔔 通知与状态栏

### 两类内容**不翻译**(设计如此，非遗漏)

1. **用户数据**:配置文件名称(如 `Default`)、智能选择自定义动作标题
2. **具体值**:命令信息弹窗中的命令 / 路径 / 返回码数值(只翻译标签，值保留)

## 🔧 词典变更后重建 dylib

```bash
python3 scripts/gen_shim.py            # 读 translations_merged.json → build/zh_shim.m
clang -dynamiclib -framework Cocoa -arch arm64 -arch x86_64 -O2 \
      -o build/iTermZhPatch.dylib build/zh_shim.m

# 退出 iTerm2 后安装
cp build/iTermZhPatch.dylib /Applications/iTerm.app/Contents/Frameworks/
codesign -f -s - /Applications/iTerm.app/Contents/Frameworks/iTermZhPatch.dylib
codesign -f -s - /Applications/iTerm.app/Contents/MacOS/iTerm2
open -a iTerm
```

补充新字符串的推荐流程:

1. 用 `scripts/full_extract.py` / `scripts/nib_extract.py` 提取新版字符串
2. 对比现有词典，把缺失条目加入 `translations_merged.json`
   (右键菜单等代码硬编码文案可用 `scripts/merge_ctx_menu.py`、`scripts/merge_adv.py` 合并，二者幂等)
3. 重建 dylib 并重装(上面的命令)

> 词典中带占位符(`%@` / `%d`)的条目，翻译值统一用 `%@` 作分隔(gen_shim 按 `%@` 切分值)。
> 多行键(`名称\n描述`)会在运行时自动拆出首行/尾行两份子条目，以适配高级设置表的富文本分段。

## ⚠️ 已知限制

- 设置窗口工具栏右上搜索栏在 macOS 26 上图标+占位文字略偏上:这是上游 iTerm2
  issue 12708 的缺陷，官方 workaround 与本项目的 cell 级居中钩子均无法完全消除
  (偏移发生在工具栏私有视图布局层)。不影响功能，仅视觉偏差
- `Shell` 菜单名保留英文(Apple 官方终端中文版同样保留，属惯例)
- 个别系统级注入文案(如「允许通知」权限弹窗)来自 macOS，不翻译
- **iTerm2 升级后需重新应用**:先 `bash scripts/uninstall.sh` 再 `bash scripts/install.sh`
- 词典未收录的新字符串会保持英文显示，补充词典后重建 dylib 即可
- 安装会移除原有代码签名并改为本地 ad-hoc 签名，不影响正常使用

## 📐 翻译原则

- 📘 遵循 [Apple 官方中文本地化术语](https://developer.apple.com/cn/localization/)
- 🏷️ iTerm 品牌名保持英文
- 💻 技术术语(Shell、Terminal、xterm 等)保持英文
- ⌨️ 功能键、修饰键保持英文
- 🔣 格式化占位符(`%@`、`%d` 等)保持不变
- 🔗 代码硬编码文案的措辞与主菜单 nib 层保持一致(如「仿真级别」「粘贴括号模式」)

## 📁 项目结构

```
iTerm2_Chinese/
├── 📄 README.md                     # 本文件
├── 📄 README_完整汉化.md             # 双层方案详细说明
├── 📄 METHODOLOGY.md                # 本地化方法论(面向 AI/开发者)
├── 📄 LICENSE                       # GPLv2
├── 📄 all_translations.json         # 翻译记忆库(70 组 / 2317 条，原料)
├── 📄 translations_3.6.11.json      # 第一层:nib 层翻译数据(67 个 nib / 1421 条)
├── 📄 translations_merged.json      # 第二层:运行时词典(1543 条，核心资产)
├── 📄 manual_translations.json      # 人工补译(28 条)
├── 📂 scripts/
│   ├── install.sh                   # 一键安装(两层 + 注入 + 重签名)
│   ├── uninstall.sh                 # 一键卸载(完整还原)
│   ├── nib_patch.py                 # NIBArchive 补丁核心工具
│   ├── nib_extract.py               # nib 字符串提取
│   ├── patch_all.py                 # 批量 nib 补丁(记忆库版)
│   ├── apply_full.py                # 应用 3.6.11 nib 补丁(含备份校验与回滚)
│   ├── full_extract.py              # nib 全量字符串提取
│   ├── build_tm.py / build_final.py # 翻译记忆库构建 / nib 层数据生成
│   ├── gen_shim.py                  # 词典 → dylib 源码 build/zh_shim.m
│   ├── inject_dylib.py              # Mach-O LC_LOAD_DYLIB 注入工具(自研)
│   ├── merge_adv.py                 # 高级设置 157 条 + 退出对话框合并(幂等)
│   ├── merge_ctx_menu.py            # 终端右键菜单 74 条合并(幂等)
│   └── analyze*.py / extract_*.py / apply_pass*.py / verify_tm.py  # 分析与校验工具
├── 📂 .backup-nibs/                 # 原始英文 nib 备份(卸载依赖，勿删)
└── 📄 .gitignore
```

安装期还会产生两个备份(勿删，卸载依赖):

- `/Applications/iTerm.app/Contents/MacOS/iTerm2.orig-backup` — 注入前的主程序
- `/Applications/iTerm.app/Contents/Frameworks/iTermZhPatch.dylib` — 已安装的 dylib

## 🤖 AI / 开发者参考

> 本节为 AI 编程助手(Claude Code、Cursor、DSH 等)提供技术细节。

### 💡 原理

iTerm2 不使用 macOS 标准的 Base Internationalization，界面文本直接存在
**NIBArchive** 二进制中;另一部分则硬编码在 Objective-C/Swift 代码内。
本项目分别用 nib 二进制补丁与运行时 Method Swizzling 覆盖这两类文本。

### 🔨 手动部署

```bash
# 1. 虚拟环境
python3 -m venv build/venv
build/venv/bin/pip install nibarchive

# 2. 备份原始 nib(首次执行)
mkdir -p .backup-nibs
for f in /Applications/iTerm.app/Contents/Resources/*.nib; do
    cp "$f" ".backup-nibs/$(basename "$f")"
done

# 3. 第一层:nib 补丁
build/venv/bin/python3 scripts/apply_full.py

# 4. 第二层:构建并注入 dylib
python3 scripts/gen_shim.py build/zh_shim.m
clang -dynamiclib -framework Cocoa -arch arm64 -arch x86_64 -O2 \
      -o build/iTermZhPatch.dylib build/zh_shim.m
cp build/iTermZhPatch.dylib /Applications/iTerm.app/Contents/Frameworks/
python3 scripts/inject_dylib.py \
      '@executable_path/../Frameworks/iTermZhPatch.dylib' \
      /Applications/iTerm.app/Contents/MacOS/iTerm2

# 5. 重签名
codesign -f -s - /Applications/iTerm.app/Contents/Frameworks/iTermZhPatch.dylib
codesign -f -s - /Applications/iTerm.app/Contents/MacOS/iTerm2
```

### 🔄 跟进 iTerm2 新版本

1. 提取新版字符串:`build/venv/bin/python3 scripts/nib_extract.py new_strings.json`
2. 与 `all_translations.json` / `translations_merged.json` 对比，找出新增/变更项
3. 翻译新增条目并更新数据文件
4. 重新 `bash scripts/install.sh`

### ❓ 常见问题

<details>
<summary><b>安装后 iTerm2 无法启动?</b></summary>

运行 `bash scripts/uninstall.sh` 完整还原(恢复 nib、删除 dylib、恢复主程序)，
再检查是否有重签名错误。

</details>

<details>
<summary><b>安装后部分文字仍是英文?</b></summary>

该字符串尚未收录进词典。把确切英文文案加入 `translations_merged.json`，
重建 dylib 即可(见「词典变更后重建」)。终端内右键菜单可直接用
`scripts/merge_ctx_menu.py` 合并。

</details>

<details>
<summary><b>重启后还是不生效?</b></summary>

必须**完全退出** iTerm2(`Command+Q`)而非关闭窗口，dylib 在启动时载入。
可确认是否加载:`vmmap $(pgrep -x iTerm2 | head -1) | grep -i iTermZhPatch`

</details>

<details>
<summary><b>如何查看翻译数据?</b></summary>

`all_translations.json` 结构为 `{nib文件名: {对象索引.属性名: 翻译文本}}`;
`translations_merged.json` 是运行时的扁平 `{英文: 中文}` 词典。

</details>

> 📚 详细方案说明见 [README_完整汉化.md](README_完整汉化.md)，
> 技术方法论见 [METHODOLOGY.md](METHODOLOGY.md)

## 🔒 安全说明

- nib 补丁只替换文本字符串，不改动任何逻辑
- dylib 只做字符串查表替换，**无网络、无文件写入、无逻辑修改**
- 主程序注入前已备份(`iTerm2.orig-backup`)，卸载脚本完整还原
- 所有修改使用 ad-hoc 本地签名

## 🙏 致谢

- [gnachman/iTerm2](https://github.com/gnachman/iTerm2) — 上游软件(GPLv2)
- [Loveacup/iTerm2-zh-CN](https://github.com/Loveacup/iTerm2-zh-CN) —
  翻译记忆库 `all_translations.json` 与 nib 补丁工具链来源
- 本项目在其基础上扩展为**双层方案**，跟进至 iTerm2 3.6.11，
  并补齐高级设置、标签右键菜单、终端内右键菜单等运行时文案

## 📄 许可证

本项目基于 [GPLv2](LICENSE) 许可证发布，与 [iTerm2](https://github.com/gnachman/iTerm2) 保持一致。
