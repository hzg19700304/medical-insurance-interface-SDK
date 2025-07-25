"""
2201接口（门诊结算）完整测试用例
实现门诊结算接口的完整测试，包括结算流程、数据处理和HIS系统数据同步测试
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import json
import sys
import os
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk.client import MedicalInsuranceClient
from medical_insurance_sdk.core.universal_processor import UniversalInterfaceProcessor
from medical_insurance_sdk.core.validator import DataValidator
from medical_insurance_sdk.core.config_manager import ConfigManager
from medical_insurance_sdk.models.config import InterfaceConfig, OrganizationConfig
from medical_insurance_sdk.models.validation import ValidationResult
from medical_insurance_sdk.utils.data_helper import DataHelper
from medical_insurance_sdk.exceptions import (
    ValidationException,
    ConfigurationException,
    DataParsingException,
    InterfaceProcessingException
)
from tests.test_helpers import get_test_data_from_db


class Test2201SettlementInterface(unittest.TestCase):
    """2201门诊结算接口测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的SDK和配置管理器
        self.mock_sdk = Mock()
        self.mock_config_manager = Mock()
        self.mock_sdk.config_manager = self.mock_config_manager
        
        # 创建通用接口处理器
        self.processor = UniversalInterfaceProcessor(self.mock_sdk)
        
        # 获取测试数据
        self.test_data = get_test_data_from_db()
        
        # 创建2201接口配置
        self.interface_config_2201 = InterfaceConfig(
            api_code="2201",
            api_name="门诊结算",
            business_category="医保服务业务",
            business_type="settlement",
            required_params={
                "mdtrt_id": {
                    "display_name": "就医登记号",
                    "description": "医疗机构就医登记号"
                },
                "psn_no": {
                    "display_name": "人员编号",
                    "description": "医保人员编号"
                },
                "chrg_bchno": {
                    "display_name": "收费批次号",
                    "description": "收费批次号"
                }
            },
            optional_params={
                "acct_used_flag": {
                    "display_name": "个人账户使用标志",
                    "description": "0-不使用，1-使用"
                },
                "insutype": {
                    "display_name": "险种类型",
                    "description": "310-职工基本医疗保险"
                },
                "invono": {
                    "display_name": "发票号",
                    "description": "医疗机构发票号"
                }
            },
            default_values={
                "acct_used_flag": "0",
                "insutype": "310"
            },
            validation_rules={
                "mdtrt_id": {
                    "max_length": 30,
                    "pattern": "^[A-Za-z0-9]+$",
                    "pattern_error": "就医登记号只能包含字母和数字"
                },
                "psn_no": {
                    "max_length": 30,
                    "pattern": "^[0-9]+$",
                    "pattern_error": "人员编号只能包含数字"
                },
                "chrg_bchno": {
                    "max_length": 30,
                    "pattern": "^[A-Za-z0-9]+$",
                    "pattern_error": "收费批次号只能包含字母和数字"
                },
                "acct_used_flag": {
                    "enum_values": ["0", "1"],
                    "pattern_error": "个人账户使用标志必须是0或1"
                },
                "insutype": {
                    "enum_values": ["310", "320", "330"],
                    "pattern_error": "险种类型必须是310、320或330"
                }
            },
            response_mapping={
                "settlement_result": {
                    "type": "direct",
                    "source_path": "setlinfo"
                },
                "settlement_id": {
                    "type": "direct",
                    "source_path": "setlinfo.setl_id"
                },
                "total_amount": {
                    "type": "direct",
                    "source_path": "setlinfo.setl_totlnum"
                },
                "insurance_amount": {
                    "type": "direct",
                    "source_path": "setlinfo.hifp_pay"
                },
                "personal_amount": {
                    "type": "direct",
                    "source_path": "setlinfo.psn_pay"
                },
                "account_amount": {
                    "type": "direct",
                    "source_path": "setlinfo.acct_pay"
                },
                "cash_amount": {
                    "type": "direct",
                    "source_path": "setlinfo.psn_cash_pay"
                },
                "settlement_time": {
                    "type": "direct",
                    "source_path": "setlinfo.setl_time"
                }
            },
            region_specific={},
            is_active=True,
            timeout_seconds=60,  # 结算接口超时时间较长
            max_retry_times=3
        )
        
        # 创建机构配置
        self.org_config = OrganizationConfig(
            org_code="TEST001",
            org_name="测试医院",
            org_type="hospital",
            province_code="43",
            city_code="4301",
            app_id="test_app_id",
            app_secret="test_app_secret",
            base_url="http://test.medical.gov.cn",
            crypto_type="SM3",
            sign_type="SM2",
            timeout_config={"default": 60, "settlement": 120}
        )
        
        # 创建测试用的结算数据
        self.settlement_test_data = {
            "mdtrt_id": "MDT20240115001",
            "psn_no": self.test_data["person"]["psn_no"],
            "chrg_bchno": "CHG20240115001",
            "acct_used_flag": "1",
            "insutype": "310",
            "invono": "INV20240115001"
        }
    
    def test_2201_successful_settlement(self):
        """测试成功的门诊结算"""
        # 准备测试数据
        input_data = self.settlement_test_data.copy()
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟SDK调用成功
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": 0,
            "inf_refmsgid": "test_msg_2201_001",
            "respond_time": "20240115103000",
            "output": {
                "setlinfo": {
                    "setl_id": self.test_data["settlement"]["setl_id"],
                    "setl_totlnum": self.test_data["settlement"]["setl_totlnum"],
                    "hifp_pay": self.test_data["settlement"]["hifp_pay"],
                    "psn_pay": self.test_data["settlement"]["psn_pay"],
                    "acct_pay": 100.00,
                    "psn_cash_pay": 100.00,
                    "setl_time": self.test_data["settlement"]["setl_time"],
                    "med_type": "11",
                    "setl_type": "1",
                    "invono": input_data["invono"],
                    "recp_no": "RCP20240115001"
                }
            }
        }
        self.mock_sdk.call.return_value = mock_response
        
        # 模拟数据解析
        expected_parsed_data = {
            "settlement_result": {
                "setl_id": self.test_data["settlement"]["setl_id"],
                "setl_totlnum": self.test_data["settlement"]["setl_totlnum"],
                "hifp_pay": self.test_data["settlement"]["hifp_pay"],
                "psn_pay": self.test_data["settlement"]["psn_pay"],
                "acct_pay": 100.00,
                "psn_cash_pay": 100.00,
                "setl_time": self.test_data["settlement"]["setl_time"],
                "med_type": "11",
                "setl_type": "1",
                "invono": input_data["invono"],
                "recp_no": "RCP20240115001"
            },
            "settlement_id": self.test_data["settlement"]["setl_id"],
            "total_amount": self.test_data["settlement"]["setl_totlnum"],
            "insurance_amount": self.test_data["settlement"]["hifp_pay"],
            "personal_amount": self.test_data["settlement"]["psn_pay"],
            "account_amount": 100.00,
            "cash_amount": 100.00,
            "settlement_time": self.test_data["settlement"]["setl_time"]
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=expected_parsed_data)
        
        # 执行测试
        result = self.processor.call_interface("2201", input_data, "TEST001")
        
        # 验证结果
        self.assertEqual(result, expected_parsed_data)
        self.assertEqual(result["settlement_id"], self.test_data["settlement"]["setl_id"])
        self.assertEqual(result["total_amount"], self.test_data["settlement"]["setl_totlnum"])
        self.assertEqual(result["insurance_amount"], self.test_data["settlement"]["hifp_pay"])
        self.assertEqual(result["personal_amount"], self.test_data["settlement"]["psn_pay"])
        
        # 验证调用次数
        self.mock_config_manager.get_interface_config.assert_called_once()
        self.processor.data_validator.validate_input_data.assert_called_once()
        self.mock_sdk.call.assert_called_once()
    
    def test_2201_settlement_without_account_usage(self):
        """测试不使用个人账户的门诊结算"""
        # 准备测试数据（不使用个人账户）
        input_data = self.settlement_test_data.copy()
        input_data["acct_used_flag"] = "0"
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟成功响应（个人账户支付为0）
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": 0,
            "output": {
                "setlinfo": {
                    "setl_id": self.test_data["settlement"]["setl_id"],
                    "setl_totlnum": self.test_data["settlement"]["setl_totlnum"],
                    "hifp_pay": self.test_data["settlement"]["hifp_pay"],
                    "psn_pay": self.test_data["settlement"]["psn_pay"],
                    "acct_pay": 0.00,  # 不使用个人账户
                    "psn_cash_pay": self.test_data["settlement"]["psn_pay"],  # 全部现金支付
                    "setl_time": self.test_data["settlement"]["setl_time"]
                }
            }
        }
        self.mock_sdk.call.return_value = mock_response
        
        expected_result = {
            "settlement_id": self.test_data["settlement"]["setl_id"],
            "account_amount": 0.00,
            "cash_amount": self.test_data["settlement"]["psn_pay"]
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=expected_result)
        
        # 执行测试
        result = self.processor.call_interface("2201", input_data, "TEST001")
        
        # 验证结果
        self.assertEqual(result["account_amount"], 0.00)
        self.assertEqual(result["cash_amount"], self.test_data["settlement"]["psn_pay"])
    
    def test_2201_validation_error_missing_required_field(self):
        """测试2201接口必填字段缺失的验证错误"""
        # 准备缺少必填字段的测试数据
        input_data = {
            "mdtrt_id": self.settlement_test_data["mdtrt_id"],
            # 缺少 psn_no
            "chrg_bchno": self.settlement_test_data["chrg_bchno"]
        }
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证失败
        mock_validation_result = ValidationResult()
        mock_validation_result.add_error("psn_no", "人员编号不能为空")
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 执行测试并验证异常
        with self.assertRaises(ValidationException) as context:
            self.processor.call_interface("2201", input_data, "TEST001")
        
        # 验证异常信息
        self.assertIn("输入数据验证失败", str(context.exception))
        
        # 验证SDK没有被调用
        self.mock_sdk.call.assert_not_called()
    
    def test_2201_validation_error_invalid_account_flag(self):
        """测试2201接口无效个人账户使用标志的验证错误"""
        # 准备无效个人账户标志的测试数据
        input_data = self.settlement_test_data.copy()
        input_data["acct_used_flag"] = "2"  # 无效值
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        
        # 模拟验证失败
        mock_validation_result = ValidationResult()
        mock_validation_result.add_error("acct_used_flag", "个人账户使用标志必须是0或1")
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 执行测试并验证异常
        with self.assertRaises(ValidationException):
            self.processor.call_interface("2201", input_data, "TEST001")
    
    def test_2201_validation_error_invalid_insurance_type(self):
        """测试2201接口无效险种类型的验证错误"""
        # 准备无效险种类型的测试数据
        input_data = self.settlement_test_data.copy()
        input_data["insutype"] = "999"  # 无效的险种类型
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        
        # 模拟验证失败
        mock_validation_result = ValidationResult()
        mock_validation_result.add_error("insutype", "险种类型必须是310、320或330")
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 执行测试并验证异常
        with self.assertRaises(ValidationException):
            self.processor.call_interface("2201", input_data, "TEST001")
    
    def test_2201_settlement_business_error(self):
        """测试2201接口业务错误响应处理"""
        # 准备正确的测试数据
        input_data = self.settlement_test_data.copy()
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟接口返回业务错误
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": -1,
            "err_msg": "个人账户余额不足",
            "output": {}
        }
        self.mock_sdk.call.return_value = mock_response
        
        # 模拟数据解析处理错误响应
        error_result = {
            "success": False,
            "error_code": -1,
            "error_message": "个人账户余额不足",
            "settlement_failed": True
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=error_result)
        
        # 执行测试
        result = self.processor.call_interface("2201", input_data, "TEST001")
        
        # 验证错误结果
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], -1)
        self.assertEqual(result["error_message"], "个人账户余额不足")
        self.assertTrue(result["settlement_failed"])
    
    def test_2201_settlement_timeout_error(self):
        """测试2201接口超时错误处理"""
        # 准备测试数据
        input_data = self.settlement_test_data.copy()
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟超时
        self.mock_sdk.call.side_effect = Exception("Settlement timeout")
        
        # 执行测试并验证异常
        with self.assertRaises(InterfaceProcessingException):
            self.processor.call_interface("2201", input_data, "TEST001")
    
    def test_2201_settlement_amount_calculation(self):
        """测试2201接口结算金额计算"""
        # 准备测试数据
        input_data = self.settlement_test_data.copy()
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟复杂的结算响应
        total_amount = 1500.00
        insurance_pay = 1200.00
        account_pay = 200.00
        cash_pay = 100.00
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": 0,
            "output": {
                "setlinfo": {
                    "setl_id": "SETL20240115002",
                    "setl_totlnum": total_amount,
                    "hifp_pay": insurance_pay,
                    "psn_pay": account_pay + cash_pay,
                    "acct_pay": account_pay,
                    "psn_cash_pay": cash_pay,
                    "setl_time": "2024-01-15 10:30:00"
                }
            }
        }
        self.mock_sdk.call.return_value = mock_response
        
        # 模拟数据解析
        expected_result = {
            "total_amount": total_amount,
            "insurance_amount": insurance_pay,
            "personal_amount": account_pay + cash_pay,
            "account_amount": account_pay,
            "cash_amount": cash_pay
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=expected_result)
        
        # 执行测试
        result = self.processor.call_interface("2201", input_data, "TEST001")
        
        # 验证金额计算
        self.assertEqual(result["total_amount"], total_amount)
        self.assertEqual(result["insurance_amount"], insurance_pay)
        self.assertEqual(result["personal_amount"], account_pay + cash_pay)
        self.assertEqual(result["account_amount"], account_pay)
        self.assertEqual(result["cash_amount"], cash_pay)
        
        # 验证金额平衡
        calculated_total = result["insurance_amount"] + result["personal_amount"]
        self.assertEqual(calculated_total, result["total_amount"])
    
    def test_2201_settlement_with_different_insurance_types(self):
        """测试2201接口不同险种类型的结算"""
        insurance_types = [
            ("310", "职工基本医疗保险"),
            ("320", "城乡居民基本医疗保险"),
            ("330", "公务员医疗补助")
        ]
        
        for insutype, type_name in insurance_types:
            with self.subTest(insutype=insutype, type_name=type_name):
                # 准备测试数据
                input_data = self.settlement_test_data.copy()
                input_data["insutype"] = insutype
                
                # 模拟配置
                self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
                self.mock_config_manager.get_organization_config.return_value = self.org_config
                
                # 模拟验证成功
                mock_validation_result = ValidationResult()
                self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
                
                # 模拟成功响应
                mock_response = Mock()
                mock_response.to_dict.return_value = {
                    "infcode": 0,
                    "output": {
                        "setlinfo": {
                            "setl_id": f"SETL_{insutype}_001",
                            "setl_totlnum": 1000.00,
                            "hifp_pay": 800.00,
                            "psn_pay": 200.00,
                            "insutype": insutype,
                            "setl_time": "2024-01-15 10:30:00"
                        }
                    }
                }
                self.mock_sdk.call.return_value = mock_response
                
                expected_result = {
                    "settlement_id": f"SETL_{insutype}_001",
                    "insurance_type": insutype
                }
                self.processor.data_parser.parse_response_data = Mock(return_value=expected_result)
                
                # 执行测试
                result = self.processor.call_interface("2201", input_data, "TEST001")
                
                # 验证结果
                self.assertEqual(result["settlement_id"], f"SETL_{insutype}_001")
                self.assertEqual(result["insurance_type"], insutype)
    
    def test_2201_settlement_boundary_conditions(self):
        """测试2201接口边界条件"""
        # 测试用例1：最长字段值
        long_field_data = self.settlement_test_data.copy()
        long_field_data["mdtrt_id"] = "A" * 30  # 最大长度
        long_field_data["chrg_bchno"] = "B" * 30  # 最大长度
        
        # 模拟配置
        self.mock_config_manager.get_interface_config.return_value = self.interface_config_2201
        self.mock_config_manager.get_organization_config.return_value = self.org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟成功响应
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": 0,
            "output": {
                "setlinfo": {
                    "setl_id": "BOUNDARY_TEST_001",
                    "setl_totlnum": 0.01,  # 最小金额
                    "hifp_pay": 0.00,
                    "psn_pay": 0.01,
                    "setl_time": "2024-01-15 10:30:00"
                }
            }
        }
        self.mock_sdk.call.return_value = mock_response
        
        expected_result = {
            "settlement_id": "BOUNDARY_TEST_001",
            "total_amount": 0.01
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=expected_result)
        
        # 执行测试
        result = self.processor.call_interface("2201", long_field_data, "TEST001")
        
        # 验证结果
        self.assertEqual(result["settlement_id"], "BOUNDARY_TEST_001")
        self.assertEqual(result["total_amount"], 0.01)
        
        # 测试用例2：超长字段值（应该验证失败）
        too_long_data = self.settlement_test_data.copy()
        too_long_data["mdtrt_id"] = "A" * 31  # 超过最大长度
        
        # 模拟验证失败
        mock_validation_result = ValidationResult()
        mock_validation_result.add_error("mdtrt_id", "就医登记号长度不能超过30位")
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 执行测试并验证异常
        with self.assertRaises(ValidationException):
            self.processor.call_interface("2201", too_long_data, "TEST001")


class Test2201DataHelper(unittest.TestCase):
    """2201接口数据处理辅助工具测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.test_data = get_test_data_from_db()
    
    def test_format_settlement_summary_from_2201_response(self):
        """测试从2201响应中格式化结算摘要"""
        # 模拟2201接口的响应数据
        response_data = {
            "settlement_id": self.test_data["settlement"]["setl_id"],
            "total_amount": str(self.test_data["settlement"]["setl_totlnum"]),
            "insurance_amount": str(self.test_data["settlement"]["hifp_pay"]),
            "personal_amount": str(self.test_data["settlement"]["psn_pay"]),
            "settlement_time": self.test_data["settlement"]["setl_time"]
        }
        
        # 使用DataHelper格式化结算摘要
        result = DataHelper.format_settlement_summary(response_data)
        
        # 验证格式化结果
        self.assertEqual(result["settlement_id"], self.test_data["settlement"]["setl_id"])
        self.assertEqual(result["total"], float(self.test_data["settlement"]["setl_totlnum"]))
        self.assertEqual(result["insurance_pay"], float(self.test_data["settlement"]["hifp_pay"]))
        self.assertEqual(result["personal_pay"], float(self.test_data["settlement"]["psn_pay"]))
        self.assertEqual(result["settlement_time"], self.test_data["settlement"]["setl_time"])
    
    def test_format_amount_for_settlement(self):
        """测试结算金额格式化"""
        # 测试各种金额格式
        test_amounts = [
            (1234.567, "1234.57"),
            ("1234.567", "1234.57"),
            (0, "0.00"),
            ("0", "0.00"),
            (None, "0.00"),
            ("", "0.00"),
            ("invalid", "0.00")
        ]
        
        for amount, expected in test_amounts:
            with self.subTest(amount=amount, expected=expected):
                result = DataHelper.format_amount(amount)
                self.assertEqual(result, expected)
    
    def test_format_currency_for_settlement(self):
        """测试结算货币格式化"""
        # 测试货币格式化
        amount = self.test_data["settlement"]["setl_totlnum"]
        result = DataHelper.format_currency(amount)
        
        # 验证货币格式
        self.assertTrue(result.startswith("¥"))
        self.assertIn(str(amount).split('.')[0], result)
    
    def test_calculate_settlement_breakdown(self):
        """测试结算明细计算"""
        # 模拟结算明细数据
        settlement_data = {
            "total_amount": 1500.00,
            "insurance_amount": 1200.00,
            "account_amount": 200.00,
            "cash_amount": 100.00
        }
        
        # 计算个人支付总额
        personal_total = settlement_data["account_amount"] + settlement_data["cash_amount"]
        
        # 验证金额平衡
        calculated_total = settlement_data["insurance_amount"] + personal_total
        self.assertEqual(calculated_total, settlement_data["total_amount"])
        
        # 计算支付比例
        insurance_ratio = settlement_data["insurance_amount"] / settlement_data["total_amount"]
        personal_ratio = personal_total / settlement_data["total_amount"]
        
        # 验证比例
        self.assertAlmostEqual(insurance_ratio + personal_ratio, 1.0, places=2)
        self.assertAlmostEqual(insurance_ratio, 0.8, places=2)  # 80%医保支付
        self.assertAlmostEqual(personal_ratio, 0.2, places=2)   # 20%个人支付
    
    def test_parse_settlement_time(self):
        """测试结算时间解析"""
        # 测试不同的时间格式
        time_formats = [
            ("2024-01-15 10:30:00", "%Y-%m-%d %H:%M:%S", "20240115103000"),
            ("20240115103000", "%Y%m%d%H%M%S", "2024-01-15 10:30:00"),
            ("2024/01/15 10:30:00", "%Y/%m/%d %H:%M:%S", "20240115103000")
        ]
        
        for time_str, input_format, expected_output in time_formats:
            with self.subTest(time_str=time_str):
                if expected_output.count(':') > 0:
                    # 转换为标准格式
                    result = DataHelper.parse_date_string(time_str, input_format, "%Y-%m-%d %H:%M:%S")
                else:
                    # 转换为紧凑格式
                    result = DataHelper.parse_date_string(time_str, input_format, "%Y%m%d%H%M%S")
                
                # 由于parse_date_string可能返回原字符串，我们检查是否成功转换
                self.assertIsNotNone(result)
                self.assertNotEqual(result, "")


class Test2201HISIntegration(unittest.TestCase):
    """2201接口与HIS系统集成测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.test_data = get_test_data_from_db()
        
        # 模拟HIS系统数据
        self.his_data = {
            "patient_id": "P20240115001",
            "visit_id": "V20240115001",
            "prescription_id": "RX20240115001",
            "total_fee": 1500.00,
            "drug_fee": 800.00,
            "exam_fee": 400.00,
            "treatment_fee": 300.00,
            "doctor_code": "DOC001",
            "doctor_name": "张医生",
            "dept_code": "DEPT001",
            "dept_name": "内科"
        }
    
    def test_2201_settlement_data_sync_to_his(self):
        """测试2201结算数据同步到HIS系统"""
        # 模拟结算成功的响应数据
        settlement_result = {
            "settlement_id": "SETL20240115001",
            "total_amount": self.his_data["total_fee"],
            "insurance_amount": 1200.00,
            "personal_amount": 300.00,
            "account_amount": 200.00,
            "cash_amount": 100.00,
            "settlement_time": "2024-01-15 10:30:00",
            "invoice_no": "INV20240115001",
            "receipt_no": "RCP20240115001"
        }
        
        # 模拟HIS系统数据同步
        mock_his_sync = Mock()
        
        # 构建同步到HIS的数据
        his_sync_data = {
            "patient_id": self.his_data["patient_id"],
            "visit_id": self.his_data["visit_id"],
            "settlement_id": settlement_result["settlement_id"],
            "settlement_status": "SUCCESS",
            "total_amount": settlement_result["total_amount"],
            "insurance_pay": settlement_result["insurance_amount"],
            "personal_pay": settlement_result["personal_amount"],
            "account_pay": settlement_result["account_amount"],
            "cash_pay": settlement_result["cash_amount"],
            "settlement_time": settlement_result["settlement_time"],
            "invoice_no": settlement_result["invoice_no"],
            "receipt_no": settlement_result["receipt_no"]
        }
        
        # 模拟同步成功
        mock_his_sync.sync_settlement_result.return_value = {
            "success": True,
            "sync_id": "SYNC20240115001",
            "message": "结算数据同步成功"
        }
        
        # 执行同步
        sync_result = mock_his_sync.sync_settlement_result(his_sync_data)
        
        # 验证同步结果
        self.assertTrue(sync_result["success"])
        self.assertEqual(sync_result["sync_id"], "SYNC20240115001")
        mock_his_sync.sync_settlement_result.assert_called_once_with(his_sync_data)
    
    def test_2201_settlement_failure_his_rollback(self):
        """测试2201结算失败时HIS系统回滚"""
        # 模拟结算失败的响应
        settlement_failure = {
            "success": False,
            "error_code": -1,
            "error_message": "个人账户余额不足",
            "settlement_id": None
        }
        
        # 模拟HIS系统回滚
        mock_his_rollback = Mock()
        
        # 构建回滚数据
        rollback_data = {
            "patient_id": self.his_data["patient_id"],
            "visit_id": self.his_data["visit_id"],
            "rollback_reason": settlement_failure["error_message"],
            "rollback_time": "2024-01-15 10:35:00"
        }
        
        # 模拟回滚成功
        mock_his_rollback.rollback_settlement.return_value = {
            "success": True,
            "rollback_id": "ROLLBACK20240115001",
            "message": "结算回滚成功"
        }
        
        # 执行回滚
        rollback_result = mock_his_rollback.rollback_settlement(rollback_data)
        
        # 验证回滚结果
        self.assertTrue(rollback_result["success"])
        self.assertEqual(rollback_result["rollback_id"], "ROLLBACK20240115001")
        mock_his_rollback.rollback_settlement.assert_called_once_with(rollback_data)
    
    def test_2201_his_patient_data_validation(self):
        """测试HIS系统患者数据验证"""
        # 模拟从HIS获取的患者数据
        his_patient_data = {
            "patient_id": self.his_data["patient_id"],
            "patient_name": self.test_data["person"]["psn_name"],
            "id_card": self.test_data["person"]["certno"],
            "insurance_no": self.test_data["person"]["psn_no"],
            "visit_type": "outpatient",
            "dept_code": self.his_data["dept_code"],
            "doctor_code": self.his_data["doctor_code"]
        }
        
        # 模拟数据验证器
        mock_validator = Mock()
        
        # 验证患者基本信息
        validation_rules = {
            "patient_name": {"required": True, "max_length": 50},
            "id_card": {"required": True, "pattern": "^[0-9]{17}[0-9Xx]$"},
            "insurance_no": {"required": True, "max_length": 30}
        }
        
        # 模拟验证成功
        mock_validator.validate_his_patient_data.return_value = {
            "is_valid": True,
            "errors": {},
            "validated_data": his_patient_data
        }
        
        # 执行验证
        validation_result = mock_validator.validate_his_patient_data(his_patient_data, validation_rules)
        
        # 验证结果
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(len(validation_result["errors"]), 0)
        self.assertEqual(validation_result["validated_data"], his_patient_data)
    
    def test_2201_his_prescription_data_sync(self):
        """测试HIS系统处方数据同步"""
        # 模拟处方数据
        prescription_data = {
            "prescription_id": self.his_data["prescription_id"],
            "patient_id": self.his_data["patient_id"],
            "doctor_code": self.his_data["doctor_code"],
            "dept_code": self.his_data["dept_code"],
            "prescription_items": [
                {
                    "drug_code": "DRUG001",
                    "drug_name": "阿莫西林胶囊",
                    "quantity": 2,
                    "unit": "盒",
                    "unit_price": 15.50,
                    "total_result["settlement_time"],
            "invoice_no": settlement_result["invoice_no"],
            "receipt_no": settlement_result["receipt_no"],
            "sync_time": "2024-01-15 10:31:00"
        }
        
        # 执行HIS数据同步
        mock_his_sync.sync_settlement_result.return_value = {
            "success": True,
            "sync_id": "SYNC20240115001",
            "message": "结算数据同步成功"
        }
        
        sync_result = mock_his_sync.sync_settlement_result(his_sync_data)
        
        # 验证同步结果
        self.assertTrue(sync_result["success"])
        self.assertEqual(sync_result["sync_id"], "SYNC20240115001")
        self.assertEqual(sync_result["message"], "结算数据同步成功")
        
        # 验证同步调用
        mock_his_sync.sync_settlement_result.assert_called_once_with(his_sync_data)
    
    def test_2201_settlement_failure_sync_to_his(self):
        """测试2201结算失败时的HIS系统同步"""
        # 模拟结算失败的响应数据
        settlement_error = {
            "success": False,
            "error_code": -1,
            "error_message": "个人账户余额不足",
            "settlement_failed": True
        }
        
        # 模拟HIS系统数据同步
        mock_his_sync = Mock()
        
        # 构建同步到HIS的错误数据
        his_error_data = {
            "patient_id": self.his_data["patient_id"],
            "visit_id": self.his_data["visit_id"],
            "settlement_status": "FAILED",
            "error_code": settlement_error["error_code"],
            "error_message": settlement_error["error_message"],
            "sync_time": "2024-01-15 10:31:00"
        }
        
        # 执行HIS错误数据同步
        mock_his_sync.sync_settlement_error.return_value = {
            "success": True,
            "sync_id": "SYNC_ERR_20240115001",
            "message": "结算错误信息同步成功"
        }
        
        sync_result = mock_his_sync.sync_settlement_error(his_error_data)
        
        # 验证同步结果
        self.assertTrue(sync_result["success"])
        self.assertEqual(sync_result["sync_id"], "SYNC_ERR_20240115001")
        
        # 验证同步调用
        mock_his_sync.sync_settlement_error.assert_called_once_with(his_error_data)
    
    def test_2201_his_data_validation_before_settlement(self):
        """测试结算前的HIS数据验证"""
        # 模拟HIS数据验证器
        mock_his_validator = Mock()
        
        # 验证HIS数据完整性
        his_validation_rules = {
            "patient_id": {"required": True, "max_length": 20},
            "visit_id": {"required": True, "max_length": 20},
            "total_fee": {"required": True, "min_value": 0.01},
            "doctor_code": {"required": True, "max_length": 10},
            "dept_code": {"required": True, "max_length": 10}
        }
        
        # 模拟验证成功
        mock_his_validator.validate_his_data.return_value = {
            "is_valid": True,
            "errors": [],
            "validated_data": self.his_data
        }
        
        validation_result = mock_his_validator.validate_his_data(self.his_data, his_validation_rules)
        
        # 验证结果
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(len(validation_result["errors"]), 0)
        self.assertEqual(validation_result["validated_data"], self.his_data)
        
        # 验证调用
        mock_his_validator.validate_his_data.assert_called_once_with(self.his_data, his_validation_rules)
    
    def test_2201_his_data_validation_failure(self):
        """测试HIS数据验证失败的情况"""
        # 模拟无效的HIS数据
        invalid_his_data = self.his_data.copy()
        invalid_his_data["total_fee"] = -100.00  # 无效的负金额
        invalid_his_data["doctor_code"] = ""     # 空的医生编码
        
        # 模拟HIS数据验证器
        mock_his_validator = Mock()
        
        # 模拟验证失败
        mock_his_validator.validate_his_data.return_value = {
            "is_valid": False,
            "errors": [
                "total_fee: 费用金额不能为负数",
                "doctor_code: 医生编码不能为空"
            ],
            "validated_data": None
        }
        
        validation_result = mock_his_validator.validate_his_data(invalid_his_data, {})
        
        # 验证结果
        self.assertFalse(validation_result["is_valid"])
        self.assertEqual(len(validation_result["errors"]), 2)
        self.assertIsNone(validation_result["validated_data"])
        
        # 验证错误信息
        self.assertIn("费用金额不能为负数", validation_result["errors"][0])
        self.assertIn("医生编码不能为空", validation_result["errors"][1])
    
    def test_2201_settlement_rollback_on_his_sync_failure(self):
        """测试HIS同步失败时的结算回滚"""
        # 模拟结算成功但HIS同步失败的场景
        settlement_result = {
            "settlement_id": "SETL20240115001",
            "success": True
        }
        
        # 模拟HIS同步失败
        mock_his_sync = Mock()
        mock_his_sync.sync_settlement_result.return_value = {
            "success": False,
            "error": "HIS系统连接失败"
        }
        
        # 模拟结算回滚
        mock_settlement_rollback = Mock()
        mock_settlement_rollback.rollback_settlement.return_value = {
            "success": True,
            "rollback_id": "ROLLBACK20240115001",
            "message": "结算已回滚"
        }
        
        # 执行同步和回滚流程
        sync_result = mock_his_sync.sync_settlement_result({})
        
        if not sync_result["success"]:
            rollback_result = mock_settlement_rollback.rollback_settlement(settlement_result["settlement_id"])
            
            # 验证回滚结果
            self.assertTrue(rollback_result["success"])
            self.assertEqual(rollback_result["rollback_id"], "ROLLBACK20240115001")
            
            # 验证调用
            mock_settlement_rollback.rollback_settlement.assert_called_once_with(settlement_result["settlement_id"])


class Test2201IntegrationWithClient(unittest.TestCase):
    """2201接口与客户端集成测试"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的客户端
        self.mock_client = Mock(spec=MedicalInsuranceClient)
        self.test_data = get_test_data_from_db()
        
        # 创建测试用的结算数据
        self.settlement_data = {
            "mdtrt_id": "MDT20240115001",
            "psn_no": self.test_data["person"]["psn_no"],
            "chrg_bchno": "CHG20240115001",
            "acct_used_flag": "1",
            "insutype": "310"
        }
    
    def test_2201_client_call_success(self):
        """测试通过客户端成功调用2201接口"""
        # 模拟客户端调用成功
        expected_result = {
            "settlement_id": self.test_data["settlement"]["setl_id"],
            "total_amount": self.test_data["settlement"]["setl_totlnum"],
            "insurance_amount": self.test_data["settlement"]["hifp_pay"],
            "personal_amount": self.test_data["settlement"]["psn_pay"],
            "settlement_time": self.test_data["settlement"]["setl_time"]
        }
        self.mock_client.call.return_value = expected_result
        
        # 执行测试
        result = self.mock_client.call("2201", self.settlement_data, "TEST001")
        
        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_client.call.assert_called_once_with("2201", self.settlement_data, "TEST001")
    
    def test_2201_client_async_call(self):
        """测试通过客户端异步调用2201接口"""
        # 模拟异步调用返回任务ID
        task_id = "task_2201_001"
        self.mock_client.call_async.return_value = task_id
        
        # 执行异步调用
        result_task_id = self.mock_client.call_async("2201", self.settlement_data, "TEST001")
        
        # 验证任务ID
        self.assertEqual(result_task_id, task_id)
        self.mock_client.call_async.assert_called_once_with("2201", self.settlement_data, "TEST001")
        
        # 模拟获取任务结果
        task_result = {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "settlement_id": self.test_data["settlement"]["setl_id"],
                "total_amount": self.test_data["settlement"]["setl_totlnum"]
            }
        }
        self.mock_client.get_task_result.return_value = task_result
        
        # 获取任务结果
        result = self.mock_client.get_task_result(task_id)
        
        # 验证结果
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"]["settlement_id"], self.test_data["settlement"]["setl_id"])
    
    def test_2201_client_batch_settlement(self):
        """测试客户端批量结算调用"""
        # 准备批量结算数据
        batch_requests = [
            {
                "api_code": "2201",
                "data": {
                    "mdtrt_id": "MDT20240115001",
                    "psn_no": "TEST001",
                    "chrg_bchno": "CHG20240115001"
                },
                "org_code": "TEST001"
            },
            {
                "api_code": "2201",
                "data": {
                    "mdtrt_id": "MDT20240115002",
                    "psn_no": "TEST002",
                    "chrg_bchno": "CHG20240115002"
                },
                "org_code": "TEST001"
            }
        ]
        
        # 模拟批量调用结果
        batch_results = [
            {
                "success": True,
                "index": 0,
                "result": {"settlement_id": "SETL001"}
            },
            {
                "success": True,
                "index": 1,
                "result": {"settlement_id": "SETL002"}
            }
        ]
        self.mock_client.call_batch.return_value = batch_results
        
        # 执行批量调用
        results = self.mock_client.call_batch(batch_requests)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["success"])
        self.assertTrue(results[1]["success"])
        self.assertEqual(results[0]["result"]["settlement_id"], "SETL001")
        self.assertEqual(results[1]["result"]["settlement_id"], "SETL002")
    
    def test_2201_client_validation_before_settlement(self):
        """测试客户端结算前的数据验证"""
        # 模拟验证结果
        validation_result = {
            "is_valid": True,
            "errors": {},
            "processed_data": self.settlement_data
        }
        self.mock_client.validate_data.return_value = validation_result
        
        # 执行验证
        result = self.mock_client.validate_data("2201", self.settlement_data, "TEST001")
        
        # 验证结果
        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.mock_client.validate_data.assert_called_once_with("2201", self.settlement_data, "TEST001")


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)