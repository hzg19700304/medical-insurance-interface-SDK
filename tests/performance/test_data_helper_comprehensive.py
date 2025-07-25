#!/usr/bin/env python3
"""
DataHelper 综合功能测试
测试所有数据处理工具类的功能
"""

import json
from medical_insurance_sdk.utils.data_helper import DataHelper


def test_id_card_functions():
    """测试身份证相关功能"""
    print("=== 身份证功能测试 ===")
    
    # 有效身份证
    valid_id = "110101199001011237"
    print(f"测试身份证: {valid_id}")
    print(f"  验证结果: {DataHelper.validate_id_card(valid_id)}")
    print(f"  年龄: {DataHelper.calculate_age_from_id_card(valid_id)}")
    print(f"  性别: {DataHelper.get_gender_from_id_card(valid_id)} (1-男, 2-女)")
    
    # 无效身份证
    invalid_id = "123456789"
    print(f"测试无效身份证: {invalid_id}")
    print(f"  验证结果: {DataHelper.validate_id_card(invalid_id)}")
    print(f"  年龄: {DataHelper.calculate_age_from_id_card(invalid_id)}")
    print(f"  性别: {DataHelper.get_gender_from_id_card(invalid_id)}")
    
    print()


def test_phone_validation():
    """测试手机号验证"""
    print("=== 手机号验证测试 ===")
    
    test_phones = [
        "13800138000",      # 有效手机号
        "15912345678",      # 有效手机号
        "010-12345678",     # 有效固话
        "0755-87654321",    # 有效固话
        "12345678901",      # 无效手机号
        "abc123456",        # 无效格式
    ]
    
    for phone in test_phones:
        result = DataHelper.validate_phone_number(phone)
        print(f"  {phone}: {result}")
    
    print()


def test_organization_code():
    """测试机构编码验证"""
    print("=== 机构编码验证测试 ===")
    
    test_codes = [
        "123456789012",     # 有效12位
        "12345678901",      # 无效11位
        "1234567890123",    # 无效13位
        "abc123456789",     # 无效格式
    ]
    
    for code in test_codes:
        result = DataHelper.validate_organization_code(code)
        print(f"  {code}: {result}")
    
    print()


def test_data_extraction():
    """测试数据提取功能"""
    print("=== 数据提取功能测试 ===")
    
    # 模拟医保接口响应数据
    response_data = {
        "infcode": "0",
        "output": {
            "baseinfo": {
                "psn_name": "张三",
                "psn_no": "1234567890",
                "certno": "110101199001011237",
                "gend": "1",
                "brdy": "1990-01-01",
                "age": 34,
                "tel": "13800138000",
                "addr": "北京市朝阳区"
            },
            "insuinfo": [
                {
                    "insutype": "310",
                    "psn_type": "1",
                    "balc": 1500.50,
                    "psn_insu_stas": "1",
                    "psn_insu_date": "2020-01-01"
                },
                {
                    "insutype": "320",
                    "psn_type": "2",
                    "balc": 800.25,
                    "psn_insu_stas": "1",
                    "psn_insu_date": "2021-01-01"
                }
            ],
            "idetinfo": [
                {
                    "psn_idet_type": "1",
                    "psn_type_lv": "1",
                    "begntime": "2020-01-01 00:00:00",
                    "endtime": "2025-12-31 23:59:59"
                }
            ]
        }
    }
    
    # 测试人员信息提取
    person_info = DataHelper.extract_person_basic_info(response_data)
    print("人员基本信息:")
    for key, value in person_info.items():
        print(f"  {key}: {value}")
    
    # 测试参保信息提取
    insurance_info = DataHelper.extract_insurance_info(response_data)
    print(f"\n参保信息 ({len(insurance_info)}条):")
    for i, info in enumerate(insurance_info):
        print(f"  [{i+1}] 险种: {info['insurance_type_name']}, 余额: {info['balance']}")
    
    # 测试总余额计算
    total_balance = DataHelper.calculate_total_balance(insurance_info)
    print(f"\n总余额: {total_balance}")
    
    # 测试身份信息提取
    identity_info = DataHelper.extract_identity_info(response_data)
    print(f"\n身份信息 ({len(identity_info)}条):")
    for i, info in enumerate(identity_info):
        print(f"  [{i+1}] 类型: {info['identity_name']}, 级别: {info['level']}")
    
    print()


def test_data_formatting():
    """测试数据格式化功能"""
    print("=== 数据格式化功能测试 ===")
    
    # 测试金额格式化
    amounts = [123.456, "456.789", 0, None, "invalid"]
    print("金额格式化:")
    for amount in amounts:
        formatted = DataHelper.format_amount(amount)
        currency = DataHelper.format_currency(amount)
        print(f"  {amount} -> {formatted} -> {currency}")
    
    # 测试日期格式化
    dates = ["2024-01-15", "2024/01/15", "20240115", "invalid"]
    print("\n日期格式化:")
    for date_str in dates:
        formatted = DataHelper.parse_date_string(date_str)
        print(f"  {date_str} -> {formatted}")
    
    # 测试日期时间格式化
    datetimes = ["2024-01-15 10:30:00", "2024/01/15 10:30:00", "invalid"]
    print("\n日期时间格式化:")
    for dt_str in datetimes:
        formatted = DataHelper.format_datetime(dt_str)
        print(f"  {dt_str} -> {formatted}")
    
    print()


def test_id_generation():
    """测试ID生成功能"""
    print("=== ID生成功能测试 ===")
    
    # 测试报文ID生成
    msg_id = DataHelper.generate_message_id()
    print(f"报文ID: {msg_id} (长度: {len(msg_id)})")
    
    # 测试操作ID生成
    op_id = DataHelper.generate_operation_id()
    print(f"操作ID: {op_id} (长度: {len(op_id)})")
    
    # 测试病历号格式化
    record_numbers = ["123", "456789", "MR00001234"]
    print("\n病历号格式化:")
    for record in record_numbers:
        formatted = DataHelper.format_medical_record_number(record)
        print(f"  {record} -> {formatted}")
    
    print()


def test_data_security():
    """测试数据安全功能"""
    print("=== 数据安全功能测试 ===")
    
    # 测试数据脱敏
    sensitive_data = {
        "psn_name": "张三",
        "certno": "110101199001011237",
        "tel": "13800138000",
        "addr": "北京市朝阳区某某街道123号",
        "app_secret": "secret123456",
        "normal_field": "正常数据",
        "nested": {
            "id_card": "110101199001011237",
            "phone": "13800138000"
        }
    }
    
    print("原始数据:")
    print(json.dumps(sensitive_data, ensure_ascii=False, indent=2))
    
    masked_data = DataHelper.mask_sensitive_data(sensitive_data)
    print("\n脱敏后数据:")
    print(json.dumps(masked_data, ensure_ascii=False, indent=2))
    
    # 测试日志数据清理
    cleaned_data = DataHelper.clean_data_for_logging(sensitive_data, max_length=200)
    print("\n日志清理后数据:")
    print(json.dumps(cleaned_data, ensure_ascii=False, indent=2))
    
    print()


def test_validation():
    """测试数据验证功能"""
    print("=== 数据验证功能测试 ===")
    
    # 测试必填字段验证
    test_data = {
        "psn_name": "张三",
        "certno": "110101199001011237",
        "tel": "",  # 空值
        "addr": "北京市"
        # missing_field 缺失
    }
    
    required_fields = ["psn_name", "certno", "tel", "addr", "missing_field"]
    validation_result = DataHelper.validate_required_fields(test_data, required_fields)
    
    print("必填字段验证:")
    print(f"  测试数据: {json.dumps(test_data, ensure_ascii=False)}")
    print(f"  必填字段: {required_fields}")
    print(f"  缺失字段: {validation_result['missing']}")
    print(f"  空值字段: {validation_result['empty']}")
    
    print()


def test_medical_insurance_specific():
    """测试医保业务专用功能"""
    print("=== 医保业务专用功能测试 ===")
    
    # 测试医保响应解析
    response_data = {
        "infcode": "0",
        "err_msg": "",
        "warn_msg": "注意事项",
        "output": {"data": "test"},
        "respond_time": "2024-01-15 10:30:00",
        "inf_refmsgid": "MSG123456789",
        "cainfo": "",
        "signtype": "SM2"
    }
    
    parsed = DataHelper.parse_medical_insurance_response(response_data)
    print("医保响应解析:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")
    
    # 测试标准请求构建
    org_config = {
        "mdtrtarea_admvs": "430100",
        "insuplc_admdvs": "430100",
        "fixmedins_code": "H43010000001",
        "fixmedins_name": "测试医院",
        "opter": "test_user",
        "opter_name": "测试用户"
    }
    
    input_data = {"psn_no": "1234567890"}
    request = DataHelper.build_standard_request("1101", input_data, org_config)
    
    print(f"\n标准请求构建:")
    print(f"  接口编码: {request['infno']}")
    print(f"  报文ID: {request['msgid']}")
    print(f"  机构编码: {request['fixmedins_code']}")
    print(f"  输入数据: {request['input']}")
    
    print()


def main():
    """主测试函数"""
    print("DataHelper 综合功能测试")
    print("=" * 50)
    
    try:
        test_id_card_functions()
        test_phone_validation()
        test_organization_code()
        test_data_extraction()
        test_data_formatting()
        test_id_generation()
        test_data_security()
        test_validation()
        test_medical_insurance_specific()
        
        print("=" * 50)
        print("✓ 所有测试通过！DataHelper功能完整且正常工作。")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    main()