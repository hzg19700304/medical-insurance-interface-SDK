"""
检查数据库表结构
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager

def check_database_tables():
    """检查数据库表"""
    
    # 从环境变量创建数据库配置
    db_config = DatabaseConfig.from_env()
    
    # 创建数据库管理器
    with DatabaseManager(db_config) as db:
        
        # 查看所有表
        tables = db.execute_query("SHOW TABLES")
        
        print("📋 数据库中的表:")
        if tables:
            for table in tables:
                table_name = list(table.values())[0]
                print(f"   - {table_name}")
                
                # 查看表结构
                columns = db.execute_query(f"DESCRIBE {table_name}")
                print(f"     字段:")
                for col in columns:
                    print(f"       {col['Field']} ({col['Type']}) - {col['Null']} - {col['Key']}")
                print()
        else:
            print("   (没有找到任何表)")

if __name__ == "__main__":
    try:
        check_database_tables()
    except Exception as e:
        print(f"❌ 检查失败: {e}")