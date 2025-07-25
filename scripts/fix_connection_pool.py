#!/usr/bin/env python3
"""
修复连接池重复创建问题
通过共享DatabaseManager实例来避免重复创建连接池
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_optimized_client():
    """创建优化的客户端类"""
    
    optimized_client_code = '''
"""
优化的医保接口客户端
共享DatabaseManager实例，避免重复创建连接池
"""

import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from .sdk import MedicalInsuranceSDK
from .core.universal_processor import UniversalInterfaceProcessor
from .core.database import DatabaseConfig, DatabaseManager
from .config.models import SDKConfig
from .async_processing import AsyncProcessor

class OptimizedMedicalInsuranceClient:
    """优化的医保接口客户端"""
    
    # 类级别的共享资源
    _shared_db_manager = None
    _shared_config_manager = None
    
    def __init__(self, config: Optional[SDKConfig] = None):
        """初始化客户端"""
        if config is None:
            db_config = DatabaseConfig.from_env()
            config = SDKConfig(database_config=db_config)

        # 使用共享的DatabaseManager
        if self._shared_db_manager is None:
            OptimizedMedicalInsuranceClient._shared_db_manager = DatabaseManager(config.database_config)
            print("🔧 创建共享DatabaseManager")
        
        # 创建SDK时传入共享的DatabaseManager
        self.sdk = self._create_optimized_sdk(config)
        self.universal_processor = UniversalInterfaceProcessor(self.sdk)
        
        # 创建优化的AsyncProcessor（复用DatabaseManager）
        self.async_processor = self._create_optimized_async_processor()
        
        self.logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="medical-sdk-async")
        self._async_tasks = {}
        
        self.logger.info("优化医保接口客户端初始化完成")
    
    def _create_optimized_sdk(self, config):
        """创建优化的SDK实例"""
        # 这里需要修改SDK类来接受共享的DatabaseManager
        # 暂时返回标准SDK
        return MedicalInsuranceSDK(config)
    
    def _create_optimized_async_processor(self):
        """创建优化的异步处理器"""
        # 这里需要修改AsyncProcessor来复用DatabaseManager
        # 暂时返回标准AsyncProcessor
        return AsyncProcessor()
    
    # 其他方法与原始客户端相同...
    def call(self, api_code: str, data: dict, org_code: str, **kwargs) -> dict:
        """同步调用医保接口"""
        return self.sdk.call(api_code, data, org_code, **kwargs)
'''
    
    print("💡 优化方案:")
    print("1. 在客户端类级别创建共享的DatabaseManager")
    print("2. 修改SDK和AsyncProcessor接受外部DatabaseManager")
    print("3. 避免每个组件独立创建DatabaseManager")
    
    return optimized_client_code

def suggest_architecture_improvements():
    """建议架构改进"""
    
    print("\n🏗️ 架构改进建议:")
    
    improvements = [
        {
            "问题": "多个组件独立创建DatabaseManager",
            "解决方案": "使用依赖注入，共享DatabaseManager实例",
            "优先级": "高"
        },
        {
            "问题": "AsyncProcessor和TaskManager重复创建连接池",
            "解决方案": "TaskManager复用AsyncProcessor的ConfigManager",
            "优先级": "高"
        },
        {
            "问题": "连接池名称冲突（都叫'default'）",
            "解决方案": "使用不同的连接池名称或共享同一个",
            "优先级": "中"
        },
        {
            "问题": "组件初始化顺序依赖",
            "解决方案": "使用工厂模式或服务容器",
            "优先级": "中"
        }
    ]
    
    for i, improvement in enumerate(improvements, 1):
        print(f"\n{i}. {improvement['问题']}")
        print(f"   解决方案: {improvement['解决方案']}")
        print(f"   优先级: {improvement['优先级']}")

def create_quick_fix():
    """创建快速修复方案"""
    
    print("\n⚡ 快速修复方案:")
    print("由于架构修改较大，建议采用以下快速修复:")
    
    quick_fix_code = '''
# 在AsyncProcessor初始化时复用已有的ConfigManager
class QuickFixAsyncProcessor:
    def __init__(self, config_manager=None):
        if config_manager is not None:
            # 复用传入的ConfigManager，避免创建新的DatabaseManager
            self.config_manager = config_manager
            print("🔄 复用ConfigManager，避免创建新连接池")
        else:
            # 原有逻辑
            db_config = DatabaseConfig.from_env()
            self.config_manager = ConfigManager(db_config)
        
        # TaskManager也复用ConfigManager
        self.task_manager = TaskManager(self.config_manager, reuse_db_manager=True)
'''
    
    print(quick_fix_code)

if __name__ == "__main__":
    create_optimized_client()
    suggest_architecture_improvements()
    create_quick_fix()