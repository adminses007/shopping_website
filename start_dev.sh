#!/bin/bash

# 购物网站开发环境启动脚本（使用 Flask 开发服务器）

echo "🛒 购物网站开发环境启动脚本"
echo "============================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装，请先安装pip3"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

echo "📦 安装依赖包..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依赖包安装失败"
    exit 1
fi

echo "✅ 依赖包安装完成"

echo "🚀 启动购物网站（开发模式）..."
echo "⚠️  注意：这是开发服务器，仅用于开发和测试"
echo "📱 访问地址: http://localhost:5000"
echo "👤 管理员账户: admin / admin123"
echo "============================"
echo ""

# 启动Flask开发服务器
python3 run.py

