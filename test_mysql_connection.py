#!/usr/bin/env python3
"""
MySQL连接测试脚本
"""

import os
import sys
import pymysql
from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_mysql_connection():
    """测试基础MySQL连接"""
    print("=" * 50)
    print("测试基础MySQL连接")
    print("=" * 50)
    
    # 从.env.example读取配置
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'wodemima',
        'charset': 'utf8mb4'
    }
    
    try:
        # 测试连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset']
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL连接成功！")
            print(f"   MySQL版本: {version[0]}")
            
            # 检查数据库是否存在
            cursor.execute("SHOW DATABASES LIKE 'medical_insurance'")
            db_exists = cursor.fetchone()
            
            if db_exists:
                print(f"✅ 数据库 'medical_insurance' 已存在")
            else:
                print(f"⚠️  数据库 'medical_insurance' 不存在")
                
                # 询问是否创建数据库
                create_db = input("是否创建数据库 'medical_insurance'? (y/n): ").lower().strip()
                if create_db == 'y':
                    cursor.execute("CREATE DATABASE medical_insurance DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci")
                    print(f"✅ 数据库 'medical_insurance' 创建成功")
        
        connection.close()
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 连接测试出错: {e}")
        return False

def test_database_connection():
    """测试数据库连接（包含指定数据库）"""
    print("\n" + "=" * 50)
    print("测试数据库连接（包含指定数据库）")
    print("=" * 50)
    
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'wodemima',
        'database': 'medical_insurance',
        'charset': 'utf8mb4'
    }
    
    try:
        connection = pymysql.connect(**config)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            print(f"✅ 数据库连接成功！")
            print(f"   当前数据库: {current_db[0]}")
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print(f"✅ 数据库中有 {len(tables)} 个表:")
                for table in tables[:5]:  # 只显示前5个表
                    print(f"   - {table[0]}")
                if len(tables) > 5:
                    print(f"   ... 还有 {len(tables) - 5} 个表")
            else:
                print(f"⚠️  数据库中没有表")
        
        connection.close()
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库连接失败: {e}")
        if "Unknown database" in str(e):
            print("   提示: 数据库不存在，请先运行基础连接测试创建数据库")
        return False
    except Exception as e:
        print(f"❌ 连接测试出错: {e}")
        return False

def test_sdk_database_manager():
    """测试SDK的数据库管理器"""
    print("\n" + "=" * 50)
    print("测试SDK数据库管理器")
    print("=" * 50)
    
    # 设置环境变量
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '3306'
    os.environ['DB_USERNAME'] = 'root'
    os.environ['DB_PASSWORD'] = 'wodemima'
    os.environ['DB_DATABASE'] = 'medical_insurance'
    os.environ['DB_CHARSET'] = 'utf8mb4'
    
    try:
        # 创建配置
        config = DatabaseConfig.from_env()
        print(f"✅ 配置创建成功")
        print(f"   连接URL: {config.get_connection_url()}")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(config)
        print(f"✅ 数据库管理器创建成功")
        
        # 测试连接
        if db_manager.test_connection():
            print(f"✅ SDK数据库连接测试成功")
            
            # 尝试执行简单查询
            try:
                result = db_manager.execute_query("SELECT 1 as test")
                print(f"✅ 查询执行成功: {result}")
            except Exception as e:
                print(f"⚠️  查询执行失败: {e}")
        else:
            print(f"❌ SDK数据库连接测试失败")
            
        db_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ SDK数据库管理器测试失败: {e}")
        return False

def main():
    """主函数"""
    print("MySQL连接测试工具")
    print("=" * 50)
    
    # 检查依赖
    try:
        import pymysql
        print("✅ pymysql 模块已安装")
    except ImportError:
        print("❌ pymysql 模块未安装，请运行: pip install pymysql")
        return
    
    # 运行测试
    tests = [
        ("基础MySQL连接", test_basic_mysql_connection),
        ("数据库连接", test_database_connection),
        ("SDK数据库管理器", test_sdk_database_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n用户中断测试")
            break
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 给出建议
    print("\n建议:")
    if not any(result for _, result in results):
        print("- 检查MySQL服务是否启动")
        print("- 验证用户名和密码是否正确")
        print("- 确认MySQL端口3306是否开放")
        print("- 检查防火墙设置")
    elif results[0][1] and not results[1][1]:
        print("- MySQL连接正常，但数据库不存在")
        print("- 运行数据库初始化脚本创建数据库和表")
    elif all(result for _, result in results):
        print("- 所有连接测试通过！")
        print("- 可以正常使用医保SDK")

if __name__ == "__main__":
    main()