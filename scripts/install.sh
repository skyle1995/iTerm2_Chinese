#!/bin/bash
# iTerm2 简体中文汉化补丁 - 安装脚本
# 通过 NIBArchive 二进制补丁实现界面汉化
set -e

ITERM_APP="/Applications/iTerm.app"
RESOURCES="$ITERM_APP/Contents/Resources"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  iTerm2 简体中文汉化补丁 - 安装程序"
echo "================================================"
echo ""

# 1. 检查 iTerm2
if [ ! -d "$ITERM_APP" ]; then
    echo -e "${RED}错误：未找到 iTerm2，请先安装${NC}"
    exit 1
fi
ITERM_VERSION=$(defaults read "$ITERM_APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "未知")
echo "检测到 iTerm2 版本: $ITERM_VERSION"

# 2. 检查 Python 3
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}错误：需要 Python 3，请先安装${NC}"
    exit 1
fi
echo "Python: $(python3 --version)"

# 3. 创建 venv 并安装 nibarchive
VENV_DIR="$PROJECT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "[1/4] 创建 Python 虚拟环境并安装依赖..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q nibarchive
    echo "  已安装 nibarchive"
else
    echo ""
    echo "[1/4] Python 虚拟环境已存在"
fi

# 4. 检查权限
if [ ! -w "$RESOURCES" ]; then
    echo -e "${YELLOW}需要管理员权限来修改 iTerm2 应用包${NC}"
    exec sudo "$0" "$@"
fi

# 5. 备份并补丁
echo "[2/4] 备份原始 nib 文件并应用汉化补丁..."
"$VENV_DIR/bin/python3" "$SCRIPT_DIR/patch_all.py"

# 6. 重签名
echo "[3/4] 验证签名..."
codesign --force --deep --sign - "$ITERM_APP" 2>/dev/null
echo "  签名完成"

echo ""
echo "[4/4] 安装完成！"
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  汉化补丁已应用！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "请完全退出 iTerm2（Command+Q）后重新打开即可看到中文界面。"
echo ""
echo "卸载命令: bash $SCRIPT_DIR/uninstall.sh"
