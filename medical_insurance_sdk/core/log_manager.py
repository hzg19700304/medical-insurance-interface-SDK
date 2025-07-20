"""日志管理器模块"""

import logging
import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import uuid
import traceback

from ..models.log import OperationLog
from ..models.config import OrganizationConfig, InterfaceConfig


class LogManager:
    """日志管理器 - 支持结构化日志和异步写入"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化日志管理器
        
        Args:
            config: 日志配置
                - log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
                - log_dir: 日志目录
                - max_file_size: 单个日志文件最大大小(MB)
                - backup_count: 备份文件数量
                - enable_async: 是否启用异步写入
                - enable_console: 是否启用控制台输出
                - structured_format: 是否使用结构化格式
        """
        self.config = config
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建不同类型的日志记录器
        self._setup_loggers()
        
        # 异步日志队列
        self.async_enabled = config.get('enable_async', True)
        if self.async_enabled:
            self.log_queue = Queue()
            self.async_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="LogWriter")
            self._start_async_writer()
    
    def _setup_loggers(self):
        """设置日志记录器"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        
        # 主日志记录器
        self.main_logger = self._create_logger(
            'medical_insurance_sdk',
            'medical_insurance_sdk.log',
            log_level
        )
        
        # API调用日志记录器
        self.api_logger = self._create_logger(
            'medical_insurance_sdk.api',
            'api_calls.log',
            log_level
        )
        
        # 错误日志记录器
        self.error_logger = self._create_logger(
            'medical_insurance_sdk.error',
            'errors.log',
            logging.ERROR
        )
        
        # 性能日志记录器
        self.performance_logger = self._create_logger(
            'medical_insurance_sdk.performance',
            'performance.log',
            log_level
        )
    
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """创建日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 文件处理器 - 按大小轮转
        file_handler = RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=self.config.get('max_file_size', 10) * 1024 * 1024,  # MB to bytes
            backupCount=self.config.get('backup_count', 5),
            encoding='utf-8'
        )
        
        # 时间轮转处理器 - 按天轮转
        time_handler = TimedRotatingFileHandler(
            self.log_dir / f"daily_{filename}",
            when='midnight',
            interval=1,
            backupCount=self.config.get('daily_backup_count', 30),
            encoding='utf-8'
        )
        
        # 设置格式器
        if self.config.get('structured_format', True):
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        time_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(time_handler)
        
        # 控制台处理器
        if self.config.get('enable_console', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _start_async_writer(self):
        """启动异步日志写入线程"""
        def async_writer():
            while True:
                try:
                    log_item = self.log_queue.get(timeout=1)
                    if log_item is None:  # 停止信号
                        break
                    
                    logger_name, level, message, extra = log_item
                    logger = getattr(self, f"{logger_name}_logger")
                    logger.log(level, message, extra=extra)
                    
                except Empty:
                    continue
                except Exception as e:
                    # 异步写入失败时，直接写入错误日志
                    self.error_logger.error(f"异步日志写入失败: {e}")
        
        self.async_thread = threading.Thread(target=async_writer, daemon=True)
        self.async_thread.start()
    
    def log_api_call(self, api_code: str, request_data: Dict[str, Any], 
                     response_data: Optional[Dict[str, Any]], 
                     context: Dict[str, Any]):
        """
        记录API调用日志
        
        Args:
            api_code: 接口编码
            request_data: 请求数据
            response_data: 响应数据
            context: 上下文信息
        """
        log_data = {
            'event_type': 'api_call',
            'api_code': api_code,
            'trace_id': context.get('trace_id', str(uuid.uuid4())),
            'operation_id': context.get('operation_id', str(uuid.uuid4())),
            'org_code': context.get('org_code', ''),
            'client_ip': context.get('client_ip', ''),
            'operator_id': context.get('operator_id', ''),
            'request_data': self._sanitize_sensitive_data(request_data),
            'response_data': self._sanitize_sensitive_data(response_data) if response_data else None,
            'timestamp': datetime.now().isoformat(),
            'success': response_data is not None and response_data.get('infcode') == 0 if response_data else False
        }
        
        message = f"API调用 {api_code} - {context.get('org_code', 'Unknown')}"
        
        if self.async_enabled:
            self.log_queue.put(('api', logging.INFO, message, log_data))
        else:
            self.api_logger.info(message, extra={'extra': log_data})
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """
        记录错误日志
        
        Args:
            error: 异常对象
            context: 上下文信息
        """
        log_data = {
            'event_type': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_traceback': traceback.format_exc(),
            'trace_id': context.get('trace_id', ''),
            'operation_id': context.get('operation_id', ''),
            'api_code': context.get('api_code', ''),
            'org_code': context.get('org_code', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        message = f"错误发生: {type(error).__name__} - {str(error)}"
        
        if self.async_enabled:
            self.log_queue.put(('error', logging.ERROR, message, log_data))
        else:
            self.error_logger.error(message, extra={'extra': log_data})
    
    def log_performance(self, operation: str, duration_ms: float, context: Dict[str, Any]):
        """
        记录性能日志
        
        Args:
            operation: 操作名称
            duration_ms: 持续时间(毫秒)
            context: 上下文信息
        """
        log_data = {
            'event_type': 'performance',
            'operation': operation,
            'duration_ms': duration_ms,
            'trace_id': context.get('trace_id', ''),
            'api_code': context.get('api_code', ''),
            'org_code': context.get('org_code', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        message = f"性能监控 {operation}: {duration_ms:.2f}ms"
        
        if self.async_enabled:
            self.log_queue.put(('performance', logging.INFO, message, log_data))
        else:
            self.performance_logger.info(message, extra={'extra': log_data})
    
    def log_operation(self, operation_log: OperationLog):
        """
        记录操作日志
        
        Args:
            operation_log: 操作日志对象
        """
        log_data = {
            'event_type': 'operation',
            'operation_id': operation_log.operation_id,
            'api_code': operation_log.api_code,
            'api_name': operation_log.api_name,
            'business_category': operation_log.business_category,
            'business_type': operation_log.business_type,
            'institution_code': operation_log.institution_code,
            'status': operation_log.status,
            'trace_id': operation_log.trace_id,
            'duration_seconds': operation_log.get_duration_seconds(),
            'has_error': operation_log.is_failed(),
            'timestamp': datetime.now().isoformat()
        }
        
        message = f"操作记录 {operation_log.api_code} - {operation_log.status}"
        
        if self.async_enabled:
            self.log_queue.put(('main', logging.INFO, message, log_data))
        else:
            self.main_logger.info(message, extra=log_data)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """记录信息日志"""
        log_data = {
            'event_type': 'info',
            'timestamp': datetime.now().isoformat()
        }
        if context:
            log_data.update(context)
        
        if self.async_enabled:
            self.log_queue.put(('main', logging.INFO, message, log_data))
        else:
            self.main_logger.info(message, extra={'extra': log_data})
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """记录警告日志"""
        log_data = {
            'event_type': 'warning',
            'timestamp': datetime.now().isoformat()
        }
        if context:
            log_data.update(context)
        
        if self.async_enabled:
            self.log_queue.put(('main', logging.WARNING, message, log_data))
        else:
            self.main_logger.warning(message, extra={'extra': log_data})
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理敏感数据"""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = {
            'app_secret', 'secret_key', 'password', 'token', 'certno', 
            'psn_no', 'card_sn', 'phone', 'mobile'
        }
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields:
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    sanitized[key] = '***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Args:
            hours: 统计时间范围(小时)
            
        Returns:
            统计信息字典
        """
        # 这里简化实现，实际应该从日志文件或数据库中统计
        return {
            'total_api_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'error_count': 0,
            'average_response_time': 0.0,
            'time_range_hours': hours,
            'timestamp': datetime.now().isoformat()
        }
    
    def close(self):
        """关闭日志管理器"""
        if self.async_enabled:
            # 发送停止信号
            self.log_queue.put(None)
            # 等待异步线程结束
            if hasattr(self, 'async_thread'):
                self.async_thread.join(timeout=5)
            # 关闭线程池
            self.async_executor.shutdown(wait=True)
        
        # 关闭所有日志处理器
        for logger in [self.main_logger, self.api_logger, self.error_logger, self.performance_logger]:
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record):
        """格式化日志记录"""
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外的结构化数据
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        
        # 检查record的其他属性
        for attr_name in dir(record):
            if not attr_name.startswith('_') and attr_name not in log_data:
                attr_value = getattr(record, attr_name, None)
                if isinstance(attr_value, (str, int, float, bool, dict, list)):
                    log_data[attr_name] = attr_value
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, log_manager: LogManager, **context):
        self.log_manager = log_manager
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.log_manager.log_error(exc_val, self.context)
        
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() * 1000
            operation = self.context.get('operation', 'unknown')
            self.log_manager.log_performance(operation, duration, self.context)
    
    def log_info(self, message: str):
        """在上下文中记录信息日志"""
        self.log_manager.log_info(message, self.context)
    
    def log_warning(self, message: str):
        """在上下文中记录警告日志"""
        self.log_manager.log_warning(message, self.context)


# 日志装饰器
def log_api_call(log_manager: LogManager):
    """API调用日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            context = {
                'operation': func.__name__,
                'trace_id': str(uuid.uuid4())
            }
            
            with LogContext(log_manager, **context) as log_ctx:
                try:
                    result = func(*args, **kwargs)
                    log_ctx.log_info(f"API调用成功: {func.__name__}")
                    return result
                except Exception as e:
                    log_ctx.log_info(f"API调用失败: {func.__name__} - {str(e)}")
                    raise
        
        return wrapper
    return decorator