"""
性能监控和指标收集模块
支持Prometheus指标收集和性能数据分析
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import logging

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary, Info,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        start_http_server, push_to_gateway
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # 创建占位符类以避免导入错误
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def labels(self, *args, **kwargs): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def labels(self, *args, **kwargs): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    class CollectorRegistry:
        def __init__(self): pass
    
    def generate_latest(*args): return b""
    CONTENT_TYPE_LATEST = "text/plain"
    def start_http_server(*args, **kwargs): pass
    def push_to_gateway(*args, **kwargs): pass


@dataclass
class MetricConfig:
    """指标配置"""
    enabled: bool = True
    prometheus_enabled: bool = True
    prometheus_port: int = 8000
    prometheus_gateway_url: Optional[str] = None
    collection_interval: int = 60  # 秒
    retention_days: int = 7
    max_memory_metrics: int = 10000


@dataclass
class PerformanceMetric:
    """性能指标数据"""
    timestamp: datetime
    metric_name: str
    metric_type: str  # counter, gauge, histogram, summary
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APICallMetric:
    """API调用指标"""
    api_code: str
    org_code: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "pending"  # pending, success, error
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    request_size: int = 0
    response_size: int = 0


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self, config: MetricConfig = None):
        self.config = config or MetricConfig()
        self.logger = logging.getLogger(__name__)
        
        # 内存中的指标存储
        self._metrics_buffer: deque = deque(maxlen=self.config.max_memory_metrics)
        self._api_calls_buffer: deque = deque(maxlen=self.config.max_memory_metrics)
        self._lock = threading.RLock()
        
        # 统计数据
        self._stats = {
            'total_api_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_response_time': 0.0,
            'api_call_counts': defaultdict(int),
            'error_counts': defaultdict(int),
            'org_call_counts': defaultdict(int)
        }
        
        # Prometheus指标
        self._prometheus_registry = None
        self._prometheus_metrics = {}
        
        if self.config.prometheus_enabled and PROMETHEUS_AVAILABLE:
            self._setup_prometheus_metrics()
            if self.config.prometheus_port:
                self._start_prometheus_server()
    
    def _setup_prometheus_metrics(self):
        """设置Prometheus指标"""
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning("Prometheus client not available, skipping Prometheus metrics setup")
            return
        
        self._prometheus_registry = CollectorRegistry()
        
        # API调用计数器
        self._prometheus_metrics['api_calls_total'] = Counter(
            'medical_insurance_api_calls_total',
            'Total number of API calls',
            ['api_code', 'org_code', 'status'],
            registry=self._prometheus_registry
        )
        
        # API响应时间直方图
        self._prometheus_metrics['api_duration_seconds'] = Histogram(
            'medical_insurance_api_duration_seconds',
            'API call duration in seconds',
            ['api_code', 'org_code'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self._prometheus_registry
        )
        
        # 错误计数器
        self._prometheus_metrics['api_errors_total'] = Counter(
            'medical_insurance_api_errors_total',
            'Total number of API errors',
            ['api_code', 'org_code', 'error_code'],
            registry=self._prometheus_registry
        )
        
        # 当前活跃连接数
        self._prometheus_metrics['active_connections'] = Gauge(
            'medical_insurance_active_connections',
            'Number of active database connections',
            ['connection_type'],
            registry=self._prometheus_registry
        )
        
        # 缓存命中率
        self._prometheus_metrics['cache_hit_ratio'] = Gauge(
            'medical_insurance_cache_hit_ratio',
            'Cache hit ratio',
            ['cache_type'],
            registry=self._prometheus_registry
        )
        
        # 系统信息
        self._prometheus_metrics['system_info'] = Info(
            'medical_insurance_system_info',
            'System information',
            registry=self._prometheus_registry
        )
        
        # 设置系统信息
        self._prometheus_metrics['system_info'].info({
            'version': '1.0.0',
            'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            'start_time': datetime.now().isoformat()
        })
    
    def _start_prometheus_server(self):
        """启动Prometheus HTTP服务器"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        try:
            start_http_server(
                self.config.prometheus_port,
                registry=self._prometheus_registry
            )
            self.logger.info(f"Prometheus metrics server started on port {self.config.prometheus_port}")
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus server: {e}")
    
    def record_api_call_start(self, api_code: str, org_code: str, request_size: int = 0) -> str:
        """记录API调用开始"""
        call_id = f"{api_code}_{org_code}_{int(time.time() * 1000)}"
        
        metric = APICallMetric(
            api_code=api_code,
            org_code=org_code,
            start_time=datetime.now(),
            request_size=request_size
        )
        
        with self._lock:
            self._api_calls_buffer.append((call_id, metric))
        
        return call_id
    
    def record_api_call_end(self, call_id: str, status: str, error_code: str = None, 
                           error_message: str = None, response_size: int = 0):
        """记录API调用结束"""
        end_time = datetime.now()
        
        with self._lock:
            # 查找对应的调用记录
            for i, (stored_id, metric) in enumerate(self._api_calls_buffer):
                if stored_id == call_id:
                    metric.end_time = end_time
                    metric.duration_ms = (end_time - metric.start_time).total_seconds() * 1000
                    metric.status = status
                    metric.error_code = error_code
                    metric.error_message = error_message
                    metric.response_size = response_size
                    
                    # 更新统计数据
                    self._update_stats(metric)
                    
                    # 更新Prometheus指标
                    self._update_prometheus_metrics(metric)
                    
                    break
    
    def _update_stats(self, metric: APICallMetric):
        """更新统计数据"""
        self._stats['total_api_calls'] += 1
        self._stats['api_call_counts'][metric.api_code] += 1
        self._stats['org_call_counts'][metric.org_code] += 1
        
        if metric.status == 'success':
            self._stats['successful_calls'] += 1
        else:
            self._stats['failed_calls'] += 1
            if metric.error_code:
                self._stats['error_counts'][metric.error_code] += 1
        
        if metric.duration_ms:
            self._stats['total_response_time'] += metric.duration_ms
    
    def _update_prometheus_metrics(self, metric: APICallMetric):
        """更新Prometheus指标"""
        if not self.config.prometheus_enabled or not PROMETHEUS_AVAILABLE:
            return
        
        try:
            # 更新API调用计数
            self._prometheus_metrics['api_calls_total'].labels(
                api_code=metric.api_code,
                org_code=metric.org_code,
                status=metric.status
            ).inc()
            
            # 更新响应时间
            if metric.duration_ms:
                self._prometheus_metrics['api_duration_seconds'].labels(
                    api_code=metric.api_code,
                    org_code=metric.org_code
                ).observe(metric.duration_ms / 1000.0)
            
            # 更新错误计数
            if metric.status == 'error' and metric.error_code:
                self._prometheus_metrics['api_errors_total'].labels(
                    api_code=metric.api_code,
                    org_code=metric.org_code,
                    error_code=metric.error_code
                ).inc()
        
        except Exception as e:
            self.logger.error(f"Failed to update Prometheus metrics: {e}")
    
    def record_custom_metric(self, name: str, value: float, metric_type: str = "gauge", 
                           labels: Dict[str, str] = None, additional_data: Dict[str, Any] = None):
        """记录自定义指标"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
            additional_data=additional_data or {}
        )
        
        with self._lock:
            self._metrics_buffer.append(metric)
    
    def record_database_connections(self, active_connections: int, connection_type: str = "mysql"):
        """记录数据库连接数"""
        self.record_custom_metric(
            f"database_connections_{connection_type}",
            active_connections,
            "gauge",
            {"connection_type": connection_type}
        )
        
        if self.config.prometheus_enabled and PROMETHEUS_AVAILABLE:
            self._prometheus_metrics['active_connections'].labels(
                connection_type=connection_type
            ).set(active_connections)
    
    def record_cache_hit_ratio(self, hit_ratio: float, cache_type: str = "redis"):
        """记录缓存命中率"""
        self.record_custom_metric(
            f"cache_hit_ratio_{cache_type}",
            hit_ratio,
            "gauge",
            {"cache_type": cache_type}
        )
        
        if self.config.prometheus_enabled and PROMETHEUS_AVAILABLE:
            self._prometheus_metrics['cache_hit_ratio'].labels(
                cache_type=cache_type
            ).set(hit_ratio)
    
    def get_api_statistics(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """获取API统计数据"""
        cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)
        
        with self._lock:
            # 过滤时间范围内的调用记录
            recent_calls = [
                metric for _, metric in self._api_calls_buffer
                if metric.start_time >= cutoff_time and metric.end_time
            ]
        
        if not recent_calls:
            return {
                'total_calls': 0,
                'success_rate': 0.0,
                'average_response_time': 0.0,
                'api_breakdown': {},
                'error_breakdown': {},
                'time_range_minutes': time_range_minutes
            }
        
        # 计算统计数据
        total_calls = len(recent_calls)
        successful_calls = sum(1 for call in recent_calls if call.status == 'success')
        success_rate = (successful_calls / total_calls) * 100 if total_calls > 0 else 0
        
        total_response_time = sum(call.duration_ms for call in recent_calls if call.duration_ms)
        average_response_time = total_response_time / total_calls if total_calls > 0 else 0
        
        # API调用分布
        api_breakdown = defaultdict(lambda: {'count': 0, 'success': 0, 'avg_time': 0})
        for call in recent_calls:
            api_breakdown[call.api_code]['count'] += 1
            if call.status == 'success':
                api_breakdown[call.api_code]['success'] += 1
            if call.duration_ms:
                api_breakdown[call.api_code]['avg_time'] += call.duration_ms
        
        # 计算平均时间
        for api_code, data in api_breakdown.items():
            if data['count'] > 0:
                data['avg_time'] /= data['count']
                data['success_rate'] = (data['success'] / data['count']) * 100
        
        # 错误分布
        error_breakdown = defaultdict(int)
        for call in recent_calls:
            if call.status == 'error' and call.error_code:
                error_breakdown[call.error_code] += 1
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': total_calls - successful_calls,
            'success_rate': success_rate,
            'average_response_time': average_response_time,
            'api_breakdown': dict(api_breakdown),
            'error_breakdown': dict(error_breakdown),
            'time_range_minutes': time_range_minutes,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        import psutil
        import os
        
        # 获取进程信息
        process = psutil.Process(os.getpid())
        
        # 内存使用情况
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # CPU使用情况
        cpu_percent = process.cpu_percent()
        
        # 系统内存
        system_memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk_usage = psutil.disk_usage('/')
        
        return {
            'process': {
                'pid': os.getpid(),
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms,
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'num_threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
            },
            'system': {
                'memory_total': system_memory.total,
                'memory_available': system_memory.available,
                'memory_percent': system_memory.percent,
                'cpu_count': psutil.cpu_count(),
                'disk_total': disk_usage.total,
                'disk_used': disk_usage.used,
                'disk_free': disk_usage.free,
                'disk_percent': (disk_usage.used / disk_usage.total) * 100
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def export_metrics_to_prometheus_gateway(self, gateway_url: str, job_name: str = "medical_insurance_sdk"):
        """导出指标到Prometheus Gateway"""
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning("Prometheus client not available")
            return False
        
        try:
            push_to_gateway(
                gateway_url,
                job=job_name,
                registry=self._prometheus_registry
            )
            self.logger.info(f"Metrics pushed to Prometheus Gateway: {gateway_url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to push metrics to gateway: {e}")
            return False
    
    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标数据"""
        if not PROMETHEUS_AVAILABLE or not self._prometheus_registry:
            return ""
        
        return generate_latest(self._prometheus_registry).decode('utf-8')
    
    def cleanup_old_metrics(self):
        """清理过期的指标数据"""
        cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
        
        with self._lock:
            # 清理API调用记录
            self._api_calls_buffer = deque([
                (call_id, metric) for call_id, metric in self._api_calls_buffer
                if metric.start_time >= cutoff_time
            ], maxlen=self.config.max_memory_metrics)
            
            # 清理自定义指标
            self._metrics_buffer = deque([
                metric for metric in self._metrics_buffer
                if metric.timestamp >= cutoff_time
            ], maxlen=self.config.max_memory_metrics)
    
    def generate_performance_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """生成性能报告"""
        api_stats = self.get_api_statistics(time_range_hours * 60)
        system_metrics = self.get_system_metrics()
        
        # 获取最近的自定义指标
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        with self._lock:
            recent_metrics = [
                metric for metric in self._metrics_buffer
                if metric.timestamp >= cutoff_time
            ]
        
        # 按指标名称分组
        custom_metrics_summary = defaultdict(list)
        for metric in recent_metrics:
            custom_metrics_summary[metric.metric_name].append(metric.value)
        
        # 计算统计值
        custom_metrics_stats = {}
        for name, values in custom_metrics_summary.items():
            if values:
                custom_metrics_stats[name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1] if values else 0
                }
        
        return {
            'report_time': datetime.now().isoformat(),
            'time_range_hours': time_range_hours,
            'api_statistics': api_stats,
            'system_metrics': system_metrics,
            'custom_metrics': custom_metrics_stats,
            'prometheus_available': PROMETHEUS_AVAILABLE,
            'prometheus_enabled': self.config.prometheus_enabled
        }


# 全局指标收集器实例
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器实例"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def initialize_metrics_collector(config: MetricConfig) -> MetricsCollector:
    """初始化全局指标收集器"""
    global _global_metrics_collector
    _global_metrics_collector = MetricsCollector(config)
    return _global_metrics_collector


# 装饰器：自动记录API调用指标
def monitor_api_call(api_code: str = None, org_code: str = None):
    """API调用监控装饰器"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 从参数中提取api_code和org_code
            actual_api_code = api_code or kwargs.get('api_code') or (args[0] if args else 'unknown')
            actual_org_code = org_code or kwargs.get('org_code') or 'unknown'
            
            collector = get_metrics_collector()
            call_id = collector.record_api_call_start(actual_api_code, actual_org_code)
            
            try:
                result = func(*args, **kwargs)
                collector.record_api_call_end(call_id, 'success')
                return result
            except Exception as e:
                collector.record_api_call_end(
                    call_id, 
                    'error', 
                    error_code=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator