"""
真正优化的医保接口测试
使用全局连接池管理器，确保只创建一次连接池
"""

import pytest
from unittest.mock import patch
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class GlobalConnectionPoolManager:
    """全局连接池管理器单例"""
    _instance = None
    _initialized = False
    _pool_manager = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_pool_manager(self):
        """获取全局连接池管理器"""
        if not self._initialized:
            from medical_insurance_sdk.core.connection_pool_manager import get_global_pool_manager
            print("🔧 初始化全局连接池管理器...")
            self._pool_manager = get_global_pool_manager()
            self._initialized = True
            print("✅ 全局连接池管理器初始化完成")
        return self._pool_manager

class OptimizedTestClient:
    """优化的测试客户端"""
    _instance = None
    _client = None
    _pool_manager = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self):
        """获取优化的客户端实例"""
        if self._client is None:
            # 先初始化全局连接池管理器
            global_pool = GlobalConnectionPoolManager()
            self._pool_manager = global_pool.get_pool_manager()
            
            # 然后创建客户端
            from medical_insurance_sdk.client import MedicalInsuranceClient
            print("🚀 创建优化客户端（复用连接池）...")
            self._client = MedicalInsuranceClient()
            print("✅ 优化客户端创建完成")
        return self._client

# 全局优化客户端管理器
_optimized_client_manager = OptimizedTestClient()

class TestInterfaceOptimized:
    """优化的医保接口测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别设置"""
        cls.client = _optimized_client_manager.get_client()
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_1101_optimized(self, mock_post):
        """优化的1101接口测试"""
        
        mock_post.return_value = {
            "infcode": "0",
            "output": {"baseinfo": {"psn_name": "张三"}}
        }
        
        result = self.client.call("1101", {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "psn_name": "张三"
        }, "H43010000001")
        
        assert result["infcode"] == "0"
        print("🔥 优化1101测试完成")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_2201_optimized(self, mock_post):
        """优化的2201接口测试"""
        
        mock_post.return_value = {
            "infcode": "0",
            "output": {"mdtrt_id": "MDT001"}
        }
        
        result = self.client.call("2201", {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "ipt_otp_no": "OP001"
        }, "H43010000001")
        
        assert result["infcode"] == "0"
        print("🔥 优化2201测试完成")
    
    def test_connection_pool_reuse(self):
        """测试连接池复用"""
        # 验证连接池管理器是单例
        from medical_insurance_sdk.core.connection_pool_manager import get_global_pool_manager
        
        manager1 = get_global_pool_manager()
        manager2 = get_global_pool_manager()
        
        assert manager1 is manager2, "连接池管理器应该是单例"
        print("🔥 连接池复用验证完成")
    
    def test_client_singleton(self):
        """测试客户端单例"""
        client1 = _optimized_client_manager.get_client()
        client2 = _optimized_client_manager.get_client()
        
        assert client1 is client2, "客户端应该是单例"
        print("🔥 客户端单例验证完成")