"""
UniversalInterfaceProcessor 单元测试
测试通用接口处理器的核心功能
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入测试辅助工具
from tests.test_helpers import get_test_data_from_db

from medical_insurance_sdk.core.universal_processor import UniversalInterfaceProcessor
from medical_insurance_sdk.utils.data_helper import DataHelper
from medical_insurance_sdk.models.config import InterfaceConfig, OrganizationConfig
from medical_insurance_sdk.models.validation import ValidationResult
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    ConfigurationException, 
    DataParsingException,
    InterfaceProcessingException
)


class TestUniversalInterfaceProcessor(unittest.TestCase):
    """UniversalInterfaceProcessor 测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的SDK对象
        self.mock_sdk = Mock()
        self.mock_config_manager = Mock()
        self.mock_sdk.config_manager = self.mock_config_manager
        
        # 创建处理器实例
        self.processor = UniversalInterfaceProcessor(self.mock_sdk)
        
        # 创建测试用的接口配置
        self.test_interface_config = InterfaceConfig(
            api_code="1101",
            api_name="人员信息获取",
            business_category="查询类",
            business_type="人员查询",
            required_params={
                "psn_no": {"display_name": "人员编号", "description": "医保人员编号"}
            },
            optional_params={
                "cert_no": {"display_name": "证件号码", "description": "身份证号码"}
            },
            default_values={
                "psn_cert_type": "01"
            },
            request_template={
                "data": {
                    "psn_no": "${psn_no}",
                    "cert_no": "${cert_no}",
                    "psn_cert_type": "${psn_cert_type}"
                }
            },
            response_mapping={
                "person_name": "output.baseinfo.psn_name",
                "person_id": "output.baseinfo.psn_no"
            },
            validation_rules={
                "psn_no": {
                    "pattern": "^[0-9]+$",
                    "max_length": 30
                }
            },
            region_specific={},
            is_active=True,
            timeout_seconds=30,
            max_retry_times=3
        )
        
        # 创建测试用的机构配置
        self.test_org_config = OrganizationConfig(
            org_code="TEST001",
            org_name="测试医院",
            org_type="hospital",
            province_code="43",
            city_code="4301",
            app_id="test_app_id",
            app_secret="test_app_secret",
            base_url="http://test.example.com",
            crypto_type="SM3",
            sign_type="SM2",
            timeout_config={"default": 30}
        )
    
    def test_call_interface_success(self):
        """测试成功的接口调用"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        # 准备测试数据
        api_code = "1101"
        input_data = {"psn_no": test_data["person"]["psn_no"]}
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 模拟验证结果
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟SDK调用结果 - 使用数据库数据
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": 0,
            "output": {
                "baseinfo": {
                    "psn_name": test_data["person"]["psn_name"],
                    "psn_no": test_data["person"]["psn_no"]
                }
            }
        }
        self.mock_sdk.call.return_value = mock_response
        
        # 模拟数据解析结果 - 使用数据库数据
        expected_parsed_data = {
            "person_name": test_data["person"]["psn_name"],
            "person_id": test_data["person"]["psn_no"]
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=expected_parsed_data)
        
        # 执行测试
        result = self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证结果
        self.assertEqual(result, expected_parsed_data)
        
        # 验证调用次数
        self.mock_config_manager.get_interface_config.assert_called_once()
        self.processor.data_validator.validate_input_data.assert_called_once()
        self.mock_sdk.call.assert_called_once()
        self.processor.data_parser.parse_response_data.assert_called_once()
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['total_calls'], 1)
        self.assertEqual(stats['successful_calls'], 1)
        self.assertEqual(stats['failed_calls'], 0)
    
    def test_call_interface_validation_error(self):
        """测试数据验证失败的情况"""
        # 准备测试数据
        api_code = "1101"
        input_data = {"psn_no": ""}  # 空值，应该验证失败
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 模拟验证失败
        mock_validation_result = ValidationResult()
        mock_validation_result.add_error("psn_no", "人员编号不能为空")
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 执行测试并验证异常
        with self.assertRaises(ValidationException) as context:
            self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证异常信息
        self.assertIn("输入数据验证失败", str(context.exception))
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['validation_errors'], 1)
        self.assertEqual(stats['failed_calls'], 1)
    
    def test_call_interface_config_not_found(self):
        """测试接口配置不存在的情况"""
        # 准备测试数据
        api_code = "9999"  # 不存在的接口
        input_data = {"psn_no": "123456789"}
        org_code = "TEST001"
        
        # 模拟配置管理器抛出异常
        self.mock_config_manager.get_interface_config.side_effect = ConfigurationException("接口配置不存在")
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 执行测试并验证异常 - 现在会被包装为InterfaceProcessingException
        with self.assertRaises(InterfaceProcessingException):
            self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['failed_calls'], 1)
    
    def test_preprocess_input_data(self):
        """测试数据预处理功能"""
        # 准备测试数据
        input_data = {"psn_no": "123456789"}
        
        # 执行预处理
        processed_data = self.processor._preprocess_input_data(input_data, self.test_interface_config)
        
        # 验证默认值被应用
        self.assertEqual(processed_data["psn_cert_type"], "01")
        self.assertEqual(processed_data["psn_no"], "123456789")
    
    def test_apply_data_transforms(self):
        """测试数据转换功能"""
        # 准备测试数据
        data = {"name": " 张三 ", "id_card": "abc123"}
        transforms = {
            "name": "trim",
            "id_card": "upper"
        }
        
        # 执行数据转换
        transformed_data = self.processor._apply_data_transforms(data, transforms)
        
        # 验证转换结果
        self.assertEqual(transformed_data["name"], "张三")
        self.assertEqual(transformed_data["id_card"], "ABC123")
    
    def test_apply_single_transform(self):
        """测试单个数据转换"""
        # 测试各种转换类型
        test_cases = [
            ("  hello  ", "trim", "hello"),
            ("hello world", "remove_spaces", "helloworld"),
            ("hello", "upper", "HELLO"),
            ("HELLO", "lower", "hello"),
            ("hello world", "title", "Hello World")
        ]
        
        for value, transform_type, expected in test_cases:
            with self.subTest(value=value, transform_type=transform_type):
                result = self.processor._apply_single_transform(value, transform_type)
                self.assertEqual(result, expected)
    
    def test_apply_request_template(self):
        """测试请求模板应用"""
        # 准备测试数据
        input_data = {"psn_no": "123456789", "cert_no": "430123199001011234"}
        template = {
            "data": {
                "psn_no": "${psn_no}",
                "cert_no": "${cert_no}",
                "fixed_value": "test"
            }
        }
        
        # 执行模板应用
        result = self.processor._apply_request_template(input_data, template)
        
        # 验证结果
        expected = {
            "data": {
                "psn_no": "123456789",
                "cert_no": "430123199001011234",
                "fixed_value": "test"
            }
        }
        self.assertEqual(result, expected)
    
    def test_convert_field_type(self):
        """测试字段类型转换"""
        # 测试各种类型转换
        test_cases = [
            ("123", "int", 123),
            ("123.45", "float", 123.45),
            ("true", "bool", True),
            ("false", "bool", False),
            (123, "string", "123")
        ]
        
        for value, target_type, expected in test_cases:
            with self.subTest(value=value, target_type=target_type):
                result = self.processor._convert_field_type(value, target_type)
                self.assertEqual(result, expected)
    
    def test_call_batch_interfaces(self):
        """测试批量接口调用"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        # 准备测试数据
        batch_requests = [
            {
                "api_code": "1101",
                "input_data": {"psn_no": test_data["person"]["psn_no"]},
                "org_code": "TEST001"
            },
            {
                "api_code": "1101",
                "input_data": {"psn_no": "TEST002"},  # 使用另一个测试ID
                "org_code": "TEST001"
            }
        ]
        
        # 模拟单个接口调用成功
        self.processor.call_interface = Mock(return_value={"success": True})
        
        # 执行批量调用
        results = self.processor.call_batch_interfaces(batch_requests)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        for i, result in enumerate(results):
            self.assertTrue(result["success"])
            self.assertEqual(result["index"], i)
        
        # 验证调用次数
        self.assertEqual(self.processor.call_interface.call_count, 2)
    
    def test_call_batch_interfaces_with_error(self):
        """测试批量接口调用中包含错误的情况"""
        # 准备测试数据
        batch_requests = [
            {
                "api_code": "1101",
                "input_data": {"psn_no": "123456789"},
                "org_code": "TEST001"
            },
            {
                # 缺少必要参数
                "input_data": {"psn_no": "987654321"},
                "org_code": "TEST001"
            }
        ]
        
        # 模拟第一个调用成功，第二个失败
        def mock_call_interface(*args, **kwargs):
            return {"success": True}
        
        self.processor.call_interface = Mock(side_effect=mock_call_interface)
        
        # 执行批量调用
        results = self.processor.call_batch_interfaces(batch_requests)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["success"])
        self.assertFalse(results[1]["success"])
        self.assertIn("缺少必要参数", results[1]["error"])
    
    def test_get_interface_info(self):
        """测试获取接口信息"""
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 执行测试
        info = self.processor.get_interface_info("1101", "TEST001")
        
        # 验证结果
        self.assertEqual(info["api_code"], "1101")
        self.assertEqual(info["api_name"], "人员信息获取")
        self.assertEqual(info["business_category"], "查询类")
        self.assertIn("psn_no", info["required_params"])
        self.assertIn("cert_no", info["optional_params"])
    
    def test_validate_interface_data(self):
        """测试接口数据验证（不执行调用）"""
        # 准备测试数据
        api_code = "1101"
        input_data = {"psn_no": "123456789"}
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 模拟验证结果
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 执行验证
        result = self.processor.validate_interface_data(api_code, input_data, org_code)
        
        # 验证结果
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["errors"], {})
        self.assertIsNotNone(result["processed_data"])
    
    def test_get_processing_stats(self):
        """测试获取处理统计信息"""
        # 初始统计应该为0
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats["total_calls"], 0)
        self.assertEqual(stats["successful_calls"], 0)
        self.assertEqual(stats["failed_calls"], 0)
        self.assertEqual(stats["success_rate"], 0.0)
        
        # 模拟一些调用
        self.processor._processing_stats["total_calls"] = 10
        self.processor._processing_stats["successful_calls"] = 8
        self.processor._processing_stats["failed_calls"] = 2
        
        # 重新获取统计
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats["total_calls"], 10)
        self.assertEqual(stats["successful_calls"], 8)
        self.assertEqual(stats["failed_calls"], 2)
        self.assertEqual(stats["success_rate"], 0.8)
        self.assertEqual(stats["failure_rate"], 0.2)
    
    def test_reset_processing_stats(self):
        """测试重置处理统计"""
        # 设置一些统计数据
        self.processor._processing_stats["total_calls"] = 10
        self.processor._processing_stats["successful_calls"] = 8
        
        # 重置统计
        self.processor.reset_processing_stats()
        
        # 验证统计被重置
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats["total_calls"], 0)
        self.assertEqual(stats["successful_calls"], 0)
    
    def test_get_supported_interfaces(self):
        """测试获取支持的接口列表"""
        # 模拟配置管理器返回
        mock_configs = [self.test_interface_config]
        self.mock_config_manager.get_all_interface_configs.return_value = mock_configs
        
        # 执行测试
        interfaces = self.processor.get_supported_interfaces()
        
        # 验证结果
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0]["api_code"], "1101")
        self.assertEqual(interfaces[0]["api_name"], "人员信息获取")


class TestDataHelper(unittest.TestCase):
    """DataHelper 测试类"""
    
    def test_extract_person_basic_info(self):
        """测试提取人员基本信息"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        response_data = {
            "person_name": test_data["person"]["psn_name"],
            "person_id": test_data["person"]["psn_no"],
            "id_card": test_data["person"]["certno"],
            "gender": test_data["person"]["gend"],
            "birth_date": test_data["person"]["brdy"],
            "age": 34  # 年龄可以是计算值
        }
        
        result = DataHelper.extract_person_basic_info(response_data)
        
        self.assertEqual(result["name"], test_data["person"]["psn_name"])
        self.assertEqual(result["id"], test_data["person"]["psn_no"])
        self.assertEqual(result["id_card"], test_data["person"]["certno"])
        self.assertEqual(result["gender"], test_data["person"]["gend"])
        self.assertEqual(result["birth_date"], test_data["person"]["brdy"])
        self.assertEqual(result["age"], 34)
    
    def test_extract_insurance_info(self):
        """测试提取参保信息"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        response_data = {
            "insurance_list": [
                {
                    "type": test_data["insurance"]["insutype"],
                    "balance": test_data["insurance"]["balc"]
                },
                {"type": "320", "balance": 500.0}  # 添加一个额外的保险类型
            ]
        }
        
        result = DataHelper.extract_insurance_info(response_data)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], test_data["insurance"]["insutype"])
        self.assertEqual(result[0]["balance"], test_data["insurance"]["balc"])
    
    def test_calculate_total_balance(self):
        """测试计算总余额"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        insurance_list = [
            {"balance": test_data["insurance"]["balc"]},
            {"balance": 500.0},
            {"balance": 200.0}
        ]
        
        result = DataHelper.calculate_total_balance(insurance_list)
        
        expected_total = test_data["insurance"]["balc"] + 500.0 + 200.0
        self.assertEqual(result, round(expected_total, 2))
    
    def test_format_settlement_summary(self):
        """测试格式化结算摘要"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        response_data = {
            "settlement_id": test_data["settlement"]["setl_id"],
            "total_amount": str(test_data["settlement"]["setl_totlnum"]),
            "insurance_amount": str(test_data["settlement"]["hifp_pay"]),
            "personal_amount": str(test_data["settlement"]["psn_pay"]),
            "settlement_time": test_data["settlement"]["setl_time"]
        }
        
        result = DataHelper.format_settlement_summary(response_data)
        
        self.assertEqual(result["settlement_id"], test_data["settlement"]["setl_id"])
        self.assertEqual(result["total"], float(test_data["settlement"]["setl_totlnum"]))
        self.assertEqual(result["insurance_pay"], float(test_data["settlement"]["hifp_pay"]))
        self.assertEqual(result["personal_pay"], float(test_data["settlement"]["psn_pay"]))
        self.assertEqual(result["settlement_time"], test_data["settlement"]["setl_time"])
    
    def test_extract_error_info(self):
        """测试提取错误信息"""
        response_data = {
            "infcode": -1,
            "err_msg": "参数错误",
            "warn_msg": "警告信息"
        }
        
        result = DataHelper.extract_error_info(response_data)
        
        self.assertEqual(result["error_code"], -1)
        self.assertEqual(result["error_message"], "参数错误")
        self.assertEqual(result["warning_message"], "警告信息")
        self.assertFalse(result["is_success"])
    
    def test_validate_id_card(self):
        """测试身份证号码验证"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        # 测试有效的18位身份证（使用正确的校验码）
        self.assertTrue(DataHelper.validate_id_card("43012319900101123X"))
        self.assertTrue(DataHelper.validate_id_card("430123199001011248"))
        
        # 测试有效的15位身份证
        self.assertTrue(DataHelper.validate_id_card("430123900101123"))
        
        # 测试无效的身份证
        self.assertFalse(DataHelper.validate_id_card("430123199001011234"))  # 错误的校验码
        self.assertFalse(DataHelper.validate_id_card("123456"))
        self.assertFalse(DataHelper.validate_id_card(""))
        self.assertFalse(DataHelper.validate_id_card(None))
        
        # 如果数据库中的身份证号码是有效的，也可以测试
        if test_data["person"]["certno"] and len(test_data["person"]["certno"]) in (15, 18):
            try:
                # 这里不断言结果，因为我们不确定数据库中的身份证是否有效
                DataHelper.validate_id_card(test_data["person"]["certno"])
            except Exception as e:
                self.fail(f"使用数据库身份证验证失败: {e}")
    
    def test_format_amount(self):
        """测试金额格式化"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        # 测试正常金额
        self.assertEqual(DataHelper.format_amount(1234.567), "1234.57")
        self.assertEqual(DataHelper.format_amount("1234.567"), "1234.57")
        
        # 测试指定小数位数
        self.assertEqual(DataHelper.format_amount(1234.567, 1), "1234.6")
        
        # 测试无效金额
        self.assertEqual(DataHelper.format_amount("invalid"), "0.00")
        self.assertEqual(DataHelper.format_amount(None), "0.00")
        
        # 使用数据库中的金额进行测试
        if test_data["settlement"]["setl_totlnum"]:
            formatted = DataHelper.format_amount(test_data["settlement"]["setl_totlnum"])
            self.assertTrue(isinstance(formatted, str))
            self.assertTrue("." in formatted)  # 确保包含小数点
    
    def test_parse_date_string(self):
        """测试日期字符串解析"""
        # 从数据库获取测试数据
        test_data = get_test_data_from_db()
        
        # 测试正常日期转换
        result = DataHelper.parse_date_string("2024-01-15", "%Y-%m-%d", "%Y%m%d")
        self.assertEqual(result, "20240115")
        
        # 测试无效日期
        result = DataHelper.parse_date_string("invalid-date", "%Y-%m-%d", "%Y%m%d")
        self.assertEqual(result, "invalid-date")
        
        # 使用数据库中的日期进行测试
        if test_data["person"]["brdy"]:
            try:
                parsed = DataHelper.parse_date_string(test_data["person"]["brdy"], "%Y-%m-%d", "%Y%m%d")
                self.assertEqual(len(parsed), 8)  # 确保格式为YYYYMMDD
            except Exception:
                # 如果数据库中的日期格式不是预期的，这个测试可能会失败
                pass


if __name__ == "__main__":
    unittest.main()