"""
使用正确路径测试医保接口
保持原有路径，通过请求体中的infno区分接口
"""

import requests
import json
from datetime import datetime

def test_medical_interfaces():
    """测试医保接口"""
    print("🚀 测试医保接口（正确路径）")
    print("=" * 60)
    
    # 正确的Apifox路径
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    url = f"{base_url}/fsi/api/rsfComIfsService/callService"
    
    # 测试1101接口
    print("\\n🧪 测试1101人员信息查询接口...")
    request_1101 = {
        "infno": "1101",
        "msgid": f"test_1101_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "mdtrtarea_admvs": "4301",
        "insuplc_admdvs": "4301",
        "recer_sys_code": "MDY32",
        "infver": "V1.0",
        "opter_type": "1",
        "opter": "test_user",
        "opter_name": "测试用户",
        "inf_time": datetime.now().strftime("%Y%m%d%H%M%S"),
        "fixmedins_code": "TEST001",
        "fixmedins_name": "测试医院",
        "input": {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_name": "张三"
        }
    }
    
    success_1101 = call_interface(url, request_1101, "1101人员信息查询")
    
    # 测试2201接口
    print("\\n💰 测试2201门诊结算接口...")
    request_2201 = {
        "infno": "2201",
        "msgid": f"test_2201_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "mdtrtarea_admvs": "4301",
        "insuplc_admdvs": "4301",
        "recer_sys_code": "MDY32",
        "infver": "V1.0",
        "opter_type": "1",
        "opter": "test_user",
        "opter_name": "测试用户",
        "inf_time": datetime.now().strftime("%Y%m%d%H%M%S"),
        "fixmedins_code": "TEST001",
        "fixmedins_name": "测试医院",
        "input": {
            "mdtrt_id": "MDT20240115001",
            "psn_no": "123456789",
            "chrg_bchno": "CHG20240115001",
            "acct_used_flag": "1",
            "insutype": "310",
            "invono": "INV20240115001"
        }
    }
    
    success_2201 = call_interface(url, request_2201, "2201门诊结算")
    
    # 输出总结
    print("\\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   1101人员信息查询: {'✅ 通过' if success_1101 else '❌ 失败'}")
    print(f"   2201门诊结算: {'✅ 通过' if success_2201 else '❌ 失败'}")
    
    total_passed = sum([success_1101, success_2201])
    print(f"\\n🎯 总体结果: {total_passed}/2 测试通过")
    
    return total_passed == 2

def call_interface(url, request_data, interface_name):
    """调用接口的通用方法"""
    try:
        print(f"📡 请求URL: {url}")
        print(f"📤 接口: {interface_name}")
        print(f"📤 infno: {request_data.get('infno', 'N/A')}")
        
        response = requests.post(url, json=request_data, timeout=10)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 解析响应数据
            infcode = result.get('infcode', 'N/A')
            err_msg = result.get('err_msg', '')
            output = result.get('output', {})
            
            print(f"✅ {interface_name}调用成功!")
            print(f"   - 返回码: {infcode}")
            
            if err_msg:
                print(f"   - 错误信息: {err_msg}")
            
            # 根据接口类型解析不同的输出
            if request_data.get('infno') == '1101':
                parse_1101_response(output)
            elif request_data.get('infno') == '2201':
                parse_2201_response(output)
            
            return True
            
        else:
            print(f"❌ {interface_name}调用失败: HTTP {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {interface_name}调用异常: {e}")
        return False

def parse_1101_response(output):
    """解析1101接口响应"""
    if isinstance(output, dict):
        baseinfo = output.get('baseinfo', {})
        if baseinfo:
            print(f"   - 人员编号: {baseinfo.get('psn_no', 'N/A')}")
            print(f"   - 人员姓名: {baseinfo.get('psn_name', 'N/A')}")
            print(f"   - 性别: {baseinfo.get('gend', 'N/A')}")
            print(f"   - 身份证号: {baseinfo.get('certno', 'N/A')}")
        
        insuinfo = output.get('insuinfo', [])
        if insuinfo and isinstance(insuinfo, list):
            print(f"   - 参保信息数量: {len(insuinfo)}")
            for i, info in enumerate(insuinfo):
                print(f"     [{i+1}] 险种: {info.get('insutype', 'N/A')}, 余额: {info.get('balc', 'N/A')}")

def parse_2201_response(output):
    """解析2201接口响应"""
    if isinstance(output, dict):
        setlinfo = output.get('setlinfo', {})
        if setlinfo:
            print(f"   - 结算ID: {setlinfo.get('setl_id', 'N/A')}")
            print(f"   - 总金额: {setlinfo.get('setl_totlnum', 'N/A')}")
            print(f"   - 医保支付: {setlinfo.get('hifp_pay', 'N/A')}")
            print(f"   - 个人支付: {setlinfo.get('psn_pay', 'N/A')}")
            print(f"   - 账户支付: {setlinfo.get('acct_pay', 'N/A')}")
            print(f"   - 现金支付: {setlinfo.get('psn_cash_pay', 'N/A')}")

if __name__ == "__main__":
    test_medical_interfaces()