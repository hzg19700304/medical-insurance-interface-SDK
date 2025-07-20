"""基础功能测试"""

import pytest
from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.core.database import DatabaseConfig
from medical_insurance_sdk.config.models import SDKConfig


def test_sdk_import():
    """测试SDK导入"""
    from medical_insurance_sdk import (
        MedicalInsuranceClient,
        MedicalInsuranceSDK,
        MedicalInsuranceException
    )
    
    assert MedicalInsuranceClient is not None
    assert MedicalInsuranceSDK is not None
    assert MedicalInsuranceException is not None


def test_database_config():
    """测试数据库配置"""
    config = DatabaseConfig()
    assert config.host == "localhost"
    assert config.port == 3306
    assert config.database == "medical_insurance"


def test_client_creation():
    """测试客户端创建"""
    # 使用默认配置创建客户端
    db_config = DatabaseConfig()
    sdk_config = SDKConfig(database_config=db_config)
    client = MedicalInsuranceClient(sdk_config)
    
    assert client is not None
    assert client.sdk is not None


def test_config_from_env():
    """测试从环境变量加载配置"""
    import os
    
    # 设置测试环境变量
    os.environ['DB_HOST'] = 'test_host'
    os.environ['DB_PORT'] = '3307'
    os.environ['DB_DATABASE'] = 'test_db'
    
    config = DatabaseConfig.from_env()
    
    assert config.host == 'test_host'
    assert config.port == 3307
    assert config.database == 'test_db'
    
    # 清理环境变量
    del os.environ['DB_HOST']
    del os.environ['DB_PORT']
    del os.environ['DB_DATABASE']


if __name__ == "__main__":
    pytest.main([__file__])