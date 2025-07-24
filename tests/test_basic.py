"""
基础功能测试
测试SDK的基本导入和初始化功能
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入测试辅助工具
from tests.test_helpers import get_test_data_from_db


class TestBasic(unittest.TestCase):
    """基础功能测试类"""
    
    def test_sdk_import(self):
        """测试SDK模块导入"""
        try:
            import medical_insurance_sdk
            self.assertTrue(True, "SDK模块导入成功")
        except ImportError as e:
            self.fail(f"SDK模块导入失败: {e}")
    
    def test_exceptions_import(self):
        """测试异常模块导入"""
        try:
            from medical_insurance_sdk.exceptions import (
                ValidationException,
                ConfigurationException,
                DataParsingException,
                InterfaceProcessingException
            )
            self.assertTrue(True, "异常模块导入成功")
        except ImportError as e:
            self.fail(f"异常模块导入失败: {e}")
    
    def test_models_import(self):
        """测试模型模块导入"""
        try:
            from medical_insurance_sdk.models.config import InterfaceConfig, OrganizationConfig
            from medical_insurance_sdk.models.validation import ValidationResult
            self.assertTrue(True, "模型模块导入成功")
        except ImportError as e:
            self.fail(f"模型模块导入失败: {e}")
    
    def test_core_components_import(self):
        """测试核心组件导入"""
        try:
            from medical_insurance_sdk.core.universal_processor import UniversalInterfaceProcessor
            from medical_insurance_sdk.core.validator import DataValidator
            from medical_insurance_sdk.core.config_manager import ConfigManager
            self.assertTrue(True, "核心组件导入成功")
        except ImportError as e:
            self.fail(f"核心组件导入失败: {e}")
    
    def test_utils_import(self):
        """测试工具模块导入"""
        try:
            from medical_insurance_sdk.utils.data_helper import DataHelper
            self.assertTrue(True, "工具模块导入成功")
        except ImportError as e:
            self.fail(f"工具模块导入失败: {e}")
    
    def test_validation_result_creation(self):
        """测试ValidationResult创建"""
        try:
            from medical_insurance_sdk.models.validation import ValidationResult
            
            result = ValidationResult()
            self.assertTrue(result.is_valid)
            self.assertEqual(len(result.errors), 0)
            
            # 测试添加错误
            result.add_error("test_field", "测试错误")
            self.assertFalse(result.is_valid)
            self.assertIn("test_field", result.errors)
            self.assertEqual(result.errors["test_field"], ["测试错误"])
            
        except Exception as e:
            self.fail(f"ValidationResult创建失败: {e}")
    
    def test_interface_config_creation(self):
        """测试InterfaceConfig创建"""
        try:
            from medical_insurance_sdk.models.config import InterfaceConfig
            
            config = InterfaceConfig(
                api_code="1101",
                api_name="测试接口",
                business_category="测试类",
                business_type="测试"
            )
            
            self.assertEqual(config.api_code, "1101")
            self.assertEqual(config.api_name, "测试接口")
            self.assertEqual(config.business_category, "测试类")
            self.assertEqual(config.business_type, "测试")
            self.assertTrue(config.is_active)
            
        except Exception as e:
            self.fail(f"InterfaceConfig创建失败: {e}")
    
    def test_organization_config_creation(self):
        """测试OrganizationConfig创建"""
        try:
            from medical_insurance_sdk.models.config import OrganizationConfig
            
            config = OrganizationConfig(
                org_code="TEST001",
                org_name="测试医院",
                province_code="43",
                app_id="test_app_id",
                app_secret="test_app_secret",
                base_url="http://test.example.com"
            )
            
            self.assertEqual(config.org_code, "TEST001")
            self.assertEqual(config.org_name, "测试医院")
            self.assertEqual(config.province_code, "43")
            self.assertTrue(config.is_active)
            
        except Exception as e:
            self.fail(f"OrganizationConfig创建失败: {e}")
    
    def test_data_helper_basic_functions(self):
        """测试DataHelper基本功能"""
        try:
            from medical_insurance_sdk.utils.data_helper import DataHelper
            
            # 从数据库获取测试数据
            test_data = get_test_data_from_db()
            
            # 测试身份证验证
            self.assertTrue(DataHelper.validate_id_card("43012319900101123X"))
            self.assertFalse(DataHelper.validate_id_card("invalid_id"))
            
            # 测试金额格式化
            self.assertEqual(DataHelper.format_amount(123.456), "123.46")
            self.assertEqual(DataHelper.format_amount("invalid"), "0.00")
            
            # 测试人员信息提取 - 使用数据库数据
            person_data = {
                "person_name": test_data["person"]["psn_name"],
                "person_id": test_data["person"]["psn_no"],
                "id_card": test_data["person"]["certno"]
            }
            person_info = DataHelper.extract_person_basic_info(person_data)
            self.assertEqual(person_info["name"], test_data["person"]["psn_name"])
            self.assertEqual(person_info["id"], test_data["person"]["psn_no"])
            
        except Exception as e:
            self.fail(f"DataHelper基本功能测试失败: {e}")


if __name__ == "__main__":
    unittest.main()