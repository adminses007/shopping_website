# 购物网站部署指南

本指南介绍如何使用 Gunicorn + Nginx 部署购物网站到生产环境。

## 📋 前置要求

- Ubuntu/Debian Linux 服务器
- Python 3.8+
- Nginx
- 域名或 IP 地址（可选）

## 🚀 快速部署

### 方法一：使用部署脚本（推荐）

```bash
cd /home/adminses/My_Projects/shopping_website
chmod +x deploy.sh
bash deploy.sh
```

### 方法二：手动部署

#### 1. 安装依赖

```bash
# 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx

# 创建虚拟环境
cd /home/adminses/My_Projects/shopping_website
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. 配置 Gunicorn

```bash
# 创建日志目录
mkdir -p logs

# 测试 Gunicorn 启动
gunicorn --config gunicorn_config.py app:app
```

如果成功，按 `Ctrl+C` 停止。

#### 3. 配置 Systemd 服务

```bash
# 复制服务文件
sudo cp shopping_website.service /etc/systemd/system/

# 编辑服务文件（修改用户、路径等）
sudo nano /etc/systemd/system/shopping_website.service

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable shopping_website
sudo systemctl start shopping_website

# 检查服务状态
sudo systemctl status shopping_website
```

#### 4. 配置 Nginx

```bash
# 复制 Nginx 配置文件
sudo cp nginx.conf /etc/nginx/sites-available/shopping_website

# 编辑配置文件，修改域名或 IP
sudo nano /etc/nginx/sites-available/shopping_website

# 创建符号链接
sudo ln -s /etc/nginx/sites-available/shopping_website /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

## ⚙️ 配置说明

### Gunicorn 配置

配置文件：`gunicorn_config.py`

主要配置项：
- `bind`: Gunicorn 监听地址和端口（默认：127.0.0.1:8000）
- `workers`: 工作进程数（自动根据 CPU 核心数计算）
- `timeout`: 请求超时时间（秒）
- `accesslog`: 访问日志路径
- `errorlog`: 错误日志路径

### Nginx 配置

配置文件：`/etc/nginx/sites-available/shopping_website`

需要修改的地方：
1. `server_name`: 改为您的域名或 IP 地址
2. `alias`: 确保静态文件路径正确

### Systemd 服务配置

配置文件：`/etc/systemd/system/shopping_website.service`

需要修改的地方：
1. `User` 和 `Group`: 改为运行服务的用户
2. `WorkingDirectory`: 确保项目路径正确
3. `Environment`: 设置环境变量，特别是 `SECRET_KEY`

## 🔒 安全配置

### 1. 设置强密码 SECRET_KEY

```bash
# 生成随机密钥
python3 -c "import secrets; print(secrets.token_hex(32))"

# 编辑服务文件，设置 SECRET_KEY
sudo nano /etc/systemd/system/shopping_website.service
```

### 2. 配置 HTTPS（推荐）

使用 Let's Encrypt 免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书（替换为您的域名）
sudo certbot --nginx -d mrcolourtech.it.com -d www.mrcolourtech.it.com

# 证书会自动续期
```

然后取消 Nginx 配置文件中 HTTPS 部分的注释。

### 3. 防火墙配置

```bash
# 允许 HTTP 和 HTTPS
sudo ufw allow 'Nginx Full'
# 或分别允许
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## 📊 监控和维护

### 查看服务状态

```bash
# Gunicorn 服务状态
sudo systemctl status shopping_website

# Nginx 状态
sudo systemctl status nginx
```

### 查看日志

```bash
# Gunicorn 日志
sudo journalctl -u shopping_website -f
tail -f logs/gunicorn_access.log
tail -f logs/gunicorn_error.log

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 重启服务

```bash
# 重启 Gunicorn
sudo systemctl restart shopping_website

# 重启 Nginx
sudo systemctl restart nginx

# 重载 Nginx 配置（不中断服务）
sudo systemctl reload nginx
```

### 更新应用

```bash
cd /home/adminses/My_Projects/shopping_website
source venv/bin/activate

# 拉取最新代码（如果使用 Git）
# git pull

# 更新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl restart shopping_website
```

## 🐛 故障排除

### 1. 服务无法启动

```bash
# 检查服务状态
sudo systemctl status shopping_website

# 查看详细日志
sudo journalctl -u shopping_website -n 50

# 检查配置文件语法
gunicorn --check-config --config gunicorn_config.py app:app
```

### 2. Nginx 502 错误

- 检查 Gunicorn 是否运行：`sudo systemctl status shopping_website`
- 检查端口是否正确：`netstat -tlnp | grep 8000`
- 检查 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### 3. 静态文件无法加载

- 检查 Nginx 配置中的 `alias` 路径是否正确
- 检查文件权限：`ls -la static/`
- 确保 Nginx 有读取权限

### 4. 数据库错误

- 检查数据库文件权限
- 确保数据库路径正确
- 检查日志中的具体错误信息

## 📝 性能优化

### 1. 调整 Gunicorn 工作进程数

根据服务器 CPU 核心数调整 `workers`：

```python
# gunicorn_config.py
workers = 4  # 根据实际情况调整
```

### 2. 启用 Nginx 缓存

在 Nginx 配置中已经包含了静态文件缓存配置。

### 3. 使用数据库连接池

如果使用 PostgreSQL 或 MySQL，可以配置连接池提高性能。

## 🔄 备份

定期备份数据库和上传的文件：

```bash
# 备份数据库
cp shopping_website.db shopping_website.db.backup.$(date +%Y%m%d)

# 备份上传的文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz static/uploads/
```

## 📞 支持

如有问题，请检查：
1. 服务日志
2. Nginx 日志
3. 系统日志：`sudo journalctl -xe`

---

**部署完成后，访问您的域名或 IP 地址即可使用购物网站！**

