#!/bin/bash
# iTerm2 简体中文汉化包 - 安装脚本
# 支持 iTerm2 3.x
set -e

ITERM_APP="/Applications/iTerm.app"
RESOURCES="$ITERM_APP/Contents/Resources"
INFO_PLIST="$ITERM_APP/Contents/Info.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LPROJ_SRC="$PROJECT_DIR/zh-Hans.lproj"
BACKUP_DIR="$PROJECT_DIR/.backup"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  iTerm2 简体中文汉化包 - 安装程序"
echo "================================================"
echo ""

# 检查 iTerm2 是否已安装
if [ ! -d "$ITERM_APP" ]; then
    echo -e "${RED}错误：未找到 iTerm2，请先安装 iTerm2${NC}"
    exit 1
fi

# 获取 iTerm2 版本
ITERM_VERSION=$(defaults read "$INFO_PLIST" CFBundleShortVersionString 2>/dev/null || echo "未知")
echo "检测到 iTerm2 版本: $ITERM_VERSION"

# 检查翻译文件是否存在
if [ ! -d "$LPROJ_SRC" ]; then
    echo -e "${RED}错误：未找到翻译文件目录 zh-Hans.lproj${NC}"
    exit 1
fi

# 检查是否需要 sudo
if [ ! -w "$RESOURCES" ]; then
    echo -e "${YELLOW}需要管理员权限来修改 iTerm2 应用包${NC}"
    exec sudo "$0" "$@"
fi

# 备份
echo ""
echo "[1/4] 备份原始文件..."
mkdir -p "$BACKUP_DIR"
if [ ! -f "$BACKUP_DIR/Info.plist" ]; then
    cp "$INFO_PLIST" "$BACKUP_DIR/Info.plist"
    echo "  已备份 Info.plist"
else
    echo "  备份已存在，跳过"
fi

# 复制翻译文件
echo "[2/4] 安装中文翻译文件..."
cp -R "$LPROJ_SRC" "$RESOURCES/zh-Hans.lproj"
echo "  已复制 zh-Hans.lproj 到 iTerm2 资源目录"

# 修改 Info.plist 添加中文本地化支持
echo "[3/4] 配置本地化支持..."
# 检查是否已有 CFBundleLocalizations
HAS_LOCALIZATIONS=$(/usr/libexec/PlistBuddy -c "Print :CFBundleLocalizations" "$INFO_PLIST" 2>/dev/null && echo "yes" || echo "no")
if [ "$HAS_LOCALIZATIONS" = "no" ]; then
    /usr/libexec/PlistBuddy -c "Add :CFBundleLocalizations array" "$INFO_PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleLocalizations:0 string en" "$INFO_PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleLocalizations:1 string zh-Hans" "$INFO_PLIST"
    echo "  已添加 CFBundleLocalizations (en, zh-Hans)"
else
    # 检查是否已包含 zh-Hans
    HAS_ZH=$(/usr/libexec/PlistBuddy -c "Print :CFBundleLocalizations" "$INFO_PLIST" 2>/dev/null | grep "zh-Hans" && echo "yes" || echo "no")
    if [ "$HAS_ZH" = "no" ]; then
        /usr/libexec/PlistBuddy -c "Add :CFBundleLocalizations: string zh-Hans" "$INFO_PLIST"
        echo "  已添加 zh-Hans 到 CFBundleLocalizations"
    else
        echo "  zh-Hans 已存在，跳过"
    fi
fi

# 重签名
echo "[4/4] 重签名应用..."
codesign --force --deep --sign - "$ITERM_APP" 2>/dev/null
echo "  重签名完成"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "请完全退出 iTerm2（Command+Q）后重新打开即可看到中文界面。"
echo "如果系统语言不是中文，请在「系统设置 → 通用 → 语言与地区」中"
echo "将简体中文设为首选语言。"
echo ""
echo "卸载命令: bash $(dirname "$0")/uninstall.sh"
