# iTerm2 本地化方法论

本文档面向 AI 编程助手和开发者，详细说明 iTerm2 简体中文汉化的技术方案。

## 1. 为什么标准 .lproj 方案不生效

macOS 应用本地化通常通过 Base Internationalization 实现：将界面文件放在 `Base.lproj/`，翻译文件放在 `zh-Hans.lproj/` 等目录中。系统根据用户语言偏好自动加载对应翻译。

然而 **iTerm2 不使用 Base Internationalization**。它的 nib 文件直接放在 `Contents/Resources/` 根目录下（如 `MainMenu.nib`），而不是 `Base.lproj/MainMenu.nib`。这意味着：

- 即使创建了 `zh-Hans.lproj/MainMenu.strings`，系统也不会将其与根目录的 `MainMenu.nib` 关联
- 修改 `Info.plist` 添加 `CFBundleLocalizations` 也无效，因为 nib 不在 `Base.lproj` 中
- 传统 `.strings` 文件只能翻译显式标记为可本地化的字符串（约 462 条），覆盖率极低

因此，必须直接修改 nib 二进制文件。

## 2. NIBArchive 格式

`.nib` 文件实际上是 NIBArchive 格式的二进制文件，结构如下：

### 文件头（50 字节）

```
偏移  大小  内容
0     10    魔数 "NIBArchive"
10    4     unknown_1（版本?）
14    4     unknown_2
18    4     对象数量
22    4     对象节偏移
26    4     键数量
30    4     键节偏移
34    4     值数量
38    4     值节偏移
42    4     类名数量
46    4     类名节偏移
```

### 四大节

1. **Objects（对象）**：每个 UI 元素是一个对象，包含类名索引、值起始索引、值数量
2. **Keys（键）**：属性名列表，如 `NSTitle`、`NSLabel`、`NS.bytes`
3. **Values（值）**：属性值列表，每个值有类型标记 + 数据。字符串存储为 `DATA` 类型（type=0x06）
4. **Class Names（类名）**：NSObject 子类名列表，如 `NSMenuItem`、`NSButton`

### Varint 编码

NIBArchive 使用自定义 varint 编码（非 protobuf 标准）：
- 最高位（0x80）标记**最后一个字节**（与 protobuf 相反）
- 单字节值：`value | 0x80`
- 多字节值：低 7 位在前，最后一个字节设置 0x80

### 字符串存储

用户可见的字符串以 UTF-8 编码存储在 DATA 类型值中：
- **没有 null 终止符**（这是一个重要的发现，最初的实现错误地添加了 `\x00`）
- 长度由 varint 前缀指定
- 常见的字符串属性键：`NSTitle`、`NSLabel`、`NSWindowTitle`、`NSPlaceholderString`、`NS.bytes` 等

## 3. 补丁原理

### 流程

1. **解析**：使用 `nibarchive` Python 库解析 nib 文件为内存对象
2. **定位**：遍历所有对象的所有值，找到 DATA 类型的字符串
3. **替换**：将英文字符串替换为中文翻译（UTF-8 编码）
4. **序列化**：将修改后的内存对象重新序列化为二进制
5. **写入**：覆盖原始 nib 文件
6. **重签名**：对整个 iTerm2.app 进行 ad-hoc 签名

### 翻译数据格式

`all_translations.json` 结构：

```json
{
  "MainMenu.nib": {
    "5.NSTitle": "文件",
    "6.NSTitle": "编辑",
    "12.NS.bytes": "显示剪贴板"
  },
  "PreferencePanel.nib": {
    "3.NSTitle": "通用",
    "4.NSTitle": "外观"
  }
}
```

键格式为 `{对象索引}.{属性名}`，值为翻译后的中文文本。

## 4. 关键注意事项

### 字符串无 null 终止符

NIBArchive 中的 DATA 字符串**不包含** `\x00` 终止符。序列化时直接写入 UTF-8 字节，长度由 varint 前缀决定。

这是最初实现中的一个 bug：序列化器错误地在字符串末尾添加了 `\x00`，导致 UI 显示异常。修复方法是移除 null 终止符的添加。

### 不可翻译的字符串

以下类型的字符串不应翻译：
- **IBOutlet 名称**：以 `_` 开头的标识符
- **类名**：CamelCase 格式的 Objective-C 类名
- **选择器**：以 `:` 结尾的方法名（如 `performAction:`）
- **IB 标识符**：以 `IB` 或 `NS` 开头的内部标识
- **图片名称**：以 `NSImage` 开头

### 格式占位符

翻译文本中的格式占位符必须保留：
- `%@` — 字符串参数
- `%d` — 整数参数
- `%ld` — 长整数参数
- `%1$@` — 带位置的参数

## 5. 翻译提取策略

`nib_extract.py` 使用以下启发式规则判断字符串是否为用户可见文本：

1. 长度 >= 2 个字符
2. 不以 `_`、`NS`、`IB` 开头
3. 不以 `:` 结尾（排除选择器）
4. 不是纯 CamelCase（排除类名）
5. 不以 `NSImage`、`NSMenu` 开头
6. 包含至少一个字母字符

关键属性键优先提取：`NSTitle`、`NSLabel`、`NSWindowTitle`、`NSPlaceholderString`、`NSHeaderTitle`、`NSPrompt`、`NSMessage`、`NSInformativeText`、`NSToolTip`。

## 6. 版本升级指南

当 iTerm2 发布新版本时：

1. **提取新版字符串**：
   ```bash
   .venv/bin/python3 scripts/nib_extract.py new_strings.json
   ```

2. **对比差异**：比较 `new_strings.json` 和 `all_translations.json`，找出：
   - 新增的 nib 文件
   - 新增的字符串条目
   - 对象索引变化导致的键名变更

3. **翻译新增条目**：将新字符串翻译为中文，更新 `all_translations.json`

4. **处理索引变化**：如果 iTerm2 修改了 nib 文件的结构，对象索引可能变化。需要通过字符串内容匹配而非索引来关联旧翻译。

5. **测试**：运行安装脚本，验证 iTerm2 启动正常、界面显示正确。

## 7. 局限性

### 代码硬编码字符串

iTerm2 中大量字符串直接写在 Objective-C/Swift 源代码中（如 `@"Advanced Settings"`），这些字符串：
- 不存在于 nib 文件中
- 无法通过 nib 补丁修改
- 需要修改源代码并重新编译才能翻译

典型的硬编码区域：
- 高级设置页面（Advanced Settings）
- 快捷键动作描述
- 部分状态栏信息
- 错误消息和提示

### nib 结构版本依赖

翻译数据中的对象索引（如 `5.NSTitle`）是特定 iTerm2 版本的 nib 文件结构决定的。当 iTerm2 更新时，nib 文件可能被重新编译，导致对象索引变化。因此每次版本更新都需要重新提取和映射字符串。
