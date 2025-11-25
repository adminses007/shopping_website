# 🚀 购物网站启动指南

本指南介绍如何在不同环境下启动购物网站服务。

## 📋 目录

- [开发环境启动](#开发环境启动)
- [生产环境启动（Gunicorn）](#生产环境启动gunicorn)
- [生产环境启动（Systemd + Nginx）](#生产环境启动systemd--nginx)
- [常用命令](#常用命令)
- [故障排除](#故障排除)

---

## 🛠️ 开发环境启动

适用于本地开发和测试（使用 Flask 开发服务器，会有警告信息，这是正常的）。

### 方法一：使用开发启动脚本（推荐）

```bash
cd /home/adminses/My_Projects/shopping_website
bash start_dev.sh
```

### 方法二：直接运行 Python 脚本

```bash
cd /home/adminses/My_Projects/shopping_website
python3 run.py
```

### 方法三：直接运行 Flask 应用

```bash
cd /home/adminses/My_Projects/shopping_website
python3 app.py
```

**访问地址：** http://localhost:5000

**默认管理员账户：**
- 用户名：`admin`
- 密码：`admin123`

**注意：** 开发服务器会显示警告信息，这是正常的。如需消除警告，请使用生产环境启动方式。

---

## 🏭 生产环境启动（Gunicorn）

适用于生产环境，使用 Gunicorn 作为 WSGI 服务器（不会显示警告信息）。

### 快速启动（推荐）

```bash
cd /home/adminses/My_Projects/shopping_website
bash start.sh
```

**注意：** `start.sh` 现在默认使用 Gunicorn 启动，不会显示开发服务器警告。

### 前置准备

```bash
# 1. 创建虚拟环境（如果还没有）
cd /home/adminses/My_Projects/shopping_website
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 3. 创建日志目录
mkdir -p logs
```

### 启动方式

#### 方法一：使用启动脚本

```bash
cd /home/adminses/My_Projects/shopping_website
bash start_gunicorn.sh
```

#### 方法二：直接运行 Gunicorn

```bash
cd /home/adminses/My_Projects/shopping_website
source venv/bin/activate
gunicorn --config gunicorn_config.py app:app
```

#### 方法三：后台运行

```bash
cd /home/adminses/My_Projects/shopping_website
source venv/bin/activate
nohup gunicorn --config gunicorn_config.py app:app > logs/gunicorn.log 2>&1 &
```

**访问地址：** http://localhost:8000（Gunicorn 默认监听 8000 端口）

---

## 🌐 生产环境启动（Systemd + Nginx）

适用于正式生产环境，使用 Systemd 管理服务，Nginx 作为反向代理。

### 完整部署步骤

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

#### 2. 配置 Systemd 服务

```bash
# 编辑服务文件（修改用户、路径等）
nano shopping_website.service

# 复制到系统目录
sudo cp shopping_website.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable shopping_website

# 启动服务
sudo systemctl start shopping_website

# 检查服务状态
sudo systemctl status shopping_website
```

#### 3. 配置 Nginx

```bash
# 编辑 Nginx 配置（修改 server_name 为您的域名或 IP）
nano nginx.conf

# 复制到 Nginx 配置目录
sudo cp nginx.conf /etc/nginx/sites-available/shopping_website

# 创建符号链接
sudo ln -s /etc/nginx/sites-available/shopping_website /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 4. 使用自动部署脚本（推荐）

```bash
cd /home/adminses/My_Projects/shopping_website
bash deploy.sh
```

**访问地址：** http://mrcolourtech.it.com 或 http://your-ip-address

---

## 📝 常用命令

### 服务管理

```bash
# 启动服务
sudo systemctl start shopping_website

# 停止服务
sudo systemctl stop shopping_website

# 重启服务
sudo systemctl restart shopping_website

# 查看服务状态
sudo systemctl status shopping_website

# 查看服务日志
sudo journalctl -u shopping_website -f

# 启用开机自启
sudo systemctl enable shopping_website

# 禁用开机自启
sudo systemctl disable shopping_website
```

### Nginx 管理

```bash
# 启动 Nginx
sudo systemctl start nginx

# 停止 Nginx
sudo systemctl stop nginx

# 重启 Nginx
sudo systemctl restart nginx

# 重载 Nginx 配置（不中断服务）
sudo systemctl reload nginx

# 查看 Nginx 状态
sudo systemctl status nginx

# 测试 Nginx 配置
sudo nginx -t
```

### 查看日志

```bash
# Gunicorn 访问日志
tail -f logs/gunicorn_access.log

# Gunicorn 错误日志
tail -f logs/gunicorn_error.log

# Systemd 服务日志
sudo journalctl -u shopping_website -n 50

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 进程管理

```bash
# 查看 Gunicorn 进程
ps aux | grep gunicorn

# 查看端口占用
netstat -tlnp | grep 8000

# 杀死 Gunicorn 进程（如果需要）
pkill -f gunicorn
```

---

## 🔧 故障排除

### 1. 服务无法启动

**检查服务状态：**
```bash
sudo systemctl status shopping_website
```

**查看详细日志：**
```bash
sudo journalctl -u shopping_website -n 50
```

**常见问题：**
- 虚拟环境路径不正确
- 端口被占用
- 权限问题
- 配置文件错误

### 2. Nginx 502 错误

**检查 Gunicorn 是否运行：**
```bash
sudo systemctl status shopping_website
ps aux | grep gunicorn
```

**检查端口：**
```bash
netstat -tlnp | grep 8000
```

**检查 Nginx 错误日志：**
```bash
sudo tail -f /var/log/nginx/error.log
```

### 3. 静态文件无法加载

**检查 Nginx 配置中的路径：**
```bash
sudo nano /etc/nginx/sites-available/shopping_website
```

**检查文件权限：**
```bash
ls -la static/
```

**确保 Nginx 有读取权限：**
```bash
sudo chmod -R 755 static/
```

### 4. 数据库错误

**检查数据库文件：**
```bash
ls -la shopping_website.db
```

**检查数据库权限：**
```bash
chmod 644 shopping_website.db
```

### 5. 端口冲突

**检查端口占用：**
```bash
# 检查 5000 端口（开发环境）
netstat -tlnp | grep 5000

# 检查 8000 端口（Gunicorn）
netstat -tlnp | grep 8000

# 检查 80 端口（Nginx）
netstat -tlnp | grep 80
```

**修改端口：**
- 开发环境：编辑 `run.py` 或 `app.py` 中的 `port=5000`
- Gunicorn：编辑 `gunicorn_config.py` 中的 `bind = "127.0.0.1:8000"`
- Nginx：编辑 `nginx.conf` 中的 `listen 80`

---

## 📊 快速启动检查清单

### 开发环境
- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] 数据库文件存在
- [ ] 运行 `bash start.sh` 或 `python3 run.py`
- [ ] 访问 http://localhost:5000

### 生产环境（Gunicorn）
- [ ] 虚拟环境已创建并激活
- [ ] 所有依赖已安装
- [ ] 日志目录已创建（`mkdir -p logs`）
- [ ] 运行 `bash start_gunicorn.sh`
- [ ] 访问 http://localhost:8000

### 生产环境（Systemd + Nginx）
- [ ] 虚拟环境已创建
- [ ] 所有依赖已安装
- [ ] Systemd 服务已配置并启动
- [ ] Nginx 已配置并启动
- [ ] 防火墙已开放 80/443 端口
- [ ] 访问 http://your-domain.com

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志文件
2. 检查服务状态
3. 查看 `DEPLOYMENT.md` 详细部署文档
4. 检查配置文件是否正确

---

**祝您使用愉快！** 🎉

