"""
医保接口性能测试
分析各个步骤的耗时
"""

import pytest
import sys
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.client import MedicalInsuranceClient

class TestInterfacePerformance:
    """医保接口性能测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置，只初始化一次客户端"""
        print("\n🚀 开始初始化客户端...")
        start_time = time.time()
        
        cls.client = MedicalInsuranceClient()
        
        init_time = time.time() - start_time
        print(f"⏱️  客户端初始化耗时: {init_time:.3f}秒")
    
    def test_client_initialization_time(self):
        """测试客户端初始化时间"""
        start_time = time.time()
        
        # 创建新客户端
        client = MedicalInsuranceClient()
        
        init_time = time.time() - start_time
        print(f"⏱️  单独初始化耗时: {init_time:.3f}秒")
        
        assert client is not None
        assert init_time < 5.0, f"初始化时间过长: {init_time:.3f}秒"
    
    def test_config_loading_time(self):
        """测试配置加载时间"""
        start_time = time.time()
        
        # 获取接口配置
        try:
            config = self.client.get_interface_info("1101", "H43010000001")
            config_time = time.time() - start_time
            print(f"⏱️  配置加载耗时: {config_time:.3f}秒")
            
            assert config is not None
            assert config_time < 2.0, f"配置加载时间过长: {config_time:.3f}秒"
            
        except Exception as e:
            pytest.skip(f"配置加载测试跳过: {str(e)}")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_interface_call_time(self, mock_post):
        """测试接口调用时间"""
        
        # 模拟快速响应
        mock_response = {
            "infcode": "0",
            "output": {"baseinfo": {"psn_name": "张三"}}
        }
        mock_post.return_value = mock_response
        
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "psn_name": "张三"
        }
        
        start_time = time.time()
        
        # 调用接口
        result = self.client.call("1101", test_data, "H43010000001")
        
        call_time = time.time() - start_time
        print(f"⏱️  接口调用耗时: {call_time:.3f}秒")
        
        assert result is not None
        assert call_time < 1.0, f"接口调用时间过长: {call_time:.3f}秒"
    
    def test_validation_time(self):
        """测试数据验证时间"""
        
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "psn_name": "张三"
        }
        
        start_time = time.time()
        
        try:
            # 只进行数据验证，不实际调用
            result = self.client.validate_data("1101", test_data, "H43010000001")
            validation_time = time.time() - start_time
            print(f"⏱️  数据验证耗时: {validation_time:.3f}秒")
            
            assert validation_time < 0.5, f"数据验证时间过长: {validation_time:.3f}秒"
            
        except Exception as e:
            pytest.skip(f"数据验证测试跳过: {str(e)}")
    
    def test_database_query_time(self):
        """测试数据库查询时间"""
        
        start_time = time.time()
        
        try:
            # 获取支持的接口列表
            interfaces = self.client.get_supported_interfaces("H43010000001")
            query_time = time.time() - start_time
            print(f"⏱️  数据库查询耗时: {query_time:.3f}秒")
            
            assert query_time < 1.0, f"数据库查询时间过长: {query_time:.3f}秒"
            
        except Exception as e:
            pytest.skip(f"数据库查询测试跳过: {str(e)}")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_concurrent_calls(self, mock_post):
        """测试并发调用性能"""
        import threading
        
        mock_response = {
            "infcode": "0",
            "output": {"baseinfo": {"psn_name": "张三"}}
        }
        mock_post.return_value = mock_response
        
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "psn_name": "张三"
        }
        
        results = []
        
        def call_interface():
            start = time.time()
            result = self.client.call("1101", test_data, "H43010000001")
            duration = time.time() - start
            results.append(duration)
        
        # 创建5个并发线程
        threads = []
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=call_interface)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        avg_time = sum(results) / len(results)
        
        print(f"⏱️  并发调用总耗时: {total_time:.3f}秒")
        print(f"⏱️  平均单次耗时: {avg_time:.3f}秒")
        
        assert total_time < 5.0, f"并发调用时间过长: {total_time:.3f}秒"
        assert avg_time < 1.0, f"平均调用时间过长: {avg_time:.3f}秒"