# iTerm2 3.6.11 完整简体中文汉化包(双层方案)

本目录包含针对 **iTerm2 3.6.11** 的完整界面汉化数据与工具。汉化分两层实现,
两层配合后,界面文字(菜单、设置窗口含全部 455 条高级设置、对话框、
标签右键菜单、终端内右键菜单、通知等)基本实现 100% 中文。

## 方案概述

### 第一层:nib 静态补丁(界面布局文件)

iTerm2 的窗口、设置面板等界面布局存放在 nib 文件中。本层把 nib 内的
英文字符串替换为中文:

1. 下载官方 iTerm2 3.6.6,提取其 nib 英文字符串
2. 与 Loveacup/iTerm2-zh-CN 项目的 `all_translations.json` 按索引对接,
   得到经过验证的"英文 → 中文"翻译记忆库(1667 条)
3. 按字符串内容(而非索引)匹配 3.6.11 的全部界面字符串
4. 翻译记忆未覆盖的字符串人工补译(`manual_translations.json`)
5. 占位符(%@、%d 等)一致性校验通过后才应用

### 第二层:运行时翻译 dylib(代码硬编码字符串)

大量文字硬编码在程序代码中(nib 补丁无法触及):高级设置全部 455 条、
标签右键菜单、终端内右键菜单(含「终端状态」子菜单、图片/文件菜单、
命令信息弹窗等)、退出确认对话框、运行时动态生成的对话框等。本层通过
Method Swizzling 在运行时拦截 AppKit 的字符串设置方法并翻译:

- `iTermZhPatch.dylib` 经 `LC_LOAD_DYLIB` 注入 iTerm2 主程序,启动即加载
- 内嵌完整翻译词典(`translations_merged.json`,1543 条,含正则模板)
- 拦截点:`NSMenuItem/NSMenu/NSWindow/NSControl/NSCell/NSAlert/
  NSTabViewItem/NSToolbarItem/NSSegmentedControl` 的 setTitle、
  setStringValue、setAttributedStringValue、setMessageText、
  addButtonWithTitle、setLabel、setToolTip、addItemWithTitle 等
- 富文本按 run 翻译,保留各段原有字号(高级设置表中 8pt 分隔行、
  13pt 名称、11pt 描述不再互相污染)
- 对 `itemWithTitle:`、`indexOfItemWithTitle:` 等按英文标题查找的内部调用
  做了兼容,翻译后查找仍然有效
- 对 macOS 26 设置窗口右上搜索栏图标/文字不居中的上游缺陷
  (iTerm2 issue 12708)做了 cell 级垂直居中校正(延迟到主队列安装,
  钩住 `iTermPrefsSearchFieldCell` 的 `titleRectForBounds:` /
  `searchButtonRectForBounds:` / `drawingRectForBounds:`);在部分系统
  版本上可改善,见「已知限制」

## 文件说明

| 文件 | 用途 |
|------|------|
| `translations_merged.json` | 运行时词典主数据(1543 条,核心资产) |
| `translations_3.6.11.json` | nib 层翻译数据 |
| `manual_translations.json` | 人工补译条目(3.6.11 新增字符串) |
| `scripts/install.sh` | 一键安装(nib 补丁 + dylib 构建与注入;全相对路径,项目可随意移动) |
| `scripts/apply_full.py` | 应用 nib 补丁(含备份保护,出错自动恢复) |
| `scripts/gen_shim.py` | 由词典生成 dylib 源码 `build/zh_shim.m` |
| `scripts/inject_dylib.py` | Mach-O `LC_LOAD_DYLIB` 注入工具(自研,无第三方依赖) |
| `scripts/merge_adv.py` | 高级设置 157 条 + 退出对话框等翻译合并脚本 |
| `scripts/merge_ctx_menu.py` | 终端右键菜单 74 条翻译合并脚本(幂等) |
| `scripts/uninstall.sh` | 一键卸载(nib + dylib + 主程序备份全部恢复) |
| `scripts/full_extract.py` | nib 全量字符串提取工具 |
| `scripts/build_tm.py` | 翻译记忆库构建工具 |
| `scripts/build_final.py` | nib 层翻译数据生成工具 |
| `.backup-nibs/` | 原始英文 nib 备份(卸载依赖,勿删) |

另有两个安装期产生的备份(勿删,卸载依赖):

- `/Applications/iTerm.app/Contents/MacOS/iTerm2.orig-backup` — 注入前的原始主程序
- `/Applications/iTerm.app/Contents/Frameworks/iTermZhPatch.dylib` — 已安装的 dylib

## 安装 / 重建

所有脚本的路径都相对脚本自身位置推导,项目目录移动到任何地方都能直接
运行;iTerm2 的系统安装位置可用环境变量 `ITERM_APP` 覆盖(默认
`/Applications/iTerm.app`)。

```bash
bash scripts/install.sh     # 一键:nib 补丁 + dylib 构建/注入/重签名
```

词典变更后只重建 dylib:

```bash
python3 scripts/gen_shim.py            # 读本目录 translations_merged.json → build/zh_shim.m
clang -dynamiclib -framework Cocoa -arch arm64 -arch x86_64 -O2 \
      -o build/iTermZhPatch.dylib build/zh_shim.m
# 退出 iTerm2 后安装
cp build/iTermZhPatch.dylib "$ITERM_APP/Contents/Frameworks/"   # 默认 /Applications/iTerm.app
codesign -f -s - "$ITERM_APP/Contents/Frameworks/iTermZhPatch.dylib"
codesign -f -s - "$ITERM_APP/Contents/MacOS/iTerm2"
open -a iTerm
```

注意:词典中带占位符(%@/%d 等)的条目,翻译值里统一用 `%@` 作分隔
(gen_shim 按 `%@` 切分值)。多行键(`名称\n描述`)会在运行时自动拆出
首行/尾行两份子条目,以适配高级设置表的富文本分段。

## 卸载汉化

```bash
cd /Volumes/Device/Project/Python/iTerm2_Chinese
bash scripts/uninstall.sh
```

脚本依次:恢复 nib 备份 → 删除 dylib → 恢复原始主程序(移除
LC_LOAD_DYLIB 注入)→ ad-hoc 重签名。

## 已知限制

- 设置窗口工具栏右上搜索栏在本机系统(macOS 26 / Darwin 25.5.0)上
  图标+占位文字略偏上:这是上游 iTerm2 issue 12708 的缺陷,实测其
  3.6.11 的 workaround 与我们的 cell 级居中钩子在该系统版本上均无法
  完全消除(偏移发生在工具栏私有视图布局层,22pt 搜索域被置于
  ~36pt 胶囊顶部;强行改私有视图布局风险大,经用户同意跳过)。
  不影响功能,仅视觉偏差
- `Shell` 菜单名保留英文(Apple 自家终端中文版同样保留,属惯例)
- 个别系统注入文案(如「允许通知」权限弹窗)来自 macOS,不翻译
- iTerm2 更新后需重新应用:先 `uninstall.sh` 再重新安装
- 词典未收录的新字符串会保持英文显示,补充词典后重建 dylib 即可

## 安全说明

- nib 补丁只替换文本字符串,不动任何逻辑
- dylib 只做字符串查表替换,无网络、无文件写入、无逻辑修改
- 主程序注入前已备份(`iTerm2.orig-backup`),卸载脚本完整还原
- 所有修改使用 ad-hoc 重签名

## 其他说明

为实现某些功能验证,曾通过 defaults 关闭过会话恢复相关选项
(`runJobsInServers`、`multiserver`、`useRestorableStateController`)。
如需恢复原状:

```bash
defaults delete com.googlecode.iterm2 runJobsInServers
defaults delete com.googlecode.iterm2 multiserver
defaults delete com.googlecode.iterm2 useRestorableStateController
```
