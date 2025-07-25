"""
快速医保接口测试
使用共享客户端，避免重复初始化
"""

import pytest
from unittest.mock import patch
from .test_base import IntegrationTestBase

class TestInterfaceFast(IntegrationTestBase):
    """快速医保接口测试类"""
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_1101_interface_fast(self, mock_post):
        """快速测试1101接口"""
        
        mock_response = {
            "infcode": "0",
            "output": {
                "baseinfo": {
                    "psn_no": "H430100000000000001",
                    "psn_name": "张三"
                }
            }
        }
        mock_post.return_value = mock_response
        
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "psn_name": "张三"
        }
        
        result = self.client.call("1101", test_data, "H43010000001")
        
        assert result is not None
        assert result["infcode"] == "0"
        print(f"✅ 1101接口测试成功")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_2201_interface_fast(self, mock_post):
        """快速测试2201接口"""
        
        mock_response = {
            "infcode": "0",
            "output": {
                "mdtrt_id": "MDT202501250001",
                "psn_no": "H430100000000000001"
            }
        }
        mock_post.return_value = mock_response
        
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "ipt_otp_no": "OP202501250001"
        }
        
        result = self.client.call("2201", test_data, "H43010000001")
        
        assert result is not None
        assert result["infcode"] == "0"
        print(f"✅ 2201接口测试成功")
    
    def test_client_ready(self):
        """测试客户端就绪状态"""
        assert self.client is not None
        assert self.client.sdk is not None
        print(f"✅ 客户端就绪")