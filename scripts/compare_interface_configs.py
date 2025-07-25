"""
对比1101和2201接口的配置差异
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

def compare_interface_configs():
    """对比1101和2201接口配置"""
    
    try:
        # 初始化客户端
        client = MedicalInsuranceClient()
        sdk = client.sdk
        
        print("🔍 对比1101和2201接口配置...")
        
        # 获取1101接口配置
        config_1101 = sdk.get_interface_config("1101")
        print(f"\n📋 1101接口配置:")
        print(f"   - 接口名称: {config_1101.get('api_name')}")
        print(f"   - response_mapping: {json.dumps(config_1101.get('response_mapping', {}), ensure_ascii=False, indent=4)}")
        
        # 获取2201接口配置
        config_2201 = sdk.get_interface_config("2201")
        print(f"\n📋 2201接口配置:")
        print(f"   - 接口名称: {config_2201.get('api_name')}")
        print(f"   - response_mapping: {json.dumps(config_2201.get('response_mapping', {}), ensure_ascii=False, indent=4)}")
        
        # 测试1101接口调用
        print(f"\n🧪 测试1101接口调用...")
        test_data_1101 = {
            "psn_no": "123456789",
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_name": "张三"
        }
        
        result_1101 = client.call("1101", test_data_1101, "TEST001")
        print(f"✅ 1101调用结果类型: {type(result_1101)}")
        print(f"✅ 1101顶级字段: {list(result_1101.keys()) if isinstance(result_1101, dict) else 'N/A'}")
        
        # 检查1101是否有解析后的字段
        if isinstance(result_1101, dict):
            # 检查是否有person_info等解析后的字段
            for key in ["person_info", "insurance_list", "identity_list"]:
                if key in result_1101:
                    print(f"   ✅ 1101有解析字段 {key}: {type(result_1101[key])}")
                else:
                    print(f"   ❌ 1101缺少解析字段 {key}")
        
        # 测试2201接口调用
        print(f"\n🧪 测试2201接口调用...")
        test_data_2201 = {
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
        
        result_2201 = client.call("2201", test_data_2201, "TEST001")
        print(f"✅ 2201调用结果类型: {type(result_2201)}")
        print(f"✅ 2201顶级字段: {list(result_2201.keys()) if isinstance(result_2201, dict) else 'N/A'}")
        
        # 检查2201是否有解析后的字段
        if isinstance(result_2201, dict):
            # 检查是否有解析后的字段
            for key in ["mdtrt_id", "psn_no", "ipt_otp_no", "exp_content", "registration_result"]:
                if key in result_2201:
                    print(f"   ✅ 2201有解析字段 {key}: {result_2201[key]}")
                else:
                    print(f"   ❌ 2201缺少解析字段 {key}")
            
            # 检查原始output字段
            if "output" in result_2201:
                output = result_2201["output"]
                print(f"   📋 2201原始output字段: {output}")
                if isinstance(output, dict):
                    for key, value in output.items():
                        print(f"      - {key}: '{value}' (类型: {type(value)})")
        
        # 分析配置差异
        print(f"\n🔍 配置差异分析:")
        
        # 检查response_mapping的结构差异
        mapping_1101 = config_1101.get('response_mapping', {})
        mapping_2201 = config_2201.get('response_mapping', {})
        
        print(f"   - 1101 mapping字段数: {len(mapping_1101)}")
        print(f"   - 2201 mapping字段数: {len(mapping_2201)}")
        
        # 检查映射类型
        print(f"\n   📋 1101映射类型分析:")
        for key, value in mapping_1101.items():
            if isinstance(value, dict):
                print(f"      - {key}: 复杂映射 (类型: {value.get('type', 'unknown')})")
            else:
                print(f"      - {key}: 简单路径映射 ({value})")
        
        print(f"\n   📋 2201映射类型分析:")
        for key, value in mapping_2201.items():
            if isinstance(value, dict):
                print(f"      - {key}: 复杂映射 (类型: {value.get('type', 'unknown')})")
            else:
                print(f"      - {key}: 简单路径映射 ({value})")
        
    except Exception as e:
        print(f"❌ 对比失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_interface_configs()