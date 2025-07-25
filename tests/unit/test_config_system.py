#!/usr/bin/env python3
"""测试配置系统"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_insurance_sdk.config import (
    create_config,
    get_config_info,
    validate_config,
    env_manager,
    config_factory
)


def test_basic_configuration():
    """测试基本配置功能"""
    print("=== 测试基本配置功能 ===")
    
    try:
        # 设置测试环境变量
        os.environ['MEDICAL_INSURANCE_ENV'] = 'development'
        os.environ['MEDICAL_DB_NAME'] = 'test_db'
        os.environ['MEDICAL_DB_USER'] = 'test_user'
        
        # 创建配置
        config = create_config(environment='development')
        
        print(f"✓ 配置创建成功")
        print(f"  环境: {config.environment}")
        print(f"  调试模式: {config.debug}")
        print(f"  数据库主机: {config.database.host}")
        print(f"  数据库名称: {config.database.database}")
        print(f"  Redis主机: {config.redis.host}")
        print(f"  日志级别: {config.logging.level}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置创建失败: {str(e)}")
        return False


def test_environment_variables():
    """测试环境变量管理"""
    print("\n=== 测试环境变量管理 ===")
    
    try:
        # 加载环境变量
        env_vars = env_manager.load_environment_variables()
        print(f"✓ 加载了 {len(env_vars)} 个环境变量")
        
        # 验证环境变量
        validation = env_manager.validate_environment()
        print(f"✓ 环境变量验证: {'通过' if validation['valid'] else '失败'}")
        print(f"  总定义: {validation['total_count']}")
        print(f"  已加载: {validation['loaded_count']}")
        
        if validation['errors']:
            print(f"  错误: {len(validation['errors'])}")
            for error in validation['errors'][:3]:  # 只显示前3个错误
                print(f"    - {error}")
        
        if validation['missing_required']:
            print(f"  缺少必需: {validation['missing_required']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 环境变量测试失败: {str(e)}")
        return False


def test_configuration_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    try:
        # 创建配置
        config = create_config(environment='development', validate=False)
        
        # 验证配置
        validation_result = validate_config(config)
        
        print(f"✓ 配置验证完成")
        print(f"  有效: {'是' if validation_result['is_valid'] else '否'}")
        print(f"  错误数量: {validation_result['error_count']}")
        print(f"  警告数量: {validation_result['warning_count']}")
        
        if validation_result['errors']:
            print("  错误:")
            for error in validation_result['errors'][:3]:  # 只显示前3个错误
                print(f"    - {error}")
        
        if validation_result['warnings']:
            print("  警告:")
            for warning in validation_result['warnings'][:3]:  # 只显示前3个警告
                print(f"    - {warning}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置验证失败: {str(e)}")
        return False


def test_configuration_templates():
    """测试配置模板生成"""
    print("\n=== 测试配置模板生成 ===")
    
    try:
        # 生成配置模板
        templates = config_factory.generate_configuration_template(
            environment='testing',
            include_env_file=True,
            include_sensitive=False
        )
        
        print(f"✓ 生成了 {len(templates)} 个模板文件")
        for filename in templates.keys():
            print(f"  - {filename}")
        
        # 生成环境变量模板
        env_template = env_manager.generate_env_template(include_sensitive=False)
        print(f"✓ 环境变量模板长度: {len(env_template)} 字符")
        
        return True
        
    except Exception as e:
        print(f"✗ 模板生成失败: {str(e)}")
        return False


def test_configuration_info():
    """测试配置信息获取"""
    print("\n=== 测试配置信息获取 ===")
    
    try:
        info = get_config_info()
        
        print("✓ 配置信息获取成功")
        
        env_info = info.get('environment_variables', {})
        print(f"  环境变量总数: {env_info.get('total_defined', 0)}")
        print(f"  环境变量加载数: {env_info.get('loaded_count', 0)}")
        
        config_info = info.get('config_files', {})
        print(f"  配置目录: {config_info.get('config_directory', 'N/A')}")
        
        available_envs = config_info.get('available_environments', [])
        print(f"  可用环境: {', '.join(available_envs) if available_envs else '无'}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置信息获取失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("医保接口SDK配置系统测试")
    print("=" * 50)
    
    tests = [
        test_basic_configuration,
        test_environment_variables,
        test_configuration_validation,
        test_configuration_templates,
        test_configuration_info,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！配置系统工作正常。")
        return 0
    else:
        print("✗ 部分测试失败，请检查配置系统。")
        return 1


if __name__ == '__main__':
    sys.exit(main())