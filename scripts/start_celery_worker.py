#!/usr/bin/env python3
"""
启动Celery Worker的脚本
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_celery_worker():
    """启动Celery Worker"""
    
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(project_root))
    
    # Celery worker命令
    cmd = [
        'celery',
        '-A', 'medical_insurance_sdk.async_processing.celery_app',
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=default,medical_interface,medical_batch,maintenance'
    ]
    
    print("Starting Celery Worker...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    print("-" * 50)
    
    try:
        # 启动Celery worker
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\nCelery Worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery Worker: {e}")
        sys.exit(1)

def start_celery_beat():
    """启动Celery Beat调度器"""
    
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(project_root))
    
    # Celery beat命令
    cmd = [
        'celery',
        '-A', 'medical_insurance_sdk.async_processing.celery_app',
        'beat',
        '--loglevel=info'
    ]
    
    print("Starting Celery Beat...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    print("-" * 50)
    
    try:
        # 启动Celery beat
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\nCelery Beat stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery Beat: {e}")
        sys.exit(1)

def start_celery_flower():
    """启动Celery Flower监控"""
    
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(project_root))
    
    # Celery flower命令
    cmd = [
        'celery',
        '-A', 'medical_insurance_sdk.async_processing.celery_app',
        'flower',
        '--port=5555'
    ]
    
    print("Starting Celery Flower...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    print("Flower will be available at: http://localhost:5555")
    print("-" * 50)
    
    try:
        # 启动Celery flower
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\nCelery Flower stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery Flower: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Start Celery services')
    parser.add_argument('service', choices=['worker', 'beat', 'flower'], 
                       help='Service to start')
    
    args = parser.parse_args()
    
    if args.service == 'worker':
        start_celery_worker()
    elif args.service == 'beat':
        start_celery_beat()
    elif args.service == 'flower':
        start_celery_flower()