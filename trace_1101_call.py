"""
跟踪1101接口调用的完整流程
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

def trace_1101_call():
    """跟踪1101接口调用流程"""
    
    try:
        # 初始化客户端
        client = MedicalInsuranceClient()
        
        print("🔍 跟踪1101接口调用流程...")
        
        # 准备测试数据
        test_data = {
            "psn_no": "123456789",
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_name": "张三"
        }
        
        print(f"\n📤 原始测试数据:")
        print(json.dumps(test_data, ensure_ascii=False, indent=2))
        
        # 1. 测试直接调用SDK的call方法
        print(f"\n🔍 1. 测试直接调用SDK.call方法...")
        try:
            # 构造SDK期望的数据格式
            sdk_data = {"data": test_data}
            result = client.sdk.call("1101", sdk_data, org_code="TEST001")
            print(f"✅ SDK.call调用成功: {type(result)}")
            if hasattr(result, 'to_dict'):
                print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ SDK.call调用失败: {e}")
            print(f"异常类型: {type(e)}")
            if hasattr(e, 'field_errors'):
                print(f"字段错误: {e.field_errors}")
        
        # 2. 测试通过UniversalProcessor调用
        print(f"\n🔍 2. 测试通过UniversalProcessor调用...")
        try:
            result = client.universal_processor.call_interface("1101", test_data, "TEST001")
            print(f"✅ UniversalProcessor调用成功:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ UniversalProcessor调用失败: {e}")
            print(f"异常类型: {type(e)}")
            if hasattr(e, 'field_errors'):
                print(f"字段错误: {e.field_errors}")
        
        # 3. 测试通过Client调用
        print(f"\n🔍 3. 测试通过Client调用...")
        try:
            result = client.call("1101", test_data, "TEST001")
            print(f"✅ Client调用成功:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ Client调用失败: {e}")
            print(f"异常类型: {type(e)}")
            if hasattr(e, 'field_errors'):
                print(f"字段错误: {e.field_errors}")
            
    except Exception as e:
        print(f"❌ 跟踪失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_1101_call()