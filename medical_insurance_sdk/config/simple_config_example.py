#!/usr/bin/env python3
"""简化配置使用示例"""

import os
from medical_insurance_sdk.config import create_config

def simple_usage_example():
    """简单使用示例 - 单数据库配置"""
    
    print("=== 简单配置使用示例 ===")
    
    # 方式1: 使用环境变量（推荐）
    os.environ['MEDICAL_DB_HOST'] = 'localhost'
    os.environ['MEDICAL_DB_NAME'] = 'medical_insurance'  # 只需要一个数据库
    os.environ['MEDICAL_DB_USER'] = 'root'
    os.environ['MEDICAL_DB_PASSWORD'] = 'your_password'
    
    # 创建配置（会自动使用环境变量）
    config = create_config()
    
    print(f"当前环境: {config.environment}")
    print(f"数据库配置:")
    print(f"  主机: {config.database.host}")
    print(f"  数据库: {config.database.database}")
    print(f"  用户: {config.database.username}")
    print(f"  密码: {'***' if config.database.password else '(空)'}")
    
    return config

def multi_env_example():
    """多环境示例 - 同一数据库不同配置"""
    
    print("\n=== 多环境配置示例 ===")
    
    # 基础数据库信息（所有环境共用）
    os.environ['MEDICAL_DB_HOST'] = 'localhost'
    os.environ['MEDICAL_DB_USER'] = 'root'
    os.environ['MEDICAL_DB_PASSWORD'] = 'your_password'
    
    # 开发环境 - 使用调试模式
    os.environ['MEDICAL_INSURANCE_ENV'] = 'development'
    os.environ['MEDICAL_DB_NAME'] = 'medical_insurance'  # 同一个数据库
    os.environ['MEDICAL_DEBUG'] = 'true'
    os.environ['MEDICAL_LOG_LEVEL'] = 'DEBUG'
    
    dev_config = create_config()
    print(f"开发环境配置:")
    print(f"  数据库: {dev_config.database.database}")
    print(f"  调试模式: {dev_config.debug}")
    print(f"  日志级别: {dev_config.logging.level}")
    
    # 生产环境 - 使用相同数据库但不同设置
    os.environ['MEDICAL_INSURANCE_ENV'] = 'production'
    os.environ['MEDICAL_DEBUG'] = 'false'
    os.environ['MEDICAL_LOG_LEVEL'] = 'INFO'
    
    prod_config = create_config()
    print(f"\n生产环境配置:")
    print(f"  数据库: {prod_config.database.database}")  # 同一个数据库
    print(f"  调试模式: {prod_config.debug}")
    print(f"  日志级别: {prod_config.logging.level}")

def minimal_config_example():
    """最小化配置示例"""
    
    print("\n=== 最小化配置示例 ===")
    
    # 只设置必需的配置
    os.environ['MEDICAL_DB_NAME'] = 'medical_insurance'
    os.environ['MEDICAL_DB_USER'] = 'root'
    # 其他配置使用默认值
    
    config = create_config()
    
    print("最小配置结果:")
    print(f"  数据库主机: {config.database.host} (默认)")
    print(f"  数据库端口: {config.database.port} (默认)")
    print(f"  数据库名称: {config.database.database} (设置)")
    print(f"  用户名: {config.database.username} (设置)")

if __name__ == '__main__':
    # 运行示例
    simple_usage_example()
    multi_env_example()
    minimal_config_example()