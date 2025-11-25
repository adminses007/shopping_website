#!/bin/bash
# 快速启动 Gunicorn（用于测试）
# 使用方法: bash start_gunicorn.sh

cd /home/adminses/My_Projects/shopping_website

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动 Gunicorn
echo "🚀 启动 Gunicorn..."
gunicorn --config gunicorn_config.py app:app

