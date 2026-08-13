#!/bin/bash
# iTerm2 简体中文汉化补丁 - 卸载脚本
# 从备份恢复原始 nib 文件
set -e

ITERM_APP="${ITERM_APP:-/Applications/iTerm.app}"
RESOURCES="$ITERM_APP/Contents/Resources"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/.backup-nibs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  iTerm2 简体中文汉化补丁 - 卸载程序"
echo "================================================"
echo ""

if [ ! -d "$ITERM_APP" ]; then
    echo -e "${RED}错误：未找到 iTerm2${NC}"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}错误：未找到备份目录 .backup-nibs/${NC}"
    echo "可能尚未安装汉化补丁，或备份已被删除。"
    exit 1
fi

# 检查权限
if [ ! -w "$RESOURCES" ]; then
    echo -e "${YELLOW}需要管理员权限${NC}"
    exec sudo "$0" "$@"
fi

# 先退出 iTerm2
osascript -e 'tell application "iTerm2" to quit' 2>/dev/null || true
sleep 2

# 恢复备份
echo "[1/4] 从备份恢复原始 nib 文件..."
restored=0
for backup_file in "$BACKUP_DIR"/*.nib; do
    nib_name=$(basename "$backup_file")
    target="$RESOURCES/$nib_name"
    if [ -f "$target" ]; then
        cp "$backup_file" "$target"
        restored=$((restored + 1))
    fi
done
echo "  已恢复 $restored 个 nib 文件"

# 移除运行时汉化 dylib
echo "[2/4] 移除运行时汉化 dylib..."
if [ -f "$ITERM_APP/Contents/Frameworks/iTermZhPatch.dylib" ]; then
    rm -f "$ITERM_APP/Contents/Frameworks/iTermZhPatch.dylib"
    echo "  已删除 iTermZhPatch.dylib"
else
    echo "  未发现 iTermZhPatch.dylib，跳过"
fi

# 恢复原始主程序（移除 LC_LOAD_DYLIB 注入）
echo "[3/4] 恢复原始主程序..."
if [ -f "$ITERM_APP/Contents/MacOS/iTerm2.orig-backup" ]; then
    cp "$ITERM_APP/Contents/MacOS/iTerm2.orig-backup" "$ITERM_APP/Contents/MacOS/iTerm2"
    echo "  已从 iTerm2.orig-backup 恢复（LC_LOAD_DYLIB 注入随之移除）"
else
    echo -e "  ${YELLOW}未找到主程序备份 iTerm2.orig-backup。${NC}"
    echo "  若曾注入 dylib，请手动用 install_name_tool -d 移除加载项，"
    echo "  或重新安装官方 iTerm2。"
fi

# 重签名
echo "[4/4] 重签名应用..."
codesign --force --deep --sign - "$ITERM_APP" 2>/dev/null
echo "  签名完成"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  卸载完成！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "请完全退出 iTerm2（Command+Q）后重新打开。"
