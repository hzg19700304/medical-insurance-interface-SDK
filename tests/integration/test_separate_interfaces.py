"""
测试独立的医保接口
分别测试1101和2201接口
"""

import requests
import json
from datetime import datetime

def test_1101_interface():
    """测试1101人员信息查询接口"""
    print("🧪 测试1101人员信息查询接口...")
    
    # 使用独立的1101接口路径
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    url = f"{base_url}/fsi/api/rsfComIfsService/callService/1101"
    
    # 构建请求数据
    request_data = {
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
    
    try:
        print(f"📡 请求URL: {url}")
        print(f"📤 请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=request_data, timeout=10)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析响应数据
            infcode = result.get('infcode', 'N/A')
            output = result.get('output', {})
            
            print("\\n✅ 1101接口调用成功!")
            print(f"   - 返回码: {infcode}")
            
            if isinstance(output, dict):
                baseinfo = output.get('baseinfo', {})
                if baseinfo:
                    print(f"   - 人员编号: {baseinfo.get('psn_no', 'N/A')}")
                    print(f"   - 人员姓名: {baseinfo.get('psn_name', 'N/A')}")
                    print(f"   - 性别: {baseinfo.get('gend', 'N/A')}")
                    print(f"   - 身份证号: {baseinfo.get('certno', 'N/A')}")
                    print(f"   - 电话: {baseinfo.get('tel', 'N/A')}")
                
                insuinfo = output.get('insuinfo', [])
                if insuinfo and isinstance(insuinfo, list):
                    print(f"   - 参保信息数量: {len(insuinfo)}")
                    for i, info in enumerate(insuinfo):
                        print(f"     [{i+1}] 险种: {info.get('insutype', 'N/A')}, 余额: {info.get('balc', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ 1101接口调用失败: HTTP {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 1101接口调用异常: {e}")
        return False

def test_2201_interface():
    """测试2201门诊结算接口"""
    print("\\n💰 测试2201门诊结算接口...")
    
    # 使用独立的2201接口路径
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    url = f"{base_url}/fsi/api/rsfComIfsService/callService/2201"
    
    # 构建请求数据
    request_data = {
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
    
    try:
        print(f"📡 请求URL: {url}")
        print(f"📤 请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=request_data, timeout=10)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析响应数据
            infcode = result.get('infcode', 'N/A')
            output = result.get('output', {})
            
            print("\\n✅ 2201接口调用成功!")
            print(f"   - 返回码: {infcode}")
            
            if isinstance(output, dict):
                setlinfo = output.get('setlinfo', {})
                if setlinfo:
                    print(f"   - 结算ID: {setlinfo.get('setl_id', 'N/A')}")
                    print(f"   - 总金额: {setlinfo.get('setl_totlnum', 'N/A')}")
                    print(f"   - 医保支付: {setlinfo.get('hifp_pay', 'N/A')}")
                    print(f"   - 个人支付: {setlinfo.get('psn_pay', 'N/A')}")
                    print(f"   - 账户支付: {setlinfo.get('acct_pay', 'N/A')}")
                    print(f"   - 现金支付: {setlinfo.get('psn_cash_pay', 'N/A')}")
                    print(f"   - 结算时间: {setlinfo.get('setl_time', 'N/A')}")
                    print(f"   - 发票号: {setlinfo.get('invono', 'N/A')}")
            
            return True
            
        else:
            print(f"❌ 2201接口调用失败: HTTP {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 2201接口调用异常: {e}")
        return False

def test_error_scenarios():
    """测试错误场景"""
    print("\\n⚠️  测试错误场景...")
    
    base_url = "https://m1.apifoxmock.com/m1/6809354-6523017-default"
    
    # 测试不存在的接口
    url_404 = f"{base_url}/fsi/api/rsfComIfsService/callService/9999"
    
    try:
        response = requests.post(url_404, json={"test": "data"}, timeout=5)
        print(f"📡 测试不存在接口: {response.status_code}")
        if response.status_code == 404:
            print("✅ 正确返回404错误")
        else:
            print(f"⚠️  意外状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主函数"""
    print("🚀 独立医保接口测试")
    print("=" * 60)
    
    # 测试1101接口
    success_1101 = test_1101_interface()
    
    # 测试2201接口
    success_2201 = test_2201_interface()
    
    # 测试错误场景
    test_error_scenarios()
    
    # 输出总结
    print("\\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   1101人员信息查询: {'✅ 通过' if success_1101 else '❌ 失败'}")
    print(f"   2201门诊结算: {'✅ 通过' if success_2201 else '❌ 失败'}")
    
    total_passed = sum([success_1101, success_2201])
    print(f"\\n🎯 总体结果: {total_passed}/2 测试通过")
    
    if total_passed == 2:
        print("🎉 所有测试通过！独立接口配置成功！")
        print("\\n📋 下一步:")
        print("   1. 在Apifox中创建这两个独立接口")
        print("   2. 配置对应的Mock数据")
        print("   3. 启动Mock服务器")
        print("   4. 重新运行此测试验证")
    else:
        print("⚠️  部分测试失败，请先在Apifox中配置对应接口")

if __name__ == "__main__":
    main()