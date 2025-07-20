#!/usr/bin/env python3
"""
医保接口客户端使用示例
演示MedicalInsuranceClient和DataHelper的使用方法
"""

import sys
import os
import asyncio
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medical_insurance_sdk import MedicalInsuranceClient, DataHelper
from medical_insurance_sdk.config.models import SDKConfig
from medical_insurance_sdk.core.database import DatabaseConfig


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    try:
        # 初始化客户端（使用默认配置）
        client = MedicalInsuranceClient()
        
        # 示例：调用人员信息查询接口
        api_code = "1101"
        input_data = {
            "mdtrt_cert_type": "02",  # 身份证
            "mdtrt_cert_no": "110101199001011234",
            "psn_cert_type": "01",
            "certno": "110101199001011234",
            "psn_name": "张三"
        }
        org_code = "123456789012"
        
        print(f"调用接口: {api_code}")
        print(f"输入数据: {input_data}")
        
        # 注意：这里会因为没有真实的数据库配置而失败，仅作为示例
        # result = client.call(api_code, input_data, org_code)
        # print(f"调用结果: {result}")
        
        print("✓ 基本使用示例代码结构正确")
        
    except Exception as e:
        print(f"基本使用示例执行异常（预期）: {e}")


def example_data_validation():
    """数据验证示例"""
    print("\n=== 数据验证示例 ===")
    
    try:
        client = MedicalInsuranceClient()
        
        # 示例数据验证
        api_code = "1101"
        test_data = {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "110101199001011234",
            "psn_name": "张三"
        }
        org_code = "123456789012"
        
        print(f"验证接口数据: {api_code}")
        print(f"测试数据: {test_data}")
        
        # 注意：这里会因为没有真实的数据库配置而失败，仅作为示例
        # validation_result = client.validate_data(api_code, test_data, org_code)
        # print(f"验证结果: {validation_result}")
        
        print("✓ 数据验证示例代码结构正确")
        
    except Exception as e:
        print(f"数据验证示例执行异常（预期）: {e}")


def example_async_usage():
    """异步调用示例"""
    print("\n=== 异步调用示例 ===")
    
    try:
        client = MedicalInsuranceClient()
        
        # 异步调用示例
        api_code = "1101"
        input_data = {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "110101199001011234",
            "psn_name": "张三"
        }
        org_code = "123456789012"
        
        print(f"提交异步任务: {api_code}")
        
        # 注意：这里会因为没有真实的数据库配置而失败，仅作为示例
        # task_id = client.call_async(api_code, input_data, org_code)
        # print(f"任务ID: {task_id}")
        
        # 查询任务结果
        # task_result = client.get_task_result(task_id)
        # print(f"任务结果: {task_result}")
        
        print("✓ 异步调用示例代码结构正确")
        
    except Exception as e:
        print(f"异步调用示例执行异常（预期）: {e}")


def example_batch_usage():
    """批量调用示例"""
    print("\n=== 批量调用示例 ===")
    
    try:
        client = MedicalInsuranceClient()
        
        # 批量请求示例
        batch_requests = [
            {
                "api_code": "1101",
                "input_data": {
                    "mdtrt_cert_type": "02",
                    "mdtrt_cert_no": "110101199001011234",
                    "psn_name": "张三"
                },
                "org_code": "123456789012"
            },
            {
                "api_code": "1101",
                "input_data": {
                    "mdtrt_cert_type": "02",
                    "mdtrt_cert_no": "110101199001011235",
                    "psn_name": "李四"
                },
                "org_code": "123456789012"
            }
        ]
        
        print(f"批量调用，请求数量: {len(batch_requests)}")
        
        # 注意：这里会因为没有真实的数据库配置而失败，仅作为示例
        # results = client.call_batch(batch_requests)
        # print(f"批量调用结果: {results}")
        
        print("✓ 批量调用示例代码结构正确")
        
    except Exception as e:
        print(f"批量调用示例执行异常（预期）: {e}")


def example_data_helper_usage():
    """DataHelper使用示例"""
    print("\n=== DataHelper使用示例 ===")
    
    # 模拟接口响应数据
    mock_response = {
        "infcode": 0,
        "err_msg": "",
        "output": {
            "baseinfo": {
                "psn_name": "张三",
                "psn_no": "1234567890123456",
                "certno": "110101199001011234",
                "gend": "1",
                "brdy": "1990-01-01",
                "age": 34,
                "tel": "13800138000",
                "addr": "北京市朝阳区"
            },
            "insuinfo": [
                {
                    "insutype": "310",
                    "balc": 1500.50,
                    "psn_insu_stas": "1",
                    "psn_insu_date": "2020-01-01"
                },
                {
                    "insutype": "320",
                    "balc": 800.25,
                    "psn_insu_stas": "1",
                    "psn_insu_date": "2020-01-01"
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
    
    print("模拟响应数据处理:")
    
    # 提取人员基本信息
    person_info = DataHelper.extract_person_basic_info(mock_response)
    print(f"人员基本信息: {person_info}")
    
    # 提取参保信息
    insurance_info = DataHelper.extract_insurance_info(mock_response)
    print(f"参保信息: {insurance_info}")
    
    # 计算总余额
    total_balance = DataHelper.calculate_total_balance(insurance_info)
    print(f"总余额: {total_balance}")
    
    # 提取身份信息
    identity_info = DataHelper.extract_identity_info(mock_response)
    print(f"身份信息: {identity_info}")
    
    # 提取错误信息
    error_info = DataHelper.extract_error_info(mock_response)
    print(f"错误信息: {error_info}")
    
    print("\n数据验证示例:")
    
    # 身份证验证
    test_ids = ["110101199001011234", "123456", ""]
    for test_id in test_ids:
        is_valid = DataHelper.validate_id_card(test_id)
        print(f"身份证 '{test_id}' 验证结果: {is_valid}")
    
    # 手机号验证
    test_phones = ["13800138000", "010-12345678", "123", ""]
    for phone in test_phones:
        is_valid = DataHelper.validate_phone_number(phone)
        print(f"手机号 '{phone}' 验证结果: {is_valid}")
    
    print("\n数据格式化示例:")
    
    # 金额格式化
    test_amounts = [123.456, "1000.789", 0, None, ""]
    for amount in test_amounts:
        formatted = DataHelper.format_amount(amount)
        currency = DataHelper.format_currency(amount)
        print(f"金额 {amount} -> 格式化: {formatted}, 货币: {currency}")
    
    # 日期格式化
    test_dates = ["2024-01-15", "2024/01/15", "20240115", ""]
    for date_str in test_dates:
        formatted = DataHelper.parse_date_string(date_str)
        print(f"日期 '{date_str}' -> 格式化: {formatted}")
    
    print("✓ DataHelper使用示例完成")


def example_connection_test():
    """连接测试示例"""
    print("\n=== 连接测试示例 ===")
    
    try:
        client = MedicalInsuranceClient()
        
        org_code = "123456789012"
        print(f"测试机构连接: {org_code}")
        
        # 注意：这里会因为没有真实的数据库配置而失败，仅作为示例
        # test_result = client.test_connection(org_code)
        # print(f"连接测试结果: {test_result}")
        
        print("✓ 连接测试示例代码结构正确")
        
    except Exception as e:
        print(f"连接测试示例执行异常（预期）: {e}")


def example_interface_info():
    """接口信息查询示例"""
    print("\n=== 接口信息查询示例 ===")
    
    try:
        client = MedicalInsuranceClient()
        
        api_code = "1101"
        print(f"查询接口信息: {api_code}")
        
        # 注意：这里会因为没有真实的数据库配置而失败，仅作为示例
        # interface_info = client.get_interface_info(api_code)
        # print(f"接口信息: {interface_info}")
        
        # 获取支持的接口列表
        # supported_interfaces = client.get_supported_interfaces()
        # print(f"支持的接口数量: {len(supported_interfaces)}")
        
        print("✓ 接口信息查询示例代码结构正确")
        
    except Exception as e:
        print(f"接口信息查询示例执行异常（预期）: {e}")


def example_context_manager():
    """上下文管理器使用示例"""
    print("\n=== 上下文管理器使用示例 ===")
    
    try:
        # 使用with语句自动管理资源
        with MedicalInsuranceClient() as client:
            print("客户端已初始化")
            
            # 获取处理统计
            # stats = client.get_processing_stats()
            # print(f"处理统计: {stats}")
            
            print("客户端将自动关闭")
        
        print("✓ 上下文管理器使用示例完成")
        
    except Exception as e:
        print(f"上下文管理器示例执行异常（预期）: {e}")


def main():
    """主函数"""
    print("医保接口客户端使用示例")
    print("=" * 60)
    
    examples = [
        example_basic_usage,
        example_data_validation,
        example_async_usage,
        example_batch_usage,
        example_data_helper_usage,
        example_connection_test,
        example_interface_info,
        example_context_manager
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"示例执行异常: {e}")
    
    print("\n" + "=" * 60)
    print("所有使用示例演示完成！")
    print("\n注意事项:")
    print("1. 实际使用时需要配置正确的数据库连接")
    print("2. 需要在数据库中配置接口和机构信息")
    print("3. 某些示例因为缺少真实配置会抛出异常，这是正常的")
    print("4. 生产环境使用前请确保所有配置正确")


if __name__ == "__main__":
    main()