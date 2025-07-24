"""
更新机构配置的base_url为正确的Apifox Mock URL
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager

def update_organization_config():
    """更新机构配置"""
    
    # 从环境变量创建数据库配置
    db_config = DatabaseConfig.from_env()
    
    # 创建数据库管理器
    with DatabaseManager(db_config) as db:
        
        # 正确的Apifox Mock URL
        correct_base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default/fsi/api/rsfComIfsService/callService"
        
        print(f"🔧 更新TEST001机构的base_url为: {correct_base_url}")
        
        # 更新机构配置
        affected_rows = db.execute_update("""
            UPDATE medical_organization_config 
            SET base_url = %s, updated_at = NOW()
            WHERE org_code = %s
        """, (correct_base_url, "TEST001"))
        
        if affected_rows > 0:
            print("✅ 机构配置更新成功")
            
            # 验证更新结果
            updated_config = db.execute_query_one(
                "SELECT org_code, org_name, base_url FROM medical_organization_config WHERE org_code = %s",
                ("TEST001",)
            )
            
            if updated_config:
                print(f"✅ 验证成功:")
                print(f"   - 机构代码: {updated_config['org_code']}")
                print(f"   - 机构名称: {updated_config['org_name']}")
                print(f"   - 基础URL: {updated_config['base_url']}")
                
                print(f"\n📋 完整的接口URL将是:")
                print(f"   - 1101接口: {updated_config['base_url']}/1101")
                print(f"   - 2201接口: {updated_config['base_url']}/2201")
            else:
                print("❌ 验证失败：无法找到更新后的配置")
        else:
            print("❌ 更新失败：没有找到TEST001机构或没有变更")

if __name__ == "__main__":
    try:
        update_organization_config()
    except Exception as e:
        print(f"❌ 更新配置失败: {e}")