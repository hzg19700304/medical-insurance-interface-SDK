"""
调试2201接口Apifox返回的实际数据结构
"""

import requests
import json

def test_apifox_2201_response():
    """测试Apifox 2201接口的实际响应数据"""
    
    print("🔍 测试Apifox 2201接口实际响应数据...")
    
    # Apifox Mock URL
    url = "https://m1.apifoxmock.com/m1/6809354-6523017-default/fsi/api/rsfComIfsService/callService/2201"
    
    # 测试数据
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
    
    # 构造请求数据
    request_data = {
        "data": test_data
    }
    
    headers = {
        'Content-Type': 'text/plain; charset=utf-8'
    }
    
    try:
        print(f"📤 发送请求到: {url}")
        print(f"📤 请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, data=json.dumps(request_data, ensure_ascii=False), headers=headers)
        
        print(f"\n📥 HTTP状态码: {response.status_code}")
        print(f"📥 响应头: {dict(response.headers)}")
        print(f"📥 原始响应: {response.text}")
        
        if response.ok:
            try:
                json_response = response.json()
                print(f"\n📋 JSON响应结构分析:")
                print(f"   - 响应类型: {type(json_response)}")
                
                if isinstance(json_response, dict):
                    print(f"   - 顶级字段: {list(json_response.keys())}")
                    
                    # 分析每个字段
                    for key, value in json_response.items():
                        print(f"   - {key}: {type(value)} = {value}")
                        
                        # 如果是output字段，进一步分析
                        if key == 'output' and isinstance(value, dict):
                            print(f"     output字段详细分析:")
                            for sub_key, sub_value in value.items():
                                print(f"       - {sub_key}: {type(sub_value)} = {sub_value}")
                
                # 测试当前的response_mapping配置
                print(f"\n🔍 测试当前response_mapping配置:")
                current_mapping = {
                    "mdtrt_id": "output.mdtrt_id",
                    "psn_no": "output.psn_no", 
                    "ipt_otp_no": "output.ipt_otp_no",
                    "exp_content": "output.exp_content",
                    "registration_result": {
                        "mdtrt_id": "output.mdtrt_id",
                        "psn_no": "output.psn_no",
                        "ipt_otp_no": "output.ipt_otp_no"
                    }
                }
                
                print(f"   当前映射配置: {json.dumps(current_mapping, ensure_ascii=False, indent=4)}")
                
                # 手动测试路径提取
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
                
                print(f"\n🧪 手动测试路径提取:")
                for field, path in [
                    ("mdtrt_id", "output.mdtrt_id"),
                    ("psn_no", "output.psn_no"),
                    ("ipt_otp_no", "output.ipt_otp_no"),
                    ("exp_content", "output.exp_content")
                ]:
                    value = extract_by_path(json_response, path)
                    print(f"   - {field} (路径: {path}): {value}")
                    if value is None:
                        print(f"     ❌ 路径 {path} 无法提取到数据")
                    else:
                        print(f"     ✅ 成功提取: {value}")
                
                # 建议正确的映射配置
                print(f"\n💡 建议的response_mapping配置:")
                if isinstance(json_response, dict) and 'output' in json_response:
                    output_data = json_response['output']
                    if isinstance(output_data, dict):
                        suggested_mapping = {}
                        for key in output_data.keys():
                            suggested_mapping[key] = f"output.{key}"
                        
                        print(f"   基于实际响应的映射配置:")
                        print(json.dumps(suggested_mapping, ensure_ascii=False, indent=4))
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"   响应内容不是有效的JSON格式")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_apifox_2201_response()