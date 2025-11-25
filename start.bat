@echo off
chcp 65001 >nul
title 购物网站启动脚本

echo 🛒 购物网站启动脚本
echo ====================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装Python
    pause
    exit /b 1
)

REM 检查pip是否安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip 未安装，请先安装pip
    pause
    exit /b 1
)

echo 📦 安装依赖包...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依赖包安装失败
    pause
    exit /b 1
)

echo ✅ 依赖包安装完成

echo 🚀 启动购物网站...
python run.py

pause
