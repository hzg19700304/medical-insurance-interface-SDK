#!/usr/bin/env python3
"""
测试客户端接口实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入是否正常"""
    try:
        from medical_insurance_sdk import MedicalInsuranceClient, DataHelper
        print("✓ 导入成功: MedicalInsuranceClient, DataHelper")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_data_helper():
    """测试DataHelper功能"""
    try:
        from medical_insurance_sdk import DataHelper
        
        # 测试身份证验证
        valid_id = "110101199001011237"  # 使用有效的身份证号码
        invalid_id = "123456"
        
        print(f"身份证验证测试:")
        print(f"  有效身份证 {valid_id}: {DataHelper.validate_id_card(valid_id)}")
        print(f"  无效身份证 {invalid_id}: {DataHelper.validate_id_card(invalid_id)}")
        
        # 测试金额格式化
        amount = 123.456
        formatted = DataHelper.format_amount(amount)
        currency = DataHelper.format_currency(amount)
        
        print(f"金额格式化测试:")
        print(f"  原始金额: {amount}")
        print(f"  格式化金额: {formatted}")
        print(f"  货币格式: {currency}")
        
        # 测试数据提取
        test_response = {
            "output": {
                "baseinfo": {
                    "psn_name": "张三",
                    "psn_no": "1234567890",
                    "certno": "110101199001011234",
                    "gend": "1",
                    "brdy": "1990-01-01",
                    "age": 34
                },
                "insuinfo": [
                    {
                        "insutype": "310",
                        "balc": 1500.50,
                        "psn_insu_stas": "1"
                    }
                ]
            }
        }
        
        person_info = DataHelper.extract_person_basic_info(test_response)
        insurance_info = DataHelper.extract_insurance_info(test_response)
        total_balance = DataHelper.calculate_total_balance(insurance_info)
        
        print(f"数据提取测试:")
        print(f"  人员信息: {person_info}")
        print(f"  参保信息: {insurance_info}")
        print(f"  总余额: {total_balance}")
        
        print("✓ DataHelper功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ DataHelper测试失败: {e}")
        return False

def test_client_structure():
    """测试客户端结构"""
    try:
        from medical_insurance_sdk import MedicalInsuranceClient
        
        # 检查客户端方法
        expected_methods = [
            'call', 'call_async', 'get_task_result', 'call_batch',
            'validate_data', 'get_interface_info', 'get_supported_interfaces',
            'test_connection', 'get_processing_stats', 'close'
        ]
        
        missing_methods = []
        for method in expected_methods:
            if not hasattr(MedicalInsuranceClient, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"✗ 客户端缺少方法: {missing_methods}")
            return False
        
        print("✓ 客户端结构检查通过")
        return True
        
    except Exception as e:
        print(f"✗ 客户端结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试客户端接口实现...")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_imports),
        ("DataHelper功能测试", test_data_helper),
        ("客户端结构测试", test_client_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"测试失败: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！客户端接口实现完成。")
        return True
    else:
        print("✗ 部分测试失败，请检查实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)