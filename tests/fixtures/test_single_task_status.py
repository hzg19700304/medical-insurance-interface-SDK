#!/usr/bin/env python3
"""
测试单个任务状态的获取
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.async_processing import TaskManager
from medical_insurance_sdk.config.manager import ConfigManager
from medical_insurance_sdk.core.database import DatabaseConfig
from dotenv import load_dotenv

def test_single_task_operations():
    """测试单个任务的操作"""
    print("=== 测试单个任务操作 ===")
    
    try:
        # 加载环境变量
        load_dotenv('medical_insurance_sdk/.env')
        
        # 创建任务管理器
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        task_manager = TaskManager(config_manager)
        print("✓ 任务管理器创建成功")
        
        # 测试任务ID
        test_task_id = f"single_test_{int(time.time())}"
        test_data = {
            'api_code': '1101',
            'org_code': 'test_org',
            'test_message': 'This is a test task',
            'created_at': datetime.now().isoformat()
        }
        
        print(f"\n--- 测试任务ID: {test_task_id} ---")
        
        # 1. 插入任务状态
        print("1. 插入任务状态...")
        try:
            task_manager._update_task_status_in_db(test_task_id, 'TESTING', test_data)
            print("✓ 插入成功")
        except Exception as e:
            print(f"✗ 插入失败: {e}")
            return False
        
        # 2. 直接查询数据库验证插入
        print("2. 直接查询数据库验证...")
        try:
            with task_manager.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT task_id, status, data, created_at, updated_at
                    FROM async_task_status
                    WHERE task_id = %s
                """, (test_task_id,))
                
                row = cursor.fetchone()
                if row:
                    print("✓ 数据库中找到记录:")
                    print(f"  任务ID: {row['task_id']}")
                    print(f"  状态: {row['status']}")
                    print(f"  数据: {row['data']}")
                    print(f"  创建时间: {row['created_at']}")
                    print(f"  更新时间: {row['updated_at']}")
                else:
                    print("✗ 数据库中未找到记录")
                    return False
        except Exception as e:
            print(f"✗ 直接查询失败: {e}")
            return False
        
        # 3. 使用TaskManager方法获取
        print("3. 使用TaskManager方法获取...")
        try:
            status = task_manager._get_task_status_from_db(test_task_id)
            if status:
                print("✓ TaskManager获取成功:")
                print(f"  任务ID: {status['task_id']}")
                print(f"  状态: {status['status']}")
                print(f"  数据: {json.dumps(status['data'], indent=2, ensure_ascii=False)}")
                print(f"  创建时间: {status['created_at']}")
                print(f"  更新时间: {status['updated_at']}")
            else:
                print("✗ TaskManager获取失败，返回None")
                return False
        except Exception as e:
            print(f"✗ TaskManager获取异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 4. 更新任务状态
        print("4. 更新任务状态...")
        updated_data = test_data.copy()
        updated_data['updated_message'] = 'Task has been updated'
        updated_data['updated_at'] = datetime.now().isoformat()
        
        try:
            task_manager._update_task_status_in_db(test_task_id, 'UPDATED', updated_data)
            print("✓ 更新成功")
            
            # 再次获取验证更新
            status = task_manager._get_task_status_from_db(test_task_id)
            if status and status['status'] == 'UPDATED':
                print("✓ 更新验证成功")
                print(f"  新状态: {status['status']}")
                print(f"  新数据: {json.dumps(status['data'], indent=2, ensure_ascii=False)}")
            else:
                print("✗ 更新验证失败")
                return False
        except Exception as e:
            print(f"✗ 更新失败: {e}")
            return False
        
        # 5. 清理测试数据
        print("5. 清理测试数据...")
        try:
            with task_manager.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM async_task_status WHERE task_id = %s", (test_task_id,))
                conn.commit()
            print("✓ 清理成功")
        except Exception as e:
            print(f"⚠ 清理失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始测试单个任务状态操作...")
    print("=" * 50)
    
    if test_single_task_operations():
        print("\n✓ 单个任务状态操作测试通过")
        return 0
    else:
        print("\n✗ 单个任务状态操作测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())