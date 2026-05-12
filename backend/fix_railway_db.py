#!/usr/bin/env python3
"""
Railway 数据库连接问题快速诊断和修复工具
"""

import os
import sys
from dotenv import load_dotenv

def diagnose_railway_db_issue():
    """诊断Railway数据库连接问题"""
    print("=" * 70)
    print("Railway 数据库连接问题诊断")
    print("=" * 70)
    
    # 加载环境变量
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("✓ 已加载 .env 文件")
    else:
        print("⚠ 未找到 .env 文件")
    
    database_url = os.getenv("DATABASE_URL", "")
    
    print("\n当前配置:")
    print("-" * 70)
    
    if not database_url:
        print("❌ DATABASE_URL 未设置")
        print("\n建议:")
        print("  1. 在 Railway 后端服务中设置 DATABASE_URL 环境变量")
        print("  2. 使用公网地址（因为后端和数据库不在同一项目）")
        return False
    
    # 分析当前配置
    print(f"DATABASE_URL: {database_url}")
    
    if 'mysql.railway.internal' in database_url:
        print("\n⚠ 检测到问题: 使用了私有网络地址")
        print("  原因: 后端和数据库不在同一个Railway项目中")
        print("  结果: 无法解析主机名，连接失败")
        return False
    elif 'railway.app' in database_url or 'rlwy.net' in database_url:
        print("\n✓ 使用公网地址（正确）")
        return True
    else:
        print("\n⚠ 未知的数据库地址")
        return False

def generate_fix():
    """生成修复建议"""
    print("\n" + "=" * 70)
    print("修复方案")
    print("=" * 70)
    
    print("\n【方案1: 修改 Railway 环境变量（推荐）】")
    print("-" * 70)
    print("1. 登录 Railway 控制台")
    print("2. 选择你的后端服务")
    print("3. 点击 'Variables' 标签")
    print("4. 修改 DATABASE_URL 环境变量:")
    print("\n   ❌ 错误配置:")
    print("   DATABASE_URL=mysql+pymysql://root:password@mysql.railway.internal:3306/railway")
    print("\n   ✅ 正确配置:")
    print("   DATABASE_URL=mysql+pymysql://root:password@yamabiko.proxy.rlwy.net:17973/railway")
    print("\n5. Railway 会自动重新部署")
    
    print("\n【方案2: 将后端和数据库移到同一项目】")
    print("-" * 70)
    print("1. 创建新的 Railway 项目")
    print("2. 在新项目中添加 MySQL 数据库服务")
    print("3. 在新项目中添加后端服务")
    print("4. 使用私有网络地址:")
    print("   DATABASE_URL=mysql+pymysql://root:password@mysql.railway.internal:3306/railway")
    
    print("\n【方案3: 使用备用数据库配置】")
    print("-" * 70)
    print("在 Railway 后端服务中添加两个环境变量:")
    print("\n   DATABASE_URL=mysql+pymysql://root:password@mysql.railway.internal:3306/railway")
    print("   DATABASE_URL_BACKUP=mysql+pymysql://root:password@yamabiko.proxy.rlwy.net:17973/railway")
    print("\n系统会自动尝试连接主数据库，失败后尝试备用数据库")

def get_railway_connection_info():
    """获取Railway连接信息"""
    print("\n" + "=" * 70)
    print("如何获取正确的数据库连接信息")
    print("=" * 70)
    
    print("\n步骤:")
    print("1. 在 Railway 中选择你的 MySQL 数据库服务")
    print("2. 点击 'Connect' 按钮")
    print("3. 选择 'Public Networking' 标签")
    print("4. 复制连接字符串")
    print("5. 格式应该类似:")
    print("   mysql://root:your_password@yamabiko.proxy.rlwy.net:17973/railway")
    print("6. 将 mysql:// 替换为 mysql+pymysql://")
    print("   mysql+pymysql://root:your_password@yamabiko.proxy.rlwy.net:17973/railway")

def verify_fix():
    """验证修复"""
    print("\n" + "=" * 70)
    print("验证修复")
    print("=" * 70)
    
    print("\n修复后，在 Railway 后端服务日志中应该看到:")
    print("-" * 70)
    print("✓ INFO:database:主数据库: yamabiko.proxy.rlwy.net:17973/railway")
    print("✓ INFO:database:检测到MySQL数据库，使用pymysql驱动")
    print("✓ INFO:database:主数据库连接成功")
    print("✓ INFO:root:数据库初始化成功")
    
    print("\n而不是:")
    print("-" * 70)
    print("❌ ERROR:database:数据库连接测试失败: (pymysql.err.OperationalError)")
    print("   (2003, \"Can't connect to MySQL server on 'mysql.railway.internal'\")")

def test_current_connection():
    """测试当前连接"""
    print("\n" + "=" * 70)
    print("测试当前数据库连接")
    print("=" * 70)
    
    try:
        from database import engine, logger
        
        print("\n正在测试连接...")
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
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
            return False
            
    except ImportError as e:
        print(f"✗ 无法导入数据库模块: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("TerraiNav Railway 数据库连接问题快速修复工具")
    print("=" * 70)
    
    # 1. 诊断问题
    is_correct = diagnose_railway_db_issue()
    
    # 2. 生成修复方案
    generate_fix()
    
    # 3. 获取连接信息
    get_railway_connection_info()
    
    # 4. 验证修复
    verify_fix()
    
    # 5. 测试当前连接
    print("\n" + "=" * 70)
    response = input("\n是否测试当前数据库连接? (y/n): ").strip().lower()
    
    if response == 'y':
        success = test_current_connection()
        
        if success:
            print("\n✓ 数据库连接正常！")
            print("\n下一步:")
            print("  1. 测试用户注册功能")
            print("  2. 测试用户登录功能")
            print("  3. 验证数据完整性")
        else:
            print("\n✗ 数据库连接失败")
            print("\n请按照上述修复方案进行修复")
    
    print("\n" + "=" * 70)
    print("详细文档: RAILWAY_DB_FIX.md")
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