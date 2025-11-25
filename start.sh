#!/bin/bash

# 购物网站启动脚本（生产环境 - 使用 Gunicorn）

echo "🛒 购物网站启动脚本（生产环境）"
echo "================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查并安装依赖
echo "📦 检查依赖包..."
if ! python3 -c "import gunicorn" 2>/dev/null; then
    echo "📦 安装依赖包..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "❌ 依赖包安装失败"
        exit 1
    fi
    echo "✅ 依赖包安装完成"
else
    echo "✅ 依赖包已安装"
fi

# 创建日志目录
mkdir -p logs

# 检查 Gunicorn 是否安装
if ! command -v gunicorn &> /dev/null; then
    echo "❌ Gunicorn 未安装，正在安装..."
    pip install gunicorn
fi

echo "🚀 使用 Gunicorn 启动购物网站..."
echo "📱 访问地址: http://localhost:8000"
echo "👤 管理员账户: admin / admin123"
echo "================================"
echo ""

# 启动 Gunicorn
gunicorn --config gunicorn_config.py app:app
