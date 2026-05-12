#!/usr/bin/env python3
"""
MySQL 认证问题快速诊断工具
"""

import sys
import subprocess
from sqlalchemy import text

def check_cryptography():
    """检查 cryptography 包是否已安装"""
    print("=" * 70)
    print("检查 cryptography 包")
    print("=" * 70)
    
    try:
        import cryptography
        print(f"✓ cryptography 包已安装")
        print(f"  版本: {cryptography.__version__}")
        return True
    except ImportError:
        print("✗ cryptography 包未安装")
        print("\n安装方法:")
        print("  pip install cryptography>=41.0.0")
        return False

def check_mysql_auth():
    """检查MySQL认证方法"""
    print("\n" + "=" * 70)
    print("检查MySQL认证方法")
    print("=" * 70)
    
    try:
        from database import engine, logger
        
        if engine.dialect.name == 'mysql':
            print("✓ 使用MySQL数据库")
            
            try:
                with engine.connect() as conn:
                    # 检查MySQL版本
                    version_result = conn.execute(text("SELECT VERSION()"))
                    version = version_result.fetchone()
                    if version:
                        print(f"  MySQL版本: {version[0]}")
                        
                        # 检查默认认证方法
                        if '8.0' in version[0]:
                            print("  ⚠ MySQL 8.0+ 默认使用 caching_sha2_password")
                            print("  ⚠ 需要 cryptography 包支持")
                        else:
                            print("  ✓ MySQL 5.7 或更早版本")
                    
                    # 检查当前用户的认证方法
                    user_result = conn.execute(text("SELECT user, host, plugin FROM mysql.user WHERE user='root'"))
                    users = user_result.fetchall()
                    
                    if users:
                        print("\n  Root用户认证方法:")
                        for user in users:
                            print(f"    {user[0]}@{user[1]}: {user[2]}")
                            
                            if 'sha256' in user[2].lower() or 'caching' in user[2].lower():
                                print(f"      ⚠ 需要 cryptography 包")
                    
                    return True
            except Exception as e:
                print(f"✗ 无法连接到MySQL: {e}")
                return False
        else:
            print(f"ℹ 当前使用数据库: {engine.dialect.name}")
            return False
            
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def test_connection():
    """测试数据库连接"""
    print("\n" + "=" * 70)
    print("测试数据库连接")
    print("=" * 70)
    
    try:
        from database import engine, logger
        
        print("\n正在测试连接...")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✓ 数据库连接成功")
                print(f"  数据库类型: {engine.dialect.name}")
                print(f"  数据库驱动: {engine.driver}")
                
                # 显示连接的主机
                if '@' in str(engine.url):
                    parts = str(engine.url).split('@')
                    if len(parts) > 1:
                        host_part = parts[1].split('/')[0]
                        print(f"  连接主机: {host_part}")
                
                return True
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            
            if 'cryptography' in str(e):
                print("\n  原因: 缺少 cryptography 包")
                print("  解决: pip install cryptography>=41.0.0")
            
            return False
            
    except ImportError as e:
        print(f"✗ 无法导入数据库模块: {e}")
        return False

def check_requirements():
    """检查 requirements.txt"""
    print("\n" + "=" * 70)
    print("检查 requirements.txt")
    print("=" * 70)
    
    import os
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            content = f.read()
        
        if 'cryptography' in content:
            print("✓ requirements.txt 包含 cryptography")
            
            # 提取版本
            for line in content.split('\n'):
                if 'cryptography' in line:
                    print(f"  {line.strip()}")
            
            return True
        else:
            print("✗ requirements.txt 不包含 cryptography")
            print("\n  需要添加:")
            print("  cryptography>=41.0.0")
            return False
    else:
        print("✗ 未找到 requirements.txt")
        return False

def generate_fix():
    """生成修复建议"""
    print("\n" + "=" * 70)
    print("修复建议")
    print("=" * 70)
    
    print("\n【快速修复】")
    print("-" * 70)
    print("1. requirements.txt 已更新，添加了 cryptography>=41.0.0")
    print("2. 提交并推送代码:")
    print("   git add requirements.txt")
    print("   git commit -m 'fix: 添加cryptography包支持MySQL 8.0+认证'")
    print("   git push")
    print("3. Railway 会自动重新部署")
    print("4. 查看日志确认连接成功")
    
    print("\n【本地测试】")
    print("-" * 70)
    print("如果需要在本地测试:")
    print("  pip install -r requirements.txt")
    print("  python test_db.py")

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("TerraiNav MySQL 认证问题诊断工具")
    print("=" * 70)
    
    # 1. 检查 cryptography 包
    has_cryptography = check_cryptography()
    
    # 2. 检查 MySQL 认证方法
    check_mysql_auth()
    
    # 3. 检查 requirements.txt
    has_in_requirements = check_requirements()
    
    # 4. 测试连接
    connection_ok = test_connection()
    
    # 5. 生成修复建议
    generate_fix()
    
    # 6. 总结
    print("\n" + "=" * 70)
    print("诊断总结")
    print("=" * 70)
    
    print(f"\n✓ cryptography 包已安装: {has_cryptography}")
    print(f"✓ requirements.txt 包含 cryptography: {has_in_requirements}")
    print(f"✓ 数据库连接成功: {connection_ok}")
    
    if not has_cryptography:
        print("\n⚠ 需要安装 cryptography 包:")
        print("  pip install cryptography>=41.0.0")
    
    if not connection_ok:
        print("\n⚠ 数据库连接失败，请检查:")
        print("  1. cryptography 包是否已安装")
        print("  2. Railway 环境变量配置")
        print("  3. MySQL 数据库服务状态")
    
    if has_cryptography and connection_ok:
        print("\n✓ 所有检查通过！数据库连接正常")
    else:
        print("\n⚠ 需要按照上述修复建议进行修复")
    
    print("\n" + "=" * 70)
    print("详细文档: MYSQL_AUTH_FIX.md")
    print("=" * 70)

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