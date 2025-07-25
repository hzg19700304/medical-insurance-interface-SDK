"""
真实的SDK测试程序
使用完整的SDK功能，从.env文件获取数据库配置，从数据库读取机构和接口配置
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from medical_insurance_sdk.client import MedicalInsuranceClient
from medical_insurance_sdk.core.database import DatabaseConfig
from medical_insurance_sdk.exceptions import (
    ValidationException,
    ConfigurationException,
    InterfaceProcessingException
)

class ApifoxSDKTester:
    """Apifox SDK测试器"""
    
    def __init__(self):
        self.client = None
        self.org_code = "APIFOX_TEST"  # 假设数据库中有这个机构配置
        
    def setup_database_config(self):
        """从.env文件设置数据库配置"""
        print("🔗 从.env文件获取数据库配置...")
        
        try:
            # 使用SDK的DatabaseConfig.from_env()方法
            db_config = DatabaseConfig.from_env()
            
            print(f"   数据库配置: {db_config.host}:{db_config.port}/{db_config.database}")
            print(f"   用户: {db_config.user}")
            
            return db_config
                
        except Exception as e:
            print(f"❌ 数据库配置获取失败: {e}")
            return None
    
    def initialize_sdk_client(self):
        """初始化SDK客户端"""
        print("\\n🚀 初始化SDK客户端...")
        
        try:
            # 获取数据库配置
            db_config = self.setup_database_config()
            if not db_config:
                return False
            
            # 创建医保客户端，让它从数据库读取机构配置
            self.client = MedicalInsuranceClient(
                org_code=self.org_code,
                database_config=db_config
            )
            
            print("✅ SDK客户端初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ SDK客户端初始化失败: {e}")
            return False
    
    def test_database_config_loading(self):
        """测试从数据库加载配置"""
        print("\\n🗄️  测试从数据库加载配置...")
        
        try:
            if not self.client:
                print("❌ SDK客户端未初始化")
                return False
            
            # 测试获取机构配置
            config_manager = self.client.sdk.config_manager
            
            try:
                org_config = config_manager.get_organization_config(self.org_code)
                print(f"✅ 机构配置加载成功:")
                print(f"   - 机构代码: {org_config.org_code}")
                print(f"   - 机构名称: {org_config.org_name}")
                print(f"   - 基础URL: {org_config.base_url}")
                print(f"   - 环境: {org_config.environment}")
            except Exception as e:
                print(f"⚠️  机构配置加载失败: {e}")
                return False
            
            # 测试获取1101接口配置
            try:
                interface_1101 = config_manager.get_interface_config("1101")
                print(f"✅ 1101接口配置加载成功:")
                print(f"   - 接口名称: {interface_1101.api_name}")
                print(f"   - 业务类型: {interface_1101.business_type}")
                print(f"   - 必填参数数量: {len(interface_1101.required_params)}")
            except Exception as e:
                print(f"⚠️  1101接口配置加载失败: {e}")
                return False
            
            # 测试获取2201接口配置
            try:
                interface_2201 = config_manager.get_interface_config("2201")
                print(f"✅ 2201接口配置加载成功:")
                print(f"   - 接口名称: {interface_2201.api_name}")
                print(f"   - 业务类型: {interface_2201.business_type}")
                print(f"   - 必填参数数量: {len(interface_2201.required_params)}")
            except Exception as e:
                print(f"⚠️  2201接口配置加载失败: {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库配置加载测试失败: {e}")
            return False
    
    def test_1101_interface(self):
        """测试1101人员信息查询接口"""
        print("\\n🧪 测试1101人员信息查询接口（通过SDK）...")
        
        try:
            # 准备测试数据
            input_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
            
            print(f"📤 输入数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            # 调用SDK接口
            result = self.client.call_interface("1101", input_data)
            
            print(f"📥 SDK返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析结果
            if isinstance(result, dict):
                person_info = result.get('person_info', {})
                insurance_list = result.get('insurance_list', [])
                identity_list = result.get('identity_list', [])
                
                print("\\n✅ 1101接口调用成功!")
                if person_info:
                    print(f"   - 人员编号: {person_info.get('psn_no', 'N/A')}")
                    print(f"   - 人员姓名: {person_info.get('psn_name', 'N/A')}")
                    print(f"   - 性别: {person_info.get('gend', 'N/A')}")
                    print(f"   - 身份证号: {person_info.get('certno', 'N/A')}")
                
                if insurance_list:
                    print(f"   - 参保信息数量: {len(insurance_list)}")
                    for i, info in enumerate(insurance_list):
                        print(f"     [{i+1}] 险种: {info.get('insurance_type', 'N/A')}, 余额: {info.get('balance', 'N/A')}")
                
                if identity_list:
                    print(f"   - 身份信息数量: {len(identity_list)}")
            
            return True
            
        except ValidationException as e:
            print(f"❌ 1101接口数据验证失败: {e}")
            return False
        except InterfaceProcessingException as e:
            print(f"❌ 1101接口处理失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 1101接口调用异常: {e}")
            return False
    
    def test_2201_interface(self):
        """测试2201门诊结算接口"""
        print("\\n💰 测试2201门诊结算接口（通过SDK）...")
        
        try:
            # 准备测试数据
            input_data = {
                "mdtrt_id": "MDT20240115001",
                "psn_no": "123456789",
                "chrg_bchno": "CHG20240115001",
                "acct_used_flag": "1",
                "insutype": "310",
                "invono": "INV20240115001"
            }
            
            print(f"📤 输入数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            # 调用SDK接口
            result = self.client.call_interface("2201", input_data)
            
            print(f"📥 SDK返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析结果
            if isinstance(result, dict):
                settlement_result = result.get('settlement_result', {})
                
                print("\\n✅ 2201接口调用成功!")
                print(f"   - 结算ID: {result.get('settlement_id', 'N/A')}")
                print(f"   - 总金额: {result.get('total_amount', 'N/A')}")
                print(f"   - 医保支付: {result.get('insurance_amount', 'N/A')}")
                print(f"   - 个人支付: {result.get('personal_amount', 'N/A')}")
                print(f"   - 账户支付: {result.get('account_amount', 'N/A')}")
                print(f"   - 现金支付: {result.get('cash_amount', 'N/A')}")
                print(f"   - 结算时间: {result.get('settlement_time', 'N/A')}")
            
            return True
            
        except ValidationException as e:
            print(f"❌ 2201接口数据验证失败: {e}")
            return False
        except InterfaceProcessingException as e:
            print(f"❌ 2201接口处理失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 2201接口调用异常: {e}")
            return False
    
    def run_full_test(self):
        """运行完整测试"""
        print("🚀 医保SDK + Apifox集成测试")
        print("=" * 60)
        
        # 测试步骤
        steps = [
            ("SDK客户端初始化", self.initialize_sdk_client),
            ("数据库配置加载", self.test_database_config_loading),
            ("1101接口测试", self.test_1101_interface),
            ("2201接口测试", self.test_2201_interface)
        ]
        
        results = []
        for step_name, step_func in steps:
            print(f"\\n📋 {step_name}...")
            try:
                success = step_func()
                results.append((step_name, success))
                if success:
                    print(f"✅ {step_name} - 成功")
                else:
                    print(f"❌ {step_name} - 失败")
                    # 如果关键步骤失败，停止后续测试
                    if step_name in ["SDK客户端初始化"]:
                        break
            except Exception as e:
                print(f"❌ {step_name} - 异常: {e}")
                results.append((step_name, False))
                if step_name in ["SDK客户端初始化"]:
                    break
        
        # 输出测试总结
        print("\\n" + "=" * 60)
        print("📊 测试结果总结:")
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for step_name, success in results:
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {step_name}: {status}")
        
        print(f"\\n🎯 总体结果: {passed}/{total} 步骤成功")
        
        if passed == total:
            print("🎉 所有测试通过！SDK + Apifox集成成功！")
            print("\\n📋 集成信息:")
            print("   - SDK使用数据库配置进行接口调用")
            print("   - 机构配置和接口配置从数据库读取")
            print("   - 数据解析使用数据库中的映射配置")
            print("   - Apifox提供Mock数据响应")
        else:
            print("⚠️  部分测试失败，请检查配置和环境")

def main():
    """主函数"""
    tester = ApifoxSDKTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()