"""医保SDK错误处理器

统一的异常处理逻辑，包括错误重试和降级机制
"""

import time
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, List, Union, Type
from functools import wraps
from datetime import datetime, timedelta

from ..exceptions import (
    MedicalInsuranceException,
    NetworkException,
    TimeoutException,
    ConnectionException,
    TooManyRequestsException,
    CircuitBreakerException,
    ServiceUnavailableException,
    ExceptionFactory
)


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            NetworkException,
            TimeoutException,
            ConnectionException,
            ServiceUnavailableException
        ]
    
    def is_retryable(self, exception: Exception) -> bool:
        """判断异常是否可重试"""
        if isinstance(exception, MedicalInsuranceException):
            return exception.is_retryable()
        
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
    
    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        self._lock = asyncio.Lock() if asyncio.iscoroutinefunction else None
    
    def is_open(self) -> bool:
        """判断熔断器是否开启"""
        if self.state == "OPEN":
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        """记录成功调用"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None
    
    def record_failure(self):
        """记录失败调用"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        if self.is_open():
            raise CircuitBreakerException(
                service_name=func.__name__,
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise


class FallbackHandler:
    """降级处理器"""
    
    def __init__(self):
        self.fallback_strategies: Dict[str, Callable] = {}
    
    def register_fallback(self, operation_name: str, fallback_func: Callable):
        """注册降级策略"""
        self.fallback_strategies[operation_name] = fallback_func
    
    def execute_fallback(self, operation_name: str, exception: Exception, *args, **kwargs):
        """执行降级策略"""
        if operation_name in self.fallback_strategies:
            try:
                return self.fallback_strategies[operation_name](exception, *args, **kwargs)
            except Exception as fallback_error:
                logging.error(f"降级策略执行失败: {fallback_error}")
                raise exception
        
        # 默认降级策略
        return self._default_fallback(exception, *args, **kwargs)
    
    def _default_fallback(self, exception: Exception, *args, **kwargs):
        """默认降级策略"""
        if isinstance(exception, NetworkException):
            return {
                "success": False,
                "error": "网络异常，请稍后重试",
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": False,
            "error": "服务暂时不可用，请稍后重试",
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        enable_circuit_breaker: bool = True,
        enable_fallback: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        self.retry_config = retry_config or RetryConfig()
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_fallback = enable_fallback
        self.logger = logger or logging.getLogger(__name__)
        
        # 熔断器实例字典，按服务名称分组
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 降级处理器
        self.fallback_handler = FallbackHandler()
        
        # 错误统计
        self.error_stats: Dict[str, Dict[str, Any]] = {}
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """获取或创建熔断器"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def record_error_stats(self, operation: str, exception: Exception):
        """记录错误统计"""
        if operation not in self.error_stats:
            self.error_stats[operation] = {
                "total_errors": 0,
                "error_types": {},
                "last_error_time": None
            }
        
        stats = self.error_stats[operation]
        stats["total_errors"] += 1
        stats["last_error_time"] = datetime.now()
        
        error_type = type(exception).__name__
        if error_type not in stats["error_types"]:
            stats["error_types"][error_type] = 0
        stats["error_types"][error_type] += 1
    
    def handle_exception(
        self,
        exception: Exception,
        operation_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理异常并返回标准化的错误响应"""
        context = context or {}
        
        # 记录错误统计
        self.record_error_stats(operation_name, exception)
        
        # 标准化异常
        if not isinstance(exception, MedicalInsuranceException):
            exception = self._standardize_exception(exception)
        
        # 记录日志
        self._log_exception(exception, operation_name, context)
        
        # 构建错误响应
        error_response = {
            "success": False,
            "error_code": exception.error_code if hasattr(exception, 'error_code') else "UNKNOWN_ERROR",
            "error_message": str(exception),
            "operation": operation_name,
            "timestamp": datetime.now().isoformat(),
            "exception_id": getattr(exception, 'exception_id', None),
            "retryable": self._is_retryable(exception),
            "context": context
        }
        
        # 添加详细信息
        if hasattr(exception, 'details'):
            error_response["details"] = exception.details
        
        if hasattr(exception, 'retry_after'):
            error_response["retry_after"] = exception.retry_after
        
        return error_response
    
    def _standardize_exception(self, exception: Exception) -> MedicalInsuranceException:
        """标准化异常为医保SDK异常"""
        if isinstance(exception, ConnectionError):
            return ConnectionException(str(exception), cause=exception)
        elif isinstance(exception, TimeoutError):
            return TimeoutException(30, cause=exception)
        elif isinstance(exception, ValueError):
            return ValidationException(str(exception), cause=exception)
        else:
            return MedicalInsuranceException(
                str(exception),
                error_code="UNKNOWN_ERROR",
                cause=exception
            )
    
    def _is_retryable(self, exception: Exception) -> bool:
        """判断异常是否可重试"""
        if isinstance(exception, MedicalInsuranceException):
            return exception.is_retryable()
        return self.retry_config.is_retryable(exception)
    
    def _log_exception(self, exception: Exception, operation_name: str, context: Dict[str, Any]):
        """记录异常日志"""
        log_data = {
            "operation": operation_name,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context": context
        }
        
        if hasattr(exception, 'exception_id'):
            log_data["exception_id"] = exception.exception_id
        
        if hasattr(exception, 'severity'):
            severity = exception.severity
            if severity == "CRITICAL":
                self.logger.critical("严重异常", extra=log_data)
            elif severity == "ERROR":
                self.logger.error("错误异常", extra=log_data)
            else:
                self.logger.warning("警告异常", extra=log_data)
        else:
            self.logger.error("未分类异常", extra=log_data)
    
    def with_retry(
        self,
        operation_name: str,
        retry_config: Optional[RetryConfig] = None
    ):
        """重试装饰器"""
        config = retry_config or self.retry_config
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(1, config.max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        if not config.is_retryable(e):
                            self.logger.info(f"异常不可重试: {e}")
                            break
                        
                        if attempt == config.max_attempts:
                            self.logger.warning(f"重试次数已达上限 ({config.max_attempts})")
                            break
                        
                        delay = config.calculate_delay(attempt)
                        self.logger.info(f"第{attempt}次重试失败，{delay:.2f}秒后重试: {e}")
                        time.sleep(delay)
                
                # 所有重试都失败了
                raise last_exception
            
            return wrapper
        return decorator
    
    def with_circuit_breaker(self, service_name: str):
        """熔断器装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enable_circuit_breaker:
                    return func(*args, **kwargs)
                
                circuit_breaker = self.get_circuit_breaker(service_name)
                return circuit_breaker.call(func, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def with_fallback(self, operation_name: str, fallback_func: Optional[Callable] = None):
        """降级装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if not self.enable_fallback:
                        raise
                    
                    self.logger.warning(f"操作 {operation_name} 失败，执行降级策略: {e}")
                    
                    if fallback_func:
                        return fallback_func(e, *args, **kwargs)
                    else:
                        return self.fallback_handler.execute_fallback(
                            operation_name, e, *args, **kwargs
                        )
            
            return wrapper
        return decorator
    
    def with_error_handling(
        self,
        operation_name: str,
        retry_config: Optional[RetryConfig] = None,
        enable_circuit_breaker: bool = True,
        fallback_func: Optional[Callable] = None
    ):
        """综合错误处理装饰器"""
        def decorator(func):
            # 应用装饰器链
            wrapped_func = func
            
            # 1. 降级处理
            if self.enable_fallback:
                wrapped_func = self.with_fallback(operation_name, fallback_func)(wrapped_func)
            
            # 2. 熔断器
            if self.enable_circuit_breaker and enable_circuit_breaker:
                wrapped_func = self.with_circuit_breaker(operation_name)(wrapped_func)
            
            # 3. 重试机制
            wrapped_func = self.with_retry(operation_name, retry_config)(wrapped_func)
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return wrapped_func(*args, **kwargs)
                except Exception as e:
                    # 最终异常处理
                    error_response = self.handle_exception(e, operation_name, {
                        "args": str(args)[:200],
                        "kwargs": {k: str(v)[:100] for k, v in kwargs.items()}
                    })
                    
                    # 重新抛出标准化异常
                    if isinstance(e, MedicalInsuranceException):
                        raise
                    else:
                        raise self._standardize_exception(e)
            
            return wrapper
        return decorator
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "error_stats": self.error_stats,
            "circuit_breaker_stats": {
                name: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure_time": cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for name, cb in self.circuit_breakers.items()
            }
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.error_stats.clear()
        for cb in self.circuit_breakers.values():
            cb.failure_count = 0
            cb.state = "CLOSED"
            cb.last_failure_time = None
    
    def register_fallback_strategy(self, operation_name: str, fallback_func: Callable):
        """注册降级策略"""
        self.fallback_handler.register_fallback(operation_name, fallback_func)
    
    def configure_retry_for_operation(self, operation_name: str, retry_config: RetryConfig):
        """为特定操作配置重试策略"""
        if not hasattr(self, 'operation_retry_configs'):
            self.operation_retry_configs = {}
        self.operation_retry_configs[operation_name] = retry_config
    
    def get_retry_config_for_operation(self, operation_name: str) -> RetryConfig:
        """获取特定操作的重试配置"""
        if hasattr(self, 'operation_retry_configs') and operation_name in self.operation_retry_configs:
            return self.operation_retry_configs[operation_name]
        return self.retry_config
    
    def is_operation_healthy(self, operation_name: str) -> bool:
        """检查操作是否健康（基于错误率和熔断器状态）"""
        # 检查熔断器状态
        if operation_name in self.circuit_breakers:
            cb = self.circuit_breakers[operation_name]
            if cb.is_open():
                return False
        
        # 检查错误率
        if operation_name in self.error_stats:
            stats = self.error_stats[operation_name]
            # 如果最近5分钟内错误超过50次，认为不健康
            if stats["total_errors"] > 50:
                from datetime import datetime, timedelta
                if stats["last_error_time"] and \
                   datetime.now() - stats["last_error_time"] < timedelta(minutes=5):
                    return False
        
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        healthy_operations = []
        unhealthy_operations = []
        
        # 检查所有已知操作
        all_operations = set()
        all_operations.update(self.error_stats.keys())
        all_operations.update(self.circuit_breakers.keys())
        
        for operation in all_operations:
            if self.is_operation_healthy(operation):
                healthy_operations.append(operation)
            else:
                unhealthy_operations.append(operation)
        
        return {
            "overall_healthy": len(unhealthy_operations) == 0,
            "healthy_operations": healthy_operations,
            "unhealthy_operations": unhealthy_operations,
            "total_operations": len(all_operations),
            "health_score": len(healthy_operations) / len(all_operations) if all_operations else 1.0
        }
    
    def force_circuit_breaker_reset(self, service_name: str):
        """强制重置熔断器"""
        if service_name in self.circuit_breakers:
            cb = self.circuit_breakers[service_name]
            cb.record_success()
            self.logger.info(f"熔断器 {service_name} 已强制重置")
    
    def set_global_error_threshold(self, threshold: int, time_window_minutes: int = 5):
        """设置全局错误阈值"""
        self.global_error_threshold = threshold
        self.global_error_time_window = time_window_minutes
    
    def check_global_error_threshold(self) -> bool:
        """检查是否超过全局错误阈值"""
        if not hasattr(self, 'global_error_threshold'):
            return False
        
        from datetime import datetime, timedelta
        current_time = datetime.now()
        time_threshold = current_time - timedelta(minutes=getattr(self, 'global_error_time_window', 5))
        
        total_recent_errors = 0
        for stats in self.error_stats.values():
            if stats["last_error_time"] and stats["last_error_time"] > time_threshold:
                total_recent_errors += stats["total_errors"]
        
        return total_recent_errors > self.global_error_threshold


# 全局错误处理器实例
default_error_handler = ErrorHandler()


def handle_medical_interface_error(func):
    """医保接口专用错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = f"medical_interface_{func.__name__}"
        
        # 医保接口特定的重试配置
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=30.0,
            retryable_exceptions=[
                NetworkException,
                TimeoutException,
                ConnectionException,
                TooManyRequestsException
            ]
        )
        
        return default_error_handler.with_error_handling(
            operation_name=operation_name,
            retry_config=retry_config,
            enable_circuit_breaker=True
        )(func)(*args, **kwargs)
    
    return wrapper


def handle_database_error(func):
    """数据库操作专用错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = f"database_{func.__name__}"
        
        # 数据库操作的重试配置
        retry_config = RetryConfig(
            max_attempts=2,
            base_delay=1.0,
            max_delay=10.0,
            retryable_exceptions=[
                ConnectionException,
                TimeoutException
            ]
        )
        
        return default_error_handler.with_error_handling(
            operation_name=operation_name,
            retry_config=retry_config,
            enable_circuit_breaker=False  # 数据库操作不使用熔断器
        )(func)(*args, **kwargs)
    
    return wrapper


def handle_cache_error(func):
    """缓存操作专用错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = f"cache_{func.__name__}"
        
        # 缓存操作的降级策略：缓存失败时直接返回None或默认值
        def cache_fallback(exception, *args, **kwargs):
            default_error_handler.logger.warning(f"缓存操作失败，使用降级策略: {exception}")
            return None
        
        return default_error_handler.with_error_handling(
            operation_name=operation_name,
            retry_config=RetryConfig(max_attempts=1),  # 缓存操作不重试
            enable_circuit_breaker=False,
            fallback_func=cache_fallback
        )(func)(*args, **kwargs)
    
    return wrapper


def handle_config_error(func):
    """配置操作专用错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = f"config_{func.__name__}"
        
        # 配置操作的重试配置
        retry_config = RetryConfig(
            max_attempts=2,
            base_delay=0.5,
            max_delay=5.0,
            retryable_exceptions=[
                ConnectionException,
                TimeoutException,
                DatabaseException
            ]
        )
        
        return default_error_handler.with_error_handling(
            operation_name=operation_name,
            retry_config=retry_config,
            enable_circuit_breaker=False  # 配置操作不使用熔断器
        )(func)(*args, **kwargs)
    
    return wrapper


def handle_validation_error(func):
    """数据验证专用错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = f"validation_{func.__name__}"
        
        try:
            return func(*args, **kwargs)
        except ValidationException:
            # 验证异常不需要重试，直接抛出
            raise
        except Exception as e:
            # 其他异常包装为验证异常
            from ..exceptions import ExceptionFactory
            wrapped_exception = ExceptionFactory.wrap_exception(e, {
                "operation": operation_name,
                "function": func.__name__
            })
            raise wrapped_exception
    
    return wrapper


def handle_async_task_error(func):
    """异步任务专用错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_name = f"async_task_{func.__name__}"
        
        # 异步任务的重试配置
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=5.0,
            max_delay=60.0,
            retryable_exceptions=[
                NetworkException,
                TimeoutException,
                ConnectionException,
                ServiceUnavailableException
            ]
        )
        
        # 异步任务的降级策略
        def async_fallback(exception, *args, **kwargs):
            default_error_handler.logger.error(f"异步任务失败，记录失败状态: {exception}")
            return {
                "success": False,
                "error": str(exception),
                "fallback": True,
                "retry_later": True
            }
        
        return default_error_handler.with_error_handling(
            operation_name=operation_name,
            retry_config=retry_config,
            enable_circuit_breaker=True,
            fallback_func=async_fallback
        )(func)(*args, **kwargs)
    
    return wrapper


class MedicalInterfaceErrorHandler:
    """医保接口专用错误处理器"""
    
    def __init__(self, base_error_handler: Optional[ErrorHandler] = None):
        self.base_handler = base_error_handler or default_error_handler
        self.interface_specific_configs = {}
        self.interface_fallback_strategies = {}
    
    def configure_interface_retry(self, api_code: str, retry_config: RetryConfig):
        """为特定接口配置重试策略"""
        self.interface_specific_configs[api_code] = retry_config
    
    def register_interface_fallback(self, api_code: str, fallback_func: Callable):
        """为特定接口注册降级策略"""
        self.interface_fallback_strategies[api_code] = fallback_func
    
    def handle_interface_call(self, api_code: str):
        """医保接口调用错误处理装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                operation_name = f"medical_interface_{api_code}"
                
                # 获取接口特定的重试配置
                retry_config = self.interface_specific_configs.get(
                    api_code,
                    RetryConfig(
                        max_attempts=3,
                        base_delay=2.0,
                        max_delay=30.0,
                        retryable_exceptions=[
                            NetworkException,
                            TimeoutException,
                            ConnectionException,
                            TooManyRequestsException
                        ]
                    )
                )
                
                # 获取接口特定的降级策略
                fallback_func = self.interface_fallback_strategies.get(api_code)
                
                return self.base_handler.with_error_handling(
                    operation_name=operation_name,
                    retry_config=retry_config,
                    enable_circuit_breaker=True,
                    fallback_func=fallback_func
                )(func)(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_interface_health_status(self, api_code: str) -> Dict[str, Any]:
        """获取特定接口的健康状态"""
        operation_name = f"medical_interface_{api_code}"
        
        is_healthy = self.base_handler.is_operation_healthy(operation_name)
        
        # 获取错误统计
        error_stats = self.base_handler.error_stats.get(operation_name, {})
        
        # 获取熔断器状态
        circuit_breaker_status = None
        if operation_name in self.base_handler.circuit_breakers:
            cb = self.base_handler.circuit_breakers[operation_name]
            circuit_breaker_status = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure_time": cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }
        
        return {
            "api_code": api_code,
            "healthy": is_healthy,
            "error_stats": error_stats,
            "circuit_breaker": circuit_breaker_status,
            "has_custom_config": api_code in self.interface_specific_configs,
            "has_fallback_strategy": api_code in self.interface_fallback_strategies
        }


# 全局医保接口错误处理器实例
medical_interface_error_handler = MedicalInterfaceErrorHandler()