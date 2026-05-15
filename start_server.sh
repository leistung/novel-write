#!/bin/bash
# NovelWrite 后端服务启动脚本

cd "$(dirname "$0")/backend"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# 启动服务
echo "正在启动 NovelWrite 后端服务..."
echo "服务将运行在 http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python run.py
