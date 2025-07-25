#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK高级使用示例

本示例展示了SDK的高级功能，包括：
- 自定义配置和扩展
- 性能优化技巧
- 高级错误处理
- 监控和调试
- 插件开发
- 集成测试

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加SDK路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk import MedicalInsuranceClient, DataHelper
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    NetworkException, 
    BusinessException
)


class AdvancedMedicalInsuranceClient:
    """高级医保接口客户端"""
    
    def __init__(self, config_path: str = None):
        """
        初始化高级客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.client = MedicalInsuranceClient.from_config_file(config_path) if config_path else MedicalInsuranceClient()
        self.request_cache = {}
        self.performance_metrics = {}
        self.error_handlers = {}
        self.middleware_stack = []
        
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware_stack.append(middleware)
    
    def register_error_handler(self, exception_type: type, handler: Callable):
        """注册错误处理器"""
        self.error_handlers[exception_type] = handler
    
    def call_with_middleware(self, api_code: str, input_data: dict, org_code: str, **kwargs):
        """带中间件的接口调用"""
        
        # 执行前置中间件
        for middleware in self.middleware_stack:
            try:
                input_data = middleware(api_code, input_data, org_code, **kwargs)
            except Exception as e:
                print(f"中间件执行失败: {str(e)}")
        
        # 执行实际调用
        try:
            result = self.client.call_interface(api_code, input_data, org_code, **kwargs)
            return result
        except Exception as e:
            # 查找并执行错误处理器
            for exception_type, handler in self.error_handlers.items():
                if isinstance(e, exception_type):
                    return handler(e, api_code, input_data, org_code)
            raise
    
    def batch_call_with_concurrency(self, requests: List[Dict], max_workers: int = 10) -> List[Dict]:
        """并发批量调用"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_request = {
                executor.submit(
                    self.call_with_middleware,
                    req['api_code'],
                    req['input_data'],
                    req['org_code'],
                    **req.get('kwargs', {})
                ): req for req in requests
            }
            
            # 收集结果
            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    result = future.result()
                    results.append({
                        'request': request,
                        'result': result,
                        'success': True
                    })
                except Exception as e:
                    results.append({
                        'request': request,
                        'result': None,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def call_with_cache(self, api_code: str, input_data: dict, org_code: str, cache_ttl: int = 300):
        """带缓存的接口调用"""
        
        # 生成缓存键
        cache_key = f"{api_code}_{org_code}_{hash(json.dumps(input_data, sort_keys=True))}"
        
        # 检查缓存
        if cache_key in self.request_cache:
            cached_result, cached_time = self.request_cache[cache_key]
            if time.time() - cached_time < cache_ttl:
                print(f"缓存命中: {cache_key}")
                return cached_result
        
        # 调用接口
        result = self.client.call_interface(api_code, input_data, org_code)
        
        # 存储到缓存
        self.request_cache[cache_key] = (result, time.time())
        
        return result
    
    def call_with_retry_and_backoff(self, api_code: str, input_data: dict, org_code: str, 
                                   max_retries: int = 3, base_delay: float = 1.0):
        """带重试和退避的接口调用"""
        
        for attempt in range(max_retries + 1):
            try:
                result = self.client.call_interface(api_code, input_data, org_code)
                
                if attempt > 0:
                    print(f"重试成功，尝试次数: {attempt + 1}")
                
                return result
                
            except (NetworkException, BusinessException) as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # 指数退避
                    print(f"调用失败，{delay}秒后重试 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                    time.sleep(delay)
                else:
                    print(f"重试次数已用完，最终失败: {str(e)}")
                    raise
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        return {
            'cache_stats': {
                'total_requests': len(self.request_cache),
                'cache_size': len(self.request_cache)
            },
            'metrics': self.performance_metrics
        }


def example_custom_middleware():
    """示例: 自定义中间件"""
    print("\n" + "="*60)
    print("高级示例01: 自定义中间件")
    print("="*60)
    
    client = AdvancedMedicalInsuranceClient()
    
    # 定义日志中间件
    def logging_middleware(api_code, input_data, org_code, **kwargs):
        print(f"[中间件] 调用接口: {api_code}, 机构: {org_code}")
        print(f"[中间件] 输入数据: {json.dumps(input_data, ensure_ascii=False)}")
        return input_data
    
    # 定义数据验证中间件
    def validation_middleware(api_code, input_data, org_code, **kwargs):
        if api_code == "1101":
            if not input_data.get('psn_name'):
                raise ValidationException("人员姓名不能为空")
            if len(input_data.get('certno', '')) != 18:
                raise ValidationException("身份证号码长度必须为18位")
        return input_data
    
    # 定义数据转换中间件
    def transform_middleware(api_code, input_data, org_code, **kwargs):
        # 统一转换为大写
        if 'psn_name' in input_data:
            input_data['psn_name'] = input_data['psn_name'].strip()
        return input_data
    
    # 注册中间件
    client.add_middleware(logging_middleware)
    client.add_middleware(validation_middleware)
    client.add_middleware(transform_middleware)
    
    # 测试中间件
    try:
        query_data = {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": "430123199001011234",
            "psn_cert_type": "01",
            "certno": "430123199001011234",
            "psn_name": "  张三  "  # 带空格，测试转换中间件
        }
        
        result = client.call_with_middleware(
            api_code="1101",
            input_data=query_data,
            org_code="H43010000001"
        )
        
        print("✓ 中间件测试成功")
        
    except Exception as e:
        print(f"✗ 中间件测试失败: {str(e)}")


def example_custom_error_handlers():
    """示例: 自定义错误处理器"""
    print("\n" + "="*60)
    print("高级示例02: 自定义错误处理器")
    print("="*60)
    
    client = AdvancedMedicalInsuranceClient()
    
    # 定义验证错误处理器
    def validation_error_handler(error, api_code, input_data, org_code):
        print(f"[错误处理器] 处理验证错误: {str(error)}")
        
        # 尝试数据修正
        if "身份证" in str(error) and len(input_data.get('certno', '')) != 18:
            print("[错误处理器] 尝试修正身份证号码...")
            # 这里可以实现具体的修正逻辑
            return {'success': False, 'error_message': '身份证号码格式错误，已记录日志'}
        
        return {'success': False, 'error_message': f'数据验证失败: {str(error)}'}
    
    # 定义网络错误处理器
    def network_error_handler(error, api_code, input_data, org_code):
        print(f"[错误处理器] 处理网络错误: {str(error)}")
        
        # 记录错误日志
        error_log = {
            'timestamp': datetime.now().isoformat(),
            'api_code': api_code,
            'org_code': org_code,
            'error_type': 'network',
            'error_message': str(error)
        }
        
        print(f"[错误处理器] 错误日志: {json.dumps(error_log, ensure_ascii=False)}")
        
        return {'success': False, 'error_message': '网络连接异常，请稍后重试'}
    
    # 定义业务错误处理器
    def business_error_handler(error, api_code, input_data, org_code):
        print(f"[错误处理器] 处理业务错误: {str(error)}")
        
        # 根据不同的业务错误类型进行处理
        if "人员不存在" in str(error):
            return {'success': False, 'error_message': '未找到该人员的医保信息，请核实身份信息'}
        elif "参保状态异常" in str(error):
            return {'success': False, 'error_message': '该人员参保状态异常，请联系医保部门'}
        
        return {'success': False, 'error_message': f'业务处理失败: {str(error)}'}
    
    # 注册错误处理器
    client.register_error_handler(ValidationException, validation_error_handler)
    client.register_error_handler(NetworkException, network_error_handler)
    client.register_error_handler(BusinessException, business_error_handler)
    
    # 测试错误处理器
    test_cases = [
        {
            "name": "验证错误测试",
            "data": {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "invalid",
                "psn_cert_type": "01",
                "certno": "invalid",
                "psn_name": "测试"
            }
        },
        {
            "name": "正常调用测试",
            "data": {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        try:
            result = client.call_with_middleware(
                api_code="1101",
                input_data=test_case['data'],
                org_code="H43010000001"
            )
            print(f"结果: {result.get('error_message', '成功')}")
        except Exception as e:
            print(f"未处理的异常: {str(e)}")


def example_concurrent_processing():
    """示例: 并发处理"""
    print("\n" + "="*60)
    print("高级示例03: 并发处理")
    print("="*60)
    
    client = AdvancedMedicalInsuranceClient()
    
    # 准备批量请求
    requests = []
    for i in range(1, 11):
        requests.append({
            'api_code': '1101',
            'input_data': {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": f"43012319900101{i:04d}",
                "psn_cert_type": "01",
                "certno": f"43012319900101{i:04d}",
                "psn_name": f"患者{i:03d}"
            },
            'org_code': 'H43010000001'
        })
    
    print(f"准备并发处理 {len(requests)} 个请求...")
    
    # 测试不同的并发数
    for max_workers in [1, 5, 10]:
        print(f"\n使用 {max_workers} 个并发线程:")
        
        start_time = time.time()
        results = client.batch_call_with_concurrency(requests, max_workers=max_workers)
        end_time = time.time()
        
        success_count = sum(1 for r in results if r['success'])
        
        print(f"  处理时间: {end_time - start_time:.2f}秒")
        print(f"  成功数量: {success_count}/{len(requests)}")
        print(f"  成功率: {success_count/len(requests)*100:.1f}%")
        print(f"  平均QPS: {len(requests)/(end_time - start_time):.1f}")


def example_caching_strategy():
    """示例: 缓存策略"""
    print("\n" + "="*60)
    print("高级示例04: 缓存策略")
    print("="*60)
    
    client = AdvancedMedicalInsuranceClient()
    
    query_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    # 第一次调用（无缓存）
    print("第一次调用（无缓存）:")
    start_time = time.time()
    result1 = client.call_with_cache("1101", query_data, "H43010000001", cache_ttl=60)
    time1 = time.time() - start_time
    print(f"  耗时: {time1:.3f}秒")
    
    # 第二次调用（有缓存）
    print("\n第二次调用（有缓存）:")
    start_time = time.time()
    result2 = client.call_with_cache("1101", query_data, "H43010000001", cache_ttl=60)
    time2 = time.time() - start_time
    print(f"  耗时: {time2:.3f}秒")
    
    if time2 < time1:
        print(f"  缓存加速: {time1/time2:.1f}倍")
    
    # 缓存统计
    performance_report = client.get_performance_report()
    print(f"\n缓存统计:")
    print(f"  缓存项数: {performance_report['cache_stats']['cache_size']}")


def example_retry_and_backoff():
    """示例: 重试和退避策略"""
    print("\n" + "="*60)
    print("高级示例05: 重试和退避策略")
    print("="*60)
    
    client = AdvancedMedicalInsuranceClient()
    
    query_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    print("测试重试机制:")
    
    try:
        result = client.call_with_retry_and_backoff(
            api_code="1101",
            input_data=query_data,
            org_code="H43010000001",
            max_retries=3,
            base_delay=0.5
        )
        
        print("✓ 调用成功（可能经过重试）")
        
    except Exception as e:
        print(f"✗ 最终调用失败: {str(e)}")


def example_performance_monitoring():
    """示例: 性能监控"""
    print("\n" + "="*60)
    print("高级示例06: 性能监控")
    print("="*60)
    
    client = AdvancedMedicalInsuranceClient()
    
    # 模拟性能监控
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_response_time': 0,
                'min_response_time': float('inf'),
                'max_response_time': 0
            }
        
        def record_request(self, success: bool, response_time: float):
            self.metrics['total_requests'] += 1
            if success:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            self.metrics['total_response_time'] += response_time
            self.metrics['min_response_time'] = min(self.metrics['min_response_time'], response_time)
            self.metrics['max_response_time'] = max(self.metrics['max_response_time'], response_time)
        
        def get_stats(self):
            if self.metrics['total_requests'] > 0:
                avg_response_time = self.metrics['total_response_time'] / self.metrics['total_requests']
                success_rate = self.metrics['successful_requests'] / self.metrics['total_requests']
            else:
                avg_response_time = 0
                success_rate = 0
            
            return {
                'total_requests': self.metrics['total_requests'],
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'min_response_time': self.metrics['min_response_time'] if self.metrics['min_response_time'] != float('inf') else 0,
                'max_response_time': self.metrics['max_response_time']
            }
    
    monitor = PerformanceMonitor()
    
    # 模拟多次调用
    query_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    print("执行性能测试...")
    
    for i in range(10):
        start_time = time.time()
        try:
            result = client.call_with_cache("1101", query_data, "H43010000001")
            response_time = time.time() - start_time
            success = result.get('success', False)
            monitor.record_request(success, response_time)
            
        except Exception as e:
            response_time = time.time() - start_time
            monitor.record_request(False, response_time)
    
    # 输出性能统计
    stats = monitor.get_stats()
    print(f"\n性能统计:")
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均响应时间: {stats['avg_response_time']:.3f}秒")
    print(f"  最小响应时间: {stats['min_response_time']:.3f}秒")
    print(f"  最大响应时间: {stats['max_response_time']:.3f}秒")


def example_plugin_development():
    """示例: 插件开发"""
    print("\n" + "="*60)
    print("高级示例07: 插件开发")
    print("="*60)
    
    # 定义插件基类
    class Plugin:
        def __init__(self, name: str):
            self.name = name
        
        def before_request(self, api_code: str, input_data: dict, org_code: str):
            """请求前处理"""
            pass
        
        def after_request(self, api_code: str, result: dict, org_code: str):
            """请求后处理"""
            pass
        
        def on_error(self, api_code: str, error: Exception, org_code: str):
            """错误处理"""
            pass
    
    # 实现日志插件
    class LoggingPlugin(Plugin):
        def __init__(self):
            super().__init__("LoggingPlugin")
            self.request_count = 0
        
        def before_request(self, api_code: str, input_data: dict, org_code: str):
            self.request_count += 1
            print(f"[{self.name}] 请求 #{self.request_count}: {api_code} @ {org_code}")
        
        def after_request(self, api_code: str, result: dict, org_code: str):
            success = result.get('success', False)
            status = "成功" if success else "失败"
            print(f"[{self.name}] 请求完成: {api_code} - {status}")
        
        def on_error(self, api_code: str, error: Exception, org_code: str):
            print(f"[{self.name}] 请求异常: {api_code} - {str(error)}")
    
    # 实现统计插件
    class StatisticsPlugin(Plugin):
        def __init__(self):
            super().__init__("StatisticsPlugin")
            self.stats = {}
        
        def before_request(self, api_code: str, input_data: dict, org_code: str):
            if api_code not in self.stats:
                self.stats[api_code] = {'total': 0, 'success': 0, 'failed': 0}
            self.stats[api_code]['total'] += 1
        
        def after_request(self, api_code: str, result: dict, org_code: str):
            success = result.get('success', False)
            if success:
                self.stats[api_code]['success'] += 1
            else:
                self.stats[api_code]['failed'] += 1
        
        def get_statistics(self):
            return self.stats
    
    # 插件管理器
    class PluginManager:
        def __init__(self):
            self.plugins = []
        
        def register_plugin(self, plugin: Plugin):
            self.plugins.append(plugin)
            print(f"注册插件: {plugin.name}")
        
        def call_with_plugins(self, client, api_code: str, input_data: dict, org_code: str):
            # 执行前置处理
            for plugin in self.plugins:
                try:
                    plugin.before_request(api_code, input_data, org_code)
                except Exception as e:
                    print(f"插件 {plugin.name} 前置处理失败: {str(e)}")
            
            # 执行实际调用
            try:
                result = client.call_interface(api_code, input_data, org_code)
                
                # 执行后置处理
                for plugin in self.plugins:
                    try:
                        plugin.after_request(api_code, result, org_code)
                    except Exception as e:
                        print(f"插件 {plugin.name} 后置处理失败: {str(e)}")
                
                return result
                
            except Exception as error:
                # 执行错误处理
                for plugin in self.plugins:
                    try:
                        plugin.on_error(api_code, error, org_code)
                    except Exception as e:
                        print(f"插件 {plugin.name} 错误处理失败: {str(e)}")
                
                raise
    
    # 测试插件系统
    client = MedicalInsuranceClient()
    plugin_manager = PluginManager()
    
    # 注册插件
    logging_plugin = LoggingPlugin()
    stats_plugin = StatisticsPlugin()
    
    plugin_manager.register_plugin(logging_plugin)
    plugin_manager.register_plugin(stats_plugin)
    
    # 测试插件功能
    query_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    print("\n测试插件系统:")
    
    for i in range(3):
        try:
            result = plugin_manager.call_with_plugins(
                client, "1101", query_data, "H43010000001"
            )
        except Exception as e:
            print(f"调用失败: {str(e)}")
    
    # 显示统计信息
    print(f"\n插件统计信息:")
    stats = stats_plugin.get_statistics()
    for api_code, stat in stats.items():
        print(f"  {api_code}: 总计{stat['total']}, 成功{stat['success']}, 失败{stat['failed']}")


def main():
    """主函数"""
    print("医保接口SDK高级使用示例")
    print("="*80)
    
    examples = [
        example_custom_middleware,
        example_custom_error_handlers,
        example_concurrent_processing,
        example_caching_strategy,
        example_retry_and_backoff,
        example_performance_monitoring,
        example_plugin_development
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"示例执行异常: {str(e)}")
    
    print("\n" + "="*80)
    print("高级示例演示完成！")
    print("\n高级功能总结:")
    print("1. 自定义中间件 - 扩展请求处理流程")
    print("2. 自定义错误处理器 - 优雅处理各种异常")
    print("3. 并发处理 - 提升批量操作性能")
    print("4. 缓存策略 - 减少重复请求，提升响应速度")
    print("5. 重试和退避 - 提高系统稳定性")
    print("6. 性能监控 - 实时监控系统性能指标")
    print("7. 插件开发 - 灵活扩展SDK功能")
    print("\n这些高级功能可以帮助您构建更加健壮和高效的医保接口应用。")


if __name__ == "__main__":
    main()