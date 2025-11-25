#!/usr/bin/env python3
"""
脚本：恢复管理员权限
- 将 admin 用户恢复为管理员
- 保持 U Eike Soe 的管理员权限（如果存在）
"""

from app import app, db
from app import User

def restore_admin_permissions():
    with app.app_context():
        try:
            print("=" * 60)
            print("恢复管理员权限脚本")
            print("=" * 60)
            print()
            
            # 1. 查找 admin 用户
            print("正在查找 admin 用户...")
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("❌ 错误: 未找到 admin 用户")
                print("\n所有用户列表:")
                all_users = User.query.all()
                for user in all_users:
                    print(f"  - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
                return False
            
            print(f"找到 admin 用户: ID={admin_user.id}, 邮箱={admin_user.email}")
            
            # 2. 恢复 admin 用户的管理员权限
            admin_user.is_admin = True
            print(f"✅ 已将 {admin_user.username} 恢复为管理员")
            
            # 3. 检查 U Eike Soe 用户
            print("\n检查 U Eike Soe 用户...")
            eike_user = User.query.filter_by(username='U Eike Soe').first()
            if eike_user:
                if eike_user.is_admin:
                    print(f"✓ {eike_user.username} 仍然是管理员")
                else:
                    print(f"ℹ️  {eike_user.username} 不是管理员")
            else:
                print("ℹ️  未找到 U Eike Soe 用户")
            
            # 4. 提交更改
            db.session.commit()
            print("\n✅ 操作成功完成!")
            
            # 5. 显示当前所有管理员
            print("\n当前管理员列表:")
            admins = User.query.filter_by(is_admin=True).all()
            if admins:
                for admin in admins:
                    print(f"  - {admin.username} (ID: {admin.id}, 邮箱: {admin.email})")
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
    success = restore_admin_permissions()
    
    if success:
        print("\n" + "=" * 60)
        print("脚本执行完成")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("脚本执行失败，请检查错误信息")
        print("=" * 60)
        exit(1)

