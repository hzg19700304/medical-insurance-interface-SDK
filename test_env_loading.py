#!/usr/bin/env python3
"""测试.env文件加载"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_insurance_sdk.config import create_config, env_manager

def test_env_file_loading():
    """测试.env文件加载"""
    print("=== 测试.env文件加载 ===")
    
    # 检查.env文件是否存在
    env_file = Path(".env")
    if env_file.exists():
        print(f"✓ 找到.env文件: {env_file.absolute()}")
        
        # 加载.env文件
        try:
            env_manager.load_from_file(".env")
            print("✓ .env文件加载成功")
        except Exception as e:
            print(f"✗ .env文件加载失败: {e}")
            return False
    else:
        print("✗ 未找到.env文件")
        return False
    
    # 创建配置
    try:
        config = create_config()
        print("✓ 配置创建成功")
        
        print(f"\n当前配置:")
        print(f"  环境: {config.environment}")
        print(f"  调试模式: {config.debug}")
        print(f"  数据库主机: {config.database.host}")
        print(f"  数据库名称: {config.database.database}")
        print(f"  数据库用户: {config.database.username}")
        print(f"  数据库密码: {'***' if config.database.password else '(空)'}")
        print(f"  Redis主机: {config.redis.host}")
        print(f"  日志级别: {config.logging.level}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置创建失败: {e}")
        return False

def check_env_variables():
    """检查环境变量"""
    print("\n=== 检查关键环境变量 ===")
    
    key_vars = [
        'MEDICAL_INSURANCE_ENV',
        'MEDICAL_DB_HOST',
        'MEDICAL_DB_NAME',
        'MEDICAL_DB_USER',
        'MEDICAL_DB_PASSWORD'
    ]
    
    for var in key_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"  {var}: ***")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: (未设置)")

if __name__ == '__main__':
    success = test_env_file_loading()
    check_env_variables()
    
    if success:
        print("\n✓ .env文件配置正常！")
    else:
        print("\n✗ .env文件配置有问题，请检查")
        sys.exit(1)