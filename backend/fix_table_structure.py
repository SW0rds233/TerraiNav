#!/usr/bin/env python3
"""
数据库表结构修复工具
修复MySQL数据库表结构与模型定义不匹配的问题
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text, inspect

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def check_table_structure():
    """检查数据库表结构"""
    print("=" * 70)
    print("检查数据库表结构")
    print("=" * 70)
    
    try:
        from database import engine
        
        inspector = inspect(engine)
        
        # 检查users表
        if 'users' in inspector.get_table_names():
            print("\n✓ users表存在")
            users_columns = inspector.get_columns('users')
            print(f"\nusers表当前字段:")
            print("-" * 70)
            for column in users_columns:
                print(f"  {column['name']}: {column['type']} (nullable: {column['nullable']})")
            
            # 检查缺失的字段
            expected_fields = ['id', 'username', 'email', 'password_hash', 'usertype', 'created_at']
            actual_fields = [col['name'] for col in users_columns]
            missing_fields = set(expected_fields) - set(actual_fields)
            
            if missing_fields:
                print(f"\n⚠ 缺失字段: {', '.join(missing_fields)}")
                return missing_fields
            else:
                print(f"\n✓ users表结构完整")
                return set()
        else:
            print("\n✗ users表不存在")
            return None
            
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def fix_users_table():
    """修复users表结构"""
    print("\n" + "=" * 70)
    print("修复users表结构")
    print("=" * 70)
    
    try:
        from database import engine
        
        with engine.connect() as conn:
            # 检查created_at字段是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'users'
                AND column_name = 'created_at'
            """))
            count = result.fetchone()[0]
            
            if count == 0:
                print("\n添加缺失的字段: created_at")
                
                # 添加created_at字段
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()
                
                print("✓ 成功添加created_at字段")
                
                # 为现有记录设置created_at值
                conn.execute(text("""
                    UPDATE users
                    SET created_at = NOW()
                    WHERE created_at IS NULL
                """))
                conn.commit()
                
                print("✓ 成功更新现有记录的created_at值")
                return True
            else:
                print("\n✓ created_at字段已存在")
                return False
                
    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_history_table():
    """检查history表结构"""
    print("\n" + "=" * 70)
    print("检查history表结构")
    print("=" * 70)
    
    try:
        from database import engine
        
        inspector = inspect(engine)
        
        if 'history' in inspector.get_table_names():
            print("\n✓ history表存在")
            history_columns = inspector.get_columns('history')
            print(f"\nhistory表当前字段:")
            print("-" * 70)
            for column in history_columns:
                print(f"  {column['name']}: {column['type']} (nullable: {column['nullable']})")
            
            # 检查缺失的字段
            expected_fields = ['id', 'user_id', 'task_name', 'input_image_url', 'output_route_url', 'route_data', 'created_at']
            actual_fields = [col['name'] for col in history_columns]
            missing_fields = set(expected_fields) - set(actual_fields)
            
            if missing_fields:
                print(f"\n⚠ 缺失字段: {', '.join(missing_fields)}")
                return missing_fields
            else:
                print(f"\n✓ history表结构完整")
                return set()
        else:
            print("\n✗ history表不存在")
            return None
            
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def fix_history_table():
    """修复history表结构"""
    print("\n" + "=" * 70)
    print("修复history表结构")
    print("=" * 70)
    
    try:
        from database import engine
        
        with engine.connect() as conn:
            # 检查created_at字段是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'history'
                AND column_name = 'created_at'
            """))
            count = result.fetchone()[0]
            
            if count == 0:
                print("\n添加缺失的字段: created_at")
                
                # 添加created_at字段
                conn.execute(text("""
                    ALTER TABLE history
                    ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()
                
                print("✓ 成功添加created_at字段")
                
                # 为现有记录设置created_at值
                conn.execute(text("""
                    UPDATE history
                    SET created_at = NOW()
                    WHERE created_at IS NULL
                """))
                conn.commit()
                
                print("✓ 成功更新现有记录的created_at值")
                return True
            else:
                print("\n✓ created_at字段已存在")
                return False
                
    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def recreate_tables():
    """重新创建表（危险操作，会删除所有数据）"""
    print("\n" + "=" * 70)
    print("重新创建数据库表")
    print("=" * 70)
    print("⚠ 警告: 此操作将删除所有现有数据！")
    
    response = input("确定要继续吗？(输入 'yes' 确认): ").strip()
    if response.lower() != 'yes':
        print("操作已取消")
        return False
    
    try:
        from database import engine
        from models import Base
        
        print("\n正在删除所有表...")
        Base.metadata.drop_all(bind=engine)
        
        print("正在重新创建表...")
        Base.metadata.create_all(bind=engine)
        
        print("✓ 表重新创建成功")
        return True
        
    except Exception as e:
        print(f"\n✗ 重新创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("TerraiNav 数据库表结构修复工具")
    print("=" * 70)
    
    # 1. 检查users表结构
    users_missing = check_table_structure()
    
    # 2. 修复users表
    if users_missing is not None and len(users_missing) > 0:
        print(f"\n发现users表缺失字段，开始修复...")
        fix_users_table()
    
    # 3. 检查history表结构
    history_missing = check_history_table()
    
    # 4. 修复history表
    if history_missing is not None and len(history_missing) > 0:
        print(f"\n发现history表缺失字段，开始修复...")
        fix_history_table()
    
    # 5. 验证修复
    print("\n" + "=" * 70)
    print("验证修复结果")
    print("=" * 70)
    
    users_missing_after = check_table_structure()
    history_missing_after = check_history_table()
    
    # 6. 总结
    print("\n" + "=" * 70)
    print("修复总结")
    print("=" * 70)
    
    if users_missing_after is not None and len(users_missing_after) == 0:
        print("\n✓ users表结构修复成功")
    else:
        print("\n⚠ users表结构仍有问题")
    
    if history_missing_after is not None and len(history_missing_after) == 0:
        print("✓ history表结构修复成功")
    else:
        print("⚠ history表结构仍有问题")
    
    # 7. 提供下一步建议
    print("\n" + "=" * 70)
    print("下一步建议")
    print("=" * 70)
    
    if users_missing_after is not None and len(users_missing_after) == 0:
        print("\n✓ 表结构已修复，现在可以:")
        print("  1. 通过API注册新用户")
        print("  2. 测试登录功能")
        print("\n  注册命令:")
        print('  curl -X POST https://terrainav.up.railway.app/api/auth/register \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"username": "sw0rds", "email": "sw0rds@example.com", "password": "qwe123456"}\'')
    else:
        print("\n⚠ 表结构仍有问题，建议:")
        print("  1. 重新运行此脚本")
        print("  2. 或者选择重新创建表（会删除所有数据）")
        print("  3. 检查数据库连接和权限")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)