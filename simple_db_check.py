"""
简单的数据库配置检查
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager

def check_database_configs():
    """检查数据库配置"""
    
    # 从环境变量创建数据库配置
    db_config = DatabaseConfig.from_env()
    
    # 创建数据库管理器
    with DatabaseManager(db_config) as db:
        
        print("🔍 检查数据库中的配置表和数据...")
        
        # 1. 检查接口配置表
        print("\n📋 检查接口配置表:")
        try:
            # 检查 medical_interface_config 表
            interfaces = db.execute_query(
                "SELECT api_code, api_name, business_type FROM medical_interface_config ORDER BY api_code LIMIT 10"
            )
            
            if interfaces:
                print(f"   ✅ medical_interface_config 表存在，共 {len(interfaces)} 条记录:")
                for interface in interfaces:
                    print(f"      - {interface['api_code']}: {interface['api_name']} ({interface['business_type']})")
            else:
                print("   ⚠️  medical_interface_config 表存在但无数据")
                
        except Exception as e:
            print(f"   ❌ medical_interface_config 表查询失败: {e}")
            
            # 尝试检查 interface_configs 表
            try:
                interfaces = db.execute_query(
                    "SELECT api_code, api_name, business_type FROM interface_configs ORDER BY api_code LIMIT 10"
                )
                
                if interfaces:
                    print(f"   ✅ interface_configs 表存在，共 {len(interfaces)} 条记录:")
                    for interface in interfaces:
                        print(f"      - {interface['api_code']}: {interface['api_name']} ({interface['business_type']})")
                else:
                    print("   ⚠️  interface_configs 表存在但无数据")
                    
            except Exception as e2:
                print(f"   ❌ interface_configs 表也不存在: {e2}")
        
        # 2. 检查机构配置表
        print("\n🏥 检查机构配置表:")
        try:
            # 检查 medical_organization_config 表
            orgs = db.execute_query(
                "SELECT org_code, org_name, base_url FROM medical_organization_config ORDER BY org_code LIMIT 10"
            )
            
            if orgs:
                print(f"   ✅ medical_organization_config 表存在，共 {len(orgs)} 条记录:")
                for org in orgs:
                    print(f"      - {org['org_code']}: {org['org_name']} ({org['base_url']})")
            else:
                print("   ⚠️  medical_organization_config 表存在但无数据")
                
        except Exception as e:
            print(f"   ❌ medical_organization_config 表查询失败: {e}")
            
            # 尝试检查 organization_configs 表
            try:
                orgs = db.execute_query(
                    "SELECT org_code, org_name, base_url FROM organization_configs ORDER BY org_code LIMIT 10"
                )
                
                if orgs:
                    print(f"   ✅ organization_configs 表存在，共 {len(orgs)} 条记录:")
                    for org in orgs:
                        print(f"      - {org['org_code']}: {org['org_name']} ({org['base_url']})")
                else:
                    print("   ⚠️  organization_configs 表存在但无数据")
                    
            except Exception as e2:
                print(f"   ❌ organization_configs 表也不存在: {e2}")
        
        # 3. 检查特定的配置
        print("\n🔍 检查特定配置:")
        
        # 检查TEST001机构
        try:
            test_org = db.execute_query_one(
                "SELECT * FROM medical_organization_config WHERE org_code = %s",
                ("TEST001",)
            )
            
            if test_org:
                print("   ✅ TEST001机构配置存在:")
                print(f"      - 机构名称: {test_org['org_name']}")
                print(f"      - 基础URL: {test_org['base_url']}")
                print(f"      - 加密类型: {test_org.get('crypto_type', 'N/A')}")
                print(f"      - 签名类型: {test_org.get('sign_type', 'N/A')}")
            else:
                print("   ❌ TEST001机构配置不存在")
                
        except Exception as e:
            print(f"   ❌ 查询TEST001机构配置失败: {e}")
        
        # 检查1101接口
        try:
            interface_1101 = db.execute_query_one(
                "SELECT * FROM medical_interface_config WHERE api_code = %s",
                ("1101",)
            )
            
            if interface_1101:
                print("   ✅ 1101接口配置存在:")
                print(f"      - 接口名称: {interface_1101['api_name']}")
                print(f"      - 业务类型: {interface_1101['business_type']}")
                print(f"      - 必填参数: {interface_1101.get('required_params', 'N/A')}")
            else:
                print("   ❌ 1101接口配置不存在")
                
        except Exception as e:
            print(f"   ❌ 查询1101接口配置失败: {e}")
        
        # 检查2201接口
        try:
            interface_2201 = db.execute_query_one(
                "SELECT * FROM medical_interface_config WHERE api_code = %s",
                ("2201",)
            )
            
            if interface_2201:
                print("   ✅ 2201接口配置存在:")
                print(f"      - 接口名称: {interface_2201['api_name']}")
                print(f"      - 业务类型: {interface_2201['business_type']}")
                print(f"      - 必填参数: {interface_2201.get('required_params', 'N/A')}")
            else:
                print("   ❌ 2201接口配置不存在")
                
        except Exception as e:
            print(f"   ❌ 查询2201接口配置失败: {e}")

if __name__ == "__main__":
    try:
        check_database_configs()
    except Exception as e:
        print(f"❌ 检查失败: {e}")