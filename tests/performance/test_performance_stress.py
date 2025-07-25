"""
医保SDK压力测试模块
实现并发接口调用测试、数据库连接池性能测试、缓存系统效果测试
"""

import asyncio
import concurrent.futures
import logging
import random
import statistics
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from medical_insurance_sdk.client import MedicalInsuranceClient
from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.core.cache_manager import RedisCacheManager, HybridCacheManager
from medical_insurance_sdk.core.connection_pool_manager import (
    ConnectionPoolManager, MySQLPoolConfig, RedisPoolConfig
)
from medical_insurance_sdk.config.models import SDKConfig
from medical_insurance_sdk.exceptions import MedicalInsuranceException


@dataclass
class StressTestResult:
    """压力测试结果"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'test_name': self.test_name,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'total_time': round(self.total_time, 3),
            'average_response_time': round(self.average_response_time, 3),
            'min_response_time': round(self.min_response_time, 3),
            'max_response_time': round(self.max_response_time, 3),
            'p95_response_time': round(self.p95_response_time, 3),
            'p99_response_time': round(self.p99_response_time, 3),
            'requests_per_second': round(self.requests_per_second, 2),
            'error_rate': round(self.error_rate * 100, 2),
            'error_count': len(self.errors),
            'unique_errors': len(set(self.errors))
        }


class StressTestRunner:
    """压力测试执行器"""
    
    def __init__(self, client: MedicalInsuranceClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
        
        # 测试数据 - 使用数据库中实际存在的配置格式
        self.test_data = {
            '1101': {  # 人员信息获取 - 使用简化的测试数据
                'psn_no': '430123199001011234'
            },
            '2201': {  # 门诊结算 - 使用简化的测试数据
                'mdtrt_id': 'TEST20240101001',
                'psn_no': '430123199001011234',
                'chrg_bchno': 'BATCH001'
            }
        }
        
        self.org_code = 'TEST_ORG'
    
    def run_concurrent_interface_test(self, 
                                    api_code: str,
                                    concurrent_users: int = 50,
                                    requests_per_user: int = 10,
                                    ramp_up_time: int = 5) -> StressTestResult:
        """
        并发接口调用测试
        
        Args:
            api_code: 接口编码
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数
            ramp_up_time: 启动时间（秒）
        """
        self.logger.info(f"开始并发接口测试: {api_code}, 并发用户: {concurrent_users}, 每用户请求: {requests_per_user}")
        
        total_requests = concurrent_users * requests_per_user
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        # 用于同步的锁
        lock = threading.Lock()
        
        def user_worker(user_id: int, delay: float):
            """单个用户的工作函数"""
            nonlocal successful_requests, failed_requests
            
            # 启动延迟，模拟用户逐渐加入
            time.sleep(delay)
            
            for request_id in range(requests_per_user):
                start_time = time.time()
                try:
                    # 添加随机变化以模拟真实场景
                    test_data = self.test_data[api_code].copy()
                    if api_code == '1101':
                        test_data['psn_no'] = f"43012319900101{user_id:04d}"
                    elif api_code == '2201':
                        test_data['mdtrt_id'] = f"TEST{datetime.now().strftime('%Y%m%d')}{user_id:03d}{request_id:03d}"
                        test_data['psn_no'] = f"43012319900101{user_id:04d}"
                    
                    result = self.client.call(api_code, test_data, self.org_code)
                    
                    response_time = time.time() - start_time
                    
                    with lock:
                        response_times.append(response_time)
                        successful_requests += 1
                    
                    # 模拟用户思考时间
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    error_msg = f"User {user_id}, Request {request_id}: {str(e)}"
                    
                    with lock:
                        response_times.append(response_time)
                        errors.append(error_msg)
                        failed_requests += 1
                    
                    self.logger.warning(f"请求失败: {error_msg}")
        
        # 启动并发测试
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for user_id in range(concurrent_users):
                # 计算启动延迟，实现渐进式加载
                delay = (user_id / concurrent_users) * ramp_up_time
                future = executor.submit(user_worker, user_id, delay)
                futures.append(future)
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"用户工作线程异常: {e}")
        
        total_time = time.time() - start_time
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        result = StressTestResult(
            test_name=f"并发接口测试_{api_code}",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:100]  # 只保留前100个错误
        )
        
        self.logger.info(f"并发接口测试完成: {result.to_dict()}")
        return result
    
    def run_database_connection_pool_test(self, 
                                        concurrent_connections: int = 30,
                                        operations_per_connection: int = 20,
                                        test_duration: int = 60) -> StressTestResult:
        """
        数据库连接池性能测试
        
        Args:
            concurrent_connections: 并发连接数
            operations_per_connection: 每个连接的操作数
            test_duration: 测试持续时间（秒）
        """
        self.logger.info(f"开始数据库连接池测试: 并发连接: {concurrent_connections}, 每连接操作: {operations_per_connection}")
        
        db_manager = self.client.sdk.config_manager.db_manager
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        lock = threading.Lock()
        
        # 测试SQL语句
        test_queries = [
            ("SELECT COUNT(*) as count FROM medical_interface_config", ()),
            ("SELECT * FROM medical_interface_config WHERE api_code = %s", ('1101',)),
            ("SELECT * FROM medical_organization_config WHERE org_code = %s", ('TEST_ORG',)),
            ("SELECT COUNT(*) as count FROM business_operation_logs WHERE operation_time >= %s", 
             (datetime.now() - timedelta(days=1),)),
        ]
        
        def connection_worker(worker_id: int):
            """数据库连接工作函数"""
            nonlocal successful_requests, failed_requests
            
            end_time = time.time() + test_duration
            operation_count = 0
            
            while time.time() < end_time and operation_count < operations_per_connection:
                start_time = time.time()
                try:
                    # 随机选择一个查询
                    query, params = random.choice(test_queries)
                    
                    # 执行查询
                    result = db_manager.execute_query(query, params)
                    
                    response_time = time.time() - start_time
                    
                    with lock:
                        response_times.append(response_time)
                        successful_requests += 1
                    
                    operation_count += 1
                    
                    # 短暂休息
                    time.sleep(random.uniform(0.01, 0.1))
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    error_msg = f"Worker {worker_id}, Operation {operation_count}: {str(e)}"
                    
                    with lock:
                        response_times.append(response_time)
                        errors.append(error_msg)
                        failed_requests += 1
                    
                    operation_count += 1
        
        # 启动并发测试
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            futures = [executor.submit(connection_worker, i) for i in range(concurrent_connections)]
            
            # 等待所有任务完成或超时
            for future in as_completed(futures, timeout=test_duration + 10):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"数据库连接工作线程异常: {e}")
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        result = StressTestResult(
            test_name="数据库连接池性能测试",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:100]
        )
        
        self.logger.info(f"数据库连接池测试完成: {result.to_dict()}")
        return result
    
    def run_cache_system_test(self, 
                            concurrent_operations: int = 50,
                            operations_per_worker: int = 100,
                            cache_hit_ratio: float = 0.7) -> StressTestResult:
        """
        缓存系统效果测试
        
        Args:
            concurrent_operations: 并发操作数
            operations_per_worker: 每个工作线程的操作数
            cache_hit_ratio: 期望的缓存命中率
        """
        self.logger.info(f"开始缓存系统测试: 并发操作: {concurrent_operations}, 每工作线程操作: {operations_per_worker}")
        
        # 创建测试用的缓存管理器
        try:
            cache_manager = RedisCacheManager(
                host='localhost',
                port=6379,
                db=1,  # 使用测试数据库
                default_ttl=300,
                key_prefix='stress_test:'
            )
        except Exception as e:
            self.logger.warning(f"Redis不可用，跳过缓存测试: {e}")
            return StressTestResult(
                test_name="缓存系统测试",
                total_requests=0,
                successful_requests=0,
                failed_requests=1,
                total_time=0,
                average_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                error_rate=1.0,
                errors=["Redis不可用"]
            )
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        cache_hits = 0
        cache_misses = 0
        lock = threading.Lock()
        
        # 预填充缓存数据
        cache_keys = [f"test_key_{i}" for i in range(1000)]
        cache_values = [f"test_value_{i}" for i in range(1000)]
        
        # 预填充部分数据以模拟缓存命中
        prefill_count = int(len(cache_keys) * cache_hit_ratio)
        for i in range(prefill_count):
            cache_manager.set(cache_keys[i], cache_values[i])
        
        def cache_worker(worker_id: int):
            """缓存操作工作函数"""
            nonlocal successful_requests, failed_requests, cache_hits, cache_misses
            
            for operation_id in range(operations_per_worker):
                start_time = time.time()
                try:
                    # 随机选择操作类型
                    operation_type = random.choices(
                        ['get', 'set', 'delete'],
                        weights=[70, 25, 5]  # 70%读取，25%写入，5%删除
                    )[0]
                    
                    key_index = random.randint(0, len(cache_keys) - 1)
                    key = cache_keys[key_index]
                    
                    if operation_type == 'get':
                        value = cache_manager.get(key)
                        if value is not None:
                            with lock:
                                cache_hits += 1
                        else:
                            with lock:
                                cache_misses += 1
                    
                    elif operation_type == 'set':
                        value = f"updated_value_{worker_id}_{operation_id}"
                        cache_manager.set(key, value, ttl=random.randint(60, 600))
                    
                    elif operation_type == 'delete':
                        cache_manager.delete(key)
                    
                    response_time = time.time() - start_time
                    
                    with lock:
                        response_times.append(response_time)
                        successful_requests += 1
                    
                    # 短暂休息
                    time.sleep(random.uniform(0.001, 0.01))
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    error_msg = f"Worker {worker_id}, Operation {operation_id}: {str(e)}"
                    
                    with lock:
                        response_times.append(response_time)
                        errors.append(error_msg)
                        failed_requests += 1
        
        # 启动并发测试
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_operations) as executor:
            futures = [executor.submit(cache_worker, i) for i in range(concurrent_operations)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"缓存工作线程异常: {e}")
        
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests
        
        # 获取缓存统计信息
        cache_stats = cache_manager.get_stats()
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        # 清理测试数据
        cache_manager.clear_all()
        cache_manager.close()
        
        result = StressTestResult(
            test_name="缓存系统测试",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:100]
        )
        
        # 添加缓存特定的统计信息
        result_dict = result.to_dict()
        result_dict.update({
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'cache_hit_rate': cache_hits / (cache_hits + cache_misses) * 100 if (cache_hits + cache_misses) > 0 else 0,
            'cache_stats': cache_stats
        })
        
        self.logger.info(f"缓存系统测试完成: {result_dict}")
        return result


class StressTestSuite:
    """压力测试套件"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results: List[StressTestResult] = []
    
    def run_all_tests(self, client: MedicalInsuranceClient) -> Dict[str, Any]:
        """运行所有压力测试"""
        self.logger.info("开始执行完整的压力测试套件")
        
        runner = StressTestRunner(client)
        
        # 1. 并发接口调用测试
        self.logger.info("=== 1. 并发接口调用测试 ===")
        
        # 测试1101接口
        result_1101 = runner.run_concurrent_interface_test(
            api_code='1101',
            concurrent_users=20,
            requests_per_user=5,
            ramp_up_time=3
        )
        self.results.append(result_1101)
        
        # 测试2201接口
        result_2201 = runner.run_concurrent_interface_test(
            api_code='2201',
            concurrent_users=15,
            requests_per_user=3,
            ramp_up_time=2
        )
        self.results.append(result_2201)
        
        # 2. 数据库连接池性能测试
        self.logger.info("=== 2. 数据库连接池性能测试 ===")
        
        db_result = runner.run_database_connection_pool_test(
            concurrent_connections=25,
            operations_per_connection=15,
            test_duration=30
        )
        self.results.append(db_result)
        
        # 3. 缓存系统效果测试
        self.logger.info("=== 3. 缓存系统效果测试 ===")
        
        cache_result = runner.run_cache_system_test(
            concurrent_operations=30,
            operations_per_worker=50,
            cache_hit_ratio=0.7
        )
        self.results.append(cache_result)
        
        # 生成测试报告
        report = self.generate_test_report()
        
        self.logger.info("压力测试套件执行完成")
        return report
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        report = {
            'test_summary': {
                'total_tests': len(self.results),
                'test_time': datetime.now().isoformat(),
                'overall_status': 'PASSED'
            },
            'test_results': [],
            'performance_analysis': {},
            'recommendations': []
        }
        
        total_requests = 0
        total_successful = 0
        total_failed = 0
        
        for result in self.results:
            result_dict = result.to_dict()
            report['test_results'].append(result_dict)
            
            total_requests += result.total_requests
            total_successful += result.successful_requests
            total_failed += result.failed_requests
            
            # 检查是否有测试失败
            if result.error_rate > 0.1:  # 错误率超过10%
                report['test_summary']['overall_status'] = 'FAILED'
        
        # 性能分析
        report['performance_analysis'] = {
            'total_requests': total_requests,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'overall_error_rate': (total_failed / total_requests * 100) if total_requests > 0 else 0,
            'average_rps': sum(r.requests_per_second for r in self.results) / len(self.results) if self.results else 0
        }
        
        # 生成建议
        self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]):
        """生成性能优化建议"""
        recommendations = []
        
        # 分析错误率
        overall_error_rate = report['performance_analysis']['overall_error_rate']
        if overall_error_rate > 5:
            recommendations.append(f"整体错误率较高({overall_error_rate:.1f}%)，建议检查系统稳定性")
        
        # 分析各个测试结果
        for result_dict in report['test_results']:
            test_name = result_dict['test_name']
            error_rate = result_dict['error_rate']
            avg_response_time = result_dict['average_response_time']
            rps = result_dict['requests_per_second']
            
            if error_rate > 10:
                recommendations.append(f"{test_name}: 错误率过高({error_rate:.1f}%)，需要优化")
            
            if avg_response_time > 2.0:
                recommendations.append(f"{test_name}: 平均响应时间过长({avg_response_time:.2f}s)，建议优化")
            
            if '接口测试' in test_name and rps < 10:
                recommendations.append(f"{test_name}: 吞吐量较低({rps:.1f} RPS)，建议优化接口性能")
            
            if '数据库' in test_name and rps < 50:
                recommendations.append(f"{test_name}: 数据库操作性能较低，建议优化连接池配置")
            
            if '缓存' in test_name and rps < 100:
                recommendations.append(f"{test_name}: 缓存操作性能较低，建议检查Redis配置")
        
        # 如果没有问题，给出正面反馈
        if not recommendations:
            recommendations.append("所有测试表现良好，系统性能符合预期")
        
        report['recommendations'] = recommendations


# 测试用例
class TestStressPerformance:
    """压力测试用例类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        try:
            db_config = DatabaseConfig.from_env()
            sdk_config = SDKConfig(database_config=db_config)
            return MedicalInsuranceClient(sdk_config)
        except Exception as e:
            pytest.skip(f"无法创建客户端: {e}")
    
    def test_concurrent_interface_calls(self, client):
        """测试并发接口调用"""
        runner = StressTestRunner(client)
        
        # 测试1101接口
        result = runner.run_concurrent_interface_test(
            api_code='1101',
            concurrent_users=10,
            requests_per_user=3,
            ramp_up_time=2
        )
        
        # 验证测试结果
        assert result.total_requests == 30
        assert result.error_rate < 0.5  # 错误率应该小于50%
        assert result.average_response_time < 10.0  # 平均响应时间应该小于10秒
        
        print(f"并发接口测试结果: {result.to_dict()}")
    
    def test_database_connection_pool_performance(self, client):
        """测试数据库连接池性能"""
        runner = StressTestRunner(client)
        
        result = runner.run_database_connection_pool_test(
            concurrent_connections=15,
            operations_per_connection=10,
            test_duration=20
        )
        
        # 验证测试结果
        assert result.total_requests > 0
        assert result.error_rate < 0.3  # 错误率应该小于30%
        assert result.average_response_time < 5.0  # 平均响应时间应该小于5秒
        
        print(f"数据库连接池测试结果: {result.to_dict()}")
    
    def test_cache_system_effectiveness(self, client):
        """测试缓存系统效果"""
        runner = StressTestRunner(client)
        
        result = runner.run_cache_system_test(
            concurrent_operations=20,
            operations_per_worker=30,
            cache_hit_ratio=0.6
        )
        
        # 验证测试结果
        assert result.total_requests > 0
        assert result.error_rate < 0.2  # 错误率应该小于20%
        assert result.average_response_time < 1.0  # 缓存操作应该很快
        
        print(f"缓存系统测试结果: {result.to_dict()}")
    
    def test_full_stress_test_suite(self, client):
        """运行完整的压力测试套件"""
        suite = StressTestSuite()
        report = suite.run_all_tests(client)
        
        # 验证测试报告
        assert report['test_summary']['total_tests'] > 0
        assert len(report['test_results']) > 0
        assert 'performance_analysis' in report
        assert 'recommendations' in report
        
        # 打印测试报告
        print("\n=== 压力测试报告 ===")
        print(f"测试总数: {report['test_summary']['total_tests']}")
        print(f"整体状态: {report['test_summary']['overall_status']}")
        print(f"总请求数: {report['performance_analysis']['total_requests']}")
        print(f"成功请求: {report['performance_analysis']['total_successful']}")
        print(f"失败请求: {report['performance_analysis']['total_failed']}")
        print(f"整体错误率: {report['performance_analysis']['overall_error_rate']:.2f}%")
        print(f"平均RPS: {report['performance_analysis']['average_rps']:.2f}")
        
        print("\n=== 优化建议 ===")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        # 验证整体性能指标
        assert report['performance_analysis']['overall_error_rate'] < 20  # 整体错误率应该小于20%


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行压力测试
    try:
        db_config = DatabaseConfig.from_env()
        sdk_config = SDKConfig(database_config=db_config)
        client = MedicalInsuranceClient(sdk_config)
        
        suite = StressTestSuite()
        report = suite.run_all_tests(client)
        
        print("\n" + "="*60)
        print("压力测试完成！")
        print("="*60)
        
        # 输出简化报告
        print(f"测试状态: {report['test_summary']['overall_status']}")
        print(f"总请求数: {report['performance_analysis']['total_requests']}")
        print(f"成功率: {100 - report['performance_analysis']['overall_error_rate']:.1f}%")
        print(f"平均RPS: {report['performance_analysis']['average_rps']:.1f}")
        
        print("\n建议:")
        for recommendation in report['recommendations']:
            print(f"- {recommendation}")
        
    except Exception as e:
        print(f"压力测试执行失败: {e}")
        import traceback
        traceback.print_exc()