#!/usr/bin/env python3
"""
脚本：更新管理员权限
- 移除所有现有管理员的管理员权限
- 将用户 "U Eike Soe" 设置为管理员
"""

from app import app, db
from app import User

def update_admin_permissions():
    with app.app_context():
        try:
            # 1. 移除所有现有管理员的管理员权限
            print("正在查找所有管理员...")
            admins = User.query.filter_by(is_admin=True).all()
            print(f"找到 {len(admins)} 个管理员:")
            for admin in admins:
                print(f"  - ID: {admin.id}, 用户名: {admin.username}, 邮箱: {admin.email}")
            
            # 移除所有管理员权限
            for admin in admins:
                admin.is_admin = False
                print(f"已移除 {admin.username} 的管理员权限")
            
            # 2. 查找用户 "U Eike Soe"
            print("\n正在查找用户 'U Eike Soe'...")
            target_user = User.query.filter_by(username='U Eike Soe').first()
            
            if not target_user:
                # 尝试查找类似的用户名
                print("未找到精确匹配，正在搜索包含 'Eike' 或 'Soe' 的用户...")
                all_users = User.query.all()
                similar_users = []
                for user in all_users:
                    if 'eike' in user.username.lower() or 'soe' in user.username.lower():
                        similar_users.append(user)
                
                if similar_users:
                    print("找到相似的用户:")
                    for user in similar_users:
                        print(f"  - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
                    print("\n请确认要设置为管理员的用户ID，或修改脚本中的用户名。")
                    return False
                else:
                    print("错误: 未找到用户 'U Eike Soe' 或相似的用户")
                    print("\n所有用户列表:")
                    all_users = User.query.all()
                    for user in all_users:
                        print(f"  - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
                    return False
            else:
                print(f"找到用户: ID={target_user.id}, 用户名={target_user.username}, 邮箱={target_user.email}")
            
            # 3. 将目标用户设置为管理员
            target_user.is_admin = True
            print(f"已将 {target_user.username} 设置为管理员")
            
            # 4. 提交更改
            db.session.commit()
            print("\n✅ 操作成功完成!")
            print(f"\n当前管理员状态:")
            admins = User.query.filter_by(is_admin=True).all()
            if admins:
                for admin in admins:
                    print(f"  - {admin.username} ({admin.email})")
            else:
                print("  (无管理员)")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("管理员权限更新脚本")
    print("=" * 60)
    print()
    
    success = update_admin_permissions()
    
    if success:
        print("\n" + "=" * 60)
        print("脚本执行完成")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("脚本执行失败，请检查错误信息")
        print("=" * 60)
        exit(1)

