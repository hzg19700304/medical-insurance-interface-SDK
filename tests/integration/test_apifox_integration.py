"""
Apifox集成测试脚本
用于测试医保SDK与Apifox模拟接口的集成
"""

import requests
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from medical_insurance_sdk.client import MedicalInsuranceClient
from medical_insurance_sdk.models.config import OrganizationConfig

class ApifoxIntegrationTest:
    """Apifox集成测试类"""
    
    def __init__(self, apifox_base_url="http://localhost:4523/m1/5234567-0-default"):
        self.apifox_base_url = apifox_base_url
        self.client = None
        
    def setup_sdk_client(self):
        """设置SDK客户端连接到Apifox"""
        # 创建机构配置，指向Apifox Mock服务器
        org_config = OrganizationConfig(
            org_code="APIFOX_TEST",
            org_name="Apifox测试医院",
            org_type="hospital",
            province_code="43",
            city_code="4301",
            app_id="apifox_test_app",
            app_secret="apifox_test_secret",
            base_url=self.apifox_base_url,
            crypto_type="NONE",  # 测试环境不加密
            sign_type="NONE",    # 测试环境不签名
            timeout_config={"default": 30},
            gateway_config={     # 网关配置
                "endpoint": "/fsi/api/rsfComIfsService/callService",
                "version": "V1.0"
            }
        )
        
        try:
            self.client = MedicalInsuranceClient(org_config)
            print(f"✅ SDK客户端已连接到Apifox: {self.apifox_base_url}")
            return True
        except Exception as e:
            print(f"❌ SDK客户端连接失败: {e}")
            return False
    
    def test_direct_apifox_call(self):
        """直接测试Apifox接口"""
        print("\\n🧪 测试直接调用Apifox接口...")
        
        # 测试1101接口 - 使用你配置的路径
        url_1101 = f"{self.apifox_base_url}/fsi/api/rsfComIfsService/callService"
        test_data_1101 = {
            "infno": "1101",  # 接口编号
            "msgid": "test_msg_001",
            "mdtrtarea_admvs": "4301",
            "insuplc_admdvs": "4301", 
            "recer_sys_code": "MDY32",
            "dev_no": "",
            "dev_safe_info": "",
            "cainfo": "",
            "signtype": "",
            "infver": "V1.0",
            "opter_type": "1",
            "opter": "test_user",
            "opter_name": "测试用户",
            "inf_time": "20240115103000",
            "fixmedins_code": "TEST001",
            "fixmedins_name": "测试医院",
            "sign_no": "",
            "input": {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
        }
        
        try:
            response = requests.post(url_1101, json=test_data_1101, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 1101接口调用成功:")
                print(f"   - 返回码: {result.get('infcode', 'N/A')}")
                print(f"   - 人员姓名: {result.get('output', {}).get('baseinfo', {}).get('psn_name', 'N/A')}")
                return True
            else:
                print(f"❌ 1101接口调用失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 1101接口调用异常: {e}")
            return False
    
    def test_sdk_with_apifox(self):
        """测试SDK与Apifox的集成"""
        if not self.client:
            print("❌ SDK客户端未初始化")
            return False
            
        print("\\n🔗 测试SDK与Apifox集成...")
        
        # 测试1101接口
        try:
            input_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "430123199001011234", 
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
            
            result = self.client.call_interface("1101", input_data)
            print(f"✅ SDK调用1101接口成功:")
            print(f"   - 人员编号: {result.get('person_info', {}).get('psn_no', 'N/A')}")
            print(f"   - 人员姓名: {result.get('person_info', {}).get('psn_name', 'N/A')}")
            print(f"   - 参保信息数量: {len(result.get('insurance_list', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ SDK调用1101接口失败: {e}")
            return False
    
    def test_2201_settlement(self):
        """测试2201结算接口"""
        if not self.client:
            print("❌ SDK客户端未初始化")
            return False
            
        print("\\n💰 测试2201结算接口...")
        
        try:
            input_data = {
                "mdtrt_id": "MDT20240115001",
                "psn_no": "123456789",
                "chrg_bchno": "CHG20240115001",
                "acct_used_flag": "1",
                "insutype": "310"
            }
            
            result = self.client.call_interface("2201", input_data)
            print(f"✅ SDK调用2201接口成功:")
            print(f"   - 结算ID: {result.get('settlement_id', 'N/A')}")
            print(f"   - 总金额: {result.get('total_amount', 'N/A')}")
            print(f"   - 医保支付: {result.get('insurance_amount', 'N/A')}")
            print(f"   - 个人支付: {result.get('personal_amount', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ SDK调用2201接口失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Apifox集成测试...")
        print(f"📡 Apifox服务器: {self.apifox_base_url}")
        print("=" * 60)
        
        # 测试步骤
        tests = [
            ("直接调用Apifox", self.test_direct_apifox_call),
            ("设置SDK客户端", self.setup_sdk_client),
            ("SDK调用1101接口", self.test_sdk_with_apifox),
            ("SDK调用2201接口", self.test_2201_settlement)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\\n📋 {test_name}...")
            try:
                success = test_func()
                results.append((test_name, success))
                if success:
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")
            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}")
                results.append((test_name, False))
        
        # 输出测试总结
        print("\\n" + "=" * 60)
        print("📊 测试结果总结:")
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print(f"\\n🎯 总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！Apifox集成配置成功！")
        else:
            print("⚠️  部分测试失败，请检查Apifox配置和网络连接")


def main():
    """主函数"""
    # 可以通过命令行参数指定Apifox服务器地址
    apifox_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4523/m1/5234567-0-default"
    
    tester = ApifoxIntegrationTest(apifox_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()