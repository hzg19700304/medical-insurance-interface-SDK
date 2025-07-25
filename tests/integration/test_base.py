"""
集成测试基类
提供共享的客户端实例，避免重复初始化
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.client import MedicalInsuranceClient

class IntegrationTestBase:
    """集成测试基类"""
    
    _shared_client = None
    _client_initialized = False
    
    @classmethod
    def get_client(cls):
        """获取共享的客户端实例"""
        if not cls._client_initialized:
            print("🚀 初始化共享客户端...")
            cls._shared_client = MedicalInsuranceClient()
            cls._client_initialized = True
            print("✅ 共享客户端初始化完成")
        
        return cls._shared_client
    
    @classmethod
    def setup_class(cls):
        """类级别设置"""
        cls.client = cls.get_client()
    
    @classmethod
    def teardown_class(cls):
        """类级别清理"""
        # 可以在这里添加清理逻辑
        pass