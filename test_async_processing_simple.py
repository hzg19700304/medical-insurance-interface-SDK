#!/usr/bin/env python3
"""
简化的异步处理系统测试（不依赖Redis）
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.async_processing import TaskManager
from medical_insurance_sdk.config.manager import ConfigManager
from medical_insurance_sdk.core.database import DatabaseConfig


def test_task_manager_database():
    """测试任务管理器的数据库功能"""
    print("=== 测试任务管理器数据库功能 ===")
    
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv('medical_insurance_sdk/.env')
        
        # 创建任务管理器
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        task_manager = TaskManager(config_manager)
        print("✓ 任务管理器创建成功")
        
        # 测试数据库连接
        print("\n--- 测试数据库操作 ---")
        
        # 插入测试任务状态
        test_task_id = "test_task_123"
        test_data = {
            'api_code': '1101',
            'org_code': 'test_org',
            'status': 'testing',
            'created_at': time.time()
        }
        
        task_manager._update_task_status_in_db(test_task_id, 'TESTING', test_data)
        print(f"✓ 插入测试任务状态: {test_task_id}")
        
        # 获取任务状态
        status = task_manager._get_task_status_from_db(test_task_id)
        if status:
            print(f"✓ 获取任务状态成功: {status['status']}")
            print(f"  任务数据: {json.dumps(status['data'], indent=2, ensure_ascii=False)}")
        else:
            print("✗ 获取任务状态失败")
            return False
        
        # 列出任务
        tasks = task_manager.list_tasks(limit=5)
        print(f"✓ 列出任务成功，获取到 {len(tasks)} 个任务")
        for task in tasks:
            print(f"  - 任务ID: {task['task_id']}, 状态: {task['status']}")
        
        # 获取统计信息
        stats = task_manager.get_task_statistics(hours=24)
        if 'error' not in stats:
            print(f"✓ 获取统计信息成功")
            print(f"  总任务数: {stats.get('total_tasks', 0)}")
            print(f"  状态统计: {stats.get('status_counts', {})}")
        else:
            print(f"⚠ 获取统计信息有错误: {stats['error']}")
        
        # 清理测试数据
        try:
            with task_manager.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM async_task_status WHERE task_id = %s", (test_task_id,))
                conn.commit()
            print("✓ 清理测试数据成功")
        except Exception as e:
            print(f"⚠ 清理测试数据失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 任务管理器数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_config():
    """测试Celery配置（不连接Redis）"""
    print("\n=== 测试Celery配置 ===")
    
    try:
        from medical_insurance_sdk.async_processing.celery_app import celery_app
        
        # 检查Celery应用配置
        print(f"✓ Celery应用名称: {celery_app.main}")
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result Backend: {celery_app.conf.result_backend}")
        print(f"✓ 任务序列化: {celery_app.conf.task_serializer}")
        print(f"✓ 时区: {celery_app.conf.timezone}")
        
        # 检查任务路由
        task_routes = celery_app.conf.task_routes
        print(f"✓ 任务路由配置: {len(task_routes)} 个路由")
        for task_name, route_config in task_routes.items():
            print(f"  - {task_name}: {route_config}")
        
        # 检查队列配置
        queues = celery_app.conf.task_queues
        print(f"✓ 队列配置: {len(queues)} 个队列")
        for queue in queues:
            print(f"  - {queue.name}")
        
        # 检查定时任务配置
        beat_schedule = celery_app.conf.beat_schedule
        print(f"✓ 定时任务配置: {len(beat_schedule)} 个任务")
        for task_name, schedule_config in beat_schedule.items():
            print(f"  - {task_name}: {schedule_config['schedule']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Celery配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_async_processor_creation():
    """测试异步处理器创建（不执行任务）"""
    print("\n=== 测试异步处理器创建 ===")
    
    try:
        from medical_insurance_sdk.async_processing import AsyncProcessor
        
        # 创建异步处理器
        async_processor = AsyncProcessor()
        print("✓ 异步处理器创建成功")
        
        # 检查组件
        print(f"✓ 配置管理器: {type(async_processor.config_manager).__name__}")
        print(f"✓ 任务管理器: {type(async_processor.task_manager).__name__}")
        
        # 测试不需要Redis的方法
        tasks = async_processor.list_tasks(limit=3)
        print(f"✓ 列出任务功能正常，获取到 {len(tasks)} 个任务")
        
        stats = async_processor.get_statistics(hours=1)
        if 'error' not in stats:
            print(f"✓ 统计功能正常，总任务数: {stats.get('total_tasks', 0)}")
        else:
            print(f"⚠ 统计功能有错误: {stats['error']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 异步处理器创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_client_integration():
    """测试客户端集成"""
    print("\n=== 测试客户端集成 ===")
    
    try:
        from medical_insurance_sdk.client import MedicalInsuranceClient
        from medical_insurance_sdk.core.database import DatabaseConfig
        from medical_insurance_sdk.config.models import SDKConfig
        
        # 创建客户端
        db_config = DatabaseConfig.from_env()
        sdk_config = SDKConfig(database_config=db_config)
        client = MedicalInsuranceClient(sdk_config)
        print("✓ 医保客户端创建成功")
        
        # 检查异步处理器
        print(f"✓ 异步处理器: {type(client.async_processor).__name__}")
        
        # 测试不需要Redis的方法
        tasks = client.list_async_tasks(limit=3)
        print(f"✓ 客户端异步任务列表功能正常，获取到 {len(tasks)} 个任务")
        
        stats = client.get_async_statistics(hours=1)
        if 'error' not in stats:
            print(f"✓ 客户端异步统计功能正常，总任务数: {stats.get('total_tasks', 0)}")
        else:
            print(f"⚠ 客户端异步统计有错误: {stats['error']}")
        
        # 关闭客户端
        client.close()
        print("✓ 客户端关闭成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 客户端集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试异步处理系统（简化版）...")
    print("=" * 60)
    
    # 设置环境变量
    os.environ.setdefault('REDIS_HOST', 'localhost')
    os.environ.setdefault('REDIS_PORT', '6379')
    os.environ.setdefault('REDIS_DB', '0')
    
    test_results = []
    
    # 测试任务管理器数据库功能
    test_results.append(test_task_manager_database())
    
    # 测试Celery配置
    test_results.append(test_celery_config())
    
    # 测试异步处理器创建
    test_results.append(test_async_processor_creation())
    
    # 测试客户端集成
    test_results.append(test_client_integration())
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("测试结果总结:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！异步处理系统实现完成")
        print("\n注意事项:")
        print("- 要使用完整的异步功能，需要启动Redis服务")
        print("- 要执行异步任务，需要启动Celery Worker")
        print("- 使用 'python scripts/start_celery_worker.py worker' 启动Worker")
        print("- 使用 'python scripts/start_celery_worker.py flower' 启动监控界面")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())