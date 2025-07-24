"""
调试2201接口的响应数据问题
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

def debug_2201_response():
    """调试2201接口响应数据"""
    
    try:
        # 初始化客户端
        client = MedicalInsuranceClient()
        sdk = client.sdk
        
        print("🔍 调试2201接口响应数据...")
        
        # 获取2201接口配置
        interface_config = sdk.get_interface_config("2201")
        print(f"\n📋 2201接口配置:")
        print(f"   - 接口名称: {interface_config.get('api_name')}")
        print(f"   - 响应映射: {json.dumps(interface_config.get('response_mapping', {}), ensure_ascii=False, indent=4)}")
        
        # 准备测试数据
        test_data = {
            "psn_no": "123456789",
            "insutype": "310",
            "begntime": "2024-01-15 09:30:00",
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_type": "101",
            "psn_name": "张三",
            "ipt_otp_no": "OPT20240115001",
            "dept_code": "001",
            "dept_name": "内科",
            "caty": "01"
        }
        
        print(f"\n📤 测试数据:")
        print(json.dumps(test_data, ensure_ascii=False, indent=2))
        
        # 调用接口
        print(f"\n🔍 调用2201接口...")
        try:
            result = client.call("2201", test_data, "TEST001")
            
            print(f"\n📥 原始响应数据:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 检查响应数据的结构
            print(f"\n🔍 响应数据分析:")
            print(f"   - infcode: {result.get('infcode')}")
            print(f"   - err_msg: {result.get('err_msg')}")
            print(f"   - output类型: {type(result.get('output'))}")
            print(f"   - output内容: {result.get('output')}")
            
            # 检查output中是否有数据
            output = result.get('output', {})
            if isinstance(output, dict):
                print(f"   - output字段数量: {len(output)}")
                for key, value in output.items():
                    print(f"     * {key}: {type(value)} = {value}")
            
        except Exception as e:
            print(f"❌ 调用失败: {e}")
            
        # 直接测试Apifox Mock接口
        print(f"\n🌐 直接测试Apifox Mock接口...")
        try:
            import requests
            
            url = "https://m1.apifoxmock.com/m1/6809354-6523017-default/fsi/api/rsfComIfsService/callService/2201"
            
            # 构造请求数据
            request_data = {
                "data": test_data
            }
            
            headers = {
                'Content-Type': 'text/plain; charset=utf-8'
            }
            
            response = requests.post(url, data=json.dumps(request_data, ensure_ascii=False), headers=headers)
            
            print(f"   - HTTP状态码: {response.status_code}")
            print(f"   - 响应头: {dict(response.headers)}")
            print(f"   - 响应内容: {response.text}")
            
            if response.ok:
                try:
                    json_response = response.json()
                    print(f"   - JSON响应: {json.dumps(json_response, ensure_ascii=False, indent=4)}")
                except:
                    print(f"   - 响应不是有效的JSON格式")
            
        except Exception as e:
            print(f"❌ 直接调用Apifox失败: {e}")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_2201_response()