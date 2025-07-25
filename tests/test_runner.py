"""
医保接口SDK测试运行器
统一管理和运行所有测试用例
"""

import sys
import os
import unittest
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    exit_code = pytest.main([
        'tests/unit/',
        '-v',
        '--tb=short'
    ])
    return exit_code == 0

def run_integration_tests():
    """运行集成测试"""
    print("🔗 运行集成测试...")
    exit_code = pytest.main([
        'tests/integration/',
        '-v',
        '--tb=short'
    ])
    return exit_code == 0

def run_performance_tests():
    """运行性能测试"""
    print("⚡ 运行性能测试...")
    exit_code = pytest.main([
        'tests/performance/',
        '-v',
        '--tb=short'
    ])
    return exit_code == 0

def run_all_tests():
    """运行所有测试"""
    print("🚀 运行所有测试...")
    
    # 使用pytest运行所有测试
    exit_code = pytest.main([
        'tests/',
        '-v',
        '--tb=short',
        '--durations=10',
        '--ignore=tests/fixtures/'
    ])
    
    return exit_code == 0

def list_tests():
    """列出所有可用的测试"""
    print("📋 可用的测试文件:")
    
    tests_dir = Path(__file__).parent
    
    for category in ['unit', 'integration', 'performance']:
        category_dir = tests_dir / category
        if category_dir.exists():
            test_files = list(category_dir.glob('test_*.py'))
            if test_files:
                print(f"\n  📁 {category.upper()} ({len(test_files)} 文件):")
                for test_file in sorted(test_files):
                    print(f"    - {test_file.name}")

def run_quick_test():
    """运行快速测试（基础功能验证）"""
    print("⚡ 运行快速测试...")
    
    # 只运行基础测试，跳过复杂的单元测试
    exit_code = pytest.main([
        'tests/test_basic.py',
        'tests/test_core_components.py',
        'tests/test_helpers.py',
        '-v',
        '--tb=short'
    ])
    return exit_code == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='医保接口SDK测试运行器')
    parser.add_argument('--unit', action='store_true', help='只运行单元测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--performance', action='store_true', help='只运行性能测试')
    parser.add_argument('--quick', action='store_true', help='运行快速测试')
    parser.add_argument('--list', action='store_true', help='列出所有测试文件')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    
    args = parser.parse_args()
    
    if args.list:
        list_tests()
        sys.exit(0)
    
    success = True
    
    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.performance:
        success = run_performance_tests()
    elif args.quick:
        success = run_quick_test()
    elif args.all or not any([args.unit, args.integration, args.performance, args.quick]):
        success = run_all_tests()
    
    if success:
        print("✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("❌ 测试失败!")
        sys.exit(1)