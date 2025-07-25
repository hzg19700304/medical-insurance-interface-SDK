"""
测试性能监控和指标收集功能
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from medical_insurance_sdk.core.metrics_collector import (
    MetricsCollector,
    MetricConfig,
    PerformanceMetric,
    APICallMetric,
    get_metrics_collector,
    initialize_metrics_collector,
    monitor_api_call
)
from medical_insurance_sdk.core.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceThreshold,
    PerformanceAlert
)


class TestMetricsCollector:
    """测试指标收集器"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = MetricConfig(
            enabled=True,
            prometheus_enabled=False,  # 测试时禁用Prometheus
            collection_interval=1,
            retention_days=1,
            max_memory_metrics=100
        )
        self.collector = MetricsCollector(self.config)
    
    def test_record_api_call_lifecycle(self):
        """测试API调用生命周期记录"""
        # 开始记录
        call_id = self.collector.record_api_call_start("1101", "test_org", 1024)
        assert call_id is not None
        assert "1101_test_org" in call_id
        
        # 模拟一些处理时间
        time.sleep(0.1)
        
        # 结束记录
        self.collector.record_api_call_end(
            call_id, 
            'success', 
            response_size=2048
        )
        
        # 检查统计数据
        stats = self.collector.get_api_statistics(5)
        assert stats['total_calls'] == 1
        assert stats['successful_calls'] == 1
        assert stats['failed_calls'] == 0
        assert stats['success_rate'] > 0
        assert stats['average_response_time'] > 0
        assert '1101' in stats['api_breakdown']
    
    def test_record_api_call_error(self):
        """测试API调用错误记录"""
        call_id = self.collector.record_api_call_start("2201", "test_org")
        
        self.collector.record_api_call_end(
            call_id,
            'error',
            error_code='ValidationException',
            error_message='数据验证失败'
        )
        
        stats = self.collector.get_api_statistics(5)
        assert stats['total_calls'] == 1
        assert stats['successful_calls'] == 0
        assert stats['failed_calls'] == 1
        assert stats['success_rate'] == 0
        assert 'ValidationException' in stats['error_breakdown']
    
    def test_record_custom_metric(self):
        """测试自定义指标记录"""
        self.collector.record_custom_metric(
            "database_connections",
            10,
            "gauge",
            {"connection_type": "mysql"}
        )
        
        self.collector.record_custom_metric(
            "cache_hit_ratio",
            0.85,
            "gauge",
            {"cache_type": "redis"}
        )
        
        # 检查指标是否被记录
        assert len(self.collector._metrics_buffer) == 2
    
    def test_database_connections_metric(self):
        """测试数据库连接数指标"""
        self.collector.record_database_connections(15, "mysql")
        self.collector.record_database_connections(5, "redis")
        
        # 检查指标记录
        metrics = list(self.collector._metrics_buffer)
        db_metrics = [m for m in metrics if "database_connections" in m.metric_name]
        assert len(db_metrics) == 2
    
    def test_cache_hit_ratio_metric(self):
        """测试缓存命中率指标"""
        self.collector.record_cache_hit_ratio(0.92, "redis")
        self.collector.record_cache_hit_ratio(0.78, "memory")
        
        # 检查指标记录
        metrics = list(self.collector._metrics_buffer)
        cache_metrics = [m for m in metrics if "cache_hit_ratio" in m.metric_name]
        assert len(cache_metrics) == 2
    
    def test_concurrent_api_calls(self):
        """测试并发API调用记录"""
        def make_api_call(api_code, org_code, should_succeed=True):
            call_id = self.collector.record_api_call_start(api_code, org_code)
            time.sleep(0.05)  # 模拟处理时间
            
            if should_succeed:
                self.collector.record_api_call_end(call_id, 'success')
            else:
                self.collector.record_api_call_end(
                    call_id, 'error', error_code='TestError'
                )
        
        # 创建多个线程并发调用
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=make_api_call,
                args=(f"110{i % 3}", f"org_{i % 2}", i % 4 != 0)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查统计数据
        stats = self.collector.get_api_statistics(5)
        assert stats['total_calls'] == 10
        assert stats['successful_calls'] > 0
        assert stats['failed_calls'] > 0
    
    def test_api_statistics_time_range(self):
        """测试不同时间范围的统计"""
        # 记录一些旧的调用
        old_call_id = self.collector.record_api_call_start("1101", "old_org")
        
        # 手动设置旧时间
        with self.collector._lock:
            for call_id, metric in self.collector._api_calls_buffer:
                if call_id == old_call_id:
                    metric.start_time = datetime.now() - timedelta(hours=2)
                    break
        
        self.collector.record_api_call_end(old_call_id, 'success')
        
        # 记录新的调用
        new_call_id = self.collector.record_api_call_start("1101", "new_org")
        self.collector.record_api_call_end(new_call_id, 'success')
        
        # 测试不同时间范围
        stats_1h = self.collector.get_api_statistics(60)  # 1小时
        stats_3h = self.collector.get_api_statistics(180)  # 3小时
        
        assert stats_1h['total_calls'] == 1  # 只有新的调用
        assert stats_3h['total_calls'] == 2  # 包含旧的调用
    
    def test_cleanup_old_metrics(self):
        """测试清理过期指标"""
        # 添加一些指标
        for i in range(5):
            self.collector.record_custom_metric(f"test_metric_{i}", i, "gauge")
        
        # 手动设置过期时间
        cutoff_time = datetime.now() - timedelta(days=2)
        with self.collector._lock:
            for metric in list(self.collector._metrics_buffer):
                if metric.metric_name in ["test_metric_0", "test_metric_1"]:
                    metric.timestamp = cutoff_time
        
        # 执行清理
        self.collector.cleanup_old_metrics()
        
        # 检查清理结果
        remaining_metrics = [
            m for m in self.collector._metrics_buffer
            if m.metric_name.startswith("test_metric_")
        ]
        assert len(remaining_metrics) == 3  # 应该剩余3个未过期的指标
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    @patch('psutil.disk_usage')
    def test_system_metrics(self, mock_disk_usage, mock_cpu_count, mock_virtual_memory, mock_process_class):
        """测试系统指标获取"""
        # Mock psutil components
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=1024*1024, vms=2048*1024)
        mock_process.memory_percent.return_value = 5.5
        mock_process.cpu_percent.return_value = 15.2
        mock_process.num_threads.return_value = 8
        mock_process.create_time.return_value = time.time() - 3600
        
        mock_process_class.return_value = mock_process
        mock_virtual_memory.return_value = Mock(
            total=8*1024*1024*1024,
            available=4*1024*1024*1024,
            percent=50.0
        )
        mock_cpu_count.return_value = 4
        mock_disk_usage.return_value = Mock(
            total=100*1024*1024*1024,
            used=60*1024*1024*1024,
            free=40*1024*1024*1024
        )
        
        # 获取系统指标
        metrics = self.collector.get_system_metrics()
        
        # 验证指标结构
        assert 'process' in metrics
        assert 'system' in metrics
        assert 'timestamp' in metrics
        
        assert metrics['process']['memory_rss'] == 1024*1024
        assert metrics['process']['cpu_percent'] == 15.2
        assert metrics['system']['cpu_count'] == 4
    
    def test_performance_report_generation(self):
        """测试性能报告生成"""
        # 添加一些测试数据
        for i in range(3):
            call_id = self.collector.record_api_call_start(f"110{i}", "test_org")
            time.sleep(0.01)
            self.collector.record_api_call_end(call_id, 'success')
        
        # 添加一个失败的调用
        fail_call_id = self.collector.record_api_call_start("2201", "test_org")
        self.collector.record_api_call_end(
            fail_call_id, 'error', error_code='TestError'
        )
        
        # 生成报告
        report = self.collector.generate_performance_report(1)
        
        # 验证报告结构
        assert 'report_time' in report
        assert 'api_statistics' in report
        assert 'system_metrics' in report
        assert 'prometheus_available' in report
        
        # 验证API统计
        api_stats = report['api_statistics']
        assert api_stats['total_calls'] == 4
        assert api_stats['successful_calls'] == 3
        assert api_stats['failed_calls'] == 1


class TestPerformanceAnalyzer:
    """测试性能分析器"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = MetricConfig(prometheus_enabled=False)
        self.collector = MetricsCollector(self.config)
        self.analyzer = PerformanceAnalyzer(self.collector)
    
    def test_set_threshold(self):
        """测试设置性能阈值"""
        threshold = PerformanceThreshold(
            api_code="1101",
            max_response_time_ms=3000.0,
            max_error_rate=0.03,
            min_success_rate=0.97
        )
        
        self.analyzer.set_threshold("1101", threshold)
        assert "1101" in self.analyzer.thresholds
        assert self.analyzer.thresholds["1101"].max_response_time_ms == 3000.0
    
    def test_analyze_api_performance_no_data(self):
        """测试无数据时的性能分析"""
        result = self.analyzer.analyze_api_performance("1101", 60)
        
        assert result['api_code'] == "1101"
        assert result['total_calls'] == 0
        assert result['status'] == 'no_data'
    
    def test_analyze_api_performance_with_data(self):
        """测试有数据时的性能分析"""
        # 添加测试数据
        for i in range(5):
            call_id = self.collector.record_api_call_start("1101", "test_org")
            time.sleep(0.01)
            status = 'success' if i < 4 else 'error'
            error_code = None if status == 'success' else 'TestError'
            self.collector.record_api_call_end(call_id, status, error_code=error_code)
        
        # 分析性能
        result = self.analyzer.analyze_api_performance("1101", 60)
        
        # 验证分析结果
        assert result['api_code'] == "1101"
        assert result['status'] == 'analyzed'
        assert result['basic_stats']['total_calls'] == 5
        assert result['basic_stats']['successful_calls'] == 4
        assert result['basic_stats']['failed_calls'] == 1
        assert result['basic_stats']['success_rate'] == 0.8
        assert result['basic_stats']['error_rate'] == 0.2
        
        # 验证响应时间统计
        response_stats = result['response_time_stats']
        assert response_stats['count'] == 5
        assert response_stats['mean'] > 0
        assert response_stats['min'] > 0
        assert response_stats['max'] > 0
        
        # 验证错误分析
        error_analysis = result['error_analysis']
        assert error_analysis['total_errors'] == 1
        assert 'TestError' in error_analysis['error_types']
        
        # 验证性能评分
        perf_score = result['performance_score']
        assert 'total_score' in perf_score
        assert 'grade' in perf_score
        assert 'components' in perf_score
        assert 'recommendations' in perf_score
    
    def test_performance_alerts(self):
        """测试性能告警"""
        # 设置严格的阈值
        threshold = PerformanceThreshold(
            api_code="1101",
            max_response_time_ms=1.0,  # 1毫秒，很容易超过
            max_error_rate=0.01,  # 1%错误率
            min_success_rate=0.99  # 99%成功率
        )
        self.analyzer.set_threshold("1101", threshold)
        
        # 添加会触发告警的数据
        for i in range(10):
            call_id = self.collector.record_api_call_start("1101", "test_org")
            time.sleep(0.01)  # 10毫秒，超过阈值
            status = 'success' if i < 8 else 'error'  # 20%错误率
            self.collector.record_api_call_end(call_id, status, error_code='TestError' if status == 'error' else None)
        
        # 分析性能（应该触发告警）
        result = self.analyzer.analyze_api_performance("1101", 60)
        
        # 检查告警
        alerts = result['alerts']
        assert len(alerts) > 0
        
        # 应该有响应时间和错误率告警
        alert_types = [alert.alert_type for alert in alerts]
        assert 'response_time' in alert_types
        assert 'error_rate' in alert_types or 'success_rate' in alert_types
    
    def test_system_performance_overview(self):
        """测试系统性能概览"""
        # 添加多个API的测试数据
        apis = ["1101", "2201", "1301"]
        for api_code in apis:
            for i in range(3):
                call_id = self.collector.record_api_call_start(api_code, "test_org")
                time.sleep(0.005)
                self.collector.record_api_call_end(call_id, 'success')
        
        # 获取系统概览
        overview = self.analyzer.get_system_performance_overview(60)
        
        # 验证概览结构
        assert 'overview_timestamp' in overview
        assert 'overall_stats' in overview
        assert 'system_metrics' in overview
        assert 'api_performance' in overview
        assert 'overall_performance_score' in overview
        assert 'recent_alerts' in overview
        assert 'alert_summary' in overview
        
        # 验证API性能数据
        api_performance = overview['api_performance']
        for api_code in apis:
            assert api_code in api_performance
            assert api_performance[api_code]['status'] == 'analyzed'
    
    def test_export_performance_report_json(self):
        """测试导出JSON格式性能报告"""
        # 添加测试数据
        call_id = self.collector.record_api_call_start("1101", "test_org")
        self.collector.record_api_call_end(call_id, 'success')
        
        # 导出JSON报告
        json_report = self.analyzer.export_performance_report(1, 'json')
        
        assert isinstance(json_report, str)
        assert '"api_code": "1101"' in json_report or "'api_code': '1101'" in json_report
    
    def test_export_performance_report_csv(self):
        """测试导出CSV格式性能报告"""
        # 添加测试数据
        call_id = self.collector.record_api_call_start("1101", "test_org")
        self.collector.record_api_call_end(call_id, 'success')
        
        # 导出CSV报告
        csv_report = self.analyzer.export_performance_report(1, 'csv')
        
        assert isinstance(csv_report, str)
        assert 'API代码' in csv_report
        assert '1101' in csv_report


class TestMonitorDecorator:
    """测试监控装饰器"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = MetricConfig(prometheus_enabled=False)
        initialize_metrics_collector(self.config)
    
    def test_monitor_api_call_decorator_success(self):
        """测试API调用监控装饰器 - 成功情况"""
        @monitor_api_call(api_code="1101", org_code="test_org")
        def test_function():
            time.sleep(0.01)
            return "success"
        
        result = test_function()
        assert result == "success"
        
        # 检查指标是否被记录
        collector = get_metrics_collector()
        stats = collector.get_api_statistics(5)
        assert stats['total_calls'] >= 1
    
    def test_monitor_api_call_decorator_error(self):
        """测试API调用监控装饰器 - 错误情况"""
        @monitor_api_call(api_code="1101", org_code="test_org")
        def test_function():
            raise ValueError("测试错误")
        
        with pytest.raises(ValueError):
            test_function()
        
        # 检查错误指标是否被记录
        collector = get_metrics_collector()
        stats = collector.get_api_statistics(5)
        assert stats['failed_calls'] >= 1
        assert 'ValueError' in stats['error_breakdown']
    
    def test_monitor_api_call_decorator_with_args(self):
        """测试监控装饰器从参数中提取信息"""
        @monitor_api_call()
        def test_function(api_code, org_code, data):
            return f"Called {api_code} for {org_code}"
        
        result = test_function("2201", "test_org", {"test": "data"})
        assert "2201" in result
        
        # 检查指标记录
        collector = get_metrics_collector()
        stats = collector.get_api_statistics(5)
        assert '2201' in stats['api_breakdown']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])