"""
ConfigManager 单元测试
测试配置管理器的核心功能
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

from medical_insurance_sdk.core.config_manager import ConfigManager, CacheManager
from medical_insurance_sdk.core.database import DatabaseConfig
from medical_insurance_sdk.models.config import InterfaceConfig, OrganizationConfig
from medical_insurance_sdk.exceptions import ConfigurationException


class TestCacheManager(unittest.TestCase):
    """CacheManager 测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.cache_manager = CacheManager(default_ttl=60)  # 60秒过期
    
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        key = "test_key"
        value = {"data": "test_value"}
        
        # 设置缓存
        self.cache_manager.set(key, value)
        
        # 获取缓存
        cached_value = self.cache_manager.get(key)
        
        # 验证结果
        self.assertEqual(cached_value, value)
    
    def test_cache_expiration(self):
        """测试缓存过期机制"""
        key = "expire_test"
        value = "test_value"
        
        # 设置短期缓存（1秒）
        self.cache_manager.set(key, value, ttl=1)
        
        # 立即获取应该成功
        cached_value = self.cache_manager.get(key)
        self.assertEqual(cached_value, value)
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后获取应该返回None
        cached_value = self.cache_manager.get(key)
        self.assertIsNone(cached_value)
    
    def test_delete(self):
        """测试删除缓存"""
        key = "delete_test"
        value = "test_value"
        
        # 设置缓存
        self.cache_manager.set(key, value)
        self.assertIsNotNone(self.cache_manager.get(key))
        
        # 删除缓存
        result = self.cache_manager.delete(key)
        self.assertTrue(result)
        
        # 验证已删除
        self.assertIsNone(self.cache_manager.get(key))
        
        # 删除不存在的键
        result = self.cache_manager.delete("non_existent")
        self.assertFalse(result)
    
    def test_clear(self):
        """测试清空缓存"""
        # 设置多个缓存项
        self.cache_manager.set("key1", "value1")
        self.cache_manager.set("key2", "value2")
        self.cache_manager.set("key3", "value3")
        
        # 验证缓存存在
        self.assertIsNotNone(self.cache_manager.get("key1"))
        self.assertIsNotNone(self.cache_manager.get("key2"))
        self.assertIsNotNone(self.cache_manager.get("key3"))
        
        # 清空缓存
        self.cache_manager.clear()
        
        # 验证缓存已清空
        self.assertIsNone(self.cache_manager.get("key1"))
        self.assertIsNone(self.cache_manager.get("key2"))
        self.assertIsNone(self.cache_manager.get("key3"))
    
    def test_cleanup_expired(self):
        """测试清理过期缓存"""
        # 设置一些缓存项，部分设置短期过期
        self.cache_manager.set("key1", "value1", ttl=60)  # 长期
        self.cache_manager.set("key2", "value2", ttl=1)   # 短期
        self.cache_manager.set("key3", "value3", ttl=1)   # 短期
        
        # 等待短期缓存过期
        time.sleep(1.1)
        
        # 清理过期缓存
        cleaned_count = self.cache_manager.cleanup_expired()
        
        # 验证清理结果
        self.assertEqual(cleaned_count, 2)  # 清理了2个过期项
        self.assertIsNotNone(self.cache_manager.get("key1"))  # 长期缓存仍存在
        self.assertIsNone(self.cache_manager.get("key2"))     # 短期缓存已清理
        self.assertIsNone(self.cache_manager.get("key3"))     # 短期缓存已清理
    
    def test_get_stats(self):
        """测试获取缓存统计"""
        # 设置一些缓存项
        self.cache_manager.set("key1", "value1", ttl=60)
        self.cache_manager.set("key2", "value2", ttl=1)
        
        # 等待部分过期
        time.sleep(1.1)
        
        # 获取统计信息
        stats = self.cache_manager.get_stats()
        
        # 验证统计信息
        self.assertEqual(stats["total_items"], 2)
        self.assertEqual(stats["active_items"], 1)
        self.assertEqual(stats["expired_items"], 1)
        self.assertEqual(stats["default_ttl"], 60)
    
    def test_thread_safety(self):
        """测试线程安全性"""
        def worker(thread_id):
            for i in range(100):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                self.cache_manager.set(key, value)
                cached_value = self.cache_manager.get(key)
                self.assertEqual(cached_value, value)
        
        # 创建多个线程并发操作缓存
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证缓存项数量
        stats = self.cache_manager.get_stats()
        self.assertEqual(stats["total_items"], 500)  # 5个线程 * 100个项


class TestConfigManager(unittest.TestCase):
    """ConfigManager 测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建模拟的数据库配置
        self.db_config = DatabaseConfig(
            host="localhost",
            port=3306,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        
        # 创建模拟的数据库管理器
        self.mock_db_manager = Mock()
        
        # 创建配置管理器并替换数据库管理器
        self.config_manager = ConfigManager(self.db_config)
        self.config_manager.db_manager = self.mock_db_manager
        
        # 创建测试用的接口配置数据
        self.test_interface_record = {
            'api_code': '1101',
            'api_name': '人员信息获取',
            'api_description': '通过人员编号获取参保人员基本信息',
            'business_category': '查询类',
            'business_type': '人员查询',
            'required_params': '{"psn_no": {"display_name": "人员编号"}}',
            'optional_params': '{"cert_no": {"display_name": "证件号码"}}',
            'default_values': '{"psn_cert_type": "01"}',
            'request_template': '{}',
            'param_mapping': '{}',
            'validation_rules': '{"psn_no": {"pattern": "^[0-9]+$"}}',
            'response_mapping': '{}',
            'success_condition': 'infcode=0',
            'error_handling': '{}',
            'region_specific': '{}',
            'province_overrides': '{}',
            'is_active': True,
            'requires_auth': True,
            'supports_batch': False,
            'max_retry_times': 3,
            'timeout_seconds': 30,
            'config_version': '1.0',
            'last_updated_by': 'test_user',
            'updated_at': '2024-01-15 10:30:00'
        }
        
        # 创建测试用的机构配置数据
        self.test_org_record = {
            'org_code': 'TEST001',
            'org_name': '测试医院',
            'org_type': 'hospital',
            'province_code': '43',
            'city_code': '4301',
            'region_code': '430100',
            'app_id': 'test_app_id',
            'app_secret': 'test_app_secret',
            'base_url': 'http://test.example.com',
            'crypto_type': 'SM3',
            'sign_type': 'SM2',
            'timeout_config': '{"default": 30}',
            'encryption_config': '{}',
            'extra_config': '{}',
            'gateway_config': '{}',
            'is_active': True,
            'environment': 'test',
            'description': '测试医院配置',
            'contact_person': '张三',
            'contact_phone': '13812345678',
            'updated_at': '2024-01-15 10:30:00'
        }
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self.config_manager, 'close'):
            self.config_manager.close()
    
    def test_get_interface_config_success(self):
        """测试成功获取接口配置"""
        api_code = "1101"
        region = "43"
        
        # 模拟数据库查询返回
        self.mock_db_manager.execute_query_one.return_value = self.test_interface_record
        
        # 执行测试
        config = self.config_manager.get_interface_config(api_code, region)
        
        # 验证结果
        self.assertIsInstance(config, InterfaceConfig)
        self.assertEqual(config.api_code, "1101")
        self.assertEqual(config.api_name, "人员信息获取")
        self.assertEqual(config.business_category, "查询类")
        self.assertIn("psn_no", config.required_params)
        self.assertIn("cert_no", config.optional_params)
        
        # 验证数据库调用
        self.mock_db_manager.execute_query_one.assert_called_once()
    
    def test_get_interface_config_not_found(self):
        """测试接口配置不存在"""
        api_code = "9999"  # 不存在的接口
        
        # 模拟数据库查询返回空
        self.mock_db_manager.execute_query_one.return_value = None
        
        # 执行测试并验证异常
        with self.assertRaises(ConfigurationException) as context:
            self.config_manager.get_interface_config(api_code)
        
        self.assertIn("接口配置不存在", str(context.exception))
    
    def test_get_interface_config_with_cache(self):
        """测试接口配置缓存功能"""
        api_code = "1101"
        
        # 模拟数据库查询返回
        self.mock_db_manager.execute_query_one.return_value = self.test_interface_record
        
        # 第一次获取配置
        config1 = self.config_manager.get_interface_config(api_code)
        
        # 第二次获取配置（应该从缓存获取）
        config2 = self.config_manager.get_interface_config(api_code)
        
        # 验证结果相同
        self.assertEqual(config1.api_code, config2.api_code)
        self.assertEqual(config1.api_name, config2.api_name)
        
        # 验证数据库只被调用一次（第二次从缓存获取）
        self.mock_db_manager.execute_query_one.assert_called_once()
    
    def test_get_organization_config_success(self):
        """测试成功获取机构配置"""
        org_code = "TEST001"
        
        # 模拟数据库查询返回
        self.mock_db_manager.execute_query_one.return_value = self.test_org_record
        
        # 执行测试
        config = self.config_manager.get_organization_config(org_code)
        
        # 验证结果
        self.assertIsInstance(config, OrganizationConfig)
        self.assertEqual(config.org_code, "TEST001")
        self.assertEqual(config.org_name, "测试医院")
        self.assertEqual(config.province_code, "43")
        self.assertEqual(config.app_id, "test_app_id")
        
        # 验证数据库调用
        self.mock_db_manager.execute_query_one.assert_called_once()
    
    def test_get_organization_config_not_found(self):
        """测试机构配置不存在"""
        org_code = "NONEXISTENT"
        
        # 模拟数据库查询返回空
        self.mock_db_manager.execute_query_one.return_value = None
        
        # 执行测试并验证异常
        with self.assertRaises(ConfigurationException) as context:
            self.config_manager.get_organization_config(org_code)
        
        self.assertIn("机构配置不存在", str(context.exception))
    
    def test_get_all_interface_configs(self):
        """测试获取所有接口配置"""
        # 模拟数据库查询返回多条记录
        self.mock_db_manager.execute_query.return_value = [
            self.test_interface_record,
            {**self.test_interface_record, 'api_code': '1102', 'api_name': '其他接口'}
        ]
        
        # 执行测试
        configs = self.config_manager.get_all_interface_configs()
        
        # 验证结果
        self.assertEqual(len(configs), 2)
        self.assertIsInstance(configs[0], InterfaceConfig)
        self.assertIsInstance(configs[1], InterfaceConfig)
        self.assertEqual(configs[0].api_code, "1101")
        self.assertEqual(configs[1].api_code, "1102")
    
    def test_get_all_interface_configs_by_category(self):
        """测试按业务类别获取接口配置"""
        business_category = "查询类"
        
        # 模拟数据库查询返回
        self.mock_db_manager.execute_query.return_value = [self.test_interface_record]
        
        # 执行测试
        configs = self.config_manager.get_all_interface_configs(business_category)
        
        # 验证结果
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].business_category, business_category)
        
        # 验证SQL查询参数
        call_args = self.mock_db_manager.execute_query.call_args
        self.assertIn(business_category, call_args[0])
    
    def test_get_all_organization_configs(self):
        """测试获取所有机构配置"""
        # 模拟数据库查询返回多条记录
        self.mock_db_manager.execute_query.return_value = [
            self.test_org_record,
            {**self.test_org_record, 'org_code': 'TEST002', 'org_name': '测试医院2'}
        ]
        
        # 执行测试
        configs = self.config_manager.get_all_organization_configs()
        
        # 验证结果
        self.assertEqual(len(configs), 2)
        self.assertIsInstance(configs[0], OrganizationConfig)
        self.assertIsInstance(configs[1], OrganizationConfig)
        self.assertEqual(configs[0].org_code, "TEST001")
        self.assertEqual(configs[1].org_code, "TEST002")
    
    def test_get_all_organization_configs_by_province(self):
        """测试按省份获取机构配置"""
        province_code = "43"
        
        # 模拟数据库查询返回
        self.mock_db_manager.execute_query.return_value = [self.test_org_record]
        
        # 执行测试
        configs = self.config_manager.get_all_organization_configs(province_code)
        
        # 验证结果
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].province_code, province_code)
        
        # 验证SQL查询参数
        call_args = self.mock_db_manager.execute_query.call_args
        self.assertIn(province_code, call_args[0])
    
    def test_reload_config_interface(self):
        """测试重新加载接口配置"""
        api_code = "1101"
        
        # 先获取配置（会被缓存）
        self.mock_db_manager.execute_query_one.return_value = self.test_interface_record
        config1 = self.config_manager.get_interface_config(api_code)
        
        # 重新加载特定接口配置
        self.config_manager.reload_config("interface", api_code)
        
        # 再次获取配置（应该重新从数据库加载）
        config2 = self.config_manager.get_interface_config(api_code)
        
        # 验证数据库被调用了两次（缓存被清理）
        self.assertEqual(self.mock_db_manager.execute_query_one.call_count, 2)
    
    def test_reload_config_organization(self):
        """测试重新加载机构配置"""
        org_code = "TEST001"
        
        # 先获取配置（会被缓存）
        self.mock_db_manager.execute_query_one.return_value = self.test_org_record
        config1 = self.config_manager.get_organization_config(org_code)
        
        # 重新加载特定机构配置
        self.config_manager.reload_config("organization", org_code)
        
        # 再次获取配置（应该重新从数据库加载）
        config2 = self.config_manager.get_organization_config(org_code)
        
        # 验证数据库被调用了两次（缓存被清理）
        self.assertEqual(self.mock_db_manager.execute_query_one.call_count, 2)
    
    def test_reload_config_all(self):
        """测试重新加载所有配置"""
        # 先获取一些配置（会被缓存）
        self.mock_db_manager.execute_query_one.return_value = self.test_interface_record
        config1 = self.config_manager.get_interface_config("1101")
        
        self.mock_db_manager.execute_query_one.return_value = self.test_org_record
        config2 = self.config_manager.get_organization_config("TEST001")
        
        # 重新加载所有配置
        self.config_manager.reload_config()
        
        # 再次获取配置（应该重新从数据库加载）
        self.mock_db_manager.execute_query_one.return_value = self.test_interface_record
        config3 = self.config_manager.get_interface_config("1101")
        
        self.mock_db_manager.execute_query_one.return_value = self.test_org_record
        config4 = self.config_manager.get_organization_config("TEST001")
        
        # 验证数据库被调用了4次（所有缓存被清理）
        self.assertEqual(self.mock_db_manager.execute_query_one.call_count, 4)
    
    def test_apply_region_config(self):
        """测试应用地区特殊配置"""
        # 创建带有地区特殊配置的接口配置
        interface_record = {
            **self.test_interface_record,
            'region_specific': '{"43": {"special_params": {"recer_sys_code": "HIS_HN"}, "encryption": "SM4", "timeout": 60}}'
        }
        
        self.mock_db_manager.execute_query_one.return_value = interface_record
        
        # 获取带地区配置的接口配置
        config = self.config_manager.get_interface_config("1101", "43")
        
        # 验证地区特殊配置被应用
        self.assertEqual(config.default_values.get("recer_sys_code"), "HIS_HN")
        self.assertEqual(config.timeout_seconds, 60)
        self.assertIn("encryption_config", config.region_specific)
    
    def test_get_config_stats(self):
        """测试获取配置统计信息"""
        # 模拟数据库统计查询
        self.mock_db_manager.execute_query_one.side_effect = [
            {'total_interfaces': 10, 'active_interfaces': 8, 'categories': 3},  # 接口统计
            {'total_organizations': 5, 'active_organizations': 4, 'provinces': 2}  # 机构统计
        ]
        
        # 执行测试
        stats = self.config_manager.get_config_stats()
        
        # 验证结果
        self.assertIn('interface_config', stats)
        self.assertIn('organization_config', stats)
        self.assertIn('cache', stats)
        self.assertIn('monitor_status', stats)
        
        self.assertEqual(stats['interface_config']['total_interfaces'], 10)
        self.assertEqual(stats['organization_config']['total_organizations'], 5)
        self.assertIn('total_items', stats['cache'])
        self.assertIn('running', stats['monitor_status'])
    
    @patch('threading.Thread')
    def test_config_monitor_startup(self, mock_thread):
        """测试配置监控线程启动"""
        # 创建新的配置管理器（会启动监控线程）
        config_manager = ConfigManager(self.db_config)
        config_manager.db_manager = self.mock_db_manager
        
        # 验证监控线程被创建和启动
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
    
    def test_cache_cleanup_on_expired(self):
        """测试缓存过期清理"""
        # 设置短期缓存
        self.config_manager.cache_manager.set("test_key", "test_value", ttl=1)
        
        # 验证缓存存在
        self.assertIsNotNone(self.config_manager.cache_manager.get("test_key"))
        
        # 等待过期
        time.sleep(1.1)
        
        # 手动触发清理
        cleaned_count = self.config_manager.cache_manager.cleanup_expired()
        
        # 验证过期缓存被清理
        self.assertEqual(cleaned_count, 1)
        self.assertIsNone(self.config_manager.cache_manager.get("test_key"))
    
    def test_database_error_handling(self):
        """测试数据库错误处理"""
        api_code = "1101"
        
        # 模拟数据库异常
        self.mock_db_manager.execute_query_one.side_effect = Exception("Database connection failed")
        
        # 执行测试并验证异常处理
        with self.assertRaises(ConfigurationException) as context:
            self.config_manager.get_interface_config(api_code)
        
        self.assertIn("获取接口配置失败", str(context.exception))
    
    def test_json_parsing_error_handling(self):
        """测试JSON解析错误处理"""
        # 创建包含无效JSON的配置记录
        invalid_record = {
            **self.test_interface_record,
            'required_params': 'invalid json string'  # 无效的JSON
        }
        
        self.mock_db_manager.execute_query_one.return_value = invalid_record
        
        # 执行测试（应该不抛出异常，使用默认值）
        config = self.config_manager.get_interface_config("1101")
        
        # 验证使用了默认值
        self.assertEqual(config.required_params, {})
    
    def test_concurrent_access(self):
        """测试并发访问"""
        def worker(thread_id):
            try:
                self.mock_db_manager.execute_query_one.return_value = self.test_interface_record
                config = self.config_manager.get_interface_config("1101")
                self.assertEqual(config.api_code, "1101")
            except Exception as e:
                self.fail(f"Thread {thread_id} failed: {e}")
        
        # 创建多个线程并发访问配置
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有异常发生（如果有异常，测试会失败）


if __name__ == "__main__":
    unittest.main()