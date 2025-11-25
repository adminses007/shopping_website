#!/bin/bash
# 清理项目中不需要的文件
# 使用方法: bash cleanup.sh

set -e

PROJECT_DIR="/home/adminses/My_Projects/shopping_website"

echo "=========================================="
echo "🧹 开始清理项目文件..."
echo "=========================================="

cd "$PROJECT_DIR"

# 1. 删除测试文件
echo "🗑️  删除测试文件..."
rm -f test_*.py
rm -f test_image.html
echo "✅ 已删除测试文件"

# 2. 删除临时文件
echo "🗑️  删除临时文件..."
rm -f cookies.txt
rm -f images.jpeg
echo "✅ 已删除临时文件"

# 3. 删除数据库备份文件（保留最新的一个）
echo "🗑️  删除旧的数据库备份文件..."
rm -f shopping_website.db.backup_20251119_103826
rm -f shopping_website.db.backup_20251119_111413
# 保留最新的备份: shopping_website.db.backup_20251119_122924
echo "✅ 已删除旧数据库备份（保留最新备份）"

# 4. 删除开发过程中的说明文档（保留重要文档）
echo "🗑️  删除开发说明文档..."
rm -f 字体更改说明.md
rm -f 立即购买功能问题解决方案.md
rm -f 商品图片飞入购物车按钮动画功能说明.md
rm -f 飞入购物车商品图片动画功能说明.md
rm -f 飞入购物车图案动画功能说明.md
rm -f 飞入右上角动画功能说明.md
rm -f 飞入购物车数量动画最终实现说明.md
rm -f 飞入购物车数量动画功能说明.md
rm -f 飞入购物车动画功能说明.md
rm -f 商品详情UndefinedError解决方案.md
rm -f 订单管理UndefinedError解决方案.md
rm -f 加入购物车TypeError解决方案.md
rm -f 加入购物车问题解决方案.md
rm -f 用户管理OperationalError解决方案.md
rm -f 图片显示问题修复报告.md
rm -f 商品删除问题解决方案.md
rm -f 最终测试报告.md
rm -f 图片显示问题解决方案.md
rm -f 功能实现总结.md
# 保留: README.md, DEPLOYMENT.md, 项目说明.md
echo "✅ 已删除开发说明文档（保留 README.md, DEPLOYMENT.md, 项目说明.md）"

# 5. 删除 Python 缓存目录
echo "🗑️  删除 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✅ 已删除 Python 缓存"

# 6. 删除迁移脚本（可选，已执行过的迁移脚本）
echo "🗑️  删除已执行的数据库迁移脚本..."
# 这些脚本已经执行过了，可以删除
rm -f fix_order_unique_constraint.py
rm -f add_contact_info_field.py
rm -f add_variants_field.py
rm -f fix_image_display.py
echo "✅ 已删除数据库迁移脚本（迁移已完成）"

echo "=========================================="
echo "✅ 清理完成！"
echo "=========================================="
echo "📋 保留的重要文件："
echo "  - README.md (项目说明)"
echo "  - DEPLOYMENT.md (部署文档)"
echo "  - 项目说明.md (项目说明)"
echo "  - shopping_website.db.backup_20251119_122924 (最新数据库备份)"
echo "=========================================="

