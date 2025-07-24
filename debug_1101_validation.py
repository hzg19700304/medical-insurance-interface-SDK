"""
调试1101接口的数据验证问题
"""

import sys
import os
import json
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.client import MedicalInsuranceClient

def debug_1101_validation():
    """调试1101接口验证问题"""
    
    try:
        # 初始化客户端
        client = MedicalInsuranceClient()
        sdk = client.sdk
        
        print("🔍 调试1101接口数据验证问题...")
        
        # 获取1101接口配置
        interface_config = sdk.get_interface_config("1101")
        print(f"\n📋 1101接口配置:")
        print(f"   - 接口名称: {interface_config.get('api_name')}")
        print(f"   - 必填参数: {json.dumps(interface_config.get('required_params', {}), ensure_ascii=False, indent=4)}")
        print(f"   - 可选参数: {json.dumps(interface_config.get('optional_params', {}), ensure_ascii=False, indent=4)}")
        print(f"   - 验证规则: {json.dumps(interface_config.get('validation_rules', {}), ensure_ascii=False, indent=4)}")
        
        # 准备测试数据
        test_data = {
            "psn_no": "123456789",
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_name": "张三"
        }
        
        print(f"\n📤 测试数据:")
        print(json.dumps(test_data, ensure_ascii=False, indent=2))
        
        # 测试通过universal_processor的完整流程
        print(f"\n🔍 测试通过universal_processor的完整流程...")
        try:
            # 直接调用universal_processor的call_interface方法，但捕获ValidationException
            print(f"\n📋 调用universal_processor.call_interface...")
            try:
                result = client.universal_processor.call_interface("1101", test_data, "TEST001")
                print(f"✅ 调用成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except Exception as e:
                print(f"❌ 调用失败: {e}")
                print(f"异常类型: {type(e)}")
                
                # 如果是ValidationException，获取详细错误信息
                if hasattr(e, 'field_errors'):
                    print(f"字段错误: {e.field_errors}")
                    
        except Exception as e:
            print(f"❌ universal_processor测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 检查数据库中的验证规则
        print(f"\n🗄️  检查数据库中的验证规则...")
        try:
            db_manager = sdk.db_manager
            validation_rules = db_manager.execute_query(
                "SELECT field_name, validation_type, validation_rule, error_message FROM validation_rules WHERE api_code = %s",
                ("1101",)
            )
            
            if validation_rules:
                print(f"✅ 数据库中的验证规则:")
                for rule in validation_rules:
                    print(f"   - 字段: {rule['field_name']}")
                    print(f"     类型: {rule['validation_type']}")
                    print(f"     规则: {rule['validation_rule']}")
                    print(f"     错误信息: {rule['error_message']}")
                    print()
            else:
                print("⚠️  数据库中没有找到1101接口的验证规则")
                
        except Exception as e:
            print(f"❌ 查询验证规则失败: {e}")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")

if __name__ == "__main__":
    debug_1101_validation()