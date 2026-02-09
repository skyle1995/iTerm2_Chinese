#!/bin/bash
# iTerm2 简体中文汉化包 - 卸载脚本
set -e

ITERM_APP="/Applications/iTerm.app"
RESOURCES="$ITERM_APP/Contents/Resources"
INFO_PLIST="$ITERM_APP/Contents/Info.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/.backup"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  iTerm2 简体中文汉化包 - 卸载程序"
echo "================================================"
echo ""

if [ ! -d "$ITERM_APP" ]; then
    echo -e "${RED}错误：未找到 iTerm2${NC}"
    exit 1
fi

# 检查是否需要 sudo
if [ ! -w "$RESOURCES" ]; then
    echo -e "${YELLOW}需要管理员权限${NC}"
    exec sudo "$0" "$@"
fi

# 删除翻译文件
echo "[1/3] 移除中文翻译文件..."
if [ -d "$RESOURCES/zh-Hans.lproj" ]; then
    rm -rf "$RESOURCES/zh-Hans.lproj"
    echo "  已删除 zh-Hans.lproj"
else
    echo "  zh-Hans.lproj 不存在，跳过"
fi

# 恢复 Info.plist
echo "[2/3] 恢复 Info.plist..."
if [ -f "$BACKUP_DIR/Info.plist" ]; then
    cp "$BACKUP_DIR/Info.plist" "$INFO_PLIST"
    echo "  已从备份恢复"
else
    # 没有备份，手动移除 CFBundleLocalizations
    /usr/libexec/PlistBuddy -c "Delete :CFBundleLocalizations" "$INFO_PLIST" 2>/dev/null || true
    echo "  已移除 CFBundleLocalizations"
fi

# 重签名
echo "[3/3] 重签名应用..."
codesign --force --deep --sign - "$ITERM_APP" 2>/dev/null
echo "  重签名完成"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  卸载完成！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "请完全退出 iTerm2（Command+Q）后重新打开。"
