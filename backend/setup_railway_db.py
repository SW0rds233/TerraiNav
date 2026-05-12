#!/usr/bin/env python3
"""
Railway MySQL 数据库配置助手
帮助用户快速配置和测试数据库连接
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

def check_env_file():
    """检查 .env 文件是否存在"""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    if os.path.exists(env_path):
        print("✓ 找到 .env 文件")
        load_dotenv(env_path)
        
        # 读取并显示当前配置（隐藏密码）
        with open(env_path, 'r') as f:
            content = f.read()
            
        print("\n当前配置:")
        print("-" * 50)
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                if 'PASSWORD' in line.upper() or 'SECRET' in line.upper():
                    # 隐藏密码
                    parts = line.split('=')
                    if len(parts) >= 2:
                        print(f"{parts[0]}=***HIDDEN***")
                else:
                    print(line)
        print("-" * 50)
        return True
    else:
        print("✗ 未找到 .env 文件")
        print(f"  位置: {env_path}")
        return False

def validate_database_url(url):
    """验证 DATABASE_URL 格式"""
    if not url:
        print("✗ DATABASE_URL 未设置")
        return False
    
    print(f"\n验证 DATABASE_URL:")
    print("-" * 50)
    
    # 检查协议
    if url.startswith('mysql://'):
        print("✓ 检测到 MySQL 协议")
        print("  提示: 会自动转换为 mysql+pymysql://")
    elif url.startswith('mysql+pymysql://'):
        print("✓ 检测到 MySQL (pymysql) 协议")
    elif url.startswith('postgresql://'):
        print("✓ 检测到 PostgreSQL 协议")
    elif url.startswith('sqlite://'):
        print("✓ 检测到 SQLite 协议")
    else:
        print("✗ 未知的数据库协议")
        return False
    
    # 检查主机
    if '@' in url:
        parts = url.split('@')
        if len(parts) > 1:
            host_part = parts[1]
            print(f"✓ 主机地址: {host_part.split('/')[0]}")
            
            # 检查是否使用 Railway 私有网络
            if 'mysql.railway.internal' in url:
                print("  ✓ 使用 Railway 私有网络（推荐）")
            elif 'railway.app' in url or 'rlwy.net' in url:
                print("  ⚠ 使用 Railway 公网地址（仅用于本地开发）")
    else:
        print("⚠ URL 格式可能不正确")
    
    print("-" * 50)
    return True

def generate_railway_config():
    """生成 Railway 配置建议"""
    print("\n" + "=" * 60)
    print("Railway MySQL 配置建议")
    print("=" * 60)
    
    print("\n1. 在 Railway 后端服务中设置环境变量:")
    print("-" * 60)
    print("变量名: DATABASE_URL")
    print("变量值: mysql+pymysql://<username>:<password>@mysql.railway.internal:3306/<database>")
    print("\n提示: 在 Railway 数据库服务中点击 'Connect' 获取完整的连接字符串")
    
    print("\n2. 本地开发环境配置:")
    print("-" * 60)
    print("选项 A: 连接到 Railway MySQL（使用公网）")
    print("  DATABASE_URL=mysql+pymysql://<username>:<password>@yamabiko.proxy.rlwy.net:17973/<database>")
    print("\n选项 B: 使用本地 SQLite（推荐）")
    print("  # 不设置 DATABASE_URL，会自动使用 SQLite")
    print("  DATABASE_URL=")
    
    print("\n3. Railway Networking 对比:")
    print("-" * 60)
    print("私有网络 (生产环境推荐):")
    print("  地址: mysql.railway.internal:3306")
    print("  优点: 更快、更安全、免费")
    print("\n公网地址 (仅用于本地开发):")
    print("  地址: yamabiko.proxy.rlwy.net:17973")
    print("  用途: 本地开发、外部工具连接")

def test_connection():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("测试数据库连接")
    print("=" * 60)
    
    try:
        from database import engine, logger
        
        print("\n正在连接数据库...")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✓ 数据库连接成功")
                print(f"  数据库类型: {engine.dialect.name}")
                print(f"  数据库驱动: {engine.driver}")
                
                # 如果是 MySQL，显示更多信息
                if engine.dialect.name == 'mysql':
                    try:
                        version_result = conn.execute(text("SELECT VERSION()"))
                        version = version_result.fetchone()
                        if version:
                            print(f"  MySQL 版本: {version[0]}")
                    except Exception as e:
                        print(f"  无法获取 MySQL 版本: {e}")
                    
                    # 显示数据库列表
                    try:
                        db_result = conn.execute(text("SHOW DATABASES"))
                        databases = [row[0] for row in db_result.fetchall()]
                        print(f"  可用数据库: {', '.join(databases)}")
                    except Exception as e:
                        print(f"  无法获取数据库列表: {e}")
                
                return True
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            print("\n可能的原因:")
            print("  1. DATABASE_URL 配置错误")
            print("  2. 数据库服务未启动")
            print("  3. 网络连接问题")
            print("  4. 用户名或密码错误")
            return False
            
    except ImportError as e:
        print(f"✗ 无法导入数据库模块: {e}")
        print("  请确保已安装所有依赖: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("TerraiNav Railway MySQL 配置助手")
    print("=" * 60)
    
    # 1. 检查环境文件
    if not check_env_file():
        print("\n提示: 请创建 .env 文件并配置 DATABASE_URL")
        print("      可以参考 .env.example 文件")
    
    # 2. 验证 DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        validate_database_url(database_url)
    else:
        print("\n⚠ DATABASE_URL 未设置")
    
    # 3. 生成配置建议
    generate_railway_config()
    
    # 4. 询问是否测试连接
    print("\n" + "=" * 60)
    response = input("\n是否测试数据库连接? (y/n): ").strip().lower()
    
    if response == 'y':
        success = test_connection()
        if success:
            print("\n✓ 配置完成！数据库连接正常")
        else:
            print("\n✗ 配置有问题，请检查上述错误信息")
            print("\n建议:")
            print("  1. 检查 Railway 环境变量配置")
            print("  2. 确认数据库服务正在运行")
            print("  3. 验证用户名和密码")
            print("  4. 查看详细配置指南: RAILWAY_MYSQL_SETUP.md")
    
    print("\n" + "=" * 60)

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