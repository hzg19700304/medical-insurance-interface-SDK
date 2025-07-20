#!/usr/bin/env python3
"""
测试异步处理系统
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.async_processing import AsyncProcessor, TaskManager
from medical_insurance_sdk.config.manager import ConfigManager


def test_async_processor():
    """测试异步处理器"""
    print("=== 测试异步处理器 ===")
    
    try:
        # 创建异步处理器
        async_processor = AsyncProcessor()
        print("✓ 异步处理器创建成功")
        
        # 测试提交单个接口调用任务
        print("\n--- 测试单个接口调用 ---")
        task_id = async_processor.submit_interface_call(
            api_code='1101',
            input_data={
                'mdtrt_cert_type': '01',
                'mdtrt_cert_no': 'test123',
                'psn_cert_type': '01',
                'certno': '430123199001011234',
                'psn_name': '测试用户'
            },
            org_code='test_org',
            task_options={
                'max_retries': 2,
                'countdown': 5  # 5秒后执行
            }
        )
        print(f"✓ 任务提交成功，任务ID: {task_id}")
        
        # 获取任务状态
        status = async_processor.get_task_status(task_id)
        print(f"✓ 任务状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 测试批量接口调用
        print("\n--- 测试批量接口调用 ---")
        batch_requests = [
            {
                'api_code': '1101',
                'input_data': {
                    'mdtrt_cert_type': '01',
                    'mdtrt_cert_no': 'test001',
                    'psn_cert_type': '01',
                    'certno': '430123199001011001',
                    'psn_name': '测试用户1'
                },
                'org_code': 'test_org'
            },
            {
                'api_code': '1101',
                'input_data': {
                    'mdtrt_cert_type': '01',
                    'mdtrt_cert_no': 'test002',
                    'psn_cert_type': '01',
                    'certno': '430123199001011002',
                    'psn_name': '测试用户2'
                },
                'org_code': 'test_org'
            }
        ]
        
        batch_task_id = async_processor.submit_batch_interface_call(
            batch_requests=batch_requests,
            task_options={'countdown': 10}
        )
        print(f"✓ 批量任务提交成功，任务ID: {batch_task_id}")
        
        # 获取批量任务状态
        batch_status = async_processor.get_task_status(batch_task_id)
        print(f"✓ 批量任务状态: {json.dumps(batch_status, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 异步处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_manager():
    """测试任务管理器"""
    print("\n=== 测试任务管理器 ===")
    
    try:
        # 创建任务管理器
        task_manager = TaskManager()
        print("✓ 任务管理器创建成功")
        
        # 列出任务
        print("\n--- 列出任务 ---")
        tasks = task_manager.list_tasks(limit=5)
        print(f"✓ 获取到 {len(tasks)} 个任务")
        for task in tasks:
            print(f"  - 任务ID: {task['task_id']}, 状态: {task['status']}")
        
        # 获取统计信息
        print("\n--- 获取统计信息 ---")
        stats = task_manager.get_task_statistics(hours=24)
        print(f"✓ 统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 任务管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_connection():
    """测试Celery连接"""
    print("\n=== 测试Celery连接 ===")
    
    try:
        from medical_insurance_sdk.async_processing.celery_app import celery_app
        
        # 检查Celery应用配置
        print(f"✓ Celery应用名称: {celery_app.main}")
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result Backend: {celery_app.conf.result_backend}")
        
        # 检查连接
        inspect = celery_app.control.inspect()
        
        # 获取活跃任务（这会测试连接）
        try:
            active_tasks = inspect.active()
            if active_tasks is not None:
                print("✓ Celery连接正常")
                print(f"✓ 活跃Worker数量: {len(active_tasks)}")
            else:
                print("⚠ Celery连接正常，但没有活跃的Worker")
        except Exception as e:
            print(f"⚠ 无法连接到Celery Worker: {e}")
            print("  请确保Redis服务正在运行，并启动Celery Worker")
        
        return True
        
    except Exception as e:
        print(f"✗ Celery连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试异步处理系统...")
    print("=" * 50)
    
    # 设置环境变量
    os.environ.setdefault('REDIS_HOST', 'localhost')
    os.environ.setdefault('REDIS_PORT', '6379')
    os.environ.setdefault('REDIS_DB', '0')
    
    test_results = []
    
    # 测试Celery连接
    test_results.append(test_celery_connection())
    
    # 测试任务管理器
    test_results.append(test_task_manager())
    
    # 测试异步处理器
    test_results.append(test_async_processor())
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("测试结果总结:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())