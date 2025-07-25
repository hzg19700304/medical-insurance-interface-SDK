#!/usr/bin/env python3
"""
更新测试数据中的URL配置
使用Apifox Mock服务器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig

def update_test_urls():
    """更新测试URL配置"""
    try:
        print("🔧 更新测试URL配置...")
        
        # 初始化数据库连接
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 更新机构配置中的base_url
            # 使用Apifox Mock服务器URL
            apifox_mock_url = "https://mock.apifox.com/m1/5678901-5234567-default"
            
            update_org_sql = """
                UPDATE medical_organization_config 
                SET base_url = %s 
                WHERE org_code = 'H43010000001'
            """
            
            cursor.execute(update_org_sql, (apifox_mock_url,))
            
            # 验证更新结果
            cursor.execute("SELECT org_code, base_url FROM medical_organization_config WHERE org_code = 'H43010000001'")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ 机构配置已更新:")
                print(f"   机构代码: {result['org_code']}")
                print(f"   Base URL: {result['base_url']}")
            
            conn.commit()
            print("🎉 URL配置更新完成！")
            
    except Exception as e:
        print(f"❌ 更新URL配置失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_test_urls()