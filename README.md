# iTerm2 简体中文汉化补丁

社区维护的 iTerm2 简体中文界面汉化补丁，与 [iTerm2 官方项目](https://github.com/gnachman/iTerm2) 无关。

通过 NIBArchive 二进制补丁直接修改界面文件，实现菜单栏、设置面板、对话框等界面元素的汉化。

## 支持版本

- iTerm2 **3.6.6**（已测试）

## 安装

```bash
git clone https://github.com/Loveacup/iTerm2-zh-CN.git
cd iTerm2-zh-CN
bash scripts/install.sh
```

安装脚本会自动：
1. 创建 Python 虚拟环境并安装 `nibarchive` 依赖
2. 备份所有原始 nib 文件到 `.backup-nibs/`
3. 应用中文翻译补丁到 70 个界面文件
4. 重签名应用

安装完成后，完全退出 iTerm2（Command+Q）再重新打开即可。

**前提条件**：Python 3（macOS 自带或通过 Homebrew 安装）

## 卸载

```bash
bash scripts/uninstall.sh
```

从备份恢复所有原始 nib 文件并重签名。

## 翻译覆盖范围

- **70 个 nib 文件**，共 **2317 条翻译**
- 覆盖：菜单栏、设置面板（所有标签页）、对话框、工具栏、快捷键设置等

## 已知限制

- 部分文本在 iTerm2 源码中硬编码，无法通过 nib 补丁翻译（如高级设置页面）
- iTerm2 更新后需要重新运行安装脚本
- 安装会移除原有代码签名并进行本地签名（ad-hoc signing），不影响正常使用

## 翻译原则

- 遵循 [Apple 官方中文本地化术语](https://developer.apple.com/cn/localization/)
- iTerm 品牌名保持英文
- 技术术语（Shell、Terminal、xterm 等）保持英文
- 功能键、修饰键保持英文
- 格式化占位符（`%@`、`%d` 等）保持不变

## 项目结构

```
iTerm2-zh-CN/
├── README.md                # 本文件
├── LICENSE                  # GPLv2
├── METHODOLOGY.md           # 本地化方法论（面向 AI/开发者）
├── all_translations.json    # 翻译数据（核心资产）
├── scripts/
│   ├── install.sh           # 一键安装
│   ├── uninstall.sh         # 一键卸载
│   ├── nib_patch.py         # NIB 补丁核心工具
│   ├── nib_extract.py       # 字符串提取工具
│   └── patch_all.py         # 批量补丁脚本
└── .gitignore
```

## AI 部署指南

本节为 AI 编程助手（Claude Code、Cursor 等）提供技术细节。

### 原理

iTerm2 不使用 macOS 标准的 Base Internationalization，其界面文本直接存储在 NIBArchive 二进制文件中。本项目通过解析 nib 文件、替换字符串数据、重新序列化来实现汉化。

### 依赖

- Python 3
- [nibarchive](https://pypi.org/project/nibarchive/) — NIBArchive 解析库

### 手动部署步骤

如果安装脚本不适用，可以手动执行：

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
.venv/bin/pip install nibarchive

# 2. 备份原始 nib（首次执行）
mkdir -p .backup-nibs
for f in /Applications/iTerm.app/Contents/Resources/*.nib; do
    cp "$f" ".backup-nibs/$(basename "$f")"
done

# 3. 应用补丁
.venv/bin/python3 scripts/patch_all.py

# 4. 重签名
codesign --force --deep --sign - /Applications/iTerm.app
```

### 更新翻译流程

当 iTerm2 发布新版本时：

1. 提取新版字符串：`.venv/bin/python3 scripts/nib_extract.py new_strings.json`
2. 对比 `all_translations.json` 找出新增/变更的字符串
3. 翻译新增条目，更新 `all_translations.json`
4. 重新运行 `bash scripts/install.sh`

### 常见问题

**Q: 安装后 iTerm2 无法启动？**
A: 运行 `bash scripts/uninstall.sh` 恢复原始文件，然后检查是否有重签名错误。

**Q: 安装后部分文字仍是英文？**
A: 代码中硬编码的字符串无法通过 nib 补丁修改，这是已知限制。

**Q: 如何查看翻译数据？**
A: `all_translations.json` 是一个 JSON 文件，结构为 `{nib文件名: {对象索引.属性名: 翻译文本}}`。

详细技术文档请参阅 [METHODOLOGY.md](METHODOLOGY.md)。

## 许可证

本项目基于 [GPLv2](LICENSE) 许可证发布，与 [iTerm2](https://github.com/gnachman/iTerm2) 保持一致。
