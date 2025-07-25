#!/usr/bin/env python3
"""
清理项目根目录中剩余的测试文件
根据文件内容和用途进行分类处理
"""

import os
import shutil
import glob
from pathlib import Path

def analyze_and_cleanup():
    """分析并清理剩余的测试文件"""
    
    root_dir = Path(__file__).parent.parent
    
    # 文件分类规则
    file_categories = {
        # 保留并移动到tests/unit/的文件
        "unit_tests": {
            "patterns": [
                "test_mysql_connection.py",
                "test_redis_connection.py", 
                "test_redis_cache.py",
                "test_env_loading.py",
                "test_error_handling.py"
            ],
            "action": "move_to_unit",
            "reason": "基础组件连接测试，有保留价值"
        },
        
        # 保留并移动到tests/integration/的文件
        "integration_tests": {
            "patterns": [
                "test_async_processing.py",
                "test_async_tasks.py",
                "test_new_interfaces.py",
                "test_separate_interfaces.py"
            ],
            "action": "move_to_integration", 
            "reason": "异步处理和接口集成测试"
        },
        
        # 保留并移动到tests/performance/的文件
        "performance_tests": {
            "patterns": [
                "test_connection_pool*.py",
                "test_data_helper_comprehensive.py",
                "test_data_sync_service_comprehensive.py"
            ],
            "action": "move_to_performance",
            "reason": "性能和压力测试相关"
        },
        
        # 保留并移动到tests/fixtures/的文件
        "fixture_files": {
            "patterns": [
                "test_logging_monitoring*.py",
                "test_single_task_status.py",
                "test_worker_quick.py"
            ],
            "action": "move_to_fixtures",
            "reason": "测试工具和监控脚本"
        },
        
        # 删除的临时测试文件
        "temp_files": {
            "patterns": [
                "test_correct_path.py",
                "test_database.db"
            ],
            "action": "delete",
            "reason": "临时测试文件，无保留价值"
        },
        
        # 保留的配置和数据文件
        "keep_files": {
            "patterns": [
                "add_*.py",
                "compare_*.py", 
                "init_*.py",
                "insert_*.py",
                "setup_*.py",
                "error_handling_demo.py"
            ],
            "action": "move_to_scripts",
            "reason": "配置和初始化脚本，移动到scripts目录"
        }
    }
    
    print("🧹 开始清理项目根目录中的剩余测试文件...")
    
    moved_count = 0
    deleted_count = 0
    kept_count = 0
    
    # 处理每个分类
    for category, config in file_categories.items():
        print(f"\n📂 处理 {category}...")
        
        for pattern in config["patterns"]:
            files = list(root_dir.glob(pattern))
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                    
                action = config["action"]
                
                if action == "move_to_unit":
                    dest = root_dir / "tests" / "unit" / file_path.name
                    print(f"📁 移动 {file_path.name} -> tests/unit/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                    
                elif action == "move_to_integration":
                    dest = root_dir / "tests" / "integration" / file_path.name
                    print(f"📁 移动 {file_path.name} -> tests/integration/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                    
                elif action == "move_to_performance":
                    dest = root_dir / "tests" / "performance" / file_path.name
                    print(f"📁 移动 {file_path.name} -> tests/performance/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                    
                elif action == "move_to_fixtures":
                    dest = root_dir / "tests" / "fixtures" / file_path.name
                    print(f"📋 移动 {file_path.name} -> tests/fixtures/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                    
                elif action == "move_to_scripts":
                    dest = root_dir / "scripts" / file_path.name
                    print(f"🔧 移动 {file_path.name} -> scripts/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                    
                elif action == "delete":
                    print(f"🗑️  删除 {file_path.name}")
                    file_path.unlink()
                    deleted_count += 1
                    
                elif action == "keep":
                    print(f"📌 保留 {file_path.name}")
                    kept_count += 1
    
    # 处理其他配置文件
    config_files = [
        "apifox_*.json",
        "apifox_*.js", 
        "*.md",
        "*.log",
        "*.csv",
        "performance_report.*"
    ]
    
    print(f"\n📋 处理配置和报告文件...")
    for pattern in config_files:
        files = list(root_dir.glob(pattern))
        for file_path in files:
            if file_path.is_file() and file_path.name not in ["README.md", "COMMANDS.md"]:
                if file_path.suffix in ['.md', '.log', '.csv']:
                    dest = root_dir / "docs" / file_path.name
                    print(f"📄 移动 {file_path.name} -> docs/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
                elif 'apifox' in file_path.name:
                    dest = root_dir / "tests" / "fixtures" / file_path.name
                    print(f"🔧 移动 {file_path.name} -> tests/fixtures/")
                    shutil.move(str(file_path), str(dest))
                    moved_count += 1
    
    print(f"\n✅ 清理完成!")
    print(f"📁 移动文件: {moved_count}")
    print(f"🗑️  删除文件: {deleted_count}")
    print(f"📌 保留文件: {kept_count}")
    
    # 显示清理后的根目录状态
    print(f"\n📂 根目录清理后状态:")
    remaining_test_files = list(root_dir.glob("test_*.py"))
    if remaining_test_files:
        print("⚠️  仍有测试文件未处理:")
        for file in remaining_test_files:
            print(f"    - {file.name}")
    else:
        print("✅ 根目录已无测试文件")
    
    # 显示各测试目录的文件数量
    print(f"\n📊 测试目录统计:")
    for subdir in ["unit", "integration", "performance", "fixtures"]:
        subdir_path = root_dir / "tests" / subdir
        if subdir_path.exists():
            py_files = list(subdir_path.glob("*.py"))
            print(f"  tests/{subdir}/: {len(py_files)} 个文件")

if __name__ == "__main__":
    analyze_and_cleanup()