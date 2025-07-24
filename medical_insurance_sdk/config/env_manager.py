"""环境变量管理器 - 统一管理环境变量"""

import os
import logging
from typing import Dict, Any, Optional, Union, List, Callable
from pathlib import Path
from dataclasses import dataclass, field
import json

from ..exceptions import ConfigurationException


@dataclass
class EnvVarDefinition:
    """环境变量定义"""
    name: str                           # 环境变量名称
    description: str                    # 描述
    default_value: Any = None           # 默认值
    required: bool = False              # 是否必需
    var_type: str = "string"           # 变量类型: string, int, float, bool, json
    validator: Optional[Callable] = None # 验证函数
    sensitive: bool = False             # 是否敏感信息
    config_path: Optional[List[str]] = None  # 对应的配置路径


class EnvironmentVariableManager:
    """环境变量管理器"""
    
    def __init__(self):
        """初始化环境变量管理器"""
        self._env_definitions: Dict[str, EnvVarDefinition] = {}
        self._loaded_values: Dict[str, Any] = {}
        self._setup_default_definitions()
    
    def _setup_default_definitions(self):
        """设置默认的环境变量定义"""
        # 基础环境配置
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_INSURANCE_ENV",
            description="运行环境 (development/testing/production)",
            default_value="development",
            var_type="string",
            validator=lambda x: x in ["development", "testing", "production"],
            config_path=["environment"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DEBUG",
            description="是否启用调试模式",
            default_value="true",
            var_type="bool",
            config_path=["debug"]
        ))
        
        # 数据库相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DB_HOST",
            description="数据库主机地址",
            default_value="localhost",
            var_type="string",
            config_path=["database", "host"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DB_PORT",
            description="数据库端口",
            default_value="3306",
            var_type="int",
            validator=lambda x: isinstance(x, int) and 1 <= x <= 65535,
            config_path=["database", "port"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DB_NAME",
            description="数据库名称",
            required=True,
            var_type="string",
            config_path=["database", "database"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DB_USER",
            description="数据库用户名",
            required=True,
            var_type="string",
            config_path=["database", "username"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DB_PASSWORD",
            description="数据库密码",
            var_type="string",
            sensitive=True,
            config_path=["database", "password"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_DB_POOL_SIZE",
            description="数据库连接池大小",
            default_value="10",
            var_type="int",
            validator=lambda x: isinstance(x, int) and x > 0,
            config_path=["database", "pool_size"]
        ))
        
        # Redis相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_REDIS_HOST",
            description="Redis主机地址",
            default_value="localhost",
            var_type="string",
            config_path=["redis", "host"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_REDIS_PORT",
            description="Redis端口",
            default_value="6379",
            var_type="int",
            validator=lambda x: isinstance(x, int) and 1 <= x <= 65535,
            config_path=["redis", "port"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_REDIS_DB",
            description="Redis数据库编号",
            default_value="0",
            var_type="int",
            validator=lambda x: isinstance(x, int) and 0 <= x <= 15,
            config_path=["redis", "db"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_REDIS_PASSWORD",
            description="Redis密码",
            var_type="string",
            sensitive=True,
            config_path=["redis", "password"]
        ))
        
        # 日志相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_LOG_LEVEL",
            description="日志级别",
            default_value="INFO",
            var_type="string",
            validator=lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            config_path=["logging", "level"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_LOG_FILE",
            description="日志文件路径",
            default_value="logs/medical_insurance_sdk.log",
            var_type="string",
            config_path=["logging", "file_path"]
        ))
        
        # 安全相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_ENCRYPTION_KEY",
            description="加密密钥",
            var_type="string",
            sensitive=True,
            config_path=["security", "encryption_key"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_CRYPTO_TYPE",
            description="默认加密类型",
            default_value="SM4",
            var_type="string",
            validator=lambda x: x in ["SM4", "AES", "DES"],
            config_path=["security", "default_crypto_type"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_SIGN_TYPE",
            description="默认签名类型",
            default_value="SM3",
            var_type="string",
            validator=lambda x: x in ["SM3", "SHA1", "SHA256", "MD5"],
            config_path=["security", "default_sign_type"]
        ))
        
        # HTTP相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_HTTP_TIMEOUT",
            description="HTTP请求超时时间（秒）",
            default_value="30",
            var_type="int",
            validator=lambda x: isinstance(x, int) and x > 0,
            config_path=["http", "timeout"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_HTTP_MAX_RETRIES",
            description="HTTP最大重试次数",
            default_value="3",
            var_type="int",
            validator=lambda x: isinstance(x, int) and x >= 0,
            config_path=["http", "max_retries"]
        ))
        
        # 异步处理相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_CELERY_BROKER",
            description="Celery代理URL",
            default_value="redis://localhost:6379/1",
            var_type="string",
            config_path=["async_processing", "celery_broker_url"]
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_CELERY_BACKEND",
            description="Celery结果后端URL",
            default_value="redis://localhost:6379/2",
            var_type="string",
            config_path=["async_processing", "celery_result_backend"]
        ))
        
        # 配置文件相关环境变量
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_CONFIG_DIR",
            description="配置文件目录",
            var_type="string"
        ))
        
        self.register_env_var(EnvVarDefinition(
            name="MEDICAL_CONFIG_FILE",
            description="指定配置文件路径",
            var_type="string"
        ))
    
    def register_env_var(self, definition: EnvVarDefinition):
        """注册环境变量定义
        
        Args:
            definition: 环境变量定义
        """
        self._env_definitions[definition.name] = definition
    
    def load_environment_variables(self) -> Dict[str, Any]:
        """加载所有环境变量
        
        Returns:
            dict: 加载的环境变量值
        """
        self._loaded_values.clear()
        errors = []
        
        for name, definition in self._env_definitions.items():
            try:
                value = self._load_single_env_var(definition)
                if value is not None:
                    self._loaded_values[name] = value
            except Exception as e:
                error_msg = f"加载环境变量 {name} 失败: {str(e)}"
                errors.append(error_msg)
                logging.error(error_msg)
        
        if errors:
            raise ConfigurationException(f"环境变量加载失败: {'; '.join(errors)}")
        
        return self._loaded_values.copy()
    
    def _load_single_env_var(self, definition: EnvVarDefinition) -> Any:
        """加载单个环境变量
        
        Args:
            definition: 环境变量定义
            
        Returns:
            Any: 环境变量值
        """
        raw_value = os.getenv(definition.name)
        
        # 如果环境变量不存在
        if raw_value is None:
            if definition.required:
                raise ConfigurationException(f"必需的环境变量 {definition.name} 未设置")
            return definition.default_value
        
        # 类型转换
        try:
            converted_value = self._convert_value(raw_value, definition.var_type)
        except Exception as e:
            raise ConfigurationException(f"环境变量 {definition.name} 类型转换失败: {str(e)}")
        
        # 验证
        if definition.validator and not definition.validator(converted_value):
            raise ConfigurationException(f"环境变量 {definition.name} 验证失败: {converted_value}")
        
        return converted_value
    
    def _convert_value(self, value: str, var_type: str) -> Any:
        """转换环境变量值类型
        
        Args:
            value: 原始字符串值
            var_type: 目标类型
            
        Returns:
            Any: 转换后的值
        """
        if var_type == "string":
            return value
        elif var_type == "int":
            return int(value)
        elif var_type == "float":
            return float(value)
        elif var_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif var_type == "json":
            return json.loads(value)
        else:
            raise ValueError(f"不支持的类型: {var_type}")
    
    def get_env_value(self, name: str, default: Any = None) -> Any:
        """获取环境变量值
        
        Args:
            name: 环境变量名称
            default: 默认值
            
        Returns:
            Any: 环境变量值
        """
        if name in self._loaded_values:
            return self._loaded_values[name]
        
        if name in self._env_definitions:
            definition = self._env_definitions[name]
            try:
                value = self._load_single_env_var(definition)
                if value is not None:
                    self._loaded_values[name] = value
                    return value
            except Exception:
                pass
        
        return default
    
    def set_env_value(self, name: str, value: Any):
        """设置环境变量值
        
        Args:
            name: 环境变量名称
            value: 值
        """
        os.environ[name] = str(value)
        if name in self._env_definitions:
            definition = self._env_definitions[name]
            converted_value = self._convert_value(str(value), definition.var_type)
            self._loaded_values[name] = converted_value
    
    def apply_to_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """将环境变量应用到配置字典
        
        Args:
            config_dict: 配置字典
            
        Returns:
            dict: 更新后的配置字典
        """
        result = config_dict.copy()
        
        for name, value in self._loaded_values.items():
            if name in self._env_definitions:
                definition = self._env_definitions[name]
                if definition.config_path:
                    self._set_nested_value(result, definition.config_path, value)
        
        return result
    
    def _set_nested_value(self, config_dict: Dict[str, Any], path: List[str], value: Any):
        """设置嵌套字典值
        
        Args:
            config_dict: 配置字典
            path: 路径列表
            value: 值
        """
        current = config_dict
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get_env_definitions(self) -> Dict[str, EnvVarDefinition]:
        """获取所有环境变量定义
        
        Returns:
            dict: 环境变量定义字典
        """
        return self._env_definitions.copy()
    
    def validate_environment(self) -> Dict[str, Any]:
        """验证当前环境变量
        
        Returns:
            dict: 验证结果
        """
        errors = []
        warnings = []
        missing_required = []
        
        for name, definition in self._env_definitions.items():
            raw_value = os.getenv(name)
            
            if raw_value is None:
                if definition.required:
                    missing_required.append(name)
                continue
            
            try:
                converted_value = self._convert_value(raw_value, definition.var_type)
                if definition.validator and not definition.validator(converted_value):
                    errors.append(f"{name}: 验证失败")
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
        
        return {
            "valid": len(errors) == 0 and len(missing_required) == 0,
            "errors": errors,
            "warnings": warnings,
            "missing_required": missing_required,
            "loaded_count": len(self._loaded_values),
            "total_count": len(self._env_definitions)
        }
    
    def generate_env_template(self, include_sensitive: bool = False) -> str:
        """生成环境变量模板文件
        
        Args:
            include_sensitive: 是否包含敏感信息
            
        Returns:
            str: 环境变量模板内容
        """
        lines = [
            "# 医保接口SDK环境变量配置",
            "# 请根据实际情况修改以下配置",
            ""
        ]
        
        # 按类别分组
        categories = {
            "基础配置": ["MEDICAL_INSURANCE_ENV", "MEDICAL_DEBUG"],
            "数据库配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_DB_")],
            "Redis配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_REDIS_")],
            "日志配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_LOG_")],
            "安全配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_") and any(x in name for x in ["ENCRYPTION", "CRYPTO", "SIGN"])],
            "HTTP配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_HTTP_")],
            "异步处理配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_CELERY_")],
            "其他配置": [name for name in self._env_definitions.keys() if name.startswith("MEDICAL_CONFIG_")]
        }
        
        for category, env_names in categories.items():
            if not env_names:
                continue
            
            lines.append(f"# {category}")
            for name in env_names:
                if name not in self._env_definitions:
                    continue
                
                definition = self._env_definitions[name]
                
                # 跳过敏感信息（除非明确要求包含）
                if definition.sensitive and not include_sensitive:
                    lines.append(f"# {name}=<敏感信息，请手动设置>")
                    continue
                
                # 添加注释
                lines.append(f"# {definition.description}")
                if definition.required:
                    lines.append(f"# 必需: 是")
                if definition.default_value is not None:
                    lines.append(f"# 默认值: {definition.default_value}")
                
                # 添加环境变量
                if definition.default_value is not None:
                    lines.append(f"{name}={definition.default_value}")
                else:
                    lines.append(f"# {name}=")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def load_from_file(self, file_path: str):
        """从文件加载环境变量
        
        Args:
            file_path: 文件路径
        """
        env_file = Path(file_path)
        if not env_file.exists():
            raise ConfigurationException(f"环境变量文件不存在: {file_path}")
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析环境变量
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        os.environ[key] = value
                    else:
                        logging.warning(f"环境变量文件 {file_path} 第 {line_num} 行格式错误: {line}")
        
        except Exception as e:
            raise ConfigurationException(f"加载环境变量文件失败: {str(e)}")


# 全局环境变量管理器实例
env_manager = EnvironmentVariableManager()


def load_env_vars() -> Dict[str, Any]:
    """加载环境变量的便捷函数
    
    Returns:
        dict: 环境变量值字典
    """
    return env_manager.load_environment_variables()


def get_env(name: str, default: Any = None) -> Any:
    """获取环境变量的便捷函数
    
    Args:
        name: 环境变量名称
        default: 默认值
        
    Returns:
        Any: 环境变量值
    """
    return env_manager.get_env_value(name, default)


def set_env(name: str, value: Any):
    """设置环境变量的便捷函数
    
    Args:
        name: 环境变量名称
        value: 值
    """
    env_manager.set_env_value(name, value)


def validate_env() -> Dict[str, Any]:
    """验证环境变量的便捷函数
    
    Returns:
        dict: 验证结果
    """
    return env_manager.validate_environment()