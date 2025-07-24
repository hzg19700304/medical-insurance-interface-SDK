"""
调试数据解析器的响应映射问题
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

def debug_data_parser():
    """调试数据解析器"""
    
    try:
        # 初始化客户端
        client = MedicalInsuranceClient()
        sdk = client.sdk
        
        print("🔍 调试数据解析器...")
        
        # 获取2201接口配置
        interface_config = sdk.get_interface_config("2201")
        print(f"\n📋 2201接口配置:")
        print(f"   - 接口名称: {interface_config.get('api_name')}")
        print(f"   - response_mapping存在: {bool(interface_config.get('response_mapping'))}")
        print(f"   - response_mapping内容: {json.dumps(interface_config.get('response_mapping', {}), ensure_ascii=False, indent=4)}")
        
        # 模拟Apifox返回的数据
        mock_response = {
            "infcode": 0,
            "inf_refmsgid": "405054525536871841453317086578",
            "refmsg_time": "2020-08-02 06:46:11",
            "respond_time": "1992-04-05 17:15:28",
            "err_msg": "",
            "output": {
                "mdtrt_id": "MDTRT201908069131",
                "psn_no": "5485",
                "ipt_otp_no": "OPT197808048636",
                "exp_content": ""
            },
            "warn_msg": "成功",
            "cainfo": "",
            "signtype": ""
        }
        
        print(f"\n📤 模拟响应数据:")
        print(json.dumps(mock_response, ensure_ascii=False, indent=2))
        
        # 直接测试数据解析器
        print(f"\n🔍 直接测试数据解析器...")
        try:
            data_parser = sdk.universal_processor.data_parser
            parsed_data = data_parser.parse_response_data("2201", mock_response, "TEST001")
            
            print(f"✅ 解析成功:")
            print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
            
            # 检查解析结果
            print(f"\n🧪 解析结果分析:")
            for key in ["mdtrt_id", "psn_no", "ipt_otp_no", "exp_content"]:
                value = parsed_data.get(key)
                print(f"   - {key}: {value} (类型: {type(value)})")
                if value is None:
                    print(f"     ❌ 字段 {key} 解析为None")
                elif value == "":
                    print(f"     ⚠️  字段 {key} 为空字符串")
                else:
                    print(f"     ✅ 字段 {key} 解析成功")
            
            # 检查registration_result
            registration_result = parsed_data.get("registration_result")
            if registration_result:
                print(f"\n   📋 registration_result:")
                for key, value in registration_result.items():
                    print(f"      - {key}: {value}")
            
        except Exception as e:
            print(f"❌ 数据解析失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试手动路径提取
        print(f"\n🧪 手动测试路径提取:")
        def extract_by_path(data, path):
            """根据路径提取数据"""
            if not path or not isinstance(data, dict):
                return None
            
            path_parts = path.split('.')
            current_data = data
            
            for part in path_parts:
                if isinstance(current_data, dict) and part in current_data:
                    current_data = current_data[part]
                else:
                    return None
            
            return current_data
        
        mapping_tests = [
            ("mdtrt_id", "output.mdtrt_id"),
            ("psn_no", "output.psn_no"),
            ("ipt_otp_no", "output.ipt_otp_no"),
            ("exp_content", "output.exp_content")
        ]
        
        for field, path in mapping_tests:
            value = extract_by_path(mock_response, path)
            print(f"   - {field} (路径: {path}): '{value}' (类型: {type(value)})")
        
        # 测试完整的SDK调用流程
        print(f"\n🔍 测试完整SDK调用流程...")
        try:
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
            
            result = client.call("2201", test_data, "TEST001")
            print(f"✅ SDK调用成功:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 分析SDK返回的结果
            print(f"\n🔍 SDK返回结果分析:")
            print(f"   - 结果类型: {type(result)}")
            print(f"   - 顶级字段: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            # 检查是否有解析后的字段
            if isinstance(result, dict):
                for key in ["mdtrt_id", "psn_no", "ipt_otp_no", "exp_content", "registration_result"]:
                    if key in result:
                        value = result[key]
                        print(f"   - {key}: '{value}' (类型: {type(value)})")
                    else:
                        print(f"   - {key}: 不存在")
            
        except Exception as e:
            print(f"❌ SDK调用失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_parser()