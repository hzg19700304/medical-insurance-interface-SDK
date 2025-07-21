"""
添加HIS集成配置字段到接口配置表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig

def add_his_integration_field():
    """添加HIS集成配置字段"""
    try:
        # 从环境变量创建数据库配置
        db_config = DatabaseConfig.from_env()
        print(f"连接数据库: {db_config.host}:{db_config.port}/{db_config.database}")
        
        db_manager = DatabaseManager(db_config)
        
        # 检查字段是否已存在
        check_sql = """
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'medical_interface_config' 
            AND COLUMN_NAME = 'his_integration_config'
        """
        
        result = db_manager.execute_query_one(check_sql, (db_config.database,))
        
        if result['count'] > 0:
            print("✓ his_integration_config字段已存在")
            return
        
        # 添加字段
        alter_sql = """
            ALTER TABLE medical_interface_config 
            ADD COLUMN his_integration_config JSON DEFAULT ('{}') COMMENT 'HIS集成配置（字段映射、同步配置、回写配置等）'
            AFTER province_overrides
        """
        
        db_manager.execute_update(alter_sql)
        print("✓ his_integration_config字段添加成功")
        
        # 验证字段添加
        verify_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'medical_interface_config' 
            AND COLUMN_NAME = 'his_integration_config'
        """
        
        verify_result = db_manager.execute_query_one(verify_sql, (db_config.database,))
        if verify_result:
            print(f"✓ 字段验证成功: {verify_result['COLUMN_NAME']} ({verify_result['DATA_TYPE']})")
        
    except Exception as e:
        print(f"✗ 添加HIS集成配置字段失败: {e}")

if __name__ == "__main__":
    add_his_integration_field()