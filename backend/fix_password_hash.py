#!/usr/bin/env python3
"""
快速修复明文密码问题
将数据库中的明文密码转换为正确的密码哈希
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def fix_password_hash():
    """修复密码哈希问题"""
    print("=" * 70)
    print("修复明文密码问题")
    print("=" * 70)
    
    try:
        from database import engine
        from werkzeug.security import generate_password_hash, check_password_hash
        
        with engine.connect() as conn:
            # 1. 检查当前密码哈希
            print("\n1. 检查当前密码哈希...")
            result = conn.execute(text("SELECT id, username, password_hash FROM users WHERE username = :username"), {"username": "sw0rds"})
            user = result.fetchone()
            
            if not user:
                print("   ✗ 用户不存在")
                return False
            
            user_id, username, current_hash = user
            print(f"   用户ID: {user_id}")
            print(f"   用户名: {username}")
            print(f"   当前密码哈希: {current_hash}")
            
            # 2. 检查是否是明文密码
            print("\n2. 检查密码哈希格式...")
            if current_hash == "qwe123456":
                print("   ⚠ 发现问题: password_hash 是明文密码！")
                print("   这就是登录失败的原因。")
                
                # 3. 生成正确的密码哈希
                print("\n3. 生成正确的密码哈希...")
                new_hash = generate_password_hash("qwe123456")
                print(f"   新密码哈希: {new_hash}")
                
                # 4. 更新数据库
                print("\n4. 更新数据库...")
                conn.execute(text("UPDATE users SET password_hash = :hash WHERE id = :id"), 
                            {"hash": new_hash, "id": user_id})
                conn.commit()
                print("   ✓ 密码哈希已更新")
                
                # 5. 验证修复
                print("\n5. 验证修复...")
                result = conn.execute(text("SELECT password_hash FROM users WHERE id = :id"), {"id": user_id})
                updated_hash = result.fetchone()[0]
                
                is_valid = check_password_hash(updated_hash, "qwe123456")
                print(f"   密码验证结果: {'✓ 成功' if is_valid else '✗ 失败'}")
                
                if is_valid:
                    print("\n" + "=" * 70)
                    print("✓✓✓ 问题已解决！")
                    print("=" * 70)
                    print("\n现在可以使用以下凭据登录:")
                    print(f"  用户名: {username}")
                    print(f"  密码: qwe123456")
                    print("\n请测试登录功能。")
                    return True
                else:
                    print("\n✗ 验证失败，请检查错误")
                    return False
                    
            else:
                print("   ✓ 密码哈希格式正确")
                
                # 测试密码验证
                is_valid = check_password_hash(current_hash, "qwe123456")
                print(f"   密码验证结果: {'✓ 成功' if is_valid else '✗ 失败'}")
                
                if not is_valid:
                    print("\n   ⚠ 密码哈希格式正确但验证失败")
                    print("   可能是密码不匹配，需要重置密码")
                    
                    # 重新生成密码哈希
                    print("\n   重新生成密码哈希...")
                    new_hash = generate_password_hash("qwe123456")
                    conn.execute(text("UPDATE users SET password_hash = :hash WHERE id = :id"), 
                                {"hash": new_hash, "id": user_id})
                    conn.commit()
                    print("   ✓ 密码哈希已重置")
                    
                    # 验证
                    result = conn.execute(text("SELECT password_hash FROM users WHERE id = :id"), {"id": user_id})
                    updated_hash = result.fetchone()[0]
                    is_valid = check_password_hash(updated_hash, "qwe123456")
                    print(f"   新密码验证结果: {'✓ 成功' if is_valid else '✗ 失败'}")
                    
                    if is_valid:
                        print("\n✓✓✓ 问题已解决！")
                        return True
                else:
                    print("\n✓ 密码验证成功，问题可能在其他地方")
                    return False
        
    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = fix_password_hash()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)