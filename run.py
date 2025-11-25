#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
购物网站启动脚本
"""

import os
import sys
from app import app, db

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("✅ 数据库初始化完成")

def create_admin_user():
    """创建管理员用户"""
    from app import User
    
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                phone='1234567890',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ 管理员账户已创建: admin / admin123")
        else:
            print("ℹ️  管理员账户已存在")

def add_sample_products():
    """添加示例商品"""
    from app import Product
    
    with app.app_context():
        # 检查是否已有商品
        if Product.query.count() > 0:
            print("ℹ️  商品数据已存在，跳过示例商品添加")
            return
        
        sample_products = [
            {
                'name': '苹果 iPhone 15',
                'price': 5999.00,
                'description': '最新款iPhone，配备A17 Pro芯片，48MP主摄像头，支持5G网络。颜色：深空黑色、蓝色、粉色、黄色、绿色。存储：128GB/256GB/512GB/1TB可选。',
                'stock': 50
            },
            {
                'name': '华为 Mate 60 Pro',
                'price': 6999.00,
                'description': '华为旗舰手机，麒麟9000S芯片，5000万像素超感知摄像头，支持卫星通话。颜色：雅川青、雅丹黑、南糯紫、白沙银。存储：256GB/512GB/1TB可选。',
                'stock': 30
            },
            {
                'name': '小米 14 Ultra',
                'price': 5499.00,
                'description': '小米影像旗舰，骁龙8 Gen3处理器，徕卡专业摄影系统，120W快充。颜色：黑色、白色、蓝色。存储：256GB/512GB/1TB可选。',
                'stock': 25
            },
            {
                'name': 'MacBook Pro 14英寸',
                'price': 14999.00,
                'description': 'Apple M3 Pro芯片，14.2英寸Liquid Retina XDR显示屏，8核CPU，11核GPU。颜色：深空灰色、银色。存储：512GB/1TB/2TB/4TB/8TB可选。',
                'stock': 15
            },
            {
                'name': 'iPad Air 第5代',
                'price': 4399.00,
                'description': 'Apple M1芯片，10.9英寸Liquid Retina显示屏，支持Apple Pencil 2代。颜色：深空灰色、银色、粉色、紫色、蓝色。存储：64GB/256GB可选。',
                'stock': 40
            },
            {
                'name': 'AirPods Pro 第2代',
                'price': 1899.00,
                'description': 'Apple H2芯片，主动降噪，空间音频，MagSafe充电盒。支持USB-C充电，最长6小时聆听时间。',
                'stock': 100
            }
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        print(f"✅ 已添加 {len(sample_products)} 个示例商品")

def main():
    """主函数"""
    print("🚀 正在启动购物网站...")
    print("=" * 50)
    
    # 创建必要的目录
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    # 初始化数据库
    init_database()
    
    # 创建管理员用户
    create_admin_user()
    
    # 添加示例商品
    add_sample_products()
    
    print("=" * 50)
    print("🎉 购物网站启动完成！")
    print("📱 访问地址: http://localhost:5000")
    print("👤 管理员账户: admin / admin123")
    print("🛒 开始您的购物之旅吧！")
    print("=" * 50)
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
