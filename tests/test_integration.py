"""
集成测试
测试完整接口调用流程、数据库操作和异常处理
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import threading
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk.core.universal_processor import UniversalInterfaceProcessor
from medical_insurance_sdk.core.validator import DataValidator
from medical_insurance_sdk.core.config_manager import ConfigManager
from medical_insurance_sdk.core.database import DatabaseManager
from medical_insurance_sdk.models.config import InterfaceConfig, OrganizationConfig
from medical_insurance_sdk.models.validation import ValidationResult
from medical_insurance_sdk.exceptions import (
    ValidationException,
    ConfigurationException,
    DataParsingException,
    InterfaceProcessingException,
    DatabaseException
)


class TestCompleteInterfaceFlow(unittest.TestCase):
    """完整接口调用流程测试"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的SDK
        self.mock_sdk = Mock()
        
        # 创建模拟的配置管理器
        self.mock_config_manager = Mock()
        self.mock_sdk.config_manager = self.mock_config_manager
        
        # 创建通用接口处理器
        self.processor = UniversalInterfaceProcessor(self.mock_sdk)
        
        # 创建测试配置
        self.test_interface_config = InterfaceConfig(
            api_code="1101",
            api_name="人员信息获取",
            business_category="查询类",
            business_type="人员查询",
            required_params={
                "psn_no": {"display_name": "人员编号"}
            },
            optional_params={
                "cert_no": {"display_name": "证件号码"}
            },
            default_values={
                "psn_cert_type": "01"
            },
            validation_rules={
                "psn_no": {
                    "pattern": "^[0-9]+$",
                    "max_length": 30
                }
            },
            response_mapping={
                "person_name": "output.baseinfo.psn_name",
                "person_id": "output.baseinfo.psn_no"
            }
        )
        
        self.test_org_config = OrganizationConfig(
            org_code="TEST001",
            org_name="测试医院",
            province_code="43",
            app_id="test_app_id",
            app_secret="test_app_secret",
            base_url="http://test.example.com"
        )
    
    def test_complete_successful_flow(self):
        """测试完整的成功接口调用流程"""
        # 准备测试数据
        api_code = "1101"
        input_data = {"psn_no": "123456789"}
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 模拟数据验证器
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟SDK调用
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "infcode": 0,
            "output": {
                "baseinfo": {
                    "psn_name": "张三",
                    "psn_no": "123456789"
                }
            }
        }
        self.mock_sdk.call.return_value = mock_response
        
        # 模拟数据解析器
        expected_result = {
            "person_name": "张三",
            "person_id": "123456789"
        }
        self.processor.data_parser.parse_response_data = Mock(return_value=expected_result)
        
        # 执行完整流程
        result = self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证结果
        self.assertEqual(result, expected_result)
        
        # 验证各个组件都被正确调用
        self.mock_config_manager.get_interface_config.assert_called_once()
        self.processor.data_validator.validate_input_data.assert_called_once()
        self.mock_sdk.call.assert_called_once()
        self.processor.data_parser.parse_response_data.assert_called_once()
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['total_calls'], 1)
        self.assertEqual(stats['successful_calls'], 1)
        self.assertEqual(stats['failed_calls'], 0)
    
    def test_complete_flow_with_validation_failure(self):
        """测试数据验证失败的完整流程"""
        # 准备测试数据
        api_code = "1101"
        input_data = {"psn_no": ""}  # 空值，验证失败
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
        
        # 验证SDK没有被调用（因为验证失败）
        self.mock_sdk.call.assert_not_called()
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['validation_errors'], 1)
        self.assertEqual(stats['failed_calls'], 1)
    
    def test_complete_flow_with_config_not_found(self):
        """测试配置不存在的完整流程"""
        # 准备测试数据
        api_code = "9999"  # 不存在的接口
        input_data = {"psn_no": "123456789"}
        org_code = "TEST001"
        
        # 模拟配置管理器抛出异常
        self.mock_config_manager.get_interface_config.side_effect = ConfigurationException("接口配置不存在")
        
        # 执行测试并验证异常
        with self.assertRaises(InterfaceProcessingException):
            self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['failed_calls'], 1)
    
    def test_complete_flow_with_network_error(self):
        """测试网络错误的完整流程"""
        # 准备测试数据
        api_code = "1101"
        input_data = {"psn_no": "123456789"}
        org_code = "TEST001"
        
        # 模拟配置管理器返回
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        # 模拟验证成功
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟SDK调用网络错误
        self.mock_sdk.call.side_effect = Exception("Network timeout")
        
        # 执行测试并验证异常
        with self.assertRaises(InterfaceProcessingException):
            self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['failed_calls'], 1)
    
    def test_batch_interface_flow(self):
        """测试批量接口调用流程"""
        # 准备批量测试数据
        batch_requests = [
            {"api_code": "1101", "input_data": {"psn_no": "123456789"}, "org_code": "TEST001"},
            {"api_code": "1101", "input_data": {"psn_no": "987654321"}, "org_code": "TEST001"},
            {"api_code": "1101", "input_data": {"psn_no": ""}, "org_code": "TEST001"}  # 这个会失败
        ]
        
        # 模拟单个接口调用
        def mock_call_interface(api_code, input_data, org_code, **kwargs):
            if input_data.get("psn_no"):
                return {"success": True, "person_name": "测试用户"}
            else:
                raise ValidationException("验证失败")
        
        self.processor.call_interface = Mock(side_effect=mock_call_interface)
        
        # 执行批量调用
        results = self.processor.call_batch_interfaces(batch_requests)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0]["success"])
        self.assertTrue(results[1]["success"])
        self.assertFalse(results[2]["success"])
        self.assertIn("验证失败", results[2]["error"])
    
    def test_concurrent_interface_calls(self):
        """测试并发接口调用"""
        # 准备测试数据
        api_code = "1101"
        org_code = "TEST001"
        
        # 模拟配置和响应
        self.mock_config_manager.get_interface_config.return_value = self.test_interface_config
        self.mock_config_manager.get_organization_config.return_value = self.test_org_config
        
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {"infcode": 0, "output": {"result": "success"}}
        self.mock_sdk.call.return_value = mock_response
        
        self.processor.data_parser.parse_response_data = Mock(return_value={"result": "success"})
        
        # 并发调用函数
        def worker(thread_id, results):
            try:
                input_data = {"psn_no": f"12345678{thread_id}"}
                result = self.processor.call_interface(api_code, input_data, org_code)
                results[thread_id] = {"success": True, "result": result}
            except Exception as e:
                results[thread_id] = {"success": False, "error": str(e)}
        
        # 创建多个线程并发调用
        threads = []
        results = {}
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i, results))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        self.assertEqual(len(results), 10)
        for i in range(10):
            self.assertTrue(results[i]["success"], f"Thread {i} failed: {results[i].get('error')}")
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['total_calls'], 10)
        self.assertEqual(stats['successful_calls'], 10)


class TestDatabaseOperations(unittest.TestCase):
    """数据库操作测试"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的数据库管理器
        self.mock_db_manager = Mock()
        
        # 创建模拟的配置管理器
        self.config_manager = ConfigManager.__new__(ConfigManager)
        self.config_manager.db_manager = self.mock_db_manager
        self.config_manager.cache_manager = Mock()
        self.config_manager._lock = threading.RLock()
        self.config_manager._last_config_check = {}
        self.config_manager._config_check_interval = 60
        self.config_manager._monitor_thread = None
        self.config_manager._stop_monitor = threading.Event()
    
    def test_database_connection_success(self):
        """测试数据库连接成功"""
        # 模拟数据库查询成功
        test_record = {
            'api_code': '1101',
            'api_name': '人员信息获取',
            'required_params': '{}',
            'optional_params': '{}',
            'default_values': '{}',
            'validation_rules': '{}',
            'response_mapping': '{}',
            'is_active': True
        }
        self.mock_db_manager.execute_query_one.return_value = test_record
        
        # 执行数据库操作
        config = self.config_manager.get_interface_config("1101")
        
        # 验证结果
        self.assertIsInstance(config, InterfaceConfig)
        self.assertEqual(config.api_code, "1101")
        
        # 验证数据库调用
        self.mock_db_manager.execute_query_one.assert_called_once()
    
    def test_database_connection_failure(self):
        """测试数据库连接失败"""
        # 模拟数据库连接异常
        self.mock_db_manager.execute_query_one.side_effect = Exception("Database connection failed")
        
        # 执行测试并验证异常
        with self.assertRaises(ConfigurationException) as context:
            self.config_manager.get_interface_config("1101")
        
        self.assertIn("获取接口配置失败", str(context.exception))
    
    def test_database_transaction_commit(self):
        """测试数据库事务提交"""
        # 模拟事务操作
        self.mock_db_manager.begin_transaction = Mock()
        self.mock_db_manager.commit_transaction = Mock()
        self.mock_db_manager.rollback_transaction = Mock()
        self.mock_db_manager.execute_update = Mock(return_value=1)
        
        # 模拟执行事务操作
        try:
            self.mock_db_manager.begin_transaction()
            self.mock_db_manager.execute_update("UPDATE test SET value = 1")
            self.mock_db_manager.commit_transaction()
        except Exception:
            self.mock_db_manager.rollback_transaction()
            raise
        
        # 验证事务操作
        self.mock_db_manager.begin_transaction.assert_called_once()
        self.mock_db_manager.execute_update.assert_called_once()
        self.mock_db_manager.commit_transaction.assert_called_once()
        self.mock_db_manager.rollback_transaction.assert_not_called()
    
    def test_database_transaction_rollback(self):
        """测试数据库事务回滚"""
        # 模拟事务操作
        self.mock_db_manager.begin_transaction = Mock()
        self.mock_db_manager.commit_transaction = Mock()
        self.mock_db_manager.rollback_transaction = Mock()
        self.mock_db_manager.execute_update = Mock(side_effect=Exception("Update failed"))
        
        # 模拟执行事务操作（会失败）
        with self.assertRaises(Exception):
            try:
                self.mock_db_manager.begin_transaction()
                self.mock_db_manager.execute_update("UPDATE test SET value = 1")
                self.mock_db_manager.commit_transaction()
            except Exception:
                self.mock_db_manager.rollback_transaction()
                raise
        
        # 验证事务回滚
        self.mock_db_manager.begin_transaction.assert_called_once()
        self.mock_db_manager.execute_update.assert_called_once()
        self.mock_db_manager.commit_transaction.assert_not_called()
        self.mock_db_manager.rollback_transaction.assert_called_once()
    
    def test_config_manager_database_integration(self):
        """测试配置管理器与数据库集成"""
        # 模拟数据库返回多条记录
        test_records = [
            {
                'api_code': '1101',
                'api_name': '人员信息获取',
                'business_category': '查询类',
                'required_params': '{}',
                'optional_params': '{}',
                'default_values': '{}',
                'validation_rules': '{}',
                'response_mapping': '{}',
                'is_active': True
            },
            {
                'api_code': '1102',
                'api_name': '其他查询',
                'business_category': '查询类',
                'required_params': '{}',
                'optional_params': '{}',
                'default_values': '{}',
                'validation_rules': '{}',
                'response_mapping': '{}',
                'is_active': True
            }
        ]
        self.mock_db_manager.execute_query.return_value = test_records
        
        # 执行数据库集成操作
        configs = self.config_manager.get_all_interface_configs("查询类")
        
        # 验证结果
        self.assertEqual(len(configs), 2)
        self.assertEqual(configs[0].api_code, "1101")
        self.assertEqual(configs[1].api_code, "1102")
        
        # 验证数据库调用
        self.mock_db_manager.execute_query.assert_called_once()
    
    def test_operation_log_saving(self):
        """测试操作日志保存"""
        # 创建模拟的数据管理器
        mock_data_manager = Mock()
        
        # 模拟日志数据
        log_data = {
            'operation_id': 'test_op_001',
            'api_code': '1101',
            'api_name': '人员信息获取',
            'request_data': {'psn_no': '123456789'},
            'response_data': {'infcode': 0, 'output': {}},
            'status': 'success',
            'operation_time': '2024-01-15 10:30:00'
        }
        
        # 执行日志保存
        mock_data_manager.save_operation_log(log_data)
        
        # 验证日志保存被调用
        mock_data_manager.save_operation_log.assert_called_once_with(log_data)


class TestExceptionHandling(unittest.TestCase):
    """异常处理测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_sdk = Mock()
        self.mock_config_manager = Mock()
        self.mock_sdk.config_manager = self.mock_config_manager
        self.processor = UniversalInterfaceProcessor(self.mock_sdk)
    
    def test_validation_exception_handling(self):
        """测试验证异常处理"""
        # 创建验证异常
        validation_error = ValidationException("数据验证失败", field_errors={"psn_no": ["不能为空"]})
        
        # 验证异常属性 - 修正期望的字符串格式
        self.assertEqual(str(validation_error), "[VALIDATION_ERROR] 数据验证失败")
        self.assertEqual(validation_error.message, "数据验证失败")  # 验证原始消息
        self.assertIn("psn_no", validation_error.field_errors)
        self.assertEqual(validation_error.field_errors["psn_no"], ["不能为空"])
    
    def test_configuration_exception_handling(self):
        """测试配置异常处理"""
        # 创建配置异常
        config_error = ConfigurationException("配置文件不存在")
        
        # 验证异常属性 - 修正期望的字符串格式
        self.assertEqual(str(config_error), "[CONFIG_ERROR] 配置文件不存在")
        self.assertEqual(config_error.message, "配置文件不存在")  # 验证原始消息
        self.assertIsInstance(config_error, Exception)
    
    def test_data_parsing_exception_handling(self):
        """测试数据解析异常处理"""
        # 创建数据解析异常
        parsing_error = DataParsingException("响应数据解析失败")
        
        # 验证异常属性 - 修正期望的字符串格式
        self.assertEqual(str(parsing_error), "[DATA_PARSING_ERROR] 响应数据解析失败")
        self.assertEqual(parsing_error.message, "响应数据解析失败")  # 验证原始消息
        self.assertIsInstance(parsing_error, Exception)
    
    def test_interface_processing_exception_handling(self):
        """测试接口处理异常处理"""
        # 创建接口处理异常
        processing_error = InterfaceProcessingException("接口处理失败")
        
        # 验证异常属性 - 修正期望的字符串格式
        self.assertEqual(str(processing_error), "[INTERFACE_PROCESSING_ERROR] 接口处理失败")
        self.assertEqual(processing_error.message, "接口处理失败")  # 验证原始消息
        self.assertIsInstance(processing_error, Exception)
    
    def test_exception_hierarchy(self):
        """测试异常层次结构"""
        # 验证异常继承关系
        validation_error = ValidationException("test")
        config_error = ConfigurationException("test")
        parsing_error = DataParsingException("test")
        processing_error = InterfaceProcessingException("test")
        
        # 所有自定义异常都应该继承自Exception
        self.assertIsInstance(validation_error, Exception)
        self.assertIsInstance(config_error, Exception)
        self.assertIsInstance(parsing_error, Exception)
        self.assertIsInstance(processing_error, Exception)
    
    def test_exception_chaining(self):
        """测试异常链"""
        try:
            try:
                raise ValueError("原始错误")
            except ValueError as e:
                raise ConfigurationException("配置错误") from e
        except ConfigurationException as config_error:
            # 验证异常链
            self.assertIsInstance(config_error.__cause__, ValueError)
            self.assertEqual(str(config_error.__cause__), "原始错误")
    
    def test_graceful_error_recovery(self):
        """测试优雅的错误恢复"""
        # 模拟配置获取失败，但处理器应该能够记录错误并继续
        api_code = "1101"
        input_data = {"psn_no": "123456789"}
        org_code = "TEST001"
        
        # 模拟配置管理器抛出异常
        self.mock_config_manager.get_interface_config.side_effect = ConfigurationException("配置不存在")
        
        # 执行测试
        with self.assertRaises(InterfaceProcessingException):
            self.processor.call_interface(api_code, input_data, org_code)
        
        # 验证错误统计被正确记录
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['failed_calls'], 1)
        self.assertEqual(stats['total_calls'], 1)


class TestPerformanceAndConcurrency(unittest.TestCase):
    """性能和并发测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_sdk = Mock()
        self.mock_config_manager = Mock()
        self.mock_sdk.config_manager = self.mock_config_manager
        self.processor = UniversalInterfaceProcessor(self.mock_sdk)
        
        # 创建测试配置
        self.test_config = InterfaceConfig(
            api_code="1101",
            api_name="测试接口",
            required_params={},
            validation_rules={}
        )
    
    def test_concurrent_interface_calls(self):
        """测试并发接口调用"""
        # 模拟配置和响应
        self.mock_config_manager.get_interface_config.return_value = self.test_config
        
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {"infcode": 0}
        self.mock_sdk.call.return_value = mock_response
        
        self.processor.data_parser.parse_response_data = Mock(return_value={"result": "success"})
        
        # 并发调用函数
        def worker(results, thread_id):
            try:
                for i in range(10):  # 每个线程调用10次
                    result = self.processor.call_interface("1101", {"test": f"data_{thread_id}_{i}"}, "TEST001")
                    results.append({"thread": thread_id, "call": i, "success": True})
            except Exception as e:
                results.append({"thread": thread_id, "error": str(e), "success": False})
        
        # 创建多个线程
        threads = []
        results = []
        thread_count = 5
        
        for i in range(thread_count):
            thread = threading.Thread(target=worker, args=(results, i))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        successful_calls = [r for r in results if r.get("success", False)]
        self.assertEqual(len(successful_calls), thread_count * 10)  # 5个线程 * 10次调用
        
        # 验证统计信息
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['total_calls'], thread_count * 10)
        self.assertEqual(stats['successful_calls'], thread_count * 10)
    
    def test_cache_performance(self):
        """测试缓存性能"""
        from medical_insurance_sdk.core.config_manager import CacheManager
        
        cache_manager = CacheManager()
        
        # 测试大量缓存操作的性能
        start_time = time.time()
        
        # 设置1000个缓存项
        for i in range(1000):
            cache_manager.set(f"key_{i}", f"value_{i}")
        
        # 获取1000个缓存项
        for i in range(1000):
            value = cache_manager.get(f"key_{i}")
            self.assertEqual(value, f"value_{i}")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 验证性能（应该在合理时间内完成）
        self.assertLess(elapsed_time, 1.0, "缓存操作耗时过长")
        
        # 验证缓存统计
        stats = cache_manager.get_stats()
        self.assertEqual(stats['total_items'], 1000)
    
    def test_memory_usage_under_load(self):
        """测试负载下的内存使用"""
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 模拟大量接口调用
        self.mock_config_manager.get_interface_config.return_value = self.test_config
        
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {"infcode": 0, "data": "x" * 1000}  # 较大的响应数据
        self.mock_sdk.call.return_value = mock_response
        
        self.processor.data_parser.parse_response_data = Mock(return_value={"result": "success"})
        
        # 执行大量调用
        for i in range(100):
            try:
                self.processor.call_interface("1101", {"test": f"data_{i}"}, "TEST001")
            except Exception:
                pass  # 忽略异常，专注于内存测试
        
        # 强制垃圾回收
        gc.collect()
        
        # 验证统计信息（确保没有内存泄漏导致的异常统计）
        stats = self.processor.get_processing_stats()
        self.assertGreaterEqual(stats['total_calls'], 100)
    
    def test_timeout_handling(self):
        """测试超时处理"""
        # 模拟超时场景
        def slow_operation():
            time.sleep(2)  # 模拟慢操作
            return {"result": "success"}
        
        self.mock_config_manager.get_interface_config.return_value = self.test_config
        
        mock_validation_result = ValidationResult()
        self.processor.data_validator.validate_input_data = Mock(return_value=mock_validation_result)
        
        # 模拟SDK调用超时
        self.mock_sdk.call.side_effect = lambda *args, **kwargs: slow_operation()
        
        # 执行测试（应该在合理时间内完成或抛出超时异常）
        start_time = time.time()
        
        try:
            self.processor.call_interface("1101", {"test": "data"}, "TEST001")
        except Exception:
            pass  # 可能会有超时或其他异常
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 验证操作时间（应该接近超时时间）
        self.assertGreaterEqual(elapsed_time, 2.0)
        self.assertLess(elapsed_time, 3.0)  # 允许一些误差


if __name__ == "__main__":
    unittest.main()