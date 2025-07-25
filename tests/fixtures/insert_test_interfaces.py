"""
插入测试接口配置
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
import json

def insert_test_interfaces():
    """插入测试接口配置"""
    try:
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 1101接口配置
        interface_1101 = {
            'api_code': '1101',
            'api_name': '人员信息获取',
            'api_description': '通过人员编号获取参保人员基本信息',
            'business_category': '基础信息业务',
            'business_type': 'query',
            'required_params': json.dumps({
                "psn_no": {"type": "string", "description": "人员编号"}
            }),
            'optional_params': json.dumps({
                "cert_no": {"type": "string", "description": "证件号码"}
            }),
            'default_values': json.dumps({}),
            'request_template': json.dumps({
                "infno": "1101",
                "input": {
                    "psn_no": "${psn_no}",
                    "cert_no": "${cert_no}"
                }
            }),
            'response_mapping': json.dumps({
                "person_name": "output.baseinfo.psn_name",
                "person_id": "output.baseinfo.psn_no",
                "id_card": "output.baseinfo.certno"
            }),
            'validation_rules': json.dumps({}),
            'his_integration_config': json.dumps({
                "field_mappings": {
                    "patient_id": "output.baseinfo.psn_no",
                    "patient_name": "output.baseinfo.psn_name",
                    "id_card": "output.baseinfo.certno",
                    "gender": "output.baseinfo.gend",
                    "birth_date": "output.baseinfo.brdy",
                    "age": "output.baseinfo.age"
                },
                "transformations": {
                    "gender": {
                        "type": "mapping",
                        "mapping": {"1": "M", "2": "F"}
                    }
                },
                "sync_config": {
                    "table_name": "his_patients",
                    "primary_key": "patient_id",
                    "operation": "upsert"
                },
                "consistency_check": {
                    "table_name": "his_patients",
                    "time_field": "updated_at",
                    "key_fields": ["patient_id", "id_card"]
                }
            }),
            'is_active': True
        }
        
        # 2207接口配置
        interface_2207 = {
            'api_code': '2207',
            'api_name': '门诊结算',
            'api_description': '门诊费用结算处理',
            'business_category': '医保服务业务',
            'business_type': 'settlement',
            'required_params': json.dumps({
                "mdtrt_id": {"type": "string", "description": "就医登记号"},
                "psn_no": {"type": "string", "description": "人员编号"}
            }),
            'optional_params': json.dumps({}),
            'default_values': json.dumps({}),
            'request_template': json.dumps({
                "infno": "2207",
                "input": {
                    "mdtrt_id": "${mdtrt_id}",
                    "psn_no": "${psn_no}"
                }
            }),
            'response_mapping': json.dumps({
                "settlement_id": "output.setlinfo.setl_id",
                "total_amount": "output.setlinfo.setl_totlnum"
            }),
            'validation_rules': json.dumps({}),
            'his_integration_config': json.dumps({
                "writeback_mapping": {
                    "field_mappings": {
                        "settlement_id": "output.setlinfo.setl_id",
                        "patient_id": "output.setlinfo.psn_no",
                        "total_amount": "output.setlinfo.setl_totlnum",
                        "insurance_amount": "output.setlinfo.hifp_pay",
                        "personal_amount": "output.setlinfo.psn_pay",
                        "account_amount": "output.setlinfo.acct_pay",
                        "settlement_time": "output.setlinfo.setl_time"
                    },
                    "writeback_config": {
                        "table_name": "his_settlements",
                        "primary_key": "settlement_id",
                        "operation": "upsert"
                    }
                }
            }),
            'is_active': True
        }
        
        # 插入接口配置
        insert_sql = """
            INSERT INTO medical_interface_config 
            (api_code, api_name, api_description, business_category, business_type,
             required_params, optional_params, default_values, request_template,
             response_mapping, validation_rules, his_integration_config, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            api_name = VALUES(api_name),
            api_description = VALUES(api_description),
            business_category = VALUES(business_category),
            business_type = VALUES(business_type),
            required_params = VALUES(required_params),
            optional_params = VALUES(optional_params),
            default_values = VALUES(default_values),
            request_template = VALUES(request_template),
            response_mapping = VALUES(response_mapping),
            validation_rules = VALUES(validation_rules),
            his_integration_config = VALUES(his_integration_config),
            is_active = VALUES(is_active)
        """
        
        # 插入1101接口
        params_1101 = (
            interface_1101['api_code'],
            interface_1101['api_name'],
            interface_1101['api_description'],
            interface_1101['business_category'],
            interface_1101['business_type'],
            interface_1101['required_params'],
            interface_1101['optional_params'],
            interface_1101['default_values'],
            interface_1101['request_template'],
            interface_1101['response_mapping'],
            interface_1101['validation_rules'],
            interface_1101['his_integration_config'],
            interface_1101['is_active']
        )
        
        db_manager.execute_update(insert_sql, params_1101)
        print("✓ 1101接口配置插入成功")
        
        # 插入2207接口
        params_2207 = (
            interface_2207['api_code'],
            interface_2207['api_name'],
            interface_2207['api_description'],
            interface_2207['business_category'],
            interface_2207['business_type'],
            interface_2207['required_params'],
            interface_2207['optional_params'],
            interface_2207['default_values'],
            interface_2207['request_template'],
            interface_2207['response_mapping'],
            interface_2207['validation_rules'],
            interface_2207['his_integration_config'],
            interface_2207['is_active']
        )
        
        db_manager.execute_update(insert_sql, params_2207)
        print("✓ 2207接口配置插入成功")
        
        # 验证插入结果
        verify_sql = """
            SELECT api_code, api_name, is_active
            FROM medical_interface_config 
            WHERE api_code IN ('1101', '2207')
        """
        
        results = db_manager.execute_query(verify_sql)
        print(f"\n验证结果: 插入了{len(results)}个接口配置")
        for result in results:
            print(f"  {result['api_code']}: {result['api_name']} (活跃: {result['is_active']})")
        
    except Exception as e:
        print(f"✗ 插入测试接口配置失败: {e}")

if __name__ == "__main__":
    insert_test_interfaces()