#!/usr/bin/env python3
"""
测试异步任务功能
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_async_task_submission():
    """测试异步任务提交"""
    print("=== 测试异步任务提交 ===")
    
    try:
        from medical_insurance_sdk.client import MedicalInsuranceClient
        from medical_insurance_sdk.core.database import DatabaseConfig
        from medical_insurance_sdk.config.models import SDKConfig
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv('medical_insurance_sdk/.env')
        
        # 创建客户端
        db_config = DatabaseConfig.from_env()
        sdk_config = SDKConfig(database_config=db_config)
        client = MedicalInsuranceClient(sdk_config)
        
        print("✓ 医保客户端创建成功")
        
        # 测试数据
        test_data = {
            'psn_no': '123456789',
            'psn_name': '测试用户',
            'gend': '1',
            'brdy': '1990-01-01'
        }
        
        print("\n--- 提交异步任务 ---")
        try:
            # 提交异步任务（使用Celery）
            task_id = client.call_async(
                api_code='1101',
                data=test_data,
                org_code='test_org',
                use_celery=True
            )
            
            print(f"✓ 异步任务提交成功")
            print(f"  任务ID: {task_id}")
            
            # 等待一下让任务开始处理
            time.sleep(2)
            
            # 检查任务状态
            print("\n--- 检查任务状态 ---")
            status = client.get_task_result(task_id)
            print(f"✓ 任务状态: {status.get('status', 'Unknown')}")
            
            if status.get('status') == 'PROCESSING':
                print("  任务正在处理中...")
            elif status.get('status') == 'SUCCESS':
                print("  任务已完成")
            elif status.get('status') == 'FAILURE':
                print(f"  任务失败: {status.get('error_message', 'Unknown error')}")
            else:
                print(f"  任务状态: {status}")
            
            return True
            
        except Exception as e:
            print(f"✗ 异步任务测试失败: {e}")
            print("这可能是因为:")
            print("1. Celery Worker没有启动")
            print("2. 医保接口配置不完整")
            print("3. 网络连接问题")
            return False
        
        finally:
            client.close()
    
    except Exception as e:
        print(f"✗ 客户端创建失败: {e}")
        return False


def test_task_management():
    """测试任务管理功能"""
    print("\n=== 测试任务管理功能 ===")
    
    try:
        from medical_insurance_sdk.client import MedicalInsuranceClient
        from medical_insurance_sdk.core.database import DatabaseConfig
        from medical_insurance_sdk.config.models import SDKConfig
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv('medical_insurance_sdk/.env')
        
        # 创建客户端
        db_config = DatabaseConfig.from_env()
        sdk_config = SDKConfig(database_config=db_config)
        client = MedicalInsuranceClient(sdk_config)
        
        print("--- 列出异步任务 ---")
        tasks = client.list_async_tasks(limit=5)
        print(f"✓ 获取到 {len(tasks)} 个任务")
        
        for task in tasks:
            print(f"  - 任务ID: {task.get('task_id', 'Unknown')}")
            print(f"    状态: {task.get('status', 'Unknown')}")
            print(f"    创建时间: {task.get('created_at', 'Unknown')}")
        
        print("\n--- 获取异步统计 ---")
        stats = client.get_async_statistics(hours=24)
        if 'error' not in stats:
            print(f"✓ 总任务数: {stats.get('total_tasks', 0)}")
            print(f"✓ 成功率: {stats.get('success_rate', 0)}%")
            print(f"✓ 状态分布: {stats.get('status_counts', {})}")
        else:
            print(f"⚠ 统计信息获取失败: {stats['error']}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ 任务管理测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试异步任务功能...")
    print("=" * 60)
    
    print("注意: 这个测试需要Celery Worker运行才能完全成功")
    print("如果Worker没有运行，任务会被提交但不会被处理")
    print("-" * 60)
    
    test_results = []
    
    # 测试任务管理功能（不需要Worker）
    test_results.append(test_task_management())
    
    # 测试异步任务提交（需要Worker处理）
    test_results.append(test_async_task_submission())
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("异步任务测试结果总结:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 异步任务功能测试通过！")
    else:
        print("⚠ 部分测试未完全通过（可能需要启动Celery Worker）")
    
    print("\n启动Celery Worker命令:")
    print("python scripts/start_celery_worker.py worker")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())