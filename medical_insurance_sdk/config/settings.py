"""配置设置模块 - 环境配置管理"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
import base64
import logging

from ..exceptions import ConfigurationException


@dataclass
class DatabaseSettings:
    """数据库配置"""
    host: str = "localhost"
    port: int = 3306
    database: str = "medical_insurance"
    username: str = "root"
    password: str = ""
    charset: str = "utf8mb4"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisSettings:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class LoggingSettings:
    """日志配置"""
    level: str = "INFO"
    file_path: str = "logs/medical_insurance_sdk.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_output: bool = True


@dataclass
class SecuritySettings:
    """安全配置"""
    encryption_key: Optional[str] = None
    default_crypto_type: str = "SM4"
    default_sign_type: str = "SM3"
    token_expire_minutes: int = 30
    max_login_attempts: int = 5


@dataclass
class HttpSettings:
    """HTTP客户端配置"""
    timeout: int = 30
    max_retries: int = 3
    pool_connections: int = 10
    pool_maxsize: int = 10
    verify_ssl: bool = True
    user_agent: str = "MedicalInsuranceSDK/1.0"


@dataclass
class AsyncSettings:
    """异步处理配置"""
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    task_timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 60


@dataclass
class EnvironmentSettings:
    """环境配置"""
    environment: str = "development"
    debug: bool = True
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    http: HttpSettings = field(default_factory=HttpSettings)
    async_processing: AsyncSettings = field(default_factory=AsyncSettings)
    
    # 自定义配置扩展
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """配置管理器 - 负责加载和管理不同环境的配置"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前包下的config目录
        """
        if config_dir is None:
            config_dir = Path(__file__).parent / "environments"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self._current_settings: Optional[EnvironmentSettings] = None
        self._encryption_key: Optional[bytes] = None
        
        # 初始化加密密钥
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """初始化加密密钥"""
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            # 生成新的加密密钥
            self._encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
            
            # 设置文件权限（仅所有者可读写）
            os.chmod(key_file, 0o600)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            str: 加密后的数据（Base64编码）
        """
        if not self._encryption_key:
            raise ConfigurationException("加密密钥未初始化")
        
        fernet = Fernet(self._encryption_key)
        encrypted_data = fernet.encrypt(data.encode('utf-8'))
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码）
            
        Returns:
            str: 解密后的数据
        """
        if not self._encryption_key:
            raise ConfigurationException("加密密钥未初始化")
        
        try:
            fernet = Fernet(self._encryption_key)
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise ConfigurationException(f"解密失败: {str(e)}")
    
    def load_settings(self, environment: str = None) -> EnvironmentSettings:
        """加载指定环境的配置
        
        Args:
            environment: 环境名称，默认从环境变量获取
            
        Returns:
            EnvironmentSettings: 环境配置对象
        """
        if environment is None:
            environment = os.getenv('MEDICAL_INSURANCE_ENV', 'development')
        
        config_file = self.config_dir / f"{environment}.yaml"
        
        if not config_file.exists():
            # 如果配置文件不存在，创建默认配置
            self._create_default_config(environment)
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 处理加密的敏感数据
            config_data = self._decrypt_config_data(config_data)
            
            # 应用环境变量覆盖
            config_data = self._apply_env_overrides(config_data)
            
            # 创建配置对象
            settings = self._create_settings_from_dict(config_data, environment)
            
            self._current_settings = settings
            return settings
            
        except Exception as e:
            raise ConfigurationException(f"加载配置失败: {str(e)}")
    
    def save_settings(self, settings: EnvironmentSettings, environment: str = None):
        """保存配置到文件
        
        Args:
            settings: 配置对象
            environment: 环境名称
        """
        if environment is None:
            environment = settings.environment
        
        config_file = self.config_dir / f"{environment}.yaml"
        
        # 转换为字典
        config_data = self._settings_to_dict(settings)
        
        # 加密敏感数据
        config_data = self._encrypt_config_data(config_data)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise ConfigurationException(f"保存配置失败: {str(e)}")
    
    def validate_settings(self, settings: EnvironmentSettings) -> bool:
        """验证配置的有效性
        
        Args:
            settings: 配置对象
            
        Returns:
            bool: 配置是否有效
        """
        try:
            # 验证数据库配置
            if not settings.database.host or not settings.database.database:
                raise ConfigurationException("数据库配置不完整")
            
            # 验证Redis配置
            if not settings.redis.host:
                raise ConfigurationException("Redis配置不完整")
            
            # 验证日志配置
            if not settings.logging.file_path:
                raise ConfigurationException("日志配置不完整")
            
            # 验证安全配置
            if settings.security.token_expire_minutes <= 0:
                raise ConfigurationException("令牌过期时间必须大于0")
            
            return True
            
        except Exception as e:
            logging.error(f"配置验证失败: {str(e)}")
            return False
    
    def get_current_settings(self) -> Optional[EnvironmentSettings]:
        """获取当前加载的配置"""
        return self._current_settings
    
    def _create_default_config(self, environment: str):
        """创建默认配置文件"""
        if environment == "development":
            settings = EnvironmentSettings(
                environment="development",
                debug=True,
                database=DatabaseSettings(
                    host="localhost",
                    port=3306,
                    database="medical_insurance_dev",
                    username="root",
                    password="",
                ),
                redis=RedisSettings(
                    host="localhost",
                    port=6379,
                    db=0,
                ),
                logging=LoggingSettings(
                    level="DEBUG",
                    console_output=True,
                ),
            )
        elif environment == "testing":
            settings = EnvironmentSettings(
                environment="testing",
                debug=True,
                database=DatabaseSettings(
                    host="localhost",
                    port=3306,
                    database="medical_insurance_test",
                    username="test_user",
                    password="test_password",
                ),
                redis=RedisSettings(
                    host="localhost",
                    port=6379,
                    db=1,
                ),
                logging=LoggingSettings(
                    level="DEBUG",
                    file_path="logs/test.log",
                ),
            )
        elif environment == "production":
            settings = EnvironmentSettings(
                environment="production",
                debug=False,
                database=DatabaseSettings(
                    host="prod-db-host",
                    port=3306,
                    database="medical_insurance_prod",
                    username="prod_user",
                    password="ENCRYPTED_PASSWORD_PLACEHOLDER",
                ),
                redis=RedisSettings(
                    host="prod-redis-host",
                    port=6379,
                    db=0,
                    password="ENCRYPTED_REDIS_PASSWORD_PLACEHOLDER",
                ),
                logging=LoggingSettings(
                    level="INFO",
                    console_output=False,
                ),
                security=SecuritySettings(
                    token_expire_minutes=60,
                    max_login_attempts=3,
                ),
            )
        else:
            # 默认配置
            settings = EnvironmentSettings(environment=environment)
        
        self.save_settings(settings, environment)
    
    def _decrypt_config_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """解密配置数据中的敏感信息"""
        def decrypt_recursive(obj):
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    if isinstance(value, str) and value.startswith("ENCRYPTED_"):
                        # 这是加密的数据，需要解密
                        encrypted_value = value.replace("ENCRYPTED_", "")
                        if encrypted_value != "PASSWORD_PLACEHOLDER" and encrypted_value != "REDIS_PASSWORD_PLACEHOLDER":
                            try:
                                result[key] = self.decrypt_sensitive_data(encrypted_value)
                            except:
                                result[key] = ""  # 解密失败时使用空值
                        else:
                            result[key] = ""  # 占位符使用空值
                    else:
                        result[key] = decrypt_recursive(value)
                return result
            elif isinstance(obj, list):
                return [decrypt_recursive(item) for item in obj]
            else:
                return obj
        
        return decrypt_recursive(config_data)
    
    def _encrypt_config_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """加密配置数据中的敏感信息"""
        sensitive_fields = {
            'password', 'secret', 'key', 'token', 'app_secret'
        }
        
        def encrypt_recursive(obj, parent_key=""):
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    if isinstance(value, str) and key.lower() in sensitive_fields and value:
                        # 加密敏感数据
                        result[key] = f"ENCRYPTED_{self.encrypt_sensitive_data(value)}"
                    else:
                        result[key] = encrypt_recursive(value, key)
                return result
            elif isinstance(obj, list):
                return [encrypt_recursive(item, parent_key) for item in obj]
            else:
                return obj
        
        return encrypt_recursive(config_data)
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        # 定义环境变量映射
        env_mappings = {
            'MEDICAL_DB_HOST': ['database', 'host'],
            'MEDICAL_DB_PORT': ['database', 'port'],
            'MEDICAL_DB_NAME': ['database', 'database'],
            'MEDICAL_DB_USER': ['database', 'username'],
            'MEDICAL_DB_PASSWORD': ['database', 'password'],
            'MEDICAL_REDIS_HOST': ['redis', 'host'],
            'MEDICAL_REDIS_PORT': ['redis', 'port'],
            'MEDICAL_REDIS_DB': ['redis', 'db'],
            'MEDICAL_REDIS_PASSWORD': ['redis', 'password'],
            'MEDICAL_LOG_LEVEL': ['logging', 'level'],
            'MEDICAL_DEBUG': ['debug'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 设置配置值
                current = config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # 类型转换
                final_key = config_path[-1]
                if final_key in ['port', 'db', 'pool_size', 'max_overflow']:
                    current[final_key] = int(env_value)
                elif final_key == 'debug':
                    current[final_key] = env_value.lower() in ('true', '1', 'yes')
                else:
                    current[final_key] = env_value
        
        return config_data
    
    def _create_settings_from_dict(self, config_data: Dict[str, Any], environment: str) -> EnvironmentSettings:
        """从字典创建配置对象"""
        # 类型转换辅助函数
        def safe_int(value, default=0):
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def safe_bool(value, default=False):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return default
        
        # 创建数据库配置
        db_data = config_data.get('database', {})
        database_config = DatabaseSettings(
            host=db_data.get('host', 'localhost'),
            port=safe_int(db_data.get('port'), 3306),
            database=db_data.get('database', 'medical_insurance'),
            username=db_data.get('username', 'root'),
            password=db_data.get('password', ''),
            charset=db_data.get('charset', 'utf8mb4'),
            pool_size=safe_int(db_data.get('pool_size'), 10),
            max_overflow=safe_int(db_data.get('max_overflow'), 20),
            pool_timeout=safe_int(db_data.get('pool_timeout'), 30),
            pool_recycle=safe_int(db_data.get('pool_recycle'), 3600)
        )
        
        # 创建Redis配置
        redis_data = config_data.get('redis', {})
        redis_config = RedisSettings(
            host=redis_data.get('host', 'localhost'),
            port=safe_int(redis_data.get('port'), 6379),
            db=safe_int(redis_data.get('db'), 0),
            password=redis_data.get('password'),
            max_connections=safe_int(redis_data.get('max_connections'), 10),
            socket_timeout=safe_int(redis_data.get('socket_timeout'), 5),
            socket_connect_timeout=safe_int(redis_data.get('socket_connect_timeout'), 5)
        )
        
        # 创建日志配置
        log_data = config_data.get('logging', {})
        logging_config = LoggingSettings(
            level=log_data.get('level', 'INFO'),
            file_path=log_data.get('file_path', 'logs/medical_insurance_sdk.log'),
            max_file_size=log_data.get('max_file_size', '10MB'),
            backup_count=safe_int(log_data.get('backup_count'), 5),
            format=log_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            console_output=safe_bool(log_data.get('console_output'), True)
        )
        
        # 创建安全配置
        security_data = config_data.get('security', {})
        security_config = SecuritySettings(
            encryption_key=security_data.get('encryption_key'),
            default_crypto_type=security_data.get('default_crypto_type', 'SM4'),
            default_sign_type=security_data.get('default_sign_type', 'SM3'),
            token_expire_minutes=safe_int(security_data.get('token_expire_minutes'), 30),
            max_login_attempts=safe_int(security_data.get('max_login_attempts'), 5)
        )
        
        # 创建HTTP配置
        http_data = config_data.get('http', {})
        http_config = HttpSettings(
            timeout=safe_int(http_data.get('timeout'), 30),
            max_retries=safe_int(http_data.get('max_retries'), 3),
            pool_connections=safe_int(http_data.get('pool_connections'), 10),
            pool_maxsize=safe_int(http_data.get('pool_maxsize'), 10),
            verify_ssl=safe_bool(http_data.get('verify_ssl'), True),
            user_agent=http_data.get('user_agent', 'MedicalInsuranceSDK/1.0')
        )
        
        # 创建异步配置
        async_data = config_data.get('async_processing', {})
        async_config = AsyncSettings(
            celery_broker_url=async_data.get('celery_broker_url', 'redis://localhost:6379/1'),
            celery_result_backend=async_data.get('celery_result_backend', 'redis://localhost:6379/2'),
            task_timeout=safe_int(async_data.get('task_timeout'), 300),
            max_retries=safe_int(async_data.get('max_retries'), 3),
            retry_delay=safe_int(async_data.get('retry_delay'), 60)
        )
        
        # 创建主配置对象
        settings = EnvironmentSettings(
            environment=environment,
            debug=safe_bool(config_data.get('debug'), True),
            database=database_config,
            redis=redis_config,
            logging=logging_config,
            security=security_config,
            http=http_config,
            async_processing=async_config,
            custom_settings=config_data.get('custom_settings', {})
        )
        
        return settings
    
    def _settings_to_dict(self, settings: EnvironmentSettings) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        return {
            'environment': settings.environment,
            'debug': settings.debug,
            'database': {
                'host': settings.database.host,
                'port': settings.database.port,
                'database': settings.database.database,
                'username': settings.database.username,
                'password': settings.database.password,
                'charset': settings.database.charset,
                'pool_size': settings.database.pool_size,
                'max_overflow': settings.database.max_overflow,
                'pool_timeout': settings.database.pool_timeout,
                'pool_recycle': settings.database.pool_recycle,
            },
            'redis': {
                'host': settings.redis.host,
                'port': settings.redis.port,
                'db': settings.redis.db,
                'password': settings.redis.password,
                'max_connections': settings.redis.max_connections,
                'socket_timeout': settings.redis.socket_timeout,
                'socket_connect_timeout': settings.redis.socket_connect_timeout,
            },
            'logging': {
                'level': settings.logging.level,
                'file_path': settings.logging.file_path,
                'max_file_size': settings.logging.max_file_size,
                'backup_count': settings.logging.backup_count,
                'format': settings.logging.format,
                'console_output': settings.logging.console_output,
            },
            'security': {
                'encryption_key': settings.security.encryption_key,
                'default_crypto_type': settings.security.default_crypto_type,
                'default_sign_type': settings.security.default_sign_type,
                'token_expire_minutes': settings.security.token_expire_minutes,
                'max_login_attempts': settings.security.max_login_attempts,
            },
            'http': {
                'timeout': settings.http.timeout,
                'max_retries': settings.http.max_retries,
                'pool_connections': settings.http.pool_connections,
                'pool_maxsize': settings.http.pool_maxsize,
                'verify_ssl': settings.http.verify_ssl,
                'user_agent': settings.http.user_agent,
            },
            'async_processing': {
                'celery_broker_url': settings.async_processing.celery_broker_url,
                'celery_result_backend': settings.async_processing.celery_result_backend,
                'task_timeout': settings.async_processing.task_timeout,
                'max_retries': settings.async_processing.max_retries,
                'retry_delay': settings.async_processing.retry_delay,
            },
            'custom_settings': settings.custom_settings,
        }