"""配置加载器 - 统一的配置加载入口"""

import os
import logging
from typing import Optional
from pathlib import Path

from .settings import ConfigurationManager, EnvironmentSettings
from ..exceptions import ConfigurationException


class ConfigLoader:
    """配置加载器 - 提供统一的配置加载接口"""
    
    _instance: Optional['ConfigLoader'] = None
    _settings: Optional[EnvironmentSettings] = None
    _config_manager: Optional[ConfigurationManager] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置加载器"""
        if self._config_manager is None:
            config_dir = self._get_config_directory()
            self._config_manager = ConfigurationManager(config_dir)
    
    def _get_config_directory(self) -> str:
        """获取配置文件目录"""
        # 优先使用环境变量指定的配置目录
        config_dir = os.getenv('MEDICAL_CONFIG_DIR')
        if config_dir and Path(config_dir).exists():
            return config_dir
        
        # 使用默认配置目录
        return str(Path(__file__).parent / "environments")
    
    def load_config(self, environment: Optional[str] = None, force_reload: bool = False) -> EnvironmentSettings:
        """加载配置
        
        Args:
            environment: 环境名称，默认从环境变量获取
            force_reload: 是否强制重新加载
            
        Returns:
            EnvironmentSettings: 环境配置对象
        """
        if self._settings is not None and not force_reload:
            return self._settings
        
        try:
            if environment is None:
                environment = self._detect_environment()
            
            logging.info(f"正在加载 {environment} 环境配置...")
            
            self._settings = self._config_manager.load_settings(environment)
            
            # 验证配置
            if not self._config_manager.validate_settings(self._settings):
                raise ConfigurationException(f"{environment} 环境配置验证失败")
            
            logging.info(f"{environment} 环境配置加载成功")
            return self._settings
            
        except Exception as e:
            logging.error(f"配置加载失败: {str(e)}")
            raise ConfigurationException(f"配置加载失败: {str(e)}")
    
    def get_current_config(self) -> Optional[EnvironmentSettings]:
        """获取当前配置"""
        return self._settings
    
    def reload_config(self, environment: Optional[str] = None) -> EnvironmentSettings:
        """重新加载配置
        
        Args:
            environment: 环境名称
            
        Returns:
            EnvironmentSettings: 环境配置对象
        """
        return self.load_config(environment, force_reload=True)
    
    def save_config(self, settings: EnvironmentSettings, environment: Optional[str] = None):
        """保存配置
        
        Args:
            settings: 配置对象
            environment: 环境名称
        """
        try:
            self._config_manager.save_settings(settings, environment)
            logging.info(f"配置保存成功: {environment or settings.environment}")
        except Exception as e:
            logging.error(f"配置保存失败: {str(e)}")
            raise ConfigurationException(f"配置保存失败: {str(e)}")
    
    def _detect_environment(self) -> str:
        """自动检测环境"""
        # 1. 从环境变量获取
        env = os.getenv('MEDICAL_INSURANCE_ENV')
        if env:
            return env.lower()
        
        # 2. 从Python环境变量获取
        env = os.getenv('PYTHON_ENV') or os.getenv('ENV')
        if env:
            return env.lower()
        
        # 3. 根据其他环境变量推断
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            return 'testing'
        
        if os.getenv('KUBERNETES_SERVICE_HOST') or os.getenv('DOCKER_CONTAINER'):
            return 'production'
        
        # 4. 默认为开发环境
        return 'development'
    
    def create_default_configs(self):
        """创建默认配置文件"""
        environments = ['development', 'testing', 'production']
        
        for env in environments:
            try:
                config_file = Path(self._config_manager.config_dir) / f"{env}.yaml"
                if not config_file.exists():
                    self._config_manager._create_default_config(env)
                    logging.info(f"创建默认配置文件: {config_file}")
            except Exception as e:
                logging.error(f"创建 {env} 环境默认配置失败: {str(e)}")
    
    def validate_current_config(self) -> bool:
        """验证当前配置"""
        if self._settings is None:
            return False
        
        return self._config_manager.validate_settings(self._settings)
    
    def get_config_info(self) -> dict:
        """获取配置信息"""
        if self._settings is None:
            return {"status": "未加载配置"}
        
        return {
            "environment": self._settings.environment,
            "debug": self._settings.debug,
            "database_host": self._settings.database.host,
            "database_name": self._settings.database.database,
            "redis_host": self._settings.redis.host,
            "log_level": self._settings.logging.level,
            "config_valid": self.validate_current_config(),
        }


# 全局配置加载器实例
config_loader = ConfigLoader()


def get_settings(environment: Optional[str] = None) -> EnvironmentSettings:
    """获取配置的便捷函数
    
    Args:
        environment: 环境名称
        
    Returns:
        EnvironmentSettings: 环境配置对象
    """
    return config_loader.load_config(environment)


def get_current_settings() -> Optional[EnvironmentSettings]:
    """获取当前配置的便捷函数
    
    Returns:
        EnvironmentSettings: 当前环境配置对象
    """
    return config_loader.get_current_config()


def reload_settings(environment: Optional[str] = None) -> EnvironmentSettings:
    """重新加载配置的便捷函数
    
    Args:
        environment: 环境名称
        
    Returns:
        EnvironmentSettings: 环境配置对象
    """
    return config_loader.reload_config(environment)