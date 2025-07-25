#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK基础使用示例

本示例展示了如何使用医保接口SDK进行基本的接口调用，
包括人员信息查询、门诊结算等常见场景。
"""

import os
import sys
import json
from datetime import datetime

# 添加SDK路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    NetworkException, 
    BusinessException
)

def setup_client():
    """初始化SDK客户端"""
    # 方式1: 使用配置文件初始化
    client = MedicalInsuranceClient.from_config_file('config/development.json')
    
    # 方式2: 直接传入配置参数初始化
    # client = MedicalInsuranceClient(
    #     database_url="mysql://user:password@localhost:3306/medical_insurance",
    #     redis_url="redis://localhost:6379/0",
    #     log_level="INFO"
    # )
    
    return client

def example_1_person_info_query():
    """示例1: 人员信息查询 (1101接口)"""
    print("\n=== 示例1: 人员信息查询 ===")
    
    client = setup_client()
    
    try:
        # 准备查询参数
        query_data = {
            "mdtrt_cert_type": "02",  # 身份证
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",    # 身份证
            "certno": "430123199001011234",
            "psn_name": "张三"
        }
        
        # 调用接口
        result = client.call_interface(
            api_code="1101",
            input_data=query_data,
            org_code="H43010000001"  # 机构编码
        )
        
        # 处理结果
        if result.get('success'):
            person_info = result.get('data', {})
            print(f"查询成功!")
            print(f"姓名: {person_info.get('person_name', 'N/A')}")
            print(f"性别: {person_info.get('gender', 'N/A')}")
            print(f"出生日期: {person_info.get('birth_date', 'N/A')}")
            print(f"年龄: {person_info.get('age', 'N/A')}")
            
            # 显示参保信息
            insurance_list = person_info.get('insurance_info', [])
            if insurance_list:
                print("\n参保信息:")
                for idx, insurance in enumerate(insurance_list, 1):
                    print(f"  {idx}. 险种: {insurance.get('type', 'N/A')}")
                    print(f"     余额: {insurance.get('balance', 0)}")
                    print(f"     状态: {insurance.get('status', 'N/A')}")
        else:
            print(f"查询失败: {result.get('error_message', '未知错误')}")
            
    except ValidationException as e:
        print(f"数据验证失败: {e.message}")
        print(f"详细错误: {e.details}")
    except NetworkException as e:
        print(f"网络请求失败: {e.message}")
    except BusinessException as e:
        print(f"业务处理失败: {e.message}")
    except Exception as e:
        print(f"未知错误: {str(e)}")

def example_2_outpatient_settlement():
    """示例2: 门诊结算 (2201接口)"""
    print("\n=== 示例2: 门诊结算 ===")
    
    client = setup_client()
    
    try:
        # 准备结算参数
        settlement_data = {
            "mdtrt_id": "H4301000000120240115001",  # 就医登记号
            "psn_no": "43012319900101123456789012",   # 人员编号
            "chrg_bchno": "20240115001",             # 收费批次号
            "acct_used_flag": "1",                   # 使用个人账户
            "insutype": "310",                       # 职工基本医疗保险
            "invono": "INV20240115001"               # 发票号
        }
        
        # 调用结算接口
        result = client.call_interface(
            api_code="2201",
            input_data=settlement_data,
            org_code="H43010000001"
        )
        
        # 处理结算结果
        if result.get('success'):
            settlement_info = result.get('data', {})
            print("结算成功!")
            print(f"结算单号: {settlement_info.get('settlement_id', 'N/A')}")
            print(f"总金额: ¥{settlement_info.get('total_amount', 0)}")
            print(f"医保支付: ¥{settlement_info.get('insurance_amount', 0)}")
            print(f"个人支付: ¥{settlement_info.get('personal_amount', 0)}")
            print(f"结算时间: {settlement_info.get('settlement_time', 'N/A')}")
        else:
            print(f"结算失败: {result.get('error_message', '未知错误')}")
            
    except Exception as e:
        print(f"结算过程出错: {str(e)}")

def example_3_batch_processing():
    """示例3: 批量处理"""
    print("\n=== 示例3: 批量处理 ===")
    
    client = setup_client()
    
    # 批量查询多个人员信息
    person_list = [
        {"certno": "430123199001011234", "psn_name": "张三"},
        {"certno": "430123199002021234", "psn_name": "李四"},
        {"certno": "430123199003031234", "psn_name": "王五"}
    ]
    
    results = []
    for person in person_list:
        try:
            query_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": person["certno"],
                "psn_cert_type": "01",
                "certno": person["certno"],
                "psn_name": person["psn_name"]
            }
            
            result = client.call_interface(
                api_code="1101",
                input_data=query_data,
                org_code="H43010000001"
            )
            
            results.append({
                "person": person,
                "result": result,
                "success": result.get('success', False)
            })
            
        except Exception as e:
            results.append({
                "person": person,
                "result": None,
                "success": False,
                "error": str(e)
            })
    
    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    print(f"批量查询完成: 成功 {success_count}/{len(person_list)}")
    
    for result in results:
        person = result['person']
        if result['success']:
            data = result['result'].get('data', {})
            print(f"✓ {person['psn_name']}: {data.get('person_name', 'N/A')}")
        else:
            error = result.get('error', '查询失败')
            print(f"✗ {person['psn_name']}: {error}")

def example_4_async_processing():
    """示例4: 异步处理"""
    print("\n=== 示例4: 异步处理 ===")
    
    client = setup_client()
    
    try:
        # 提交异步任务
        query_data = {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_name": "张三"
        }
        
        # 异步调用
        task_id = client.call_interface_async(
            api_code="1101",
            input_data=query_data,
            org_code="H43010000001"
        )
        
        print(f"异步任务已提交, 任务ID: {task_id}")
        
        # 轮询任务状态
        import time
        max_wait_time = 30  # 最大等待30秒
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = client.get_task_status(task_id)
            print(f"任务状态: {status.get('status', 'unknown')}")
            
            if status.get('status') == 'completed':
                result = status.get('result', {})
                print("异步任务完成!")
                print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                break
            elif status.get('status') == 'failed':
                print(f"异步任务失败: {status.get('error', '未知错误')}")
                break
            
            time.sleep(2)  # 等待2秒后再次检查
        else:
            print("异步任务超时")
            
    except Exception as e:
        print(f"异步处理出错: {str(e)}")

def example_5_error_handling():
    """示例5: 错误处理最佳实践"""
    print("\n=== 示例5: 错误处理 ===")
    
    client = setup_client()
    
    # 故意使用错误的数据来演示错误处理
    invalid_data = {
        "mdtrt_cert_type": "99",  # 无效的凭证类型
        "mdtrt_cert_no": "",      # 空的凭证号
        "psn_cert_type": "01",
        "certno": "invalid_id",   # 无效的身份证号
        "psn_name": ""            # 空的姓名
    }
    
    try:
        result = client.call_interface(
            api_code="1101",
            input_data=invalid_data,
            org_code="H43010000001"
        )
        
    except ValidationException as e:
        print("数据验证错误:")
        for field, errors in e.details.get('errors', {}).items():
            print(f"  {field}: {', '.join(errors)}")
            
    except NetworkException as e:
        print(f"网络错误: {e.message}")
        print("建议: 检查网络连接和服务器状态")
        
    except BusinessException as e:
        print(f"业务错误: {e.message}")
        print(f"错误代码: {e.error_code}")
        print("建议: 检查业务参数和医保接口状态")
        
    except Exception as e:
        print(f"系统错误: {str(e)}")
        print("建议: 联系技术支持")

def example_6_configuration_management():
    """示例6: 配置管理"""
    print("\n=== 示例6: 配置管理 ===")
    
    client = setup_client()
    
    try:
        # 获取接口配置信息
        interface_config = client.get_interface_config("1101")
        print("1101接口配置:")
        print(f"  接口名称: {interface_config.get('api_name', 'N/A')}")
        print(f"  业务分类: {interface_config.get('business_category', 'N/A')}")
        print(f"  超时时间: {interface_config.get('timeout_seconds', 30)}秒")
        
        # 获取机构配置信息
        org_config = client.get_organization_config("H43010000001")
        print(f"\n机构配置:")
        print(f"  机构名称: {org_config.get('org_name', 'N/A')}")
        print(f"  省份: {org_config.get('province_code', 'N/A')}")
        print(f"  接口地址: {org_config.get('base_url', 'N/A')}")
        
        # 获取调用统计
        stats = client.get_call_statistics(
            start_date="2024-01-01",
            end_date="2024-01-31",
            org_code="H43010000001"
        )
        print(f"\n调用统计:")
        print(f"  总调用次数: {stats.get('total_calls', 0)}")
        print(f"  成功次数: {stats.get('success_calls', 0)}")
        print(f"  失败次数: {stats.get('failed_calls', 0)}")
        print(f"  成功率: {stats.get('success_rate', 0):.2%}")
        
    except Exception as e:
        print(f"配置管理操作出错: {str(e)}")

def main():
    """主函数 - 运行所有示例"""
    print("医保接口SDK使用示例")
    print("=" * 50)
    
    # 运行各个示例
    example_1_person_info_query()
    example_2_outpatient_settlement()
    example_3_batch_processing()
    example_4_async_processing()
    example_5_error_handling()
    example_6_configuration_management()
    
    print("\n所有示例运行完成!")

if __name__ == "__main__":
    main()