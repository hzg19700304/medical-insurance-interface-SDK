"""
DataValidator 单元测试
测试配置驱动的数据验证器功能
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk.core.validator import DataValidator, ValidationRuleEngine
from medical_insurance_sdk.models.config import InterfaceConfig
from medical_insurance_sdk.models.validation import ValidationResult, FieldValidationRule
from medical_insurance_sdk.exceptions import ValidationException


class TestDataValidator(unittest.TestCase):
    """DataValidator 测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的配置管理器
        self.mock_config_manager = Mock()
        
        # 创建验证器实例
        self.validator = DataValidator(self.mock_config_manager)
        
        # 创建测试用的接口配置
        self.test_interface_config = InterfaceConfig(
            api_code="1101",
            api_name="人员信息获取",
            business_category="查询类",
            business_type="人员查询",
            required_params={
                "psn_no": {
                    "display_name": "人员编号",
                    "description": "医保人员编号"
                },
                "psn_name": {
                    "display_name": "人员姓名",
                    "description": "参保人姓名"
                }
            },
            optional_params={
                "cert_no": {
                    "display_name": "证件号码",
                    "description": "身份证号码"
                }
            },
            validation_rules={
                "psn_no": {
                    "pattern": "^[0-9]+$",
                    "max_length": 30,
                    "pattern_error": "人员编号只能包含数字"
                },
                "psn_name": {
                    "max_length": 50,
                    "pattern": "^[\\u4e00-\\u9fa5·]+$",
                    "pattern_error": "人员姓名只能包含中文字符和·"
                },
                "cert_no": {
                    "pattern": "^[0-9]{17}[0-9Xx]$",
                    "pattern_error": "身份证号码格式不正确"
                },
                "conditional_rules": [
                    {
                        "condition": {"field": "psn_no", "operator": "not_empty"},
                        "required_fields": ["psn_name"],
                        "error_message": "提供人员编号时必须提供人员姓名"
                    }
                ],
                "data_transforms": {
                    "psn_name": "trim",
                    "cert_no": "upper"
                }
            }
        )
    
    def test_validate_input_data_success(self):
        """测试成功的数据验证"""
        # 准备测试数据
        api_code = "1101"
        input_data = {
            "psn_no": "123456789",
            "psn_name": "张三",
            "cert_no": "430123199001011234"
        }
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行验证
        result = self.validator.validate_input_data(api_code, input_data, org_code)
        
        # 验证结果
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
        # 验证调用次数
        self.mock_config_manager.get_interface_config.assert_called_once_with(api_code, org_code)
    
    def test_validate_input_data_required_field_missing(self):
        """测试必填字段缺失验证"""
        # 准备测试数据（缺少必填字段psn_name）
        api_code = "1101"
        input_data = {
            "psn_no": "123456789"
            # 缺少 psn_name
        }
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行验证
        result = self.validator.validate_input_data(api_code, input_data, org_code)
        
        # 验证结果
        self.assertFalse(result.is_valid)
        self.assertIn("psn_name", result.errors)
        self.assertIn("人员姓名不能为空", result.errors["psn_name"][0])
    
    def test_validate_input_data_pattern_validation(self):
        """测试正则表达式验证"""
        # 准备测试数据（人员编号包含非数字字符）
        api_code = "1101"
        input_data = {
            "psn_no": "123abc789",  # 包含字母，不符合正则
            "psn_name": "张三"
        }
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行验证
        result = self.validator.validate_input_data(api_code, input_data, org_code)
        
        # 验证结果
        self.assertFalse(result.is_valid)
        self.assertIn("psn_no", result.errors)
        self.assertIn("人员编号只能包含数字", result.errors["psn_no"][0])
    
    def test_validate_input_data_length_validation(self):
        """测试长度验证"""
        # 准备测试数据（人员姓名超长）
        api_code = "1101"
        input_data = {
            "psn_no": "123456789",
            "psn_name": "张" * 51  # 超过50个字符
        }
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行验证
        result = self.validator.validate_input_data(api_code, input_data, org_code)
        
        # 验证结果
        self.assertFalse(result.is_valid)
        self.assertIn("psn_name", result.errors)
        self.assertIn("长度不能超过50位", result.errors["psn_name"][0])
    
    def test_validate_conditional_rules(self):
        """测试条件依赖验证"""
        # 准备测试数据（提供了psn_no但没有psn_name）
        api_code = "1101"
        input_data = {
            "psn_no": "123456789"
            # 根据条件规则，有psn_no时必须有psn_name
        }
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行验证
        result = self.validator.validate_input_data(api_code, input_data, org_code)
        
        # 验证结果
        self.assertFalse(result.is_valid)
        self.assertIn("psn_name", result.errors)
        # 应该包含条件规则错误和必填字段错误
        error_messages = result.get_error_messages()
        self.assertTrue(any("提供人员编号时必须提供人员姓名" in msg or "人员姓名不能为空" in msg for msg in error_messages))
    
    def test_evaluate_condition(self):
        """测试条件表达式评估"""
        data = {
            "field1": "value1",
            "field2": "value2",
            "field3": "",
            "field4": 10,
            "field5": ["a", "b", "c"]
        }
        
        # 测试各种条件操作符
        test_cases = [
            ({"field": "field1", "operator": "eq", "value": "value1"}, True),
            ({"field": "field1", "operator": "eq", "value": "value2"}, False),
            ({"field": "field1", "operator": "ne", "value": "value2"}, True),
            ({"field": "field1", "operator": "in", "value": ["value1", "value3"]}, True),
            ({"field": "field1", "operator": "not_in", "value": ["value2", "value3"]}, True),
            ({"field": "field3", "operator": "empty"}, True),
            ({"field": "field1", "operator": "not_empty"}, True),
            ({"field": "field4", "operator": "gt", "value": 5}, True),
            ({"field": "field4", "operator": "lt", "value": 15}, True),
            ({"field": "field1", "operator": "contains", "value": "lue"}, True),
            ({"field": "field1", "operator": "starts_with", "value": "val"}, True),
            ({"field": "field1", "operator": "ends_with", "value": "ue1"}, True),
        ]
        
        for condition, expected in test_cases:
            with self.subTest(condition=condition):
                result = self.validator._evaluate_condition(condition, data)
                self.assertEqual(result, expected)
    
    def test_apply_data_transforms(self):
        """测试数据转换应用"""
        data = {
            "name": "  张三  ",
            "id_card": "abc123def",
            "phone": "  13812345678  "
        }
        
        validation_rules = {
            "data_transforms": {
                "name": "trim",
                "id_card": "upper",
                "phone": {"type": "trim"}
            }
        }
        
        # 执行数据转换
        transformed_data = self.validator._apply_data_transforms(data, validation_rules)
        
        # 验证转换结果
        self.assertEqual(transformed_data["name"], "张三")
        self.assertEqual(transformed_data["id_card"], "ABC123DEF")
        self.assertEqual(transformed_data["phone"], "13812345678")
    
    def test_apply_single_transform(self):
        """测试单个数据转换"""
        test_cases = [
            ("  hello  ", "trim", "hello"),
            ("hello world", "remove_spaces", "helloworld"),
            ("hello", "upper", "HELLO"),
            ("HELLO", "lower", "hello"),
            ("hello world", "title", "Hello World"),
            ("hello world", {"type": "replace", "old": "world", "new": "python"}, "hello python")
        ]
        
        for value, transform_config, expected in test_cases:
            with self.subTest(value=value, transform_config=transform_config):
                result = self.validator._apply_single_transform(value, 
                    transform_config if isinstance(transform_config, str) else transform_config["type"], 
                    transform_config)
                self.assertEqual(result, expected)
    
    def test_validate_batch_data(self):
        """测试批量数据验证"""
        # 准备测试数据
        api_code = "1101"
        batch_data = [
            {"psn_no": "123456789", "psn_name": "张三"},  # 有效数据
            {"psn_no": "abc123", "psn_name": "李四"},     # 无效数据（psn_no格式错误）
            {"psn_no": "987654321", "psn_name": "王五"}   # 有效数据
        ]
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行批量验证
        results = self.validator.validate_batch_data(api_code, batch_data, org_code)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].is_valid)   # 第一条数据有效
        self.assertFalse(results[1].is_valid)  # 第二条数据无效
        self.assertTrue(results[2].is_valid)   # 第三条数据有效
        
        # 验证错误信息包含批次索引
        self.assertIn("第2条数据", results[1].get_error_messages()[0])
    
    def test_get_validation_summary(self):
        """测试获取验证规则摘要"""
        api_code = "1101"
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        
        # 执行测试
        summary = self.validator.get_validation_summary(api_code, org_code)
        
        # 验证结果
        self.assertEqual(summary["api_code"], "1101")
        self.assertEqual(summary["api_name"], "人员信息获取")
        self.assertIn("psn_no", summary["required_fields"])
        self.assertIn("psn_name", summary["required_fields"])
        self.assertIn("cert_no", summary["optional_fields"])
        self.assertTrue(summary["has_conditional_rules"])
        self.assertTrue(summary["has_data_transforms"])
        self.assertIn("pattern", summary["validation_rule_types"])
        self.assertIn("max_length", summary["validation_rule_types"])
    
    def test_register_custom_validator(self):
        """测试注册自定义验证器"""
        def custom_phone_validator(value):
            """自定义手机号验证器"""
            import re
            pattern = r'^1[3-9]\d{9}$'
            return bool(re.match(pattern, str(value)))
        
        # 注册自定义验证器
        self.validator.register_custom_validator("phone", custom_phone_validator)
        
        # 验证注册成功
        registered_validator = self.validator.rule_engine.get_custom_validator("phone")
        self.assertIsNotNone(registered_validator)
        self.assertEqual(registered_validator, custom_phone_validator)
        
        # 测试自定义验证器功能
        self.assertTrue(registered_validator("13812345678"))
        self.assertFalse(registered_validator("12345678901"))
    
    def test_register_custom_transform(self):
        """测试注册自定义数据转换器"""
        def custom_phone_format(value):
            """自定义手机号格式化"""
            phone = str(value).replace("-", "").replace(" ", "")
            if len(phone) == 11:
                return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
            return phone
        
        # 注册自定义转换器
        self.validator.register_custom_transform("phone_format", custom_phone_format)
        
        # 验证注册成功
        registered_transform = self.validator.rule_engine.get_custom_transform("phone_format")
        self.assertIsNotNone(registered_transform)
        self.assertEqual(registered_transform, custom_phone_format)
        
        # 测试自定义转换器功能
        self.assertEqual(registered_transform("13812345678"), "138-1234-5678")
        self.assertEqual(registered_transform("138-1234-5678"), "138-1234-5678")


class TestValidationRuleEngine(unittest.TestCase):
    """ValidationRuleEngine 测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.rule_engine = ValidationRuleEngine()
    
    def test_register_custom_validator(self):
        """测试注册自定义验证器"""
        def test_validator(value, rule):
            return len(str(value)) > 5
        
        self.rule_engine.register_custom_validator("test_length", test_validator)
        
        # 验证注册成功
        validator = self.rule_engine.get_custom_validator("test_length")
        self.assertIsNotNone(validator)
        self.assertEqual(validator, test_validator)
    
    def test_register_custom_transform(self):
        """测试注册自定义转换器"""
        def test_transform(value):
            return str(value).upper()
        
        self.rule_engine.register_custom_transform("test_upper", test_transform)
        
        # 验证注册成功
        transform = self.rule_engine.get_custom_transform("test_upper")
        self.assertIsNotNone(transform)
        self.assertEqual(transform, test_transform)
    
    def test_evaluate_expression(self):
        """测试表达式评估"""
        context = {
            "value1": 10,
            "value2": 20,
            "name": "test"
        }
        
        # 测试基本数学运算
        result = self.rule_engine.evaluate_expression("value1 + value2", context)
        self.assertEqual(result, 30)
        
        # 测试字符串操作
        result = self.rule_engine.evaluate_expression("len(name)", context)
        self.assertEqual(result, 4)
        
        # 测试比较运算
        result = self.rule_engine.evaluate_expression("value1 < value2", context)
        self.assertTrue(result)
    
    def test_build_validation_chain(self):
        """测试构建验证链"""
        rules = [
            {"type": "required", "message": "字段不能为空"},
            {"type": "length", "min": 5, "max": 20, "message": "长度必须在5-20之间"},
            {"type": "pattern", "pattern": r"^\d+$", "message": "只能包含数字"}
        ]
        
        validators = self.rule_engine.build_validation_chain(rules)
        
        # 验证链长度
        self.assertEqual(len(validators), 3)
        
        # 测试验证链功能
        # 测试空值
        result = validators[0](None)
        self.assertFalse(result.is_valid)
        
        # 测试长度
        result = validators[1]("123")
        self.assertFalse(result.is_valid)
        
        # 测试正则
        result = validators[2]("abc123")
        self.assertFalse(result.is_valid)
        
        # 测试有效值
        result = validators[2]("123456")
        self.assertTrue(result.is_valid)
    
    def test_create_required_validator(self):
        """测试创建必填验证器"""
        rule = {"message": "字段不能为空"}
        validator = self.rule_engine._create_required_validator(rule)
        
        # 测试空值
        result = validator(None)
        self.assertFalse(result.is_valid)
        error_messages = result.get_error_messages()
        self.assertTrue(any("字段不能为空" in msg for msg in error_messages))
        
        result = validator("")
        self.assertFalse(result.is_valid)
        
        result = validator("  ")
        self.assertFalse(result.is_valid)
        
        # 测试有效值
        result = validator("test")
        self.assertTrue(result.is_valid)
    
    def test_create_length_validator(self):
        """测试创建长度验证器"""
        rule = {"min": 5, "max": 10}
        validator = self.rule_engine._create_length_validator(rule)
        
        # 测试长度不足
        result = validator("123")
        self.assertFalse(result.is_valid)
        error_messages = result.get_error_messages()
        self.assertTrue(any("长度不能少于5位" in msg for msg in error_messages))
        
        # 测试长度超出
        result = validator("12345678901")
        self.assertFalse(result.is_valid)
        self.assertIn("长度不能超过10位", result.get_error_messages())
        
        # 测试有效长度
        result = validator("123456")
        self.assertTrue(result.is_valid)
    
    def test_create_pattern_validator(self):
        """测试创建正则验证器"""
        rule = {"pattern": r"^\d+$", "message": "只能包含数字"}
        validator = self.rule_engine._create_pattern_validator(rule)
        
        # 测试无效格式
        result = validator("abc123")
        self.assertFalse(result.is_valid)
        error_messages = result.get_error_messages()
        self.assertTrue(any("只能包含数字" in msg for msg in error_messages))
        
        # 测试有效格式
        result = validator("123456")
        self.assertTrue(result.is_valid)
    
    def test_create_enum_validator(self):
        """测试创建枚举验证器"""
        rule = {"values": ["A", "B", "C"]}
        validator = self.rule_engine._create_enum_validator(rule)
        
        # 测试无效值
        result = validator("D")
        self.assertFalse(result.is_valid)
        error_messages = result.get_error_messages()
        self.assertTrue(any("必须是以下值之一" in msg for msg in error_messages))
        
        # 测试有效值
        result = validator("A")
        self.assertTrue(result.is_valid)
    
    def test_create_range_validator(self):
        """测试创建范围验证器"""
        rule = {"min": 10, "max": 100}
        validator = self.rule_engine._create_range_validator(rule)
        
        # 测试小于最小值
        result = validator("5")
        self.assertFalse(result.is_valid)
        error_messages = result.get_error_messages()
        self.assertTrue(any("不能小于10" in msg for msg in error_messages))
        
        # 测试大于最大值
        result = validator("150")
        self.assertFalse(result.is_valid)
        self.assertIn("不能大于100", result.get_error_messages())
        
        # 测试有效值
        result = validator("50")
        self.assertTrue(result.is_valid)
        
        # 测试非数字值
        result = validator("abc")
        self.assertFalse(result.is_valid)
        self.assertIn("必须是有效的数值", result.get_error_messages())
    
    def test_create_custom_validator(self):
        """测试创建自定义验证器"""
        # 注册自定义验证器
        def custom_validator(value, rule):
            return len(str(value)) > rule.get("min_length", 0)
        
        self.rule_engine.register_custom_validator("custom_length", custom_validator)
        
        rule = {"validator": "custom_length", "min_length": 5, "message": "长度不足"}
        validator = self.rule_engine._create_custom_validator(rule)
        
        # 测试验证功能
        result = validator("123")
        self.assertFalse(result.is_valid)
        error_messages = result.get_error_messages()
        self.assertTrue(any("长度不足" in msg for msg in error_messages))
        
        result = validator("123456")
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()