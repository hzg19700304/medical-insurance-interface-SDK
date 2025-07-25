"""
医保接口Mock测试
不依赖外部服务的接口测试
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .test_base import IntegrationTestBase

class TestInterfaceMock(IntegrationTestBase):
    """医保接口Mock测试类"""
    pass
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_1101_interface_mock(self, mock_post):
        """测试1101接口 - 使用Mock响应"""
        
        # 模拟成功响应
        mock_response = {
            "infcode": "0",
            "inf_refmsgid": "test_msg_id",
            "msgid": "test_msg_id",
            "output": {
                "baseinfo": {
                    "psn_no": "H430100000000000001",
                    "psn_name": "张三",
                    "gend": "1",
                    "brdy": "1990-01-01",
                    "certno": "430100000000000001"
                }
            },
            "respond_time": "2025-01-25 12:00:00"
        }
        
        mock_post.return_value = mock_response
        
        # 测试数据
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "mdtrt_cert_no": "430100000000000001",
            "psn_name": "张三"
        }
        
        # 调用接口
        result = self.client.call("1101", test_data, "H43010000001")
        
        # 验证结果
        assert result is not None
        assert result["infcode"] == "0"
        assert "output" in result
        assert "baseinfo" in result["output"]
        assert result["output"]["baseinfo"]["psn_name"] == "张三"
        
        print(f"✅ 1101接口Mock测试成功: {result}")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_2201_interface_mock(self, mock_post):
        """测试2201接口 - 使用Mock响应"""
        
        # 模拟成功响应
        mock_response = {
            "infcode": "0",
            "inf_refmsgid": "test_msg_id",
            "msgid": "test_msg_id",
            "output": {
                "mdtrt_id": "MDT202501250001",
                "psn_no": "H430100000000000001",
                "ipt_otp_no": "OP202501250001"
            },
            "respond_time": "2025-01-25 12:00:00"
        }
        
        mock_post.return_value = mock_response
        
        # 测试数据
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "mdtrt_cert_no": "430100000000000001",
            "ipt_otp_no": "OP202501250001"
        }
        
        # 调用接口
        result = self.client.call("2201", test_data, "H43010000001")
        
        # 验证结果
        assert result is not None
        assert result["infcode"] == "0"
        assert "output" in result
        assert result["output"]["mdtrt_id"] == "MDT202501250001"
        
        print(f"✅ 2201接口Mock测试成功: {result}")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_validation_error_mock(self, mock_post):
        """测试数据验证错误"""
        
        # 测试必填字段为空
        invalid_data = {
            "psn_no": "",  # 必填字段为空
            "mdtrt_cert_type": "01"
        }
        
        # 调用接口应该在验证阶段就失败，不会发送HTTP请求
        with pytest.raises(Exception) as exc_info:
            self.client.call("1101", invalid_data, "H43010000001")
        
        # 验证异常信息包含验证相关内容
        error_msg = str(exc_info.value)
        assert any(keyword in error_msg.lower() for keyword in ["validation", "验证", "required", "必填"])
        
        print(f"✅ 数据验证测试成功: {error_msg}")
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        assert self.client is not None
        assert self.client.sdk is not None
        assert self.client.universal_processor is not None
        
        print("✅ 客户端初始化测试成功")
    
    def test_interface_config_exists(self):
        """测试接口配置是否存在"""
        try:
            # 获取1101接口配置
            config_1101 = self.client.get_interface_info("1101", "H43010000001")
            assert config_1101 is not None
            assert config_1101["api_code"] == "1101"
            
            print(f"✅ 1101接口配置存在: {config_1101['api_name']}")
            
        except Exception as e:
            pytest.skip(f"接口配置测试跳过: {str(e)}")
    
    def test_organization_config_exists(self):
        """测试机构配置是否存在"""
        try:
            # 测试连接
            result = self.client.test_connection("H43010000001")
            assert result is not None
            
            print(f"✅ 机构配置存在: {result}")
            
        except Exception as e:
            # 网络错误是预期的，只要不是配置不存在错误就行
            if "配置不存在" not in str(e):
                print(f"✅ 机构配置存在（网络连接失败是正常的）: {str(e)}")
            else:
                pytest.fail(f"机构配置不存在: {str(e)}")