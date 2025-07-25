#!/usr/bin/env python3
"""
测试文件清理脚本
将项目根目录中散乱的测试文件移动到合适的位置或删除
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_test_files():
    """清理项目根目录中的测试文件"""
    
    # 项目根目录
    root_dir = Path(__file__).parent.parent
    
    # 要移动到tests/integration/的文件模式
    integration_patterns = [
        "test_*integration*.py",
        "test_*apifox*.py", 
        "test_sdk*.py",
        "test_real*.py"
    ]
    
    # 要移动到tests/unit/的文件模式
    unit_patterns = [
        "test_config*.py",
        "test_validation*.py",
        "test_protocol*.py",
        "test_client*.py"
    ]
    
    # 要移动到tests/performance/的文件模式
    performance_patterns = [
        "test_*stress*.py",
        "test_*performance*.py",
        "*stress_test*.py"
    ]
    
    # 要删除的临时测试文件模式
    temp_patterns = [
        "test_*simple*.py",
        "test_*debug*.py",
        "test_*temp*.py",
        "debug_*.py",
        "simple_*.py",
        "demo_*.py",
        "trace_*.py"
    ]
    
    print("🧹 开始清理测试文件...")
    
    # 移动集成测试文件
    moved_count = 0
    for pattern in integration_patterns:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                dest = root_dir / "tests" / "integration" / file_path.name
                print(f"📁 移动 {file_path.name} -> tests/integration/")
                shutil.move(str(file_path), str(dest))
                moved_count += 1
    
    # 移动单元测试文件
    for pattern in unit_patterns:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                dest = root_dir / "tests" / "unit" / file_path.name
                print(f"📁 移动 {file_path.name} -> tests/unit/")
                shutil.move(str(file_path), str(dest))
                moved_count += 1
    
    # 移动性能测试文件
    for pattern in performance_patterns:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                dest = root_dir / "tests" / "performance" / file_path.name
                print(f"📁 移动 {file_path.name} -> tests/performance/")
                shutil.move(str(file_path), str(dest))
                moved_count += 1
    
    # 删除临时测试文件
    deleted_count = 0
    for pattern in temp_patterns:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                print(f"🗑️  删除临时文件 {file_path.name}")
                file_path.unlink()
                deleted_count += 1
    
    # 移动其他测试相关文件到fixtures
    other_test_files = [
        "insert_test_*.py",
        "check_*.py", 
        "verify_*.py",
        "update_*.py"
    ]
    
    fixture_count = 0
    for pattern in other_test_files:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                dest = root_dir / "tests" / "fixtures" / file_path.name
                print(f"📋 移动 {file_path.name} -> tests/fixtures/")
                shutil.move(str(file_path), str(dest))
                fixture_count += 1
    
    print(f"\n✅ 清理完成!")
    print(f"📁 移动文件: {moved_count}")
    print(f"🗑️  删除文件: {deleted_count}")
    print(f"📋 夹具文件: {fixture_count}")
    
    # 显示新的测试目录结构
    print(f"\n📂 新的测试目录结构:")
    tests_dir = root_dir / "tests"
    for subdir in ["unit", "integration", "performance", "fixtures"]:
        subdir_path = tests_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*.py"))
            if files:
                print(f"  tests/{subdir}/ ({len(files)} 文件)")
                for file in sorted(files)[:3]:  # 只显示前3个
                    print(f"    - {file.name}")
                if len(files) > 3:
                    print(f"    ... 还有 {len(files) - 3} 个文件")

if __name__ == "__main__":
    cleanup_test_files()