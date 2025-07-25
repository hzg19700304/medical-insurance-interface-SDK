"""
测试Apifox的Mock行为
验证为什么未配置的接口也能返回数据
"""

import requests
import json
from datetime import datetime

def test_unknown_interface():
    """测试一个完全不存在的接口编号"""
    print("🔍 测试未配置的接口...")
    
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    url = f"{base_url}/fsi/api/rsfComIfsService/callService"
    
    # 测试一个不存在的接口编号
    request_data = {
        "infno": "9999",  # 不存在的接口编号
        "msgid": f"test_mystery_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "mdtrtarea_admvs": "4301",
        "insuplc_admdvs": "4301",
        "input": {
            "test_field": "test_value"
        }
    }
    
    try:
        response = requests.post(url, json=request_data, timeout=10)
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_different_paths():
    """测试不同的路径"""
    print("\\n🔍 测试不同的路径...")
    
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    
    # 测试不同的路径
    test_paths = [
        "/fsi/api/rsfComIfsService/callService",
        "/api/test/nonexistent",
        "/random/path/test"
    ]
    
    for path in test_paths:
        url = f"{base_url}{path}"
        print(f"\\n📡 测试路径: {path}")
        
        try:
            response = requests.post(url, json={"test": "data"}, timeout=5)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ 返回JSON数据")
                except:
                    print(f"   📄 返回非JSON数据: {response.text[:100]}...")
            else:
                print(f"   ❌ 失败: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")

def test_multiple_2201_calls():
    """多次调用2201接口，看数据是否变化"""
    print("\\n🔍 多次调用2201接口测试...")
    
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    url = f"{base_url}/fsi/api/rsfComIfsService/callService"
    
    request_data = {
        "infno": "2201",
        "msgid": f"test_multiple_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "input": {
            "mdtrt_id": "MDT20240115001",
            "psn_no": "123456789"
        }
    }
    
    for i in range(3):
        print(f"\\n📞 第{i+1}次调用:")
        try:
            response = requests.post(url, json=request_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                infcode = result.get('infcode', 'N/A')
                psn_name = result.get('output', {}).get('baseinfo', {}).get('psn_name', 'N/A')
                print(f"   返回码: {infcode}, 姓名: {psn_name}")
            else:
                print(f"   失败: {response.status_code}")
        except Exception as e:
            print(f"   异常: {e}")

def main():
    """主函数"""
    print("🕵️ Apifox Mock行为调查")
    print("=" * 60)
    
    # 测试未知接口
    test_unknown_interface()
    
    # 测试不同路径
    test_different_paths()
    
    # 测试多次调用
    test_multiple_2201_calls()
    
    print("\\n" + "=" * 60)
    print("🤔 分析结论:")
    print("1. 如果未配置的接口也返回数据，说明Apifox启用了智能Mock")
    print("2. 如果数据每次都不同，说明使用了随机数据生成")
    print("3. 如果只有特定路径有效，说明配置了通用接口")

if __name__ == "__main__":
    main()