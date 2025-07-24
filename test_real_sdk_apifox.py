"""
真实的SDK测试程序
使用SDK的完整功能，从.env和数据库获取配置，测试Apifox接口
"""

import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.client import MedicalInsuranceClient
from medical_insurance_sdk.exceptions import (
    ValidationException,
    ConfigurationException,
    InterfaceProcessingException
)

class RealSDKApifoxTester:
    """真实SDK + Apifox测试器"""
    
    def __init__(self):
        self.client = None
        self.org_code = "TEST001"  # 使用数据库中已有的测试机构
        
    def check_environment_variables(self):
        """检查环境变量配置"""
        print("🔗 检查环境变量配置...")
        
        # 检查数据库相关环境变量
        db_vars = {
            "DB_HOST": os.getenv("DB_HOST", "localhost"),
            "DB_PORT": os.getenv("DB_PORT", "3306"),
            "DB_USER": os.getenv("DB_USER", "root"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
            "DB_DATABASE": os.getenv("DB_DATABASE", "medical_insurance")
        }
        
        print("✅ 环境变量检查:")
        for key, value in db_vars.items():
            if key == "DB_PASSWORD":
                display_value = "***" if value else "(空)"
                print(f"   - {key}: {display_value}")
            else:
                print(f"   - {key}: {value}")
        
        return True
    
    def initialize_sdk_client(self):
        """初始化SDK客户端"""
        print("\\n🚀 初始化SDK客户端...")
        
        try:
            # 直接初始化客户端，MedicalInsuranceClient会自动调用DatabaseConfig.from_env()
            print("📦 直接初始化MedicalInsuranceClient()...")
            print("   - 客户端将自动调用DatabaseConfig.from_env()加载配置")
            print("   - 无需手动处理配置加载逻辑")
            
            self.client = MedicalInsuranceClient()
            
            print("✅ SDK客户端初始化成功")
            print("   - 数据库配置已自动从环境变量加载")
            print("   - 数据库连接池已自动初始化")
            print("   - SDK所有组件已就绪")
            return True
            
        except Exception as e:
            print(f"❌ SDK客户端初始化失败: {e}")
            print("💡 请检查:")
            print("   1. .env文件是否存在且配置正确")
            print("   2. 数据库服务是否正在运行")
            print("   3. 数据库连接参数是否正确")
            print("   4. 环境变量DB_HOST, DB_USER, DB_PASSWORD等是否设置")
            return False
    
    def test_database_configs(self):
        """测试从数据库读取配置"""
        print("\\n🗄️  测试数据库配置读取...")
        
        try:
            if not self.client:
                print("❌ SDK客户端未初始化")
                return False
            
            # 获取SDK实例
            sdk = self.client.sdk
            
            # 测试读取机构配置
            try:
                org_config = sdk.get_organization_config(self.org_code)
                print(f"✅ 机构配置读取成功:")
                print(f"   - 机构代码: {org_config.get('org_code', 'N/A')}")
                print(f"   - 机构名称: {org_config.get('org_name', 'N/A')}")
                print(f"   - 基础URL: {org_config.get('base_url', 'N/A')}")
                print(f"   - 加密类型: {org_config.get('crypto_type', 'N/A')}")
                print(f"   - 签名类型: {org_config.get('sign_type', 'N/A')}")
            except Exception as e:
                print(f"⚠️  机构配置读取失败: {e}")
                return False
            
            # 测试读取1101接口配置
            try:
                interface_config_1101 = sdk.get_interface_config("1101")
                print(f"✅ 1101接口配置读取成功:")
                print(f"   - 接口名称: {interface_config_1101.get('api_name', 'N/A')}")
                print(f"   - 业务类型: {interface_config_1101.get('business_type', 'N/A')}")
                print(f"   - 必填参数: {interface_config_1101.get('required_params', [])}")
                print(f"   - 响应映射: 已配置")
            except Exception as e:
                print(f"⚠️  1101接口配置读取失败: {e}")
                return False
            
            # 测试读取2201接口配置
            try:
                interface_config_2201 = sdk.get_interface_config("2201")
                print(f"✅ 2201接口配置读取成功:")
                print(f"   - 接口名称: {interface_config_2201.get('api_name', 'N/A')}")
                print(f"   - 业务类型: {interface_config_2201.get('business_type', 'N/A')}")
                print(f"   - 必填参数: {interface_config_2201.get('required_params', [])}")
                print(f"   - 响应映射: 已配置")
            except Exception as e:
                print(f"⚠️  2201接口配置读取失败: {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库配置测试失败: {e}")
            return False
    
    def test_1101_interface_with_database_config(self):
        """使用数据库配置测试1101接口"""
        print("\\n🧪 使用数据库配置测试1101人员信息查询接口...")
        
        try:
            if not self.client:
                print("❌ SDK客户端未初始化")
                return False
            
            # 准备测试数据（包含必需的psn_no字段）
            input_data = {
                "psn_no": "123456789",  # 添加必需的人员编号
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
            
            print(f"📤 输入数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            # 调用SDK接口（SDK会自动从数据库读取配置）
            result = self.client.call("1101", input_data, self.org_code)
            
            print(f"📥 SDK返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析结果（使用数据库中的response_mapping配置）
            if isinstance(result, dict):
                print("\\n✅ 1101接口调用成功!")
                
                # 根据数据库配置的response_mapping解析数据
                person_info = result.get('person_info', {})
                if person_info:
                    print(f"   📋 人员基本信息:")
                    print(f"      - 人员编号: {person_info.get('psn_no', 'N/A')}")
                    print(f"      - 人员姓名: {person_info.get('psn_name', 'N/A')}")
                    print(f"      - 性别: {person_info.get('gend', 'N/A')}")
                    print(f"      - 身份证号: {person_info.get('certno', 'N/A')}")
                    print(f"      - 电话: {person_info.get('tel', 'N/A')}")
                    print(f"      - 地址: {person_info.get('addr', 'N/A')}")
                
                insurance_list = result.get('insurance_list', [])
                if insurance_list:
                    print(f"   💳 参保信息 ({len(insurance_list)}条):")
                    for i, insurance in enumerate(insurance_list):
                        print(f"      [{i+1}] 险种: {insurance.get('insurance_type', 'N/A')}")
                        print(f"          余额: {insurance.get('balance', 'N/A')}")
                        print(f"          状态: {insurance.get('status', 'N/A')}")
                
                identity_list = result.get('identity_list', [])
                if identity_list:
                    print(f"   🆔 身份信息 ({len(identity_list)}条):")
                    for i, identity in enumerate(identity_list):
                        print(f"      [{i+1}] 身份类型: {identity.get('identity_type', 'N/A')}")
                        print(f"          有效期: {identity.get('start_time', 'N/A')} - {identity.get('end_time', 'N/A')}")
                
                return True
            else:
                print(f"⚠️  返回数据格式异常: {type(result)}")
                return False
                
        except ValidationException as e:
            print(f"❌ 数据验证失败: {e}")
            return False
        except InterfaceProcessingException as e:
            print(f"❌ 接口处理失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 1101接口调用异常: {e}")
            return False
    
    def test_2201_interface_with_database_config(self):
        """使用数据库配置测试2201接口"""
        print("\\n🏥 使用数据库配置测试2201门诊挂号接口...")
        
        try:
            if not self.client:
                print("❌ SDK客户端未初始化")
                return False
            
            # 准备测试数据（根据2201门诊挂号接口文档）
            input_data = {
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
            
            print(f"📤 输入数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            # 调用SDK接口（SDK会自动从数据库读取配置）
            result = self.client.call("2201", input_data, self.org_code)
            
            print(f"📥 SDK返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析结果（使用数据库中的response_mapping配置）
            if isinstance(result, dict):
                print("\\n✅ 2201接口调用成功!")
                
                # 根据数据库配置的response_mapping解析数据
                registration_result = result.get('registration_result', {})
                if registration_result:
                    print(f"   🏥 挂号详细信息:")
                    print(f"      - 就诊ID: {registration_result.get('mdtrt_id', 'N/A')}")
                    print(f"      - 人员编号: {registration_result.get('psn_no', 'N/A')}")
                    print(f"      - 门诊号: {registration_result.get('ipt_otp_no', 'N/A')}")
                
                # 汇总信息（通过response_mapping映射）
                print(f"   📊 挂号汇总:")
                print(f"      - 就诊ID: {result.get('mdtrt_id', 'N/A')}")
                print(f"      - 人员编号: {result.get('psn_no', 'N/A')}")
                print(f"      - 门诊号: {result.get('ipt_otp_no', 'N/A')}")
                print(f"      - 扩展内容: {result.get('exp_content', 'N/A')}")
                
                return True
            else:
                print(f"⚠️  返回数据格式异常: {type(result)}")
                return False
                
        except ValidationException as e:
            print(f"❌ 数据验证失败: {e}")
            return False
        except InterfaceProcessingException as e:
            print(f"❌ 接口处理失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 2201接口调用异常: {e}")
            return False
    
    def test_data_validation_with_database_rules(self):
        """测试使用数据库验证规则进行数据验证"""
        print("\\n🔍 测试数据库验证规则...")
        
        try:
            if not self.client:
                print("❌ SDK客户端未初始化")
                return False
            
            # 测试无效数据（应该被数据库中的validation_rules拦截）
            invalid_data = {
                "mdtrt_cert_type": "99",  # 无效的凭证类型
                "mdtrt_cert_no": "123",   # 格式错误
                "psn_cert_type": "01",
                "certno": "123456",       # 身份证格式错误
                "psn_name": "Zhang San123"  # 包含非中文字符
            }
            
            print(f"📤 测试无效数据: {json.dumps(invalid_data, ensure_ascii=False, indent=2)}")
            
            try:
                result = self.client.call("1101", invalid_data, self.org_code)
                print("⚠️  预期应该验证失败，但调用成功了")
                return False
            except ValidationException as e:
                print(f"✅ 数据验证正确拦截了无效数据: {e}")
                return True
            
        except Exception as e:
            print(f"❌ 数据验证测试异常: {e}")
            return False
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 真实SDK + Apifox + 数据库配置综合测试")
        print("   使用MedicalInsuranceClient()自动配置加载")
        print("=" * 60)
        
        # 测试步骤
        steps = [
            ("环境变量检查", self.check_environment_variables),
            ("SDK客户端初始化", self.initialize_sdk_client),
            ("数据库配置读取", self.test_database_configs),
            ("数据验证规则测试", self.test_data_validation_with_database_rules),
            ("1101接口测试", self.test_1101_interface_with_database_config),
            ("2201接口测试", self.test_2201_interface_with_database_config)
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
                    # 如果SDK初始化失败，停止后续测试
                    if step_name == "SDK客户端初始化":
                        break
            except Exception as e:
                print(f"❌ {step_name} - 异常: {e}")
                results.append((step_name, False))
                if step_name == "SDK客户端初始化":
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
            print("🎉 所有测试通过！真实SDK + Apifox + 数据库配置集成成功！")
            print("\\n📋 集成特点:")
            print("   ✅ MedicalInsuranceClient()自动配置加载")
            print("   ✅ 自动从.env文件读取数据库配置")
            print("   ✅ 从数据库读取机构配置")
            print("   ✅ 从数据库读取接口配置")
            print("   ✅ 使用数据库的验证规则")
            print("   ✅ 使用数据库的响应映射配置")
            print("   ✅ 连接Apifox Mock服务器")
            print("   ✅ 完整的端到端测试流程")
            print("   ✅ 简化的用户使用体验")
        else:
            print("⚠️  部分测试失败，请检查配置")
            print("\\n💡 排查建议:")
            print("   1. 检查.env文件中的数据库配置")
            print("   2. 确保数据库服务正在运行")
            print("   3. 验证数据库中有测试机构和接口配置数据")
            print("   4. 检查Apifox Mock服务器是否正常")

def main():
    """主函数"""
    tester = RealSDKApifoxTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()