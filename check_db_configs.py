"""检查数据库中的配置"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.client import MedicalInsuranceClient

def check_database_configs():
    """检查数据库配置"""
    try:
        # 初始化客户端
        client = MedicalInsuranceClient()
        sdk = client.sdk
        
        print("🔍 检查数据库中的配置...")
        
        # 检查接口配置
        print("\n📋 接口配置列表:")
        try:
            # 直接查询数据库
            db_manager = sdk.db_manager
            
            # 查询所有接口配置
            interfaces = db_manager.execute_query(
                "SELECT api_code, api_name, business_type FROM interface_configs ORDER BY api_code"
            )
            
            if interfaces:
                for interface in interfaces:
                    print(f"   - {interface['api_code']}: {interface['api_name']} ({interface['business_type']})")
            else:
                print("   ❌ 没有找到接口配置")
                
        except Exception as e:
            print(f"   ❌ 查询接口配置失败: {e}")
        
        # 检查机构配置
        print("\n🏥 机构配置列表:")
        try:
            orgs = db_manager.execute_query(
                "SELECT org_code, org_name, base_url FROM organization_configs ORDER BY org_code"
            )
            
            if orgs:
                for org in orgs:
                    print(f"   - {org['org_code']}: {org['org_name']} ({org['base_url']})")
            else:
                print("   ❌ 没有找到机构配置")
                
        except Exception as e:
            print(f"   ❌ 查询机构配置失败: {e}")
        
        # 检查验证规则
        print("\n✅ 验证规则列表:")
        try:
            rules = db_manager.execute_query(
                "SELECT api_code, field_name, validation_type FROM validation_rules ORDER BY api_code, field_name"
            )
            
            if rules:
                current_api = None
                for rule in rules:
                    if rule['api_code'] != current_api:
                        current_api = rule['api_code']
                        print(f"   - {current_api}:")
                    print(f"     * {rule['field_name']}: {rule['validation_type']}")
            else:
                print("   ❌ 没有找到验证规则")
                
        except Exception as e:
            print(f"   ❌ 查询验证规则失败: {e}")
            
    except Exception as e:
        print(f"❌ 检查配置失败: {e}")

if __name__ == "__main__":
    check_database_configs()