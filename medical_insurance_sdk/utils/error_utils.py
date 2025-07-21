"""错误处理工具函数

提供错误处理相关的工具函数和辅助类
"""

import traceback
import sys
from typing import Dict, Any, Optional, List, Type
from datetime import datetime

from ..exceptions import MedicalInsuranceException, ExceptionFactory


class ErrorContext:
    """错误上下文管理器"""
    
    def __init__(self, operation: str, **context_data):
        self.operation = operation
        self.context_data = context_data
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.exception: Optional[Exception] = None
        self.success = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        if exc_type is not None:
            self.success = False
            self.exception = exc_val
        return False  # 不抑制异常
    
    def get_duration(self) -> float:
        """获取操作持续时间（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "operation": self.operation,
            "context_data": self.context_data,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration(),
            "success": self.success,
            "exception": str(self.exception) if self.exception else None,
            "exception_type": type(self.exception).__name__ if self.exception else None
        }


class ErrorAggregator:
    """错误聚合器，用于收集和分析多个错误"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}
        self.first_error_time: Optional[datetime] = None
        self.last_error_time: Optional[datetime] = None
    
    def add_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """添加错误"""
        error_time = datetime.now()
        
        if self.first_error_time is None:
            self.first_error_time = error_time
        self.last_error_time = error_time
        
        error_type = type(exception).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_info = {
            "exception_type": error_type,
            "message": str(exception),
            "timestamp": error_time.isoformat(),
            "context": context or {}
        }
        
        if isinstance(exception, MedicalInsuranceException):
            error_info.update({
                "error_code": exception.error_code,
                "details": exception.details,
                "exception_id": exception.exception_id
            })
        
        self.errors.append(error_info)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return {
            "total_errors": len(self.errors),
            "error_types": self.error_counts,
            "first_error_time": self.first_error_time.isoformat() if self.first_error_time else None,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """获取详细错误报告"""
        return {
            "summary": self.get_summary(),
            "errors": self.errors
        }
    
    def clear(self):
        """清空错误记录"""
        self.errors.clear()
        self.error_counts.clear()
        self.first_error_time = None
        self.last_error_time = None


def extract_exception_info(exception: Exception) -> Dict[str, Any]:
    """提取异常详细信息"""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    info = {
        "type": type(exception).__name__,
        "message": str(exception),
        "module": getattr(exception, '__module__', None),
        "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else None
    }
    
    # 如果是医保SDK异常，添加额外信息
    if isinstance(exception, MedicalInsuranceException):
        info.update({
            "error_code": exception.error_code,
            "details": exception.details,
            "severity": exception.severity,
            "exception_id": exception.exception_id,
            "timestamp": exception.timestamp.isoformat(),
            "retryable": exception.is_retryable(),
            "user_message": exception.get_user_message()
        })
    
    return info


def format_error_for_logging(exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """格式化错误信息用于日志记录"""
    log_data = extract_exception_info(exception)
    
    if context:
        log_data["context"] = context
    
    # 添加系统信息
    log_data["system_info"] = {
        "python_version": sys.version,
        "platform": sys.platform,
        "timestamp": datetime.now().isoformat()
    }
    
    return log_data


def format_error_for_user(exception: Exception) -> Dict[str, Any]:
    """格式化错误信息用于用户显示"""
    if isinstance(exception, MedicalInsuranceException):
        return {
            "success": False,
            "error_code": exception.error_code,
            "message": exception.get_user_message(),
            "timestamp": datetime.now().isoformat(),
            "retryable": exception.is_retryable(),
            "retry_after": getattr(exception, 'retry_after', None)
        }
    else:
        return {
            "success": False,
            "error_code": "UNKNOWN_ERROR",
            "message": "系统异常，请稍后重试",
            "timestamp": datetime.now().isoformat(),
            "retryable": False
        }


def create_error_response(
    exception: Exception,
    operation: str,
    request_id: Optional[str] = None,
    include_details: bool = False
) -> Dict[str, Any]:
    """创建标准化的错误响应"""
    response = {
        "success": False,
        "operation": operation,
        "timestamp": datetime.now().isoformat()
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if isinstance(exception, MedicalInsuranceException):
        response.update({
            "error_code": exception.error_code,
            "message": exception.get_user_message(),
            "exception_id": exception.exception_id,
            "retryable": exception.is_retryable()
        })
        
        if exception.retry_after:
            response["retry_after"] = exception.retry_after
        
        if include_details and exception.details:
            response["details"] = exception.details
    else:
        response.update({
            "error_code": "SYSTEM_ERROR",
            "message": "系统异常，请联系管理员",
            "retryable": False
        })
    
    return response


def is_critical_error(exception: Exception) -> bool:
    """判断是否为严重错误"""
    if isinstance(exception, MedicalInsuranceException):
        return exception.severity == "CRITICAL"
    
    # 系统级异常通常是严重的
    critical_types = [
        SystemError,
        MemoryError,
        KeyboardInterrupt,
        SystemExit
    ]
    
    return any(isinstance(exception, exc_type) for exc_type in critical_types)


def should_alert(exception: Exception, error_count: int = 1, time_window_minutes: int = 5) -> bool:
    """判断是否应该发送告警"""
    # 严重错误立即告警
    if is_critical_error(exception):
        return True
    
    # 短时间内大量错误需要告警
    if error_count >= 10:
        return True
    
    # 特定类型的错误需要告警
    alert_types = [
        "CircuitBreakerException",
        "ServiceUnavailableException",
        "ResourceExhaustedException"
    ]
    
    return type(exception).__name__ in alert_types


def sanitize_error_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理错误数据中的敏感信息"""
    sensitive_keys = [
        "password", "secret", "token", "key", "credential",
        "app_secret", "access_key", "private_key"
    ]
    
    def _sanitize_value(value):
        if isinstance(value, dict):
            return {k: _sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_sanitize_value(item) for item in value]
        elif isinstance(value, str):
            return value[:50] + "..." if len(value) > 50 else value
        else:
            return value
    
    def _sanitize_dict(d):
        result = {}
        for key, value in d.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                result[key] = "***REDACTED***"
            else:
                result[key] = _sanitize_value(value)
        return result
    
    return _sanitize_dict(data)


class ErrorReporter:
    """错误报告器"""
    
    def __init__(self, report_handlers: Optional[List] = None):
        self.report_handlers = report_handlers or []
        self.error_aggregator = ErrorAggregator()
    
    def add_handler(self, handler):
        """添加报告处理器"""
        self.report_handlers.append(handler)
    
    def report_error(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        should_aggregate: bool = True
    ):
        """报告错误"""
        if should_aggregate:
            self.error_aggregator.add_error(exception, context)
        
        # 清理敏感数据
        safe_context = sanitize_error_data(context or {})
        
        # 格式化错误信息
        error_info = format_error_for_logging(exception, safe_context)
        
        # 发送到各个处理器
        for handler in self.report_handlers:
            try:
                handler.handle_error(error_info)
            except Exception as handler_error:
                # 处理器本身出错不应该影响主流程
                print(f"错误报告处理器异常: {handler_error}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成错误报告"""
        return self.error_aggregator.get_detailed_report()
    
    def clear_aggregated_errors(self):
        """清空聚合的错误"""
        self.error_aggregator.clear()


# 全局错误报告器实例
default_error_reporter = ErrorReporter()


def report_error(exception: Exception, context: Optional[Dict[str, Any]] = None):
    """报告错误的便捷函数"""
    default_error_reporter.report_error(exception, context)


def with_error_context(operation: str, **context_data):
    """错误上下文装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ErrorContext(operation, **context_data) as ctx:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 添加上下文信息到异常
                    if isinstance(e, MedicalInsuranceException):
                        e.details.update(ctx.to_dict())
                    report_error(e, ctx.to_dict())
                    raise
        return wrapper
    return decorator