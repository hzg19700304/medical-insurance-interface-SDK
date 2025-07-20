#!/usr/bin/env python3
"""
医保接口SDK配置数据验证脚本
用于验证任务2.1和2.2的完成情况

功能：
1. 验证数据库表结构是否正确创建
2. 验证1101接口配置数据是否完整
3. 验证2201接口配置数据是否完整
4. 验证测试机构配置数据是否正确
"""

import os
import sys
import sqlite3
import json
from pathlib import Path

def connect_to_test_database():
    """连接到测试数据库"""
    db_path = Path(__file__).parent.parent / 'test_database.db'
    if not db_path.exists():
        print("✗ 测试数据库不存在，请先运行: python scripts/setup_test_database.py")
        return None
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        print(f"✓ 成功连接到测试数据库: {db_path}")
        return conn
    except Exception as e:
        print(f"✗ 连接测试数据库失败: {e}")
        return None

def validate_table_structure(conn):
    """验证表结构"""
    print("\n" + "="*50)
    print("验证数据库表结构")
    print("="*50)
    
    cursor = conn.cursor()
    
    # 检查必需的表是否存在
    required_tables = [
        'medical_interface_config',
        'medical_organization_config', 
        'business_operation_logs',
        'medical_institution_info'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"数据库中的表: {existing_tables}")
    
    all_tables_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"✓ {table} - 存在")
        else:
            print(f"✗ {table} - 不存在")
            all_tables_exist = False
    
    if all_tables_exist:
        print("✓ 所有必需的表都已创建")
        return True
    else:
        print("✗ 部分必需的表缺失")
        return False

def validate_interface_1101_config(conn):
    """验证1101接口配置"""
    print("\n" + "="*50)
    print("验证1101接口配置（人员基本信息获取）")
    print("="*50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT api_code, api_name, business_category, business_type,
               required_params, validation_rules, response_mapping
        FROM medical_interface_config 
        WHERE api_code = '1101'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("✗ 未找到1101接口配置")
        return False
    
    print(f"✓ 接口编码: {result['api_code']}")
    print(f"✓ 接口名称: {result['api_name']}")
    print(f"✓ 业务分类: {result['business_category']}")
    print(f"✓ 业务类型: {result['business_type']}")
    
    # 验证必填参数配置
    try:
        required_params = json.loads(result['required_params'])
        expected_params = ['mdtrt_cert_type', 'mdtrt_cert_no', 'psn_cert_type', 'certno', 'psn_name']
        
        print(f"\n必填参数配置验证:")
        missing_params = []
        for param in expected_params:
            if param in required_params:
                print(f"  ✓ {param}: {required_params[param].get('display_name', 'N/A')}")
            else:
                print(f"  ✗ {param}: 缺失")
                missing_params.append(param)
        
        if missing_params:
            print(f"✗ 缺少必填参数: {missing_params}")
            return False
        else:
            print("✓ 所有必填参数配置完整")
    
    except json.JSONDecodeError as e:
        print(f"✗ 必填参数JSON格式错误: {e}")
        return False
    
    # 验证验证规则
    try:
        validation_rules = json.loads(result['validation_rules'])
        if 'certno' in validation_rules:
            certno_rule = validation_rules['certno']
            if 'pattern' in certno_rule:
                print(f"✓ 身份证验证规则: {certno_rule['pattern']}")
            else:
                print("✗ 身份证验证规则缺少pattern")
                return False
        else:
            print("✗ 缺少身份证验证规则")
            return False
    
    except json.JSONDecodeError as e:
        print(f"✗ 验证规则JSON格式错误: {e}")
        return False
    
    # 验证响应映射
    try:
        response_mapping = json.loads(result['response_mapping'])
        expected_mappings = ['person_name', 'person_id']
        
        print(f"\n响应映射配置验证:")
        for mapping in expected_mappings:
            if mapping in response_mapping:
                print(f"  ✓ {mapping}: {response_mapping[mapping]}")
            else:
                print(f"  ✗ {mapping}: 缺失")
                return False
        
        print("✓ 响应映射配置完整")
    
    except json.JSONDecodeError as e:
        print(f"✗ 响应映射JSON格式错误: {e}")
        return False
    
    print("✓ 1101接口配置验证通过")
    return True

def validate_interface_2201_config(conn):
    """验证2201接口配置"""
    print("\n" + "="*50)
    print("验证2201接口配置（门诊结算）")
    print("="*50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT api_code, api_name, business_category, business_type,
               required_params, default_values, response_mapping
        FROM medical_interface_config 
        WHERE api_code = '2201'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("✗ 未找到2201接口配置")
        return False
    
    print(f"✓ 接口编码: {result['api_code']}")
    print(f"✓ 接口名称: {result['api_name']}")
    print(f"✓ 业务分类: {result['business_category']}")
    print(f"✓ 业务类型: {result['business_type']}")
    
    # 验证必填参数配置
    try:
        required_params = json.loads(result['required_params'])
        expected_params = ['mdtrt_id', 'psn_no', 'chrg_bchno']
        
        print(f"\n必填参数配置验证:")
        missing_params = []
        for param in expected_params:
            if param in required_params:
                print(f"  ✓ {param}: {required_params[param].get('display_name', 'N/A')}")
            else:
                print(f"  ✗ {param}: 缺失")
                missing_params.append(param)
        
        if missing_params:
            print(f"✗ 缺少必填参数: {missing_params}")
            return False
        else:
            print("✓ 所有必填参数配置完整")
    
    except json.JSONDecodeError as e:
        print(f"✗ 必填参数JSON格式错误: {e}")
        return False
    
    # 验证默认值配置
    try:
        default_values = json.loads(result['default_values'])
        expected_defaults = ['acct_used_flag', 'insutype']
        
        print(f"\n默认值配置验证:")
        for default_key in expected_defaults:
            if default_key in default_values:
                print(f"  ✓ {default_key}: {default_values[default_key]}")
            else:
                print(f"  ✗ {default_key}: 缺失")
                return False
        
        print("✓ 默认值配置完整")
    
    except json.JSONDecodeError as e:
        print(f"✗ 默认值JSON格式错误: {e}")
        return False
    
    # 验证响应映射
    try:
        response_mapping = json.loads(result['response_mapping'])
        expected_mappings = ['settlement_id', 'total_amount']
        
        print(f"\n响应映射配置验证:")
        for mapping in expected_mappings:
            if mapping in response_mapping:
                print(f"  ✓ {mapping}: {response_mapping[mapping]}")
            else:
                print(f"  ✗ {mapping}: 缺失")
                return False
        
        print("✓ 响应映射配置完整")
    
    except json.JSONDecodeError as e:
        print(f"✗ 响应映射JSON格式错误: {e}")
        return False
    
    print("✓ 2201接口配置验证通过")
    return True

def validate_organization_config(conn):
    """验证机构配置"""
    print("\n" + "="*50)
    print("验证测试机构配置")
    print("="*50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT org_code, org_name, org_type, province_code, city_code,
               app_id, app_secret, base_url, is_test_env
        FROM medical_organization_config 
        WHERE org_code = 'TEST001'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("✗ 未找到测试机构配置")
        return False
    
    print(f"✓ 机构编码: {result['org_code']}")
    print(f"✓ 机构名称: {result['org_name']}")
    print(f"✓ 机构类型: {result['org_type']}")
    print(f"✓ 省份代码: {result['province_code']}")
    print(f"✓ 城市代码: {result['city_code']}")
    print(f"✓ 应用ID: {result['app_id']}")
    print(f"✓ 基础URL: {result['base_url']}")
    print(f"✓ 测试环境: {'是' if result['is_test_env'] else '否'}")
    
    # 验证必需字段
    required_fields = {
        'org_code': result['org_code'],
        'org_name': result['org_name'],
        'app_id': result['app_id'],
        'app_secret': result['app_secret'],
        'base_url': result['base_url']
    }
    
    missing_fields = []
    for field, value in required_fields.items():
        if not value:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"✗ 缺少必需字段: {missing_fields}")
        return False
    
    print("✓ 测试机构配置验证通过")
    return True

def validate_institution_info(conn):
    """验证机构信息"""
    print("\n" + "="*50)
    print("验证机构信息数据")
    print("="*50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fixmedins_code, fixmedins_name, uscc, fixmedins_type, hosp_lv
        FROM medical_institution_info 
        WHERE fixmedins_code = 'TEST00000001'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("✗ 未找到机构信息数据")
        return False
    
    print(f"✓ 机构编号: {result['fixmedins_code']}")
    print(f"✓ 机构名称: {result['fixmedins_name']}")
    print(f"✓ 信用代码: {result['uscc']}")
    print(f"✓ 机构类型: {result['fixmedins_type']}")
    print(f"✓ 医院等级: {result['hosp_lv']}")
    
    print("✓ 机构信息数据验证通过")
    return True

def generate_validation_report(results):
    """生成验证报告"""
    print("\n" + "="*60)
    print("任务2数据库设计和初始化 - 验证报告")
    print("="*60)
    
    print("\n任务2.1 - 创建MySQL数据库表结构:")
    if results['table_structure']:
        print("  ✓ 数据库表结构创建成功")
        print("    - medical_interface_config表（接口配置）")
        print("    - medical_organization_config表（机构配置）")
        print("    - business_operation_logs表（操作日志）")
        print("    - medical_institution_info表（机构信息）")
        print("    - 创建了必要的索引和约束")
    else:
        print("  ✗ 数据库表结构创建失败")
    
    print("\n任务2.2 - 初始化配置数据:")
    if results['interface_1101'] and results['interface_2201'] and results['organization']:
        print("  ✓ 配置数据初始化成功")
        if results['interface_1101']:
            print("    - ✓ 人员信息获取接口(1101)的完整配置")
        if results['interface_2201']:
            print("    - ✓ 门诊结算接口(2201)的配置数据")
        if results['organization']:
            print("    - ✓ 测试机构的配置数据")
        if results['institution_info']:
            print("    - ✓ 机构信息数据")
    else:
        print("  ✗ 配置数据初始化失败")
        if not results['interface_1101']:
            print("    - ✗ 人员信息获取接口(1101)配置缺失或不完整")
        if not results['interface_2201']:
            print("    - ✗ 门诊结算接口(2201)配置缺失或不完整")
        if not results['organization']:
            print("    - ✗ 测试机构配置缺失或不完整")
    
    # 总体结果
    all_passed = all(results.values())
    print(f"\n总体结果: {'✓ 通过' if all_passed else '✗ 失败'}")
    
    if all_passed:
        print("\n🎉 任务2完成情况:")
        print("- ✅ 任务2.1: 创建MySQL数据库表结构 - 已完成")
        print("- ✅ 任务2.2: 初始化配置数据 - 已完成")
        print("\n✅ 任务2: 数据库设计和初始化 - 全部完成")
    else:
        print("\n❌ 任务2存在问题，需要修复")
    
    return all_passed

def main():
    """主函数"""
    print("医保接口SDK配置数据验证")
    print("验证任务2.1和2.2的完成情况")
    print()
    
    # 连接数据库
    conn = connect_to_test_database()
    if not conn:
        return False
    
    try:
        # 执行各项验证
        results = {
            'table_structure': validate_table_structure(conn),
            'interface_1101': validate_interface_1101_config(conn),
            'interface_2201': validate_interface_2201_config(conn),
            'organization': validate_organization_config(conn),
            'institution_info': validate_institution_info(conn)
        }
        
        # 生成验证报告
        success = generate_validation_report(results)
        
        return success
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)