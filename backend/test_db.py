"""
数据库测试脚本
用于测试数据库连接和用户认证
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from database import engine, get_db, UserManager
from models import Base

def test_database_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("测试数据库连接...")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print(f"✓ 数据库连接成功")
            print(f"  数据库类型: {engine.dialect.name}")
            print(f"  数据库驱动: {engine.driver}")
            print(f"  数据库URL: {engine.url}")
            
            # 如果是MySQL，显示MySQL版本
            if engine.dialect.name == 'mysql':
                try:
                    version_result = conn.execute("SELECT VERSION()")
                    version = version_result.fetchone()
                    if version:
                        print(f"  MySQL版本: {version[0]}")
                except Exception as e:
                    print(f"  无法获取MySQL版本: {e}")
            
            return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def test_user_authentication(username, password):
    """测试用户认证"""
    print("\n" + "=" * 50)
    print(f"测试用户认证: {username}")
    print("=" * 50)
    
    user = UserManager.authenticate_user(username, password)
    
    if user:
        print(f"✓ 用户认证成功")
        print(f"  用户ID: {user.id}")
        print(f"  用户名: {user.username}")
        print(f"  邮箱: {user.email}")
        print(f"  用户类型: {user.usertype}")
        print(f"  创建时间: {user.created_at}")
        return True
    else:
        print(f"✗ 用户认证失败")
        print(f"  可能原因:")
        print(f"  1. 用户名不存在")
        print(f"  2. 密码错误")
        print(f"  3. 数据库连接问题")
        return False

def list_all_users():
    """列出所有用户"""
    print("\n" + "=" * 50)
    print("数据库中的所有用户:")
    print("=" * 50)
    
    db = get_db()
    try:
        from models import User
        users = db.query(User).all()
        
        if not users:
            print("  数据库中没有用户")
        else:
            for user in users:
                print(f"  ID: {user.id}")
                print(f"  用户名: {user.username}")
                print(f"  邮箱: {user.email}")
                print(f"  用户类型: {user.usertype}")
                print(f"  创建时间: {user.created_at}")
                print(f"  密码哈希: {user.password_hash[:50]}...")
                print("  " + "-" * 40)
        
        return users
    except Exception as e:
        print(f"  查询用户失败: {e}")
        return []
    finally:
        db.close()

def create_test_user():
    """创建测试用户"""
    print("\n" + "=" * 50)
    print("创建测试用户")
    print("=" * 50)
    
    username = "testuser"
    email = "test@example.com"
    password = "test123456"
    
    user = UserManager.create_user(username, email, password)
    
    if user:
        print(f"✓ 测试用户创建成功")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  邮箱: {email}")
        return user
    else:
        print(f"✗ 测试用户创建失败（可能已存在）")
        return None

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("TerraiNav 数据库诊断工具")
    print("=" * 50)
    
    # 1. 测试数据库连接
    if not test_database_connection():
        print("\n✗ 数据库连接失败，请检查 DATABASE_URL 环境变量")
        sys.exit(1)
    
    # 2. 列出所有用户
    users = list_all_users()
    
    # 3. 测试特定用户认证
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        test_user_authentication(username, password)
    else:
        print("\n提示: 使用以下命令测试特定用户:")
        print(f"  python {sys.argv[0]} <username> <password>")
        print(f"\n例如:")
        print(f"  python {sys.argv[0]} SW0rds qwe123456")
    
    # 4. 询问是否创建测试用户
    if len(sys.argv) < 3:
        response = input("\n是否创建测试用户? (y/n): ")
        if response.lower() == 'y':
            create_test_user()
    
    print("\n" + "=" * 50)
    print("诊断完成")
    print("=" * 50)