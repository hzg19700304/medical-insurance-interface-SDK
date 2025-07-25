"""
超快速医保接口测试
使用全局单例客户端
"""

import pytest
from unittest.mock import patch

class UltraFastTestClient:
    """超快速测试客户端单例"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self):
        if self._client is None:
            import sys
            import os
            from pathlib import Path
            
            # 添加项目根目录到Python路径
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from medical_insurance_sdk.client import MedicalInsuranceClient
            
            print("🚀 创建全局单例客户端...")
            self._client = MedicalInsuranceClient()
            print("✅ 全局单例客户端创建完成")
        return self._client

# 全局客户端管理器
_client_manager = UltraFastTestClient()

class TestInterfaceUltraFast:
    """超快速医保接口测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别设置"""
        cls.client = _client_manager.get_client()
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_1101_ultra_fast(self, mock_post):
        """超快速1101接口测试"""
        
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
        print("⚡ 超快速1101测试完成")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_2201_ultra_fast(self, mock_post):
        """超快速2201接口测试"""
        
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
        print("⚡ 超快速2201测试完成")
    
    def test_client_ultra_fast(self):
        """超快速客户端测试"""
        assert self.client is not None
        print("⚡ 超快速客户端测试完成")