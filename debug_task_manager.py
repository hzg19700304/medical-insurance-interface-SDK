#!/usr/bin/env python3
"""
调试任务管理器的数据库问题
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.config.manager import ConfigManager
from medical_insurance_sdk.core.database import DatabaseConfig
from dotenv import load_dotenv

def debug_database_operations():
    """调试数据库操作"""
    print("=== 调试数据库操作 ===")
    
    try:
        # 加载环境变量
        load_dotenv('medical_insurance_sdk/.env')
        
        # 创建配置
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        
        print(f"数据库配置: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # 直接测试数据库连接
        with config_manager.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 测试基本查询
            print("\n--- 测试基本查询 ---")
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"基本查询结果: {result}")
            
            # 检查表是否存在
            print("\n--- 检查表结构 ---")
            cursor.execute("SHOW TABLES LIKE 'async_task_status'")
            table_exists = cursor.fetchone()
            print(f"表是否存在: {table_exists is not None}")
            
            if table_exists:
                # 检查表结构
                cursor.execute("DESCRIBE async_task_status")
                columns = cursor.fetchall()
                print("表结构:")
                for column in columns:
                    print(f"  - {column['Field']}: {column['Type']}")
                
                # 检查表中的数据
                print("\n--- 检查表数据 ---")
                cursor.execute("SELECT COUNT(*) as count FROM async_task_status")
                count_result = cursor.fetchone()
                count = count_result['count'] if count_result else 0
                print(f"表中记录总数: {count}")
                
                # 插入测试数据
                print("\n--- 插入测试数据 ---")
                test_task_id = f"debug_test_{int(time.time())}"
                test_data = {
                    'api_code': '1101',
                    'org_code': 'debug_org',
                    'test_time': datetime.now().isoformat()
                }
                
                cursor.execute("""
                    INSERT INTO async_task_status 
                    (task_id, status, data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    test_task_id,
                    'DEBUG',
                    json.dumps(test_data, ensure_ascii=False),
                    datetime.now(),
                    datetime.now()
                ))
                conn.commit()
                print(f"✓ 插入测试数据成功: {test_task_id}")
                
                # 查询刚插入的数据
                print("\n--- 查询测试数据 ---")
                cursor.execute("""
                    SELECT task_id, status, data, created_at, updated_at
                    FROM async_task_status
                    WHERE task_id = %s
                """, (test_task_id,))
                
                row = cursor.fetchone()
                if row:
                    print(f"✓ 查询成功:")
                    print(f"  任务ID: {row['task_id']}")
                    print(f"  状态: {row['status']}")
                    print(f"  数据: {row['data']}")
                    print(f"  创建时间: {row['created_at']}")
                    print(f"  更新时间: {row['updated_at']}")
                else:
                    print("✗ 查询失败，未找到数据")
                
                # 测试统计查询
                print("\n--- 测试统计查询 ---")
                start_time = datetime.now() - timedelta(hours=24)
                
                # 按状态统计
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM async_task_status
                    WHERE created_at >= %s
                    GROUP BY status
                """, (start_time,))
                
                status_results = cursor.fetchall()
                print(f"状态统计查询结果: {status_results}")
                
                status_counts = {row['status']: row['count'] for row in status_results}
                print(f"状态统计字典: {status_counts}")
                
                # 总数统计
                cursor.execute("""
                    SELECT COUNT(*) as total_count
                    FROM async_task_status
                    WHERE created_at >= %s
                """, (start_time,))
                
                total_result = cursor.fetchone()
                print(f"总数查询结果: {total_result}")
                total_count = total_result['total_count'] if total_result else 0
                print(f"总数: {total_count}")
                
                # 构建最终统计结果
                success_count = status_counts.get('SUCCESS', 0)
                failure_count = status_counts.get('FAILURE', 0)
                success_rate = (success_count / (success_count + failure_count) * 100) if (success_count + failure_count) > 0 else 0
                
                final_stats = {
                    'time_range_hours': 24,
                    'total_tasks': total_count,
                    'status_counts': status_counts,
                    'success_rate': round(success_rate, 2),
                    'generated_at': datetime.now().isoformat()
                }
                
                print(f"✓ 最终统计结果: {json.dumps(final_stats, indent=2, ensure_ascii=False)}")
                
                # 清理测试数据
                print("\n--- 清理测试数据 ---")
                cursor.execute("DELETE FROM async_task_status WHERE task_id = %s", (test_task_id,))
                conn.commit()
                print("✓ 清理完成")
                
            else:
                print("✗ 表不存在，需要先创建表")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始调试任务管理器数据库操作...")
    print("=" * 50)
    
    if debug_database_operations():
        print("\n✓ 调试完成，数据库操作正常")
        return 0
    else:
        print("\n✗ 调试失败，存在问题")
        return 1

if __name__ == '__main__':
    sys.exit(main())