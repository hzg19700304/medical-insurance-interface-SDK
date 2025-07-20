#!/usr/bin/env python3
"""
医保接口SDK配置数据初始化脚本
用于执行任务2.2：初始化配置数据

功能：
1. 插入人员信息获取接口(1101)的完整配置
2. 插入门诊结算接口(2201)的配置数据
3. 创建测试机构的配置数据
"""

import os
import sys
import json
import pymysql
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_database_config():
    """获取数据库配置"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'medical_insurance_sdk'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }

def create_database_connection():
    """创建数据库连接"""
    try:
        config = get_database_config()
        connection = pymysql.connect(**config)
        print(f"✓ 成功连接到MySQL数据库: {config['database']}")
        return connection
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return None

def execute_sql_file(connection, file_path):
    """执行SQL文件"""
    try:
        cursor = connection.cursor()
        
        # 读取SQL文件
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # 分割SQL语句（简单分割，基于分号）
        sql_statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('--') or line.startswith('/*'):
                continue
            
            current_statement += line + " "
            
            # 如果行以分号结尾，表示一个完整的SQL语句
            if line.endswith(';'):
                sql_statements.append(current_statement.strip())
                current_statement = ""
        
        # 执行SQL语句
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(sql_statements):
            if not statement or statement.strip() == ';':
                continue
                
            try:
                # 处理SELECT语句（用于显示信息）
                if statement.upper().strip().startswith('SELECT'):
                    cursor.execute(statement)
                    results = cursor.fetchall()
                    if results:
                        print(f"查询结果: {results}")
                else:
                    cursor.execute(statement)
                    connection.commit()
                
                success_count += 1
                
            except Exception as e:
                print(f"✗ SQL语句执行失败 (第{i+1}条): {e}")
                print(f"  语句: {statement[:100]}...")
                error_count += 1
                continue
        
        cursor.close()
        print(f"✓ SQL文件执行完成: 成功 {success_count} 条，失败 {error_count} 条")
        return error_count == 0
        
    except Exception as e:
        print(f"✗ 执行SQL文件失败: {e}")
        return False

def verify_configuration_data(connection):
    """验证配置数据是否正确插入"""
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        print("\n" + "="*60)
        print("验证配置数据插入结果")
        print("="*60)
        
        # 1. 验证接口配置数据
        print("\n1. 接口配置数据:")
        cursor.execute("""
            SELECT api_code, api_name, business_category, business_type, 
                   is_active, timeout_seconds, created_at
            FROM medical_interface_config 
            ORDER BY api_code
        """)
        
        interface_configs = cursor.fetchall()
        if interface_configs:
            print(f"   ✓ 找到 {len(interface_configs)} 个接口配置:")
            for config in interface_configs:
                print(f"     - {config['api_code']}: {config['api_name']} "
                      f"({config['business_category']}/{config['business_type']})")
        else:
            print("   ✗ 未找到接口配置数据")
            return False
        
        # 2. 验证机构配置数据
        print("\n2. 机构配置数据:")
        cursor.execute("""
            SELECT org_code, org_name, province_code, city_code, 
                   is_active, is_test_env, created_at
            FROM medical_organization_config 
            ORDER BY org_code
        """)
        
        org_configs = cursor.fetchall()
        if org_configs:
            print(f"   ✓ 找到 {len(org_configs)} 个机构配置:")
            for config in org_configs:
                env_type = "测试" if config['is_test_env'] else "生产"
                status = "启用" if config['is_active'] else "禁用"
                print(f"     - {config['org_code']}: {config['org_name']} "
                      f"({env_type}环境, {status})")
        else:
            print("   ✗ 未找到机构配置数据")
            return False
        
        # 3. 验证机构信息数据
        print("\n3. 机构信息数据:")
        cursor.execute("""
            SELECT fixmedins_code, fixmedins_name, fixmedins_type, 
                   hosp_lv, sync_time
            FROM medical_institution_info 
            ORDER BY fixmedins_code
        """)
        
        institution_infos = cursor.fetchall()
        if institution_infos:
            print(f"   ✓ 找到 {len(institution_infos)} 个机构信息:")
            for info in institution_infos:
                print(f"     - {info['fixmedins_code']}: {info['fixmedins_name']} "
                      f"(类型: {info['fixmedins_type']}, 等级: {info['hosp_lv']})")
        else:
            print("   ✗ 未找到机构信息数据")
            return False
        
        # 4. 验证统计数据
        print("\n4. 统计数据:")
        cursor.execute("""
            SELECT COUNT(*) as count FROM medical_interface_stats
        """)
        
        stats_count = cursor.fetchone()['count']
        print(f"   ✓ 找到 {stats_count} 条统计记录")
        
        # 5. 验证特定配置的详细信息
        print("\n5. 关键配置验证:")
        
        # 验证1101接口配置
        cursor.execute("""
            SELECT api_code, required_params, validation_rules, response_mapping
            FROM medical_interface_config 
            WHERE api_code = '1101'
        """)
        
        config_1101 = cursor.fetchone()
        if config_1101:
            required_params = json.loads(config_1101['required_params'])
            validation_rules = json.loads(config_1101['validation_rules'])
            response_mapping = json.loads(config_1101['response_mapping'])
            
            print(f"   ✓ 1101接口配置验证:")
            print(f"     - 必填参数数量: {len(required_params)}")
            print(f"     - 验证规则数量: {len(validation_rules)}")
            print(f"     - 响应映射数量: {len(response_mapping)}")
            
            # 检查关键字段
            required_fields = ['mdtrt_cert_type', 'mdtrt_cert_no', 'psn_cert_type', 'certno', 'psn_name']
            missing_fields = [field for field in required_fields if field not in required_params]
            if missing_fields:
                print(f"     ✗ 缺少必填参数: {missing_fields}")
                return False
            else:
                print(f"     ✓ 所有必填参数配置完整")
        else:
            print("   ✗ 未找到1101接口配置")
            return False
        
        # 验证2201接口配置
        cursor.execute("""
            SELECT api_code, required_params, default_values, response_mapping
            FROM medical_interface_config 
            WHERE api_code = '2201'
        """)
        
        config_2201 = cursor.fetchone()
        if config_2201:
            required_params = json.loads(config_2201['required_params'])
            default_values = json.loads(config_2201['default_values'])
            response_mapping = json.loads(config_2201['response_mapping'])
            
            print(f"   ✓ 2201接口配置验证:")
            print(f"     - 必填参数数量: {len(required_params)}")
            print(f"     - 默认值数量: {len(default_values)}")
            print(f"     - 响应映射数量: {len(response_mapping)}")
            
            # 检查关键字段
            required_fields = ['mdtrt_id', 'psn_no', 'chrg_bchno', 'acct_used_flag']
            missing_fields = [field for field in required_fields if field not in required_params]
            if missing_fields:
                print(f"     ✗ 缺少必填参数: {missing_fields}")
                return False
            else:
                print(f"     ✓ 所有必填参数配置完整")
        else:
            print("   ✗ 未找到2201接口配置")
            return False
        
        cursor.close()
        print(f"\n✓ 配置数据验证完成，所有数据插入成功！")
        return True
        
    except Exception as e:
        print(f"✗ 验证配置数据失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("医保接口SDK配置数据初始化")
    print("任务2.2: 初始化配置数据")
    print("="*60)
    
    # 1. 创建数据库连接
    connection = create_database_connection()
    if not connection:
        print("✗ 无法连接到数据库，初始化失败")
        return False
    
    try:
        # 2. 执行初始化SQL脚本
        sql_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'database', 'schema', '04_initial_data.sql'
        )
        
        if not os.path.exists(sql_file_path):
            print(f"✗ SQL文件不存在: {sql_file_path}")
            return False
        
        print(f"\n执行SQL文件: {sql_file_path}")
        if not execute_sql_file(connection, sql_file_path):
            print("✗ SQL文件执行失败")
            return False
        
        # 3. 验证配置数据
        if not verify_configuration_data(connection):
            print("✗ 配置数据验证失败")
            return False
        
        print("\n" + "="*60)
        print("✓ 任务2.2完成：配置数据初始化成功！")
        print("="*60)
        print("已完成:")
        print("- ✓ 插入人员信息获取接口(1101)的完整配置")
        print("- ✓ 插入门诊结算接口(2201)的配置数据")
        print("- ✓ 创建测试机构的配置数据")
        print("- ✓ 插入医药机构信息数据")
        print("- ✓ 创建初始统计数据")
        
        return True
        
    except Exception as e:
        print(f"✗ 初始化过程中发生错误: {e}")
        return False
        
    finally:
        if connection:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)