#!/usr/bin/env python3
"""
快速诊断用户认证问题
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def main():
    print("=" * 70)
    print("TerraiNav 用户认证问题快速诊断")
    print("=" * 70)
    
    try:
        from database import engine, UserManager
        
        # 1. 检查数据库类型
        print(f"\n1. 数据库类型: {engine.dialect.name}")
        print(f"   数据库URL: {engine.url}")
        
        # 2. 检查用户是否存在
        print(f"\n2. 检查用户 'sw0rds' 是否存在...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, username, email, usertype, created_at FROM users WHERE username = :username"), {"username": "sw0rds"})
            user = result.fetchone()
            
            if user:
                print(f"   ✓ 用户存在:")
                print(f"     ID: {user[0]}")
                print(f"     用户名: {user[1]}")
                print(f"     邮箱: {user[2]}")
                print(f"     用户类型: {user[3]}")
                print(f"     创建时间: {user[4]}")
                
                # 3. 检查密码哈希
                print(f"\n3. 检查密码哈希...")
                result = conn.execute(text("SELECT password_hash FROM users WHERE username = :username"), {"username": "sw0rds"})
                password_hash = result.fetchone()[0]
                print(f"   密码哈希: {password_hash[:50]}..." if len(password_hash) > 50 else f"   密码哈希: {password_hash}")
                
                # 4. 测试密码验证
                print(f"\n4. 测试密码验证...")
                test_password = "qwe123456"
                from werkzeug.security import check_password_hash
                is_valid = check_password_hash(password_hash, test_password)
                print(f"   密码 '{test_password}' 验证结果: {'✓ 正确' if is_valid else '✗ 错误'}")
                
                if not is_valid:
                    print(f"\n   ⚠ 问题发现: 密码哈希不匹配")
                    print(f"   解决方案: 重置用户密码")
                    
                    # 重置密码
                    from werkzeug.security import generate_password_hash
                    new_hash = generate_password_hash(test_password)
                    
                    conn.execute(text("UPDATE users SET password_hash = :hash WHERE username = :username"), 
                                {"hash": new_hash, "username": "sw0rds"})
                    conn.commit()
                    
                    print(f"   ✓ 密码已重置为: {test_password}")
                    
                    # 再次测试
                    result = conn.execute(text("SELECT password_hash FROM users WHERE username = :username"), {"username": "sw0rds"})
                    new_password_hash = result.fetchone()[0]
                    is_valid_now = check_password_hash(new_password_hash, test_password)
                    print(f"   新密码验证结果: {'✓ 正确' if is_valid_now else '✗ 仍然错误'}")
                    
                    if is_valid_now:
                        print(f"\n   ✓✓✓ 问题已解决！现在可以登录了")
                        print(f"   登录凭据:")
                        print(f"     用户名: sw0rds")
                        print(f"     密码: {test_password}")
                else:
                    print(f"\n   ⚠ 问题发现: 密码正确但登录仍然失败")
                    print(f"   可能的原因:")
                    print(f"     1. 前端发送的数据格式不正确")
                    print(f"     2. 后端认证逻辑有问题")
                    print(f"     3. 数据库连接有问题")
                    
                    # 测试完整的认证流程
                    print(f"\n5. 测试完整认证流程...")
                    auth_user = UserManager.authenticate_user("sw0rds", test_password)
                    if auth_user:
                        print(f"   ✓ 认证成功")
                        print(f"     用户ID: {auth_user.id}")
                        print(f"     用户名: {auth_user.username}")
                    else:
                        print(f"   ✗ 认证失败")
                        print(f"   这表明UserManager.authenticate_user()方法有问题")
            else:
                print(f"   ✗ 用户不存在")
                print(f"\n   解决方案: 创建新用户")
                
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash("qwe123456")
                
                conn.execute(text("""
                    INSERT INTO users (username, email, password_hash, usertype, created_at)
                    VALUES (:username, :email, :password_hash, :usertype, NOW())
                """), {
                    "username": "sw0rds",
                    "email": "sw0rds@example.com",
                    "password_hash": password_hash,
                    "usertype": "user"
                })
                conn.commit()
                
                print(f"   ✓ 用户创建成功")
                print(f"   登录凭据:")
                print(f"     用户名: sw0rds")
                print(f"     密码: qwe123456")
        
        print("\n" + "=" * 70)
        print("诊断完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()