#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
e#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

##!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

##!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境并安装依赖
echo "📦 安装依赖..."
cd backend#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境并安装依赖
echo "📦 安装依赖..."
cd backend
source .venv/bin/activate

if#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境并安装依赖
echo "📦 安装依赖..."
cd backend
source .venv/bin/activate

if [ ! -f ".venv/installed" ]; then
    pip install --upgrade pip
#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境并安装依赖
echo "📦 安装依赖..."
cd backend
source .venv/bin/activate

if [ ! -f ".venv/installed" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .venv/installed
    echo "✅#!/bin/bash
# NovelWrite 一键部署脚本
# 将此脚本保存到您的项目目录，然后在终端运行: bash setup_and_run.sh

set -e

echo "=========================================="
echo "  NovelWrite 项目部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 项目目录: $SCRIPT_DIR"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "backend/.venv" ]; then
    cd backend
    python3 -m venv .venv
    cd ..
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境并安装依赖
echo "📦 安装依赖..."
cd backend
source .venv/bin/activate

if [ ! -f ".venv/installed" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .venv/installed
    echo "✅ 依赖安装完成"
else
    echo "