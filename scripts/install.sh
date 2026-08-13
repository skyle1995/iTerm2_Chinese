#!/bin/bash
# iTerm2 简体中文汉化补丁 - 安装脚本(双层方案)
#   第一层:nib 静态补丁(界面布局文件)
#   第二层:运行时翻译 dylib(LC_LOAD_DYLIB 注入主程序)
# 所有项目路径均从脚本自身位置推导,项目目录可随意移动。
# iTerm2 的系统安装位置可用环境变量 ITERM_APP 覆盖(默认 /Applications/iTerm.app)。
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"
ITERM_APP="${ITERM_APP:-/Applications/iTerm.app}"
RESOURCES="$ITERM_APP/Contents/Resources"
MACOS_BIN="$ITERM_APP/Contents/MacOS/iTerm2"
DYLIB="$ITERM_APP/Contents/Frameworks/iTermZhPatch.dylib"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  iTerm2 简体中文汉化补丁 - 安装程序"
echo "================================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "目标应用: $ITERM_APP"

# 1. 检查 iTerm2 / 工具链
if [ ! -d "$ITERM_APP" ]; then
    echo -e "${RED}错误:未找到 iTerm2($ITERM_APP),请先安装;位置不同可用 ITERM_APP 环境变量指定${NC}"
    exit 1
fi
ITERM_VERSION=$(defaults read "$ITERM_APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "未知")
echo "检测到 iTerm2 版本: $ITERM_VERSION"

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}错误:需要 Python 3,请先安装${NC}"
    exit 1
fi
if ! command -v clang &>/dev/null; then
    echo -e "${RED}错误:需要 clang(Xcode 命令行工具),请先执行 xcode-select --install${NC}"
    exit 1
fi

# 2. 创建 venv 并安装 nibarchive
VENV_DIR="$BUILD_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "[1/5] 创建 Python 虚拟环境并安装依赖..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q nibarchive
    echo "  已安装 nibarchive"
else
    echo ""
    echo "[1/5] Python 虚拟环境已存在"
fi

# 3. 检查权限
if [ ! -w "$RESOURCES" ]; then
    echo -e "${YELLOW}需要管理员权限来修改 iTerm2 应用包${NC}"
    exec sudo ITERM_APP="$ITERM_APP" "$0" "$@"
fi

# 4. 第一层:nib 补丁(apply_full.py 要求 .backup-nibs 已存在,出错自动恢复)
echo "[2/5] 备份原始 nib 并应用汉化补丁..."
ITERM_APP="$ITERM_APP" "$VENV_DIR/bin/python3" "$SCRIPT_DIR/apply_full.py"

# 5. 第二层:构建运行时翻译 dylib
echo "[3/5] 构建运行时翻译 dylib..."
python3 "$SCRIPT_DIR/gen_shim.py" "$BUILD_DIR/zh_shim.m"
clang -dynamiclib -framework Cocoa -arch arm64 -arch x86_64 -O2 \
      -o "$BUILD_DIR/iTermZhPatch.dylib" "$BUILD_DIR/zh_shim.m"
echo "  已构建 build/iTermZhPatch.dylib"

# 6. 安装 dylib 并注入主程序
echo "[4/5] 安装 dylib 并注入主程序..."
mkdir -p "$(dirname "$DYLIB")"
cp "$BUILD_DIR/iTermZhPatch.dylib" "$DYLIB"
if [ ! -f "$MACOS_BIN.orig-backup" ]; then
    cp "$MACOS_BIN" "$MACOS_BIN.orig-backup"
    echo "  已备份原始主程序到 iTerm2.orig-backup"
fi
if otool -l "$MACOS_BIN" | grep -q 'iTermZhPatch.dylib'; then
    echo "  主程序已注入过,跳过"
else
    python3 "$SCRIPT_DIR/inject_dylib.py" \
        '@executable_path/../Frameworks/iTermZhPatch.dylib' "$MACOS_BIN"
fi

# 7. 重签名
echo "[5/5] 重签名..."
codesign -f -s - "$DYLIB"
codesign -f -s - "$MACOS_BIN"
echo "  签名完成"

echo ""
echo -e "${GREEN}================================================"
echo -e "  汉化补丁已应用!"
echo -e "================================================${NC}"
echo ""
echo "请完全退出 iTerm2(Command+Q)后重新打开即可看到中文界面。"
echo "卸载命令: bash $SCRIPT_DIR/uninstall.sh"
