"""
插入测试机构配置
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
import json

def insert_test_organization():
    """插入测试机构配置"""
    try:
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 测试机构配置
        org_config = {
            'org_code': 'H43010000001',
            'org_name': '测试医院',
            'org_type': 'hospital',
            'province_code': '430000',
            'city_code': '430100',
            'area_code': '430102',
            'app_id': 'test_app_id',
            'app_secret': 'test_app_secret',
            'base_url': 'http://localhost:8080/api',
            'crypto_type': 'SM4',
            'sign_type': 'SM3',
            'default_timeout': 30,
            'connect_timeout': 10,
            'read_timeout': 30,
            'max_retry_times': 3,
            'retry_interval': 1000,
            'extra_config': json.dumps({
                'his_integration_overrides': {}
            }),
            'gateway_config': json.dumps({}),
            'is_active': True,
            'is_test_env': True,
            'health_status': 'healthy'
        }
        
        # 插入机构配置
        insert_sql = """
            INSERT INTO medical_organization_config 
            (org_code, org_name, org_type, province_code, city_code, area_code,
             app_id, app_secret, base_url, crypto_type, sign_type,
             default_timeout, connect_timeout, read_timeout, max_retry_times, retry_interval,
             extra_config, gateway_config, is_active, is_test_env, health_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            org_name = VALUES(org_name),
            org_type = VALUES(org_type),
            province_code = VALUES(province_code),
            city_code = VALUES(city_code),
            area_code = VALUES(area_code),
            app_id = VALUES(app_id),
            app_secret = VALUES(app_secret),
            base_url = VALUES(base_url),
            crypto_type = VALUES(crypto_type),
            sign_type = VALUES(sign_type),
            default_timeout = VALUES(default_timeout),
            connect_timeout = VALUES(connect_timeout),
            read_timeout = VALUES(read_timeout),
            max_retry_times = VALUES(max_retry_times),
            retry_interval = VALUES(retry_interval),
            extra_config = VALUES(extra_config),
            gateway_config = VALUES(gateway_config),
            is_active = VALUES(is_active),
            is_test_env = VALUES(is_test_env),
            health_status = VALUES(health_status)
        """
        
        params = (
            org_config['org_code'],
            org_config['org_name'],
            org_config['org_type'],
            org_config['province_code'],
            org_config['city_code'],
            org_config['area_code'],
            org_config['app_id'],
            org_config['app_secret'],
            org_config['base_url'],
            org_config['crypto_type'],
            org_config['sign_type'],
            org_config['default_timeout'],
            org_config['connect_timeout'],
            org_config['read_timeout'],
            org_config['max_retry_times'],
            org_config['retry_interval'],
            org_config['extra_config'],
            org_config['gateway_config'],
            org_config['is_active'],
            org_config['is_test_env'],
            org_config['health_status']
        )
        
        db_manager.execute_update(insert_sql, params)
        print("✓ 测试机构配置插入成功")
        
        # 验证插入结果
        verify_sql = """
            SELECT org_code, org_name, is_active
            FROM medical_organization_config 
            WHERE org_code = %s
        """
        
        result = db_manager.execute_query_one(verify_sql, (org_config['org_code'],))
        if result:
            print(f"✓ 验证成功: {result['org_code']} - {result['org_name']} (活跃: {result['is_active']})")
        else:
            print("✗ 验证失败: 未找到插入的机构配置")
        
    except Exception as e:
        print(f"✗ 插入测试机构配置失败: {e}")

if __name__ == "__main__":
    insert_test_organization()