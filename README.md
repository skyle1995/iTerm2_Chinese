# iTerm2 简体中文汉化包

为 [iTerm2](https://iterm2.com/) 提供简体中文界面翻译。

iTerm2 官方不支持中文界面，本项目通过 macOS 标准本地化机制（`.lproj`）实现菜单栏、设置面板、对话框等主要界面元素的汉化。

## 支持版本

- iTerm2 **3.6.6**（已测试）
- 理论上兼容 3.x 系列其他版本

## 安装

```bash
git clone https://github.com/Loveacup/iTerm2-zh-CN.git
cd iTerm2-zh-CN
bash scripts/install.sh
```

安装完成后，完全退出 iTerm2（Command+Q）再重新打开即可。

> 前提：macOS 系统语言需包含简体中文。如未设置，请前往「系统设置 → 通用 → 语言与地区」添加。

## 卸载

```bash
cd iTerm2-zh-CN
bash scripts/uninstall.sh
```

## 翻译覆盖范围

| 文件 | 内容 | 条目数 |
|------|------|--------|
| MainMenu.strings | 菜单栏（文件、编辑、显示、窗口等） | 57 |
| iTerm.strings | 对话框、通知、提示信息 | 122 |
| PreferencePanel.strings | 设置面板 | 158 |
| AddressBook.strings | 配置文件/书签管理 | 92 |
| configPanel.strings | 配置面板 | 19 |
| UKCrashReporter.strings | 崩溃报告 | 13 |
| PseudoTerminal.strings | 终端窗口 | 1 |

**共计约 462 条翻译**，覆盖主要用户界面元素。

## 已知限制

- 部分界面文本在代码中硬编码，无法通过 `.strings` 文件翻译
- iTerm2 更新后需要重新运行安装脚本
- 安装过程会移除 iTerm2 的代码签名并重新进行本地签名（ad-hoc signing），不影响正常使用
- 翻译基于 macOS 官方术语标准，个别翻译可能与使用习惯不同

## 翻译原则

- 遵循 [Apple 官方中文本地化术语](https://developer.apple.com/cn/localization/)
- iTerm 品牌名保持英文
- 技术术语（Shell、Terminal、xterm 等）保持英文
- 功能键（F1-F20）、修饰键（Shift、Control 等）保持英文
- 格式化占位符（%@、%d 等）保持不变

## 项目结构

```
iTerm2-zh-CN/
├── zh-Hans.lproj/          # 翻译后的 .strings 文件
├── strings-original/       # 原始英文 .strings（JSON 格式，供参考）
├── scripts/
│   ├── install.sh          # 安装脚本
│   └── uninstall.sh        # 卸载脚本
└── README.md
```

## AI 部署指南

如果你使用 AI 编程助手（如 Claude Code、Cursor 等）来帮你安装本汉化包，可以直接给它以下指令：

> 帮我安装 iTerm2 中文汉化包，仓库地址 https://github.com/Loveacup/iTerm2-zh-CN

### 技术细节（供 AI 参考）

本项目通过 macOS 标准 `.lproj` 本地化机制工作，无需重新编译 iTerm2。部署流程：

1. **克隆仓库**: `git clone https://github.com/Loveacup/iTerm2-zh-CN.git`
2. **复制翻译文件**: 将 `zh-Hans.lproj/` 目录复制到 `/Applications/iTerm.app/Contents/Resources/`（需 sudo）
3. **修改 Info.plist**: 用 `/usr/libexec/PlistBuddy` 在 `/Applications/iTerm.app/Contents/Info.plist` 中添加 `CFBundleLocalizations` 数组，包含 `en` 和 `zh-Hans`
4. **重签名**: `codesign --force --deep --sign - /Applications/iTerm.app`
5. **重启 iTerm2**: 用户需完全退出（Command+Q）再重新打开

也可以直接运行 `bash scripts/install.sh` 一键完成以上步骤。

### 更新翻译流程

当 iTerm2 发布新版本时，可能需要更新翻译：

1. 从新版 iTerm2 提取 `.strings` 文件：
   ```bash
   for f in /Applications/iTerm.app/Contents/Resources/*.strings; do
       plutil -convert json -o "strings-original/$(basename "${f%.strings}.json")" "$f"
   done
   ```
2. 对比 `strings-original/` 中的新旧 JSON，找出新增/变更的 key
3. 翻译新增条目，更新 `zh-Hans.lproj/` 中对应的 `.strings` 文件
4. 重新运行 `bash scripts/install.sh`

### .strings 文件格式规范

```
/* 注释（可选） */
"English Key" = "中文翻译";
```

- 编码：UTF-8 或 UTF-16LE
- 每行一个键值对，分号结尾
- key 必须与原始 `.strings` 文件中的 key 完全一致
- 保留 `%@`、`%d`、`\n` 等格式化占位符

## 贡献

欢迎提交 Pull Request 改进翻译质量。编辑 `zh-Hans.lproj/` 下的 `.strings` 文件即可。

`.strings` 文件格式：
```
"English Key" = "中文翻译";
```

## 许可证

MIT License
