#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn 配置文件
"""

import multiprocessing
import os

# 服务器socket
bind = "127.0.0.1:8000"  # Gunicorn 监听本地8000端口，由 Nginx 反向代理
backlog = 2048

# 工作进程
workers = multiprocessing.cpu_count() * 2 + 1  # 推荐配置：CPU核心数 * 2 + 1
worker_class = "sync"  # 同步工作模式，适合 I/O 密集型应用
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志
accesslog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_access.log")
errorlog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_error.log")
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "shopping_website"

# 服务器机制
daemon = False
pidfile = os.path.join(os.path.dirname(__file__), "logs", "gunicorn.pid")
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (如果需要 HTTPS，取消注释并配置)
# keyfile = None
# certfile = None

# 性能调优
max_requests = 1000  # 工作进程处理请求数后重启，防止内存泄漏
max_requests_jitter = 50  # 随机抖动，避免所有工作进程同时重启
preload_app = True  # 预加载应用，提高性能

# 优雅重启
graceful_timeout = 30

