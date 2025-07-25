#!/usr/bin/env python3
"""
简化版医保SDK压力测试
专注于核心功能测试，避免复杂的依赖问题
"""

import os
import sys
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.core.cache_manager import RedisCacheManager


def test_database_connection_pool():
    """测试数据库连接池性能"""
    print("=== 数据库连接池性能测试 ===")
    
    try:
        # 创建数据库管理器
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 测试参数
        concurrent_connections = 10
        operations_per_connection = 5
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        lock = threading.Lock()
        
        def db_worker(worker_id):
            """数据库工作线程"""
            nonlocal successful_requests, failed_requests
            
            for i in range(operations_per_connection):
                start_time = time.time()
                try:
                    # 执行简单查询
                    result = db_manager.execute_query("SELECT 1 as test_value")
                    
                    response_time = time.time() - start_time
                    with lock:
                        response_times.append(response_time)
                        successful_requests += 1
                    
                    time.sleep(0.01)  # 短暂休息
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    with lock:
                        response_times.append(response_time)
                        errors.append(f"Worker {worker_id}: {str(e)}")
                        failed_requests += 1
        
        # 执行并发测试
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            futures = [executor.submit(db_worker, i) for i in range(concurrent_connections)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"工作线程异常: {e}")
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {successful_requests}")
        print(f"失败请求: {failed_requests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总耗时: {total_time:.3f}秒")
        print(f"平均响应时间: {avg_response_time:.3f}秒")
        print(f"最小响应时间: {min_response_time:.3f}秒")
        print(f"最大响应时间: {max_response_time:.3f}秒")
        print(f"每秒请求数: {requests_per_second:.1f} RPS")
        
        if errors:
            print(f"错误示例: {errors[:3]}")
        
        # 获取连接池状态
        pool_status = db_manager.get_pool_status()
        print(f"连接池状态: {pool_status}")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"数据库连接池测试失败: {e}")
        return False


def test_cache_system():
    """测试缓存系统性能"""
    print("\n=== 缓存系统性能测试 ===")
    
    try:
        # 创建Redis缓存管理器
        cache_manager = RedisCacheManager(
            host='localhost',
            port=6379,
            db=1,
            default_ttl=300,
            key_prefix='stress_test:'
        )
        
        # 测试参数
        concurrent_operations = 10
        operations_per_worker = 20
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        lock = threading.Lock()
        
        # 预填充一些数据
        for i in range(50):
            cache_manager.set(f"test_key_{i}", f"test_value_{i}")
        
        def cache_worker(worker_id):
            """缓存工作线程"""
            nonlocal successful_requests, failed_requests
            
            for i in range(operations_per_worker):
                start_time = time.time()
                try:
                    # 随机选择操作
                    import random
                    operation = random.choice(['get', 'set', 'get', 'get'])  # 更多读操作
                    
                    if operation == 'get':
                        key = f"test_key_{random.randint(0, 99)}"
                        value = cache_manager.get(key)
                    else:  # set
                        key = f"test_key_{worker_id}_{i}"
                        value = f"test_value_{worker_id}_{i}"
                        cache_manager.set(key, value)
                    
                    response_time = time.time() - start_time
                    with lock:
                        response_times.append(response_time)
                        successful_requests += 1
                    
                    time.sleep(0.001)  # 很短的休息
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    with lock:
                        response_times.append(response_time)
                        errors.append(f"Worker {worker_id}: {str(e)}")
                        failed_requests += 1
        
        # 执行并发测试
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_operations) as executor:
            futures = [executor.submit(cache_worker, i) for i in range(concurrent_operations)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"工作线程异常: {e}")
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {successful_requests}")
        print(f"失败请求: {failed_requests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总耗时: {total_time:.3f}秒")
        print(f"平均响应时间: {avg_response_time:.3f}秒")
        print(f"最小响应时间: {min_response_time:.3f}秒")
        print(f"最大响应时间: {max_response_time:.3f}秒")
        print(f"每秒请求数: {requests_per_second:.1f} RPS")
        
        if errors:
            print(f"错误示例: {errors[:3]}")
        
        # 获取缓存统计
        cache_stats = cache_manager.get_stats()
        print(f"缓存命中率: {cache_stats.get('hit_rate', 0):.1f}%")
        print(f"缓存健康状态: {cache_stats.get('is_healthy', False)}")
        
        # 清理测试数据
        cache_manager.clear_all()
        cache_manager.close()
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"缓存系统测试失败: {e}")
        return False


def test_concurrent_database_operations():
    """测试并发数据库操作"""
    print("\n=== 并发数据库操作测试 ===")
    
    try:
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 测试参数
        concurrent_users = 15
        operations_per_user = 3
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        lock = threading.Lock()
        
        # 测试查询
        test_queries = [
            ("SELECT COUNT(*) as count FROM medical_interface_config", ()),
            ("SELECT api_code, api_name FROM medical_interface_config LIMIT 5", ()),
            ("SELECT org_code, org_name FROM medical_organization_config LIMIT 3", ()),
        ]
        
        def user_worker(user_id):
            """用户工作线程"""
            nonlocal successful_requests, failed_requests
            
            for op_id in range(operations_per_user):
                start_time = time.time()
                try:
                    # 随机选择查询
                    import random
                    query, params = random.choice(test_queries)
                    
                    result = db_manager.execute_query(query, params)
                    
                    response_time = time.time() - start_time
                    with lock:
                        response_times.append(response_time)
                        successful_requests += 1
                    
                    time.sleep(0.05)  # 模拟用户思考时间
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    with lock:
                        response_times.append(response_time)
                        errors.append(f"User {user_id}, Op {op_id}: {str(e)}")
                        failed_requests += 1
        
        # 执行并发测试
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_worker, i) for i in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"用户工作线程异常: {e}")
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
        else:
            avg_response_time = p95_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {successful_requests}")
        print(f"失败请求: {failed_requests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总耗时: {total_time:.3f}秒")
        print(f"平均响应时间: {avg_response_time:.3f}秒")
        print(f"P95响应时间: {p95_response_time:.3f}秒")
        print(f"每秒请求数: {requests_per_second:.1f} RPS")
        
        if errors:
            print(f"错误示例: {errors[:3]}")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"并发数据库操作测试失败: {e}")
        return False


def main():
    """主函数"""
    print("开始执行医保SDK压力测试")
    print("=" * 50)
    
    results = []
    
    # 1. 数据库连接池性能测试
    db_result = test_database_connection_pool()
    results.append(("数据库连接池", db_result))
    
    # 2. 缓存系统性能测试
    cache_result = test_cache_system()
    results.append(("缓存系统", cache_result))
    
    # 3. 并发数据库操作测试
    concurrent_result = test_concurrent_database_operations()
    results.append(("并发数据库操作", concurrent_result))
    
    # 总结
    print("\n" + "=" * 50)
    print("压力测试总结")
    print("=" * 50)
    
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n整体通过率: {passed_tests}/{total_tests} ({overall_success_rate:.1f}%)")
    
    if overall_success_rate >= 80:
        print("🎉 压力测试整体通过！系统性能良好")
        return True
    else:
        print("💥 压力测试未完全通过，需要优化系统性能")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)