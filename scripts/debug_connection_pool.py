#!/usr/bin/env python3
"""
调试连接池创建过程
精确定位哪些组件在创建连接池
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def debug_connection_pool_creation():
    """调试连接池创建过程"""
    
    print("🔍 开始调试连接池创建过程...")
    
    # 1. 先检查全局连接池管理器
    print("\n1️⃣ 检查全局连接池管理器:")
    from medical_insurance_sdk.core.connection_pool_manager import get_global_pool_manager
    
    manager = get_global_pool_manager()
    print(f"   全局管理器ID: {id(manager)}")
    print(f"   当前MySQL连接池数量: {len(manager.mysql_pools)}")
    print(f"   当前Redis连接池数量: {len(manager.redis_pools)}")
    
    # 2. 逐步创建客户端，观察每一步的连接池变化
    print("\n2️⃣ 逐步创建客户端组件:")
    
    # 步骤1: 创建数据库配置
    print("   步骤1: 创建数据库配置...")
    from medical_insurance_sdk.core.database import DatabaseConfig
    db_config = DatabaseConfig.from_env()
    print(f"   连接池数量: MySQL={len(manager.mysql_pools)}, Redis={len(manager.redis_pools)}")
    
    # 步骤2: 创建SDK配置
    print("   步骤2: 创建SDK配置...")
    from medical_insurance_sdk.config.models import SDKConfig
    config = SDKConfig(database_config=db_config)
    print(f"   连接池数量: MySQL={len(manager.mysql_pools)}, Redis={len(manager.redis_pools)}")
    
    # 步骤3: 创建SDK实例
    print("   步骤3: 创建SDK实例...")
    from medical_insurance_sdk.sdk import MedicalInsuranceSDK
    sdk = MedicalInsuranceSDK(config)
    print(f"   连接池数量: MySQL={len(manager.mysql_pools)}, Redis={len(manager.redis_pools)}")
    
    # 步骤4: 创建通用处理器
    print("   步骤4: 创建通用处理器...")
    from medical_insurance_sdk.core.universal_processor import UniversalInterfaceProcessor
    processor = UniversalInterfaceProcessor(sdk)
    print(f"   连接池数量: MySQL={len(manager.mysql_pools)}, Redis={len(manager.redis_pools)}")
    
    # 步骤5: 创建异步处理器
    print("   步骤5: 创建异步处理器...")
    from medical_insurance_sdk.async_processing import AsyncProcessor
    async_processor = AsyncProcessor()
    print(f"   连接池数量: MySQL={len(manager.mysql_pools)}, Redis={len(manager.redis_pools)}")
    
    # 3. 检查连接池详情
    print("\n3️⃣ 连接池详情:")
    for pool_name, pool in manager.mysql_pools.items():
        print(f"   MySQL连接池 '{pool_name}': {id(pool)}")
    
    for pool_name, pool in manager.redis_pools.items():
        print(f"   Redis连接池 '{pool_name}': {id(pool)}")
    
    # 4. 完整创建客户端
    print("\n4️⃣ 完整创建客户端:")
    from medical_insurance_sdk.client import MedicalInsuranceClient
    client = MedicalInsuranceClient()
    print(f"   最终连接池数量: MySQL={len(manager.mysql_pools)}, Redis={len(manager.redis_pools)}")

def analyze_connection_pool_sources():
    """分析连接池创建源头"""
    
    print("\n🔬 分析连接池创建源头...")
    
    # 通过修改连接池管理器来追踪创建源头
    import traceback
    
    original_create_mysql_pool = None
    
    def traced_create_mysql_pool(self, pool_name, config):
        print(f"\n📍 创建MySQL连接池 '{pool_name}':")
        print("   调用栈:")
        for line in traceback.format_stack()[-5:-1]:  # 显示最近5层调用栈
            print(f"     {line.strip()}")
        
        return original_create_mysql_pool(self, pool_name, config)
    
    # 猴子补丁追踪连接池创建
    from medical_insurance_sdk.core.connection_pool_manager import ConnectionPoolManager
    original_create_mysql_pool = ConnectionPoolManager.create_mysql_pool
    ConnectionPoolManager.create_mysql_pool = traced_create_mysql_pool
    
    print("   开始创建客户端（带追踪）...")
    from medical_insurance_sdk.client import MedicalInsuranceClient
    client = MedicalInsuranceClient()
    
    # 恢复原始方法
    ConnectionPoolManager.create_mysql_pool = original_create_mysql_pool

if __name__ == "__main__":
    debug_connection_pool_creation()
    analyze_connection_pool_sources()