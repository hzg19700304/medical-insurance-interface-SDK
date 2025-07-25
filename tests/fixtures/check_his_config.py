"""
检查HIS集成配置是否正确保存
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
import json

def check_his_config():
    """检查HIS集成配置"""
    try:
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 检查1101接口配置
        sql = """
            SELECT api_code, api_name, his_integration_config
            FROM medical_interface_config 
            WHERE api_code IN ('1101', '2207')
            ORDER BY api_code
        """
        
        results = db_manager.execute_query(sql)
        
        print("=== HIS集成配置检查 ===")
        for result in results:
            print(f"\n接口: {result['api_code']} - {result['api_name']}")
            his_config = result.get('his_integration_config')
            if his_config:
                if isinstance(his_config, str):
                    his_config = json.loads(his_config)
                print(f"HIS配置: {json.dumps(his_config, indent=2, ensure_ascii=False)}")
            else:
                print("HIS配置: 未配置")
        
        # 检查接口是否存在
        check_sql = """
            SELECT COUNT(*) as count
            FROM medical_interface_config 
            WHERE api_code IN ('1101', '2207') AND is_active = 1
        """
        
        count_result = db_manager.execute_query_one(check_sql)
        print(f"\n活跃接口数量: {count_result['count']}")
        
    except Exception as e:
        print(f"✗ 检查HIS配置失败: {e}")

if __name__ == "__main__":
    check_his_config()