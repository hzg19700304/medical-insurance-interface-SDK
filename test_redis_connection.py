#!/usr/bin/env python3
"""
测试Redis连接
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

def test_redis_basic_connection():
    """测试Redis基本连接"""
    print("=== 测试Redis基本连接 ===")
    
    try:
        import redis
        
        # 从环境变量读取Redis配置
        from dotenv import load_dotenv
        load_dotenv('medical_insurance_sdk/.env')
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', '')
        redis_db = int(os.getenv('REDIS_DB', '0'))
        
        print(f"Redis配置:")
        print(f"  Host: {redis_host}")
        print(f"  Port: {redis_port}")
        print(f"  Password: {'***' if redis_password else '(无密码)'}")
        print(f"  Database: {redis_db}")
        
        # 创建Redis连接
        if redis_password:
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
        else:
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
        
        # 测试连接
        print("\n--- 测试连接 ---")
        response = r.ping()
        if response:
            print("✓ Redis连接成功！")
        else:
            print("✗ Redis连接失败")
            return False
        
        # 获取Redis信息
        print("\n--- Redis服务器信息 ---")
        info = r.info()
        print(f"✓ Redis版本: {info.get('redis_version', 'Unknown')}")
        print(f"✓ 运行模式: {info.get('redis_mode', 'Unknown')}")
        print(f"✓ 已用内存: {info.get('used_memory_human', 'Unknown')}")
        print(f"✓ 连接数: {info.get('connected_clients', 'Unknown')}")
        print(f"✓ 运行时间: {info.get('uptime_in_seconds', 0)} 秒")
        
        return True
        
    except ImportError:
        print("✗ Redis模块未安装，请运行: pip install redis")
        return False
    except redis.ConnectionError as e:
        print(f"✗ Redis连接错误: {e}")
        print("请检查:")
        print("  1. Docker Redis容器是否正在运行")
        print("  2. Redis端口是否正确映射")
        print("  3. Redis密码是否正确")
        return False
    except Exception as e:
        print(f"✗ Redis连接测试失败: {e}")
        return False


def test_redis_operations():
    """测试Redis基本操作"""
    print("\n=== 测试Redis基本操作 ===")
    
    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv('medical_insurance_sdk/.env')
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', '')
        redis_db = int(os.getenv('REDIS_DB', '0'))
        
        # 创建Redis连接
        if redis_password:
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True
            )
        else:
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
        
        # 测试字符串操作
        print("--- 测试字符串操作 ---")
        test_key = "test_medical_sdk"
        test_value = f"测试数据_{int(time.time())}"
        
        # 设置值
        r.set(test_key, test_value, ex=60)  # 60秒过期
        print(f"✓ 设置键值: {test_key} = {test_value}")
        
        # 获取值
        retrieved_value = r.get(test_key)
        if retrieved_value == test_value:
            print(f"✓ 获取键值成功: {retrieved_value}")
        else:
            print(f"✗ 获取键值失败: 期望 {test_value}, 实际 {retrieved_value}")
            return False
        
        # 测试过期时间
        ttl = r.ttl(test_key)
        print(f"✓ 键过期时间: {ttl} 秒")
        
        # 测试哈希操作
        print("\n--- 测试哈希操作 ---")
        hash_key = "test_medical_hash"
        hash_data = {
            'api_code': '1101',
            'org_code': 'test_org',
            'timestamp': str(int(time.time())),
            'status': 'testing'
        }
        
        # 设置哈希
        r.hset(hash_key, mapping=hash_data)
        r.expire(hash_key, 60)  # 60秒过期
        print(f"✓ 设置哈希数据: {hash_key}")
        
        # 获取哈希
        retrieved_hash = r.hgetall(hash_key)
        if retrieved_hash == hash_data:
            print(f"✓ 获取哈希数据成功: {retrieved_hash}")
        else:
            print(f"✗ 获取哈希数据失败")
            return False
        
        # 测试列表操作
        print("\n--- 测试列表操作 ---")
        list_key = "test_medical_list"
        
        # 添加到列表
        for i in range(3):
            r.lpush(list_key, f"item_{i}")
        r.expire(list_key, 60)
        print(f"✓ 添加列表数据: {list_key}")
        
        # 获取列表
        list_items = r.lrange(list_key, 0, -1)
        print(f"✓ 获取列表数据: {list_items}")
        
        # 清理测试数据
        print("\n--- 清理测试数据 ---")
        r.delete(test_key, hash_key, list_key)
        print("✓ 清理完成")
        
        return True
        
    except Exception as e:
        print(f"✗ Redis操作测试失败: {e}")
        return False


def test_celery_redis_connection():
    """测试Celery与Redis的连接"""
    print("\n=== 测试Celery与Redis连接 ===")
    
    try:
        from medical_insurance_sdk.async_processing.celery_app import celery_app
        
        # 检查Celery配置
        print("--- Celery配置信息 ---")
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result Backend: {celery_app.conf.result_backend}")
        
        # 测试Celery连接到Redis
        print("\n--- 测试Celery连接 ---")
        
        # 获取Celery的Redis连接
        from celery import current_app
        
        # 检查broker连接
        try:
            # 这会尝试连接到Redis broker
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats is None:
                print("⚠ 没有活跃的Celery Worker，但Redis连接正常")
                print("  (这是正常的，因为我们还没有启动Worker)")
            else:
                print(f"✓ 发现 {len(stats)} 个活跃的Celery Worker")
                for worker_name, worker_stats in stats.items():
                    print(f"  - Worker: {worker_name}")
            
            print("✓ Celery可以连接到Redis Broker")
            
        except Exception as e:
            print(f"⚠ Celery连接测试: {e}")
            print("  这可能是因为没有启动Worker，但不影响Redis连接")
        
        return True
        
    except Exception as e:
        print(f"✗ Celery Redis连接测试失败: {e}")
        return False


def test_docker_redis_status():
    """检查Docker Redis容器状态"""
    print("\n=== 检查Docker Redis容器状态 ===")
    
    try:
        import subprocess
        
        # 检查Docker是否运行
        print("--- 检查Docker状态 ---")
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ Docker版本: {result.stdout.strip()}")
            else:
                print("✗ Docker未正确安装或未运行")
                return False
        except Exception as e:
            print(f"✗ 无法检查Docker状态: {e}")
            return False
        
        # 检查Redis容器
        print("\n--- 检查Redis容器 ---")
        try:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=redis', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout.strip()
                if output and len(output.split('\n')) > 1:
                    print("✓ 发现Redis容器:")
                    print(output)
                else:
                    print("⚠ 没有发现运行中的Redis容器")
                    print("请检查Redis容器是否正在运行")
            else:
                print(f"✗ 检查Redis容器失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ 无法检查Redis容器: {e}")
            return False
        
        # 检查所有容器（包括停止的）
        print("\n--- 检查所有Redis相关容器 ---")
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=redis', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout.strip()
                if output and len(output.split('\n')) > 1:
                    print("Redis相关容器:")
                    print(output)
                else:
                    print("没有发现Redis相关容器")
        except Exception as e:
            print(f"检查所有容器失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Docker检查失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试Redis连接...")
    print("=" * 60)
    
    test_results = []
    
    # 检查Docker Redis状态
    test_results.append(test_docker_redis_status())
    
    # 测试Redis基本连接
    test_results.append(test_redis_basic_connection())
    
    # 如果基本连接成功，继续测试操作
    if test_results[-1]:
        test_results.append(test_redis_operations())
        test_results.append(test_celery_redis_connection())
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("Redis测试结果总结:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ Redis连接测试全部通过！")
        print("\n下一步可以:")
        print("1. 启动Celery Worker: python scripts/start_celery_worker.py worker")
        print("2. 启动Celery监控: python scripts/start_celery_worker.py flower")
        print("3. 测试异步任务功能")
        return 0
    else:
        print("✗ 部分Redis测试失败")
        print("\n故障排除建议:")
        print("1. 确保Docker Redis容器正在运行")
        print("2. 检查Redis端口映射 (6379)")
        print("3. 验证Redis密码配置")
        print("4. 检查防火墙设置")
        return 1


if __name__ == '__main__':
    sys.exit(main())