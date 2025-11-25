#!/bin/bash
# 购物网站部署脚本
# 使用方法: bash deploy.sh

set -e  # 遇到错误立即退出

PROJECT_DIR="/home/adminses/My_Projects/shopping_website"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="shopping_website"
NGINX_SITE="shopping_website"

echo "=========================================="
echo "🚀 开始部署购物网站..."
echo "=========================================="

# 1. 检查 Python 版本
echo "📋 检查 Python 版本..."
python3 --version || { echo "❌ Python 3 未安装"; exit 1; }

# 2. 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# 3. 激活虚拟环境并安装依赖
echo "📦 安装依赖..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"
pip install gunicorn

# 4. 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/static/uploads"
mkdir -p "$PROJECT_DIR/static/images"

# 5. 初始化数据库（如果需要）
echo "🗄️  初始化数据库..."
cd "$PROJECT_DIR"
python3 -c "from app import app, db; app.app_context().push(); db.create_all()" || echo "⚠️  数据库初始化跳过（可能已存在）"

# 6. 设置文件权限
echo "🔐 设置文件权限..."
chmod +x "$PROJECT_DIR/deploy.sh"
chmod +x "$PROJECT_DIR/gunicorn_config.py"

# 7. 配置 systemd 服务
echo "⚙️  配置 systemd 服务..."
sudo cp "$PROJECT_DIR/$SERVICE_NAME.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# 8. 配置 Nginx
echo "🌐 配置 Nginx..."
# 复制 Nginx 配置文件
sudo cp "$PROJECT_DIR/nginx.conf" /etc/nginx/sites-available/$NGINX_SITE

# 创建符号链接（如果不存在）
if [ ! -L "/etc/nginx/sites-enabled/$NGINX_SITE" ]; then
    sudo ln -s /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
fi

# 测试 Nginx 配置
echo "🧪 测试 Nginx 配置..."
sudo nginx -t || { echo "❌ Nginx 配置错误"; exit 1; }

# 9. 启动服务
echo "▶️  启动服务..."
sudo systemctl restart $SERVICE_NAME
sudo systemctl restart nginx

# 10. 检查服务状态
echo "📊 检查服务状态..."
sleep 2
sudo systemctl status $SERVICE_NAME --no-pager -l || echo "⚠️  服务可能未正常启动，请检查日志"

echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "📝 后续操作："
echo "1. 编辑 /etc/nginx/sites-available/$NGINX_SITE，修改 server_name 为您的域名或 IP"
echo "2. 编辑 /etc/systemd/system/$SERVICE_NAME.service，修改环境变量（特别是 SECRET_KEY）"
echo "3. 重启服务: sudo systemctl restart $SERVICE_NAME && sudo systemctl restart nginx"
echo "4. 查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo "5. 查看 Nginx 日志: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="

