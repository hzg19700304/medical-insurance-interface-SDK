#!/usr/bin/env python3
"""
连接池优化脚本
分析和优化连接池创建问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def analyze_connection_pool_issue():
    """分析连接池问题"""
    
    print("🔍 分析连接池创建问题...")
    
    # 1. 检查当前的连接池管理器
    from medical_insurance_sdk.core.connection_pool_manager import get_global_pool_manager
    
    print("📊 测试连接池管理器行为:")
    
    # 获取全局管理器
    manager1 = get_global_pool_manager()
    print(f"第一次获取管理器: {id(manager1)}")
    
    manager2 = get_global_pool_manager()
    print(f"第二次获取管理器: {id(manager2)}")
    
    print(f"是否为同一个实例: {manager1 is manager2}")
    
    # 2. 测试客户端初始化
    print("\n🧪 测试客户端初始化:")
    
    from medical_insurance_sdk.client import MedicalInsuranceClient
    
    print("创建第一个客户端...")
    client1 = MedicalInsuranceClient()
    
    print("创建第二个客户端...")
    client2 = MedicalInsuranceClient()
    
    print(f"客户端1 SDK: {id(client1.sdk)}")
    print(f"客户端2 SDK: {id(client2.sdk)}")
    print(f"是否为同一个SDK实例: {client1.sdk is client2.sdk}")

def create_optimized_test():
    """创建优化的测试示例"""
    
    print("\n🚀 创建优化的测试示例...")
    
    # 创建单例客户端管理器
    optimized_test_code = '''
"""
优化的测试客户端管理器
"""

class OptimizedTestClient:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self):
        if self._client is None:
            from medical_insurance_sdk.client import MedicalInsuranceClient
            print("🚀 创建单例客户端...")
            self._client = MedicalInsuranceClient()
            print("✅ 单例客户端创建完成")
        return self._client

# 使用示例
test_client_manager = OptimizedTestClient()
client = test_client_manager.get_client()
'''
    
    print("💡 优化建议:")
    print("1. 使用单例模式管理客户端实例")
    print("2. 在测试套件级别共享连接池")
    print("3. 延迟初始化非必要组件")
    print("4. 使用连接池预热机制")

if __name__ == "__main__":
    analyze_connection_pool_issue()
    create_optimized_test()