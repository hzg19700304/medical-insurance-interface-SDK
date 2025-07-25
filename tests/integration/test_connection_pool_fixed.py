"""
测试连接池修复效果
验证是否只创建一次连接池
"""

import pytest
from unittest.mock import patch
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestConnectionPoolFixed:
    """测试连接池修复效果"""
    
    def test_single_connection_pool_creation(self):
        """测试是否只创建一次连接池"""
        
        print("🧪 测试修复后的连接池创建...")
        
        from medical_insurance_sdk.client import MedicalInsuranceClient
        
        # 创建客户端，观察连接池创建次数
        client = MedicalInsuranceClient()
        
        # 验证客户端正常工作
        assert client is not None
        assert client.sdk is not None
        assert client.async_processor is not None
        
        print("✅ 客户端创建成功")
        
        # 验证AsyncProcessor复用了SDK的ConfigManager
        assert client.async_processor.config_manager is client.sdk.config_manager
        print("✅ AsyncProcessor复用ConfigManager成功")
        
        # 验证TaskManager复用了ConfigManager的DatabaseManager
        assert client.async_processor.task_manager.db_manager is client.sdk.config_manager.db_manager
        print("✅ TaskManager复用DatabaseManager成功")
    
    @patch('medical_insurance_sdk.core.http_client.HTTPClient.post')
    def test_interface_call_after_fix(self, mock_post):
        """测试修复后的接口调用"""
        
        mock_post.return_value = {
            "infcode": "0",
            "output": {"baseinfo": {"psn_name": "张三"}}
        }
        
        from medical_insurance_sdk.client import MedicalInsuranceClient
        client = MedicalInsuranceClient()
        
        result = client.call("1101", {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "psn_name": "张三"
        }, "H43010000001")
        
        assert result["infcode"] == "0"
        print("✅ 修复后接口调用正常")
    
    def test_connection_pool_count(self):
        """测试连接池数量"""
        
        from medical_insurance_sdk.core.connection_pool_manager import get_global_pool_manager
        from medical_insurance_sdk.client import MedicalInsuranceClient
        
        # 获取全局连接池管理器
        manager = get_global_pool_manager()
        initial_count = len(manager.mysql_pools)
        
        # 创建客户端
        client = MedicalInsuranceClient()
        
        # 检查连接池数量
        final_count = len(manager.mysql_pools)
        
        print(f"🔢 初始连接池数量: {initial_count}")
        print(f"🔢 最终连接池数量: {final_count}")
        print(f"🔢 新增连接池数量: {final_count - initial_count}")
        
        # 应该只增加1个连接池
        assert final_count - initial_count <= 1, "应该最多只创建1个连接池"
        print("✅ 连接池数量验证通过")