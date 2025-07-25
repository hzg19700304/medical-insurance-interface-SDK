"""
性能数据分析模块
提供性能数据的收集、分析和报告功能
"""

import time
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import logging
import threading

from .metrics_collector import MetricsCollector, APICallMetric, PerformanceMetric


@dataclass
class PerformanceThreshold:
    """性能阈值配置"""
    api_code: str
    max_response_time_ms: float = 5000.0  # 最大响应时间（毫秒）
    max_error_rate: float = 0.05  # 最大错误率（5%）
    min_success_rate: float = 0.95  # 最小成功率（95%）
    max_concurrent_calls: int = 100  # 最大并发调用数


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    alert_type: str  # response_time, error_rate, success_rate, concurrent_limit
    api_code: str
    org_code: str
    threshold_value: float
    actual_value: float
    severity: str  # warning, critical
    timestamp: datetime
    message: str
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTrend:
    """性能趋势数据"""
    metric_name: str
    time_points: List[datetime]
    values: List[float]
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0-1, 趋势强度
    prediction: Optional[float] = None  # 预测值


class PerformanceAnalyzer:
    """性能数据分析器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        
        # 性能阈值配置
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        
        # 告警历史
        self.alerts_history: deque = deque(maxlen=1000)
        
        # 分析缓存
        self._analysis_cache = {}
        self._cache_lock = threading.RLock()
        self._cache_ttl = 300  # 5分钟缓存
        
        # 默认阈值
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """设置默认性能阈值"""
        default_apis = ['1101', '2201', '2207', '1201', '1301']
        
        for api_code in default_apis:
            self.thresholds[api_code] = PerformanceThreshold(
                api_code=api_code,
                max_response_time_ms=5000.0,
                max_error_rate=0.05,
                min_success_rate=0.95,
                max_concurrent_calls=50
            )
    
    def set_threshold(self, api_code: str, threshold: PerformanceThreshold):
        """设置API性能阈值"""
        self.thresholds[api_code] = threshold
        self.logger.info(f"Updated performance threshold for API {api_code}")
    
    def analyze_api_performance(self, api_code: str, time_range_minutes: int = 60) -> Dict[str, Any]:
        """分析API性能"""
        cache_key = f"api_perf_{api_code}_{time_range_minutes}"
        
        # 检查缓存
        with self._cache_lock:
            if cache_key in self._analysis_cache:
                cached_data, cache_time = self._analysis_cache[cache_key]
                if time.time() - cache_time < self._cache_ttl:
                    return cached_data
        
        # 获取API调用数据
        cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)
        
        with self.metrics_collector._lock:
            api_calls = [
                metric for _, metric in self.metrics_collector._api_calls_buffer
                if (metric.api_code == api_code and 
                    metric.start_time >= cutoff_time and 
                    metric.end_time is not None)
            ]
        
        if not api_calls:
            return {
                'api_code': api_code,
                'time_range_minutes': time_range_minutes,
                'total_calls': 0,
                'analysis_timestamp': datetime.now().isoformat(),
                'status': 'no_data'
            }
        
        # 基础统计
        total_calls = len(api_calls)
        successful_calls = sum(1 for call in api_calls if call.status == 'success')
        failed_calls = total_calls - successful_calls
        success_rate = (successful_calls / total_calls) if total_calls > 0 else 0
        error_rate = (failed_calls / total_calls) if total_calls > 0 else 0
        
        # 响应时间分析
        response_times = [call.duration_ms for call in api_calls if call.duration_ms is not None]
        response_time_stats = self._calculate_response_time_stats(response_times)
        
        # 错误分析
        error_analysis = self._analyze_errors(api_calls)
        
        # 时间序列分析
        time_series_analysis = self._analyze_time_series(api_calls, time_range_minutes)
        
        # 性能评估
        performance_score = self._calculate_performance_score(
            success_rate, response_time_stats, error_rate
        )
        
        # 检查阈值告警
        alerts = self._check_performance_alerts(api_code, {
            'success_rate': success_rate,
            'error_rate': error_rate,
            'avg_response_time': response_time_stats.get('mean', 0),
            'max_response_time': response_time_stats.get('max', 0)
        })
        
        analysis_result = {
            'api_code': api_code,
            'time_range_minutes': time_range_minutes,
            'analysis_timestamp': datetime.now().isoformat(),
            'basic_stats': {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'success_rate': success_rate,
                'error_rate': error_rate
            },
            'response_time_stats': response_time_stats,
            'error_analysis': error_analysis,
            'time_series_analysis': time_series_analysis,
            'performance_score': performance_score,
            'alerts': alerts,
            'status': 'analyzed'
        }
        
        # 缓存结果
        with self._cache_lock:
            self._analysis_cache[cache_key] = (analysis_result, time.time())
        
        return analysis_result
    
    def _calculate_response_time_stats(self, response_times: List[float]) -> Dict[str, float]:
        """计算响应时间统计"""
        if not response_times:
            return {
                'count': 0,
                'mean': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'std_dev': 0,
                'p95': 0,
                'p99': 0
            }
        
        sorted_times = sorted(response_times)
        count = len(sorted_times)
        
        return {
            'count': count,
            'mean': statistics.mean(sorted_times),
            'median': statistics.median(sorted_times),
            'min': min(sorted_times),
            'max': max(sorted_times),
            'std_dev': statistics.stdev(sorted_times) if count > 1 else 0,
            'p95': sorted_times[int(count * 0.95)] if count > 0 else 0,
            'p99': sorted_times[int(count * 0.99)] if count > 0 else 0
        }
    
    def _analyze_errors(self, api_calls: List[APICallMetric]) -> Dict[str, Any]:
        """分析错误情况"""
        error_calls = [call for call in api_calls if call.status == 'error']
        
        if not error_calls:
            return {
                'total_errors': 0,
                'error_types': {},
                'error_rate_by_org': {},
                'most_common_errors': []
            }
        
        # 错误类型统计
        error_types = defaultdict(int)
        error_rate_by_org = defaultdict(lambda: {'total': 0, 'errors': 0})
        
        for call in api_calls:
            error_rate_by_org[call.org_code]['total'] += 1
            if call.status == 'error':
                if call.error_code:
                    error_types[call.error_code] += 1
                error_rate_by_org[call.org_code]['errors'] += 1
        
        # 计算各机构错误率
        org_error_rates = {}
        for org_code, data in error_rate_by_org.items():
            org_error_rates[org_code] = data['errors'] / data['total'] if data['total'] > 0 else 0
        
        # 最常见错误
        most_common_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_errors': len(error_calls),
            'error_types': dict(error_types),
            'error_rate_by_org': org_error_rates,
            'most_common_errors': most_common_errors
        }
    
    def _analyze_time_series(self, api_calls: List[APICallMetric], time_range_minutes: int) -> Dict[str, Any]:
        """时间序列分析"""
        if not api_calls:
            return {'status': 'no_data'}
        
        # 按时间分组（每5分钟一个时间段）
        interval_minutes = min(5, time_range_minutes // 12)  # 最多12个时间段
        time_buckets = defaultdict(lambda: {'calls': 0, 'errors': 0, 'total_time': 0})
        
        start_time = min(call.start_time for call in api_calls)
        
        for call in api_calls:
            # 计算时间段索引
            time_diff = (call.start_time - start_time).total_seconds() / 60
            bucket_index = int(time_diff // interval_minutes)
            bucket_key = start_time + timedelta(minutes=bucket_index * interval_minutes)
            
            time_buckets[bucket_key]['calls'] += 1
            if call.status == 'error':
                time_buckets[bucket_key]['errors'] += 1
            if call.duration_ms:
                time_buckets[bucket_key]['total_time'] += call.duration_ms
        
        # 构建时间序列数据
        time_series = []
        for bucket_time in sorted(time_buckets.keys()):
            data = time_buckets[bucket_time]
            avg_response_time = data['total_time'] / data['calls'] if data['calls'] > 0 else 0
            error_rate = data['errors'] / data['calls'] if data['calls'] > 0 else 0
            
            time_series.append({
                'timestamp': bucket_time.isoformat(),
                'calls': data['calls'],
                'errors': data['errors'],
                'error_rate': error_rate,
                'avg_response_time': avg_response_time
            })
        
        # 趋势分析
        if len(time_series) >= 3:
            call_counts = [point['calls'] for point in time_series]
            response_times = [point['avg_response_time'] for point in time_series if point['avg_response_time'] > 0]
            
            call_trend = self._calculate_trend(call_counts)
            response_time_trend = self._calculate_trend(response_times) if response_times else None
        else:
            call_trend = None
            response_time_trend = None
        
        return {
            'interval_minutes': interval_minutes,
            'time_series': time_series,
            'call_trend': call_trend,
            'response_time_trend': response_time_trend,
            'status': 'analyzed'
        }
    
    def _calculate_trend(self, values: List[float]) -> Optional[PerformanceTrend]:
        """计算趋势"""
        if len(values) < 3:
            return None
        
        # 简单线性回归计算趋势
        n = len(values)
        x = list(range(n))
        
        # 计算斜率
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # 判断趋势方向和强度
        if abs(slope) < 0.1:
            direction = 'stable'
            strength = 0.0
        elif slope > 0:
            direction = 'increasing'
            strength = min(abs(slope) / (max(values) - min(values) + 1), 1.0)
        else:
            direction = 'decreasing'
            strength = min(abs(slope) / (max(values) - min(values) + 1), 1.0)
        
        # 简单预测下一个值
        prediction = values[-1] + slope if slope != 0 else values[-1]
        
        return PerformanceTrend(
            metric_name='trend_analysis',
            time_points=[],
            values=values,
            trend_direction=direction,
            trend_strength=strength,
            prediction=prediction
        )
    
    def _calculate_performance_score(self, success_rate: float, response_time_stats: Dict[str, float], 
                                   error_rate: float) -> Dict[str, Any]:
        """计算性能评分"""
        # 成功率评分 (0-40分)
        success_score = success_rate * 40
        
        # 响应时间评分 (0-40分)
        avg_response_time = response_time_stats.get('mean', 0)
        if avg_response_time <= 1000:  # 1秒以内满分
            response_time_score = 40
        elif avg_response_time <= 3000:  # 1-3秒线性递减
            response_time_score = 40 - (avg_response_time - 1000) / 2000 * 20
        elif avg_response_time <= 5000:  # 3-5秒快速递减
            response_time_score = 20 - (avg_response_time - 3000) / 2000 * 15
        else:  # 超过5秒很低分
            response_time_score = max(5 - (avg_response_time - 5000) / 1000, 0)
        
        # 稳定性评分 (0-20分)
        std_dev = response_time_stats.get('std_dev', 0)
        if std_dev <= 500:  # 标准差500ms以内满分
            stability_score = 20
        elif std_dev <= 2000:  # 500ms-2s线性递减
            stability_score = 20 - (std_dev - 500) / 1500 * 15
        else:  # 超过2s很低分
            stability_score = max(5 - (std_dev - 2000) / 1000, 0)
        
        total_score = success_score + response_time_score + stability_score
        
        # 评级
        if total_score >= 90:
            grade = 'A'
        elif total_score >= 80:
            grade = 'B'
        elif total_score >= 70:
            grade = 'C'
        elif total_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'total_score': round(total_score, 2),
            'grade': grade,
            'components': {
                'success_rate_score': round(success_score, 2),
                'response_time_score': round(response_time_score, 2),
                'stability_score': round(stability_score, 2)
            },
            'recommendations': self._generate_recommendations(success_rate, avg_response_time, std_dev, error_rate)
        }
    
    def _generate_recommendations(self, success_rate: float, avg_response_time: float, 
                                std_dev: float, error_rate: float) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        if success_rate < 0.95:
            recommendations.append("成功率偏低，建议检查错误处理逻辑和网络连接稳定性")
        
        if avg_response_time > 3000:
            recommendations.append("平均响应时间过长，建议优化数据库查询和网络配置")
        
        if std_dev > 1000:
            recommendations.append("响应时间波动较大，建议检查系统负载和资源配置")
        
        if error_rate > 0.05:
            recommendations.append("错误率偏高，建议加强输入验证和异常处理")
        
        if avg_response_time > 1000 and std_dev < 500:
            recommendations.append("响应时间稳定但偏慢，可能是系统性能瓶颈，建议进行性能调优")
        
        if not recommendations:
            recommendations.append("性能表现良好，建议继续保持当前配置")
        
        return recommendations
    
    def _check_performance_alerts(self, api_code: str, metrics: Dict[str, float]) -> List[PerformanceAlert]:
        """检查性能告警"""
        alerts = []
        threshold = self.thresholds.get(api_code)
        
        if not threshold:
            return alerts
        
        current_time = datetime.now()
        
        # 检查响应时间告警
        avg_response_time = metrics.get('avg_response_time', 0)
        if avg_response_time > threshold.max_response_time_ms:
            severity = 'critical' if avg_response_time > threshold.max_response_time_ms * 1.5 else 'warning'
            alert = PerformanceAlert(
                alert_id=f"{api_code}_response_time_{int(time.time())}",
                alert_type='response_time',
                api_code=api_code,
                org_code='all',
                threshold_value=threshold.max_response_time_ms,
                actual_value=avg_response_time,
                severity=severity,
                timestamp=current_time,
                message=f"API {api_code} 平均响应时间 {avg_response_time:.2f}ms 超过阈值 {threshold.max_response_time_ms}ms"
            )
            alerts.append(alert)
        
        # 检查错误率告警
        error_rate = metrics.get('error_rate', 0)
        if error_rate > threshold.max_error_rate:
            severity = 'critical' if error_rate > threshold.max_error_rate * 2 else 'warning'
            alert = PerformanceAlert(
                alert_id=f"{api_code}_error_rate_{int(time.time())}",
                alert_type='error_rate',
                api_code=api_code,
                org_code='all',
                threshold_value=threshold.max_error_rate,
                actual_value=error_rate,
                severity=severity,
                timestamp=current_time,
                message=f"API {api_code} 错误率 {error_rate:.2%} 超过阈值 {threshold.max_error_rate:.2%}"
            )
            alerts.append(alert)
        
        # 检查成功率告警
        success_rate = metrics.get('success_rate', 0)
        if success_rate < threshold.min_success_rate:
            severity = 'critical' if success_rate < threshold.min_success_rate * 0.8 else 'warning'
            alert = PerformanceAlert(
                alert_id=f"{api_code}_success_rate_{int(time.time())}",
                alert_type='success_rate',
                api_code=api_code,
                org_code='all',
                threshold_value=threshold.min_success_rate,
                actual_value=success_rate,
                severity=severity,
                timestamp=current_time,
                message=f"API {api_code} 成功率 {success_rate:.2%} 低于阈值 {threshold.min_success_rate:.2%}"
            )
            alerts.append(alert)
        
        # 保存告警历史
        for alert in alerts:
            self.alerts_history.append(alert)
        
        return alerts
    
    def get_system_performance_overview(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """获取系统性能概览"""
        # 获取所有API的统计数据
        api_stats = self.metrics_collector.get_api_statistics(time_range_minutes)
        
        # 获取系统指标
        system_metrics = self.metrics_collector.get_system_metrics()
        
        # 分析各API性能
        api_performance = {}
        for api_code in api_stats.get('api_breakdown', {}).keys():
            api_performance[api_code] = self.analyze_api_performance(api_code, time_range_minutes)
        
        # 计算整体性能评分
        overall_score = self._calculate_overall_performance_score(api_performance)
        
        # 获取最近的告警
        recent_alerts = [
            alert for alert in self.alerts_history
            if alert.timestamp >= datetime.now() - timedelta(minutes=time_range_minutes)
        ]
        
        return {
            'overview_timestamp': datetime.now().isoformat(),
            'time_range_minutes': time_range_minutes,
            'overall_stats': api_stats,
            'system_metrics': system_metrics,
            'api_performance': api_performance,
            'overall_performance_score': overall_score,
            'recent_alerts': [
                {
                    'alert_id': alert.alert_id,
                    'alert_type': alert.alert_type,
                    'api_code': alert.api_code,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in recent_alerts
            ],
            'alert_summary': {
                'total_alerts': len(recent_alerts),
                'critical_alerts': sum(1 for alert in recent_alerts if alert.severity == 'critical'),
                'warning_alerts': sum(1 for alert in recent_alerts if alert.severity == 'warning')
            }
        }
    
    def _calculate_overall_performance_score(self, api_performance: Dict[str, Any]) -> Dict[str, Any]:
        """计算整体性能评分"""
        if not api_performance:
            return {'total_score': 0, 'grade': 'N/A', 'status': 'no_data'}
        
        # 计算加权平均分
        total_score = 0
        total_weight = 0
        
        for api_code, perf_data in api_performance.items():
            if perf_data.get('status') == 'analyzed':
                score = perf_data.get('performance_score', {}).get('total_score', 0)
                weight = perf_data.get('basic_stats', {}).get('total_calls', 1)
                
                total_score += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return {'total_score': 0, 'grade': 'N/A', 'status': 'no_data'}
        
        avg_score = total_score / total_weight
        
        # 评级
        if avg_score >= 90:
            grade = 'A'
        elif avg_score >= 80:
            grade = 'B'
        elif avg_score >= 70:
            grade = 'C'
        elif avg_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'total_score': round(avg_score, 2),
            'grade': grade,
            'status': 'calculated'
        }
    
    def export_performance_report(self, time_range_hours: int = 24, format: str = 'json') -> str:
        """导出性能报告"""
        report_data = self.get_system_performance_overview(time_range_hours * 60)
        
        if format.lower() == 'json':
            return json.dumps(report_data, indent=2, ensure_ascii=False, default=str)
        elif format.lower() == 'csv':
            # 简化的CSV格式
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题
            writer.writerow(['API代码', '总调用数', '成功率', '平均响应时间', '性能评分', '评级'])
            
            # 写入数据
            for api_code, perf_data in report_data.get('api_performance', {}).items():
                if perf_data.get('status') == 'analyzed':
                    basic_stats = perf_data.get('basic_stats', {})
                    perf_score = perf_data.get('performance_score', {})
                    
                    writer.writerow([
                        api_code,
                        basic_stats.get('total_calls', 0),
                        f"{basic_stats.get('success_rate', 0):.2%}",
                        f"{perf_data.get('response_time_stats', {}).get('mean', 0):.2f}ms",
                        perf_score.get('total_score', 0),
                        perf_score.get('grade', 'N/A')
                    ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")