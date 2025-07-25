#!/usr/bin/env python3
"""
设置测试数据
插入测试机构和接口配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
import json

def setup_test_data():
    """设置测试数据"""
    try:
        print("🔧 设置测试数据...")
        
        # 初始化数据库连接
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 插入测试机构配置
            print("📋 插入测试机构配置...")
            
            # 先删除可能存在的测试数据
            cursor.execute("DELETE FROM medical_organization_config WHERE org_code = 'H43010000001'")
            
            org_insert_sql = """
                INSERT INTO medical_organization_config 
                (org_code, org_name, org_type, province_code, city_code, area_code,
                 app_id, app_secret, base_url, crypto_type, sign_type,
                 default_timeout, connect_timeout, read_timeout, max_retry_times, retry_interval,
                 extra_config, gateway_config, is_active, is_test_env, health_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            org_data = (
                'H43010000001',  # org_code
                '测试医院',       # org_name
                'hospital',      # org_type
                '430000',        # province_code
                '430100',        # city_code
                '430102',        # area_code
                'test_app_id',   # app_id
                'test_app_secret', # app_secret
                'http://localhost:8080/api', # base_url
                'SM4',           # crypto_type
                'SM3',           # sign_type
                30,              # default_timeout
                10,              # connect_timeout
                30,              # read_timeout
                3,               # max_retry_times
                1000,            # retry_interval
                '{}',            # extra_config
                '{}',            # gateway_config
                True,            # is_active
                True,            # is_test_env
                'healthy'        # health_status
            )
            
            cursor.execute(org_insert_sql, org_data)
            print("✅ 测试机构配置插入成功")
            
            # 2. 插入1101接口配置
            print("📋 插入1101接口配置...")
            
            # 先删除可能存在的配置
            cursor.execute("DELETE FROM medical_interface_config WHERE api_code = '1101'")
            
            interface_1101_sql = """
                INSERT INTO medical_interface_config 
                (api_code, api_name, api_description, business_category, business_type,
                 required_params, validation_rules, response_mapping,
                 timeout_seconds, max_retry_times, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            interface_1101_data = (
                '1101',                    # api_code
                '人员信息获取',             # api_name
                '人员信息获取接口',         # api_description
                'person',                  # business_category
                'query',                   # business_type
                json.dumps({               # required_params
                    "psn_no": {"type": "string", "description": "人员编号"},
                    "mdtrt_cert_type": {"type": "string", "description": "就诊凭证类型"},
                    "psn_name": {"type": "string", "description": "人员姓名"}
                }),
                json.dumps({               # validation_rules
                    "psn_no": {"required": True, "type": "string"},
                    "mdtrt_cert_type": {"required": True, "type": "string"},
                    "psn_name": {"required": False, "type": "string"}
                }),
                json.dumps({               # response_mapping
                    "baseinfo": {
                        "psn_no": "人员编号",
                        "psn_name": "姓名",
                        "gend": "性别",
                        "brdy": "出生日期"
                    }
                }),
                30,                        # timeout_seconds
                3,                         # max_retry_times
                True                       # is_active
            )
            
            cursor.execute(interface_1101_sql, interface_1101_data)
            print("✅ 1101接口配置插入成功")
            
            # 3. 插入2201接口配置
            print("📋 插入2201接口配置...")
            
            # 先删除可能存在的配置
            cursor.execute("DELETE FROM medical_interface_config WHERE api_code = '2201'")
            
            interface_2201_data = (
                '2201',                    # api_code
                '门诊挂号',                # api_name
                '门诊挂号接口',            # api_description
                'outpatient',              # business_category
                'register',                # business_type
                json.dumps({               # required_params
                    "psn_no": {"type": "string", "description": "人员编号"},
                    "mdtrt_cert_type": {"type": "string", "description": "就诊凭证类型"},
                    "ipt_otp_no": {"type": "string", "description": "住院/门诊号"}
                }),
                json.dumps({               # validation_rules
                    "psn_no": {"required": True, "type": "string"},
                    "mdtrt_cert_type": {"required": True, "type": "string"},
                    "ipt_otp_no": {"required": True, "type": "string"}
                }),
                json.dumps({               # response_mapping
                    "output": {
                        "mdtrt_id": "就诊ID",
                        "psn_no": "人员编号",
                        "ipt_otp_no": "门诊号"
                    }
                }),
                30,                        # timeout_seconds
                3,                         # max_retry_times
                True                       # is_active
            )
            
            cursor.execute(interface_1101_sql, interface_2201_data)
            print("✅ 2201接口配置插入成功")
            
            # 提交事务
            conn.commit()
            
            # 4. 验证插入结果
            print("\n🔍 验证插入结果...")
            
            cursor.execute("SELECT org_code, org_name FROM medical_organization_config WHERE org_code = 'H43010000001'")
            org_result = cursor.fetchone()
            if org_result:
                print(f"✅ 机构配置: {org_result['org_code']} - {org_result['org_name']}")
            else:
                print("❌ 机构配置未找到")
            
            cursor.execute("SELECT api_code, api_name FROM medical_interface_config WHERE api_code IN ('1101', '2201')")
            interface_results = cursor.fetchall()
            for result in interface_results:
                print(f"✅ 接口配置: {result['api_code']} - {result['api_name']}")
            
            print("\n🎉 测试数据设置完成！")
            
    except Exception as e:
        print(f"❌ 设置测试数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_test_data()