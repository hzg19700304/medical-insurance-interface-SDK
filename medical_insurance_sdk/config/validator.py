"""配置验证器 - 验证配置的完整性和有效性"""

import re
import socket
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .settings import EnvironmentSettings
from ..exceptions import ConfigurationException


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_settings(self, settings: EnvironmentSettings) -> bool:
        """验证配置设置
        
        Args:
            settings: 环境配置对象
            
        Returns:
            bool: 验证是否通过
        """
        self.errors.clear()
        self.warnings.clear()
        
        # 验证基本设置
        self._validate_basic_settings(settings)
        
        # 验证数据库配置
        self._validate_database_settings(settings.database)
        
        # 验证Redis配置
        self._validate_redis_settings(settings.redis)
        
        # 验证日志配置
        self._validate_logging_settings(settings.logging)
        
        # 验证安全配置
        self._validate_security_settings(settings.security)
        
        # 验证HTTP配置
        self._validate_http_settings(settings.http)
        
        # 验证异步处理配置
        self._validate_async_settings(settings.async_processing)
        
        # 环境特定验证
        self._validate_environment_specific(settings)
        
        return len(self.errors) == 0
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告
        
        Returns:
            dict: 验证报告
        """
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }
    
    def _validate_basic_settings(self, settings: EnvironmentSettings):
        """验证基本设置"""
        if not settings.environment:
            self.errors.append("环境名称不能为空")
        
        if settings.environment not in ['development', 'testing', 'production']:
            self.warnings.append(f"非标准环境名称: {settings.environment}")
    
    def _validate_database_settings(self, db_settings):
        """验证数据库配置"""
        if not db_settings.host:
            self.errors.append("数据库主机地址不能为空")
        
        if not db_settings.database:
            self.errors.append("数据库名称不能为空")
        
        if not db_settings.username:
            self.errors.append("数据库用户名不能为空")
        
        # 验证端口范围
        try:
            port = int(db_settings.port)
            if not (1 <= port <= 65535):
                self.errors.append(f"数据库端口无效: {db_settings.port}")
        except (ValueError, TypeError):
            self.errors.append(f"数据库端口必须是数字: {db_settings.port}")
        
        # 验证连接池配置
        if db_settings.pool_size <= 0:
            self.errors.append("数据库连接池大小必须大于0")
        
        if db_settings.max_overflow < 0:
            self.errors.append("数据库连接池最大溢出不能为负数")
        
        if db_settings.pool_timeout <= 0:
            self.errors.append("数据库连接池超时时间必须大于0")
        
        # 验证主机连通性（仅在非生产环境）
        if db_settings.host not in ['localhost', '127.0.0.1'] and not db_settings.host.endswith('-host'):
            try:
                socket.gethostbyname(db_settings.host)
            except socket.gaierror:
                self.warnings.append(f"无法解析数据库主机: {db_settings.host}")
    
    def _validate_redis_settings(self, redis_settings):
        """验证Redis配置"""
        if not redis_settings.host:
            self.errors.append("Redis主机地址不能为空")
        
        # 验证端口范围
        try:
            port = int(redis_settings.port)
            if not (1 <= port <= 65535):
                self.errors.append(f"Redis端口无效: {redis_settings.port}")
        except (ValueError, TypeError):
            self.errors.append(f"Redis端口必须是数字: {redis_settings.port}")
        
        # 验证数据库编号
        try:
            db_num = int(redis_settings.db)
            if not (0 <= db_num <= 15):
                self.errors.append(f"Redis数据库编号无效: {redis_settings.db}")
        except (ValueError, TypeError):
            self.errors.append(f"Redis数据库编号必须是数字: {redis_settings.db}")
        
        # 验证连接配置
        if redis_settings.max_connections <= 0:
            self.errors.append("Redis最大连接数必须大于0")
        
        if redis_settings.socket_timeout <= 0:
            self.errors.append("Redis套接字超时时间必须大于0")
        
        # 验证主机连通性（仅在非生产环境）
        if redis_settings.host not in ['localhost', '127.0.0.1'] and not redis_settings.host.endswith('-host'):
            try:
                socket.gethostbyname(redis_settings.host)
            except socket.gaierror:
                self.warnings.append(f"无法解析Redis主机: {redis_settings.host}")
    
    def _validate_logging_settings(self, log_settings):
        """验证日志配置"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_settings.level not in valid_levels:
            self.errors.append(f"无效的日志级别: {log_settings.level}")
        
        if not log_settings.file_path:
            self.errors.append("日志文件路径不能为空")
        
        # 验证日志目录是否可写
        log_dir = Path(log_settings.file_path).parent
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                self.warnings.append(f"无法创建日志目录: {log_dir}")
        
        # 验证文件大小格式
        if not re.match(r'^\d+[KMGT]?B$', log_settings.max_file_size):
            self.errors.append(f"无效的日志文件大小格式: {log_settings.max_file_size}")
        
        if log_settings.backup_count < 0:
            self.errors.append("日志备份数量不能为负数")
    
    def _validate_security_settings(self, security_settings):
        """验证安全配置"""
        valid_crypto_types = ['SM4', 'AES', 'DES']
        if security_settings.default_crypto_type not in valid_crypto_types:
            self.errors.append(f"无效的加密类型: {security_settings.default_crypto_type}")
        
        valid_sign_types = ['SM3', 'SHA1', 'SHA256', 'MD5']
        if security_settings.default_sign_type not in valid_sign_types:
            self.errors.append(f"无效的签名类型: {security_settings.default_sign_type}")
        
        if security_settings.token_expire_minutes <= 0:
            self.errors.append("令牌过期时间必须大于0")
        
        if security_settings.max_login_attempts <= 0:
            self.errors.append("最大登录尝试次数必须大于0")
    
    def _validate_http_settings(self, http_settings):
        """验证HTTP配置"""
        if http_settings.timeout <= 0:
            self.errors.append("HTTP超时时间必须大于0")
        
        if http_settings.max_retries < 0:
            self.errors.append("HTTP最大重试次数不能为负数")
        
        if http_settings.pool_connections <= 0:
            self.errors.append("HTTP连接池大小必须大于0")
        
        if http_settings.pool_maxsize <= 0:
            self.errors.append("HTTP连接池最大大小必须大于0")
        
        if not http_settings.user_agent:
            self.warnings.append("HTTP用户代理为空")
    
    def _validate_async_settings(self, async_settings):
        """验证异步处理配置"""
        if not async_settings.celery_broker_url:
            self.errors.append("Celery代理URL不能为空")
        
        if not async_settings.celery_result_backend:
            self.errors.append("Celery结果后端URL不能为空")
        
        if async_settings.task_timeout <= 0:
            self.errors.append("任务超时时间必须大于0")
        
        if async_settings.max_retries < 0:
            self.errors.append("任务最大重试次数不能为负数")
        
        if async_settings.retry_delay <= 0:
            self.errors.append("任务重试延迟时间必须大于0")
        
        # 验证URL格式
        if not self._is_valid_redis_url(async_settings.celery_broker_url):
            self.errors.append(f"无效的Celery代理URL: {async_settings.celery_broker_url}")
        
        if not self._is_valid_redis_url(async_settings.celery_result_backend):
            self.errors.append(f"无效的Celery结果后端URL: {async_settings.celery_result_backend}")
    
    def _validate_environment_specific(self, settings: EnvironmentSettings):
        """环境特定验证"""
        if settings.environment == 'production':
            # 生产环境特定验证
            if settings.debug:
                self.warnings.append("生产环境建议关闭调试模式")
            
            if settings.logging.console_output:
                self.warnings.append("生产环境建议关闭控制台日志输出")
            
            if not settings.http.verify_ssl:
                self.errors.append("生产环境必须启用SSL验证")
            
            if settings.database.password == "" or "PLACEHOLDER" in settings.database.password:
                self.errors.append("生产环境数据库密码不能为空或使用占位符")
        
        elif settings.environment == 'development':
            # 开发环境特定验证
            if not settings.debug:
                self.warnings.append("开发环境建议启用调试模式")
            
            if settings.logging.level not in ['DEBUG', 'INFO']:
                self.warnings.append("开发环境建议使用DEBUG或INFO日志级别")
        
        elif settings.environment == 'testing':
            # 测试环境特定验证
            if not settings.custom_settings.get('test_mode', False):
                self.warnings.append("测试环境建议启用测试模式")
            
            if settings.database.database == settings.custom_settings.get('production_database'):
                self.errors.append("测试环境不能使用生产数据库")
    
    def _is_valid_redis_url(self, url: str) -> bool:
        """验证Redis URL格式"""
        redis_url_pattern = r'^redis://(?:[^:@]+:[^:@]*@)?[^:@/]+(?::\d+)?(?:/\d+)?$'
        return bool(re.match(redis_url_pattern, url))
    
    def test_connections(self, settings: EnvironmentSettings) -> Dict[str, bool]:
        """测试连接（可选功能）
        
        Args:
            settings: 环境配置对象
            
        Returns:
            dict: 连接测试结果
        """
        results = {}
        
        # 测试数据库连接
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=settings.database.host,
                port=settings.database.port,
                user=settings.database.username,
                password=settings.database.password,
                database=settings.database.database,
                connect_timeout=5
            )
            conn.close()
            results['database'] = True
        except Exception as e:
            results['database'] = False
            self.warnings.append(f"数据库连接测试失败: {str(e)}")
        
        # 测试Redis连接
        try:
            import redis
            r = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db,
                password=settings.redis.password,
                socket_timeout=5
            )
            r.ping()
            results['redis'] = True
        except Exception as e:
            results['redis'] = False
            self.warnings.append(f"Redis连接测试失败: {str(e)}")
        
        return results


def validate_config(settings: EnvironmentSettings) -> Dict[str, Any]:
    """验证配置的便捷函数
    
    Args:
        settings: 环境配置对象
        
    Returns:
        dict: 验证报告
    """
    validator = ConfigValidator()
    is_valid = validator.validate_settings(settings)
    report = validator.get_validation_report()
    report['is_valid'] = is_valid
    return report