#!/usr/bin/env python3
"""
设置异步处理系统所需的数据库表
"""

import os
import sys
import pymysql
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_database():
    """设置数据库"""
    
    # 数据库连接参数（从.env文件中获取）
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'wodemima',
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接到MySQL服务器
        print("连接到MySQL服务器...")
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            # 创建数据库
            print("创建数据库 medical_insurance...")
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS medical_insurance 
                DEFAULT CHARACTER SET utf8mb4 
                DEFAULT COLLATE utf8mb4_unicode_ci
            """)
            
            # 使用数据库
            cursor.execute("USE medical_insurance")
            
            # 创建异步任务状态表
            print("创建异步任务状态表...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS async_task_status (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    task_id VARCHAR(255) NOT NULL UNIQUE COMMENT '任务ID',
                    status VARCHAR(50) NOT NULL COMMENT '任务状态：PENDING/PROCESSING/SUCCESS/FAILURE/RETRY/REVOKED',
                    data JSON COMMENT '任务数据和结果',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    
                    INDEX idx_task_status (status),
                    INDEX idx_created_at (created_at),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异步任务状态表'
            """)
            
            # 检查表是否创建成功
            cursor.execute("SHOW TABLES LIKE 'async_task_status'")
            result = cursor.fetchone()
            
            if result:
                print("✓ 异步任务状态表创建成功")
                
                # 检查表结构
                cursor.execute("DESCRIBE async_task_status")
                columns = cursor.fetchall()
                print("表结构:")
                for column in columns:
                    print(f"  - {column[0]}: {column[1]}")
            else:
                print("✗ 异步任务状态表创建失败")
                return False
        
        connection.commit()
        print("✓ 数据库设置完成")
        return True
        
    except Exception as e:
        print(f"✗ 数据库设置失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def test_database_connection():
    """测试数据库连接"""
    
    try:
        # 使用SDK的数据库配置
        from medical_insurance_sdk.core.database import DatabaseConfig
        
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv('medical_insurance_sdk/.env')
        
        db_config = DatabaseConfig.from_env()
        
        print("测试数据库连接...")
        print(f"连接参数: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # 创建连接
        connection = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset=db_config.charset
        )
        
        with connection.cursor() as cursor:
            # 测试查询
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print("✓ 数据库连接测试成功")
                
                # 测试异步任务状态表
                cursor.execute("SELECT COUNT(*) FROM async_task_status")
                count = cursor.fetchone()[0]
                print(f"✓ 异步任务状态表可访问，当前记录数: {count}")
                
                return True
            else:
                print("✗ 数据库连接测试失败")
                return False
                
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """主函数"""
    print("设置异步处理系统数据库...")
    print("=" * 50)
    
    # 设置数据库
    if setup_database():
        print("\n" + "=" * 50)
        # 测试连接
        if test_database_connection():
            print("✓ 异步处理系统数据库设置完成！")
            return 0
        else:
            print("✗ 数据库连接测试失败")
            return 1
    else:
        print("✗ 数据库设置失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())