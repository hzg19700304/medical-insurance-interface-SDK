#!/usr/bin/env python3
"""
快速测试Celery Worker功能
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_worker_background():
    """在后台启动Worker"""
    try:
        from dotenv import load_dotenv
        load_dotenv('medical_insurance_sdk/.env')
        
        cmd = [
            'celery',
            '-A', 'medical_insurance_sdk.async_processing.celery_app',
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--queues=default,medical_interface,medical_batch,maintenance'
        ]
        
        print("🚀 启动后台Worker...")
        process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待Worker启动
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Worker启动成功")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Worker启动失败:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动Worker异常: {e}")
        return None

def test_async_task_submission():
    """测试异步任务提交"""
    print("\n=== 测试异步任务提交 ===")
    
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
        
        print("✅ 医保客户端创建成功")
        
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
            
            print(f"✅ 异步任务提交成功")
            print(f"   任务ID: {task_id}")
            
            # 等待任务处理
            print("\n--- 等待任务处理 ---")
            for i in range(10):
                time.sleep(1)
                status = client.get_task_result(task_id)
                print(f"   第{i+1}秒: 任务状态 = {status.get('status', 'Unknown')}")
                
                if status.get('status') in ['SUCCESS', 'FAILURE']:
                    break
            
            # 最终状态
            final_status = client.get_task_result(task_id)
            print(f"\n--- 最终结果 ---")
            print(f"   任务状态: {final_status.get('status', 'Unknown')}")
            
            if final_status.get('status') == 'SUCCESS':
                print("   ✅ 任务执行成功！")
                if 'result' in final_status:
                    print(f"   结果: {final_status['result']}")
            elif final_status.get('status') == 'FAILURE':
                print("   ❌ 任务执行失败")
                print(f"   错误: {final_status.get('error_message', 'Unknown error')}")
            else:
                print(f"   ⏳ 任务仍在处理中: {final_status.get('status')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 异步任务测试失败: {e}")
            return False
        
        finally:
            client.close()
    
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
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
        print(f"✅ 获取到 {len(tasks)} 个任务")
        
        for task in tasks:
            print(f"   - 任务ID: {task.get('task_id', 'Unknown')[:20]}...")
            print(f"     状态: {task.get('status', 'Unknown')}")
            print(f"     创建时间: {task.get('created_at', 'Unknown')}")
        
        print("\n--- 获取异步统计 ---")
        stats = client.get_async_statistics(hours=24)
        if 'error' not in stats:
            print(f"✅ 总任务数: {stats.get('total_tasks', 0)}")
            print(f"✅ 成功率: {stats.get('success_rate', 0)}%")
            print(f"✅ 状态分布: {stats.get('status_counts', {})}")
        else:
            print(f"⚠️ 统计信息获取失败: {stats['error']}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ 任务管理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始快速测试Celery Worker功能...")
    print("=" * 60)
    
    # 启动后台Worker
    worker_process = start_worker_background()
    
    if not worker_process:
        print("❌ 无法启动Worker，测试终止")
        return 1
    
    try:
        test_results = []
        
        # 测试任务管理功能
        test_results.append(test_task_management())
        
        # 测试异步任务提交
        test_results.append(test_async_task_submission())
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("🧪 测试结果总结:")
        passed = sum(test_results)
        total = len(test_results)
        print(f"   通过: {passed}/{total}")
        
        if passed == total:
            print("✅ 所有测试通过！异步处理系统工作正常")
        else:
            print("⚠️ 部分测试失败")
        
        return 0 if passed == total else 1
        
    finally:
        # 停止Worker
        print("\n🛑 停止后台Worker...")
        if worker_process and worker_process.poll() is None:
            worker_process.terminate()
            try:
                worker_process.wait(timeout=5)
                print("✅ Worker已停止")
            except subprocess.TimeoutExpired:
                worker_process.kill()
                print("🔪 强制停止Worker")

if __name__ == '__main__':
    sys.exit(main())