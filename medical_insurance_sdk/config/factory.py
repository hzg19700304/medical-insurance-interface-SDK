"""配置工厂 - 统一的配置创建和管理"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .settings import EnvironmentSettings, ConfigurationManager
from .env_manager import EnvironmentVariableManager, env_manager
from .loader import ConfigLoader
from .validator import ConfigValidator
from ..exceptions import ConfigurationException


class ConfigurationFactory:
    """配置工厂 - 负责创建和管理完整的配置对象"""
    
    def __init__(self):
        """初始化配置工厂"""
        self._config_manager: Optional[ConfigurationManager] = None
        self._env_manager: EnvironmentVariableManager = env_manager
        self._config_loader: Optional[ConfigLoader] = None
        self._validator: Optional[ConfigValidator] = None
        
        # 配置加载优先级
        self._load_priority = [
            "environment_variables",  # 环境变量（最高优先级）
            "config_file",           # 配置文件
            "default_values"         # 默认值（最低优先级）
        ]
    
    def create_configuration(self, 
                           environment: Optional[str] = None,
                           config_file: Optional[str] = None,
                           config_dir: Optional[str] = None,
                           load_env_file: Optional[str] = None,
                           validate: bool = True) -> EnvironmentSettings:
        """创建完整的配置对象
        
        Args:
            environment: 环境名称
            config_file: 指定配置文件路径
            config_dir: 配置文件目录
            load_env_file: 环境变量文件路径
            validate: 是否验证配置
            
        Returns:
            EnvironmentSettings: 完整的环境配置对象
        """
        try:
            # 1. 初始化组件
            self._initialize_components(config_dir)
            
            # 2. 加载环境变量文件（如果指定）
            if load_env_file:
                self._load_env_file(load_env_file)
            
            # 3. 确定环境
            if environment is None:
                environment = self._detect_environment()
            
            logging.info(f"正在创建 {environment} 环境配置...")
            
            # 4. 加载环境变量
            env_vars = self._env_manager.load_environment_variables()
            logging.debug(f"加载了 {len(env_vars)} 个环境变量")
            
            # 5. 加载配置文件
            if config_file:
                # 使用指定的配置文件
                config_settings = self._load_specific_config_file(config_file)
            else:
                # 使用环境对应的配置文件
                config_settings = self._config_manager.load_settings(environment)
            
            # 6. 合并配置（环境变量优先）
            merged_config = self._merge_configurations(config_settings, env_vars)
            
            # 7. 验证配置
            if validate:
                self._validate_configuration(merged_config)
            
            logging.info(f"{environment} 环境配置创建成功")
            return merged_config
            
        except Exception as e:
            logging.error(f"配置创建失败: {str(e)}")
            raise ConfigurationException(f"配置创建失败: {str(e)}")
    
    def _initialize_components(self, config_dir: Optional[str]):
        """初始化组件"""
        if config_dir is None:
            config_dir = os.getenv('MEDICAL_CONFIG_DIR')
            if config_dir is None:
                config_dir = str(Path(__file__).parent / "environments")
        
        self._config_manager = ConfigurationManager(config_dir)
        self._config_loader = ConfigLoader()
        self._validator = ConfigValidator()
    
    def _load_env_file(self, env_file_path: str):
        """加载环境变量文件"""
        try:
            self._env_manager.load_from_file(env_file_path)
            logging.info(f"已加载环境变量文件: {env_file_path}")
        except Exception as e:
            logging.warning(f"加载环境变量文件失败: {str(e)}")
    
    def _detect_environment(self) -> str:
        """检测环境"""
        # 1. 从环境变量获取
        env = os.getenv('MEDICAL_INSURANCE_ENV')
        if env:
            return env.lower()
        
        # 2. 从其他标准环境变量获取
        env = os.getenv('ENVIRONMENT') or os.getenv('ENV') or os.getenv('NODE_ENV')
        if env:
            return env.lower()
        
        # 3. 根据运行环境推断
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or os.getenv('JENKINS_URL'):
            return 'testing'
        
        if (os.getenv('KUBERNETES_SERVICE_HOST') or 
            os.getenv('DOCKER_CONTAINER') or 
            os.getenv('HEROKU_APP_NAME')):
            return 'production'
        
        # 4. 默认为开发环境
        return 'development'
    
    def _load_specific_config_file(self, config_file: str) -> EnvironmentSettings:
        """加载指定的配置文件"""
        config_path = Path(config_file)
        if not config_path.exists():
            raise ConfigurationException(f"配置文件不存在: {config_file}")
        
        # 临时设置配置目录
        original_config_dir = self._config_manager.config_dir
        self._config_manager.config_dir = config_path.parent
        
        try:
            # 加载配置
            environment = config_path.stem
            return self._config_manager.load_settings(environment)
        finally:
            # 恢复原配置目录
            self._config_manager.config_dir = original_config_dir
    
    def _merge_configurations(self, 
                            config_settings: EnvironmentSettings, 
                            env_vars: Dict[str, Any]) -> EnvironmentSettings:
        """合并配置（环境变量优先）"""
        # 将配置对象转换为字典
        config_dict = self._config_manager._settings_to_dict(config_settings)
        
        # 应用环境变量覆盖
        merged_dict = self._env_manager.apply_to_config(config_dict)
        
        # 转换回配置对象
        merged_settings = self._config_manager._create_settings_from_dict(
            merged_dict, 
            config_settings.environment
        )
        
        return merged_settings
    
    def _validate_configuration(self, settings: EnvironmentSettings):
        """验证配置"""
        if not self._validator.validate_settings(settings):
            report = self._validator.get_validation_report()
            error_msg = f"配置验证失败: {'; '.join(report['errors'])}"
            raise ConfigurationException(error_msg)
    
    def create_default_configuration(self, environment: str) -> EnvironmentSettings:
        """创建默认配置
        
        Args:
            environment: 环境名称
            
        Returns:
            EnvironmentSettings: 默认配置对象
        """
        self._initialize_components(None)
        
        # 创建默认配置文件（如果不存在）
        self._config_manager._create_default_config(environment)
        
        # 加载默认配置
        return self._config_manager.load_settings(environment)
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        env_validation = self._env_manager.validate_environment()
        
        return {
            "environment_variables": {
                "total_defined": len(self._env_manager.get_env_definitions()),
                "loaded_count": env_validation["loaded_count"],
                "validation": env_validation
            },
            "config_files": {
                "config_directory": str(self._config_manager.config_dir) if self._config_manager else None,
                "available_environments": self._get_available_environments()
            }
        }
    
    def _get_available_environments(self) -> list:
        """获取可用的环境配置"""
        if not self._config_manager:
            return []
        
        config_dir = Path(self._config_manager.config_dir)
        if not config_dir.exists():
            return []
        
        environments = []
        for config_file in config_dir.glob("*.yaml"):
            environments.append(config_file.stem)
        
        return sorted(environments)
    
    def generate_configuration_template(self, 
                                      environment: str,
                                      include_env_file: bool = True,
                                      include_sensitive: bool = False) -> Dict[str, str]:
        """生成配置模板
        
        Args:
            environment: 环境名称
            include_env_file: 是否包含环境变量文件模板
            include_sensitive: 是否包含敏感信息
            
        Returns:
            dict: 模板内容字典
        """
        templates = {}
        
        # 生成配置文件模板
        default_config = self.create_default_configuration(environment)
        config_dict = self._config_manager._settings_to_dict(default_config)
        
        # 转换为YAML格式（简化版）
        import yaml
        templates[f"{environment}.yaml"] = yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)
        
        # 生成环境变量文件模板
        if include_env_file:
            templates[".env"] = self._env_manager.generate_env_template(include_sensitive)
        
        return templates
    
    def backup_configuration(self, backup_dir: str):
        """备份配置文件
        
        Args:
            backup_dir: 备份目录
        """
        import shutil
        from datetime import datetime
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = backup_path / f"config_backup_{timestamp}"
        backup_subdir.mkdir(exist_ok=True)
        
        # 备份配置文件目录
        if self._config_manager and self._config_manager.config_dir.exists():
            shutil.copytree(
                self._config_manager.config_dir,
                backup_subdir / "environments",
                dirs_exist_ok=True
            )
        
        logging.info(f"配置文件已备份到: {backup_subdir}")
        return str(backup_subdir)
    
    def restore_configuration(self, backup_dir: str):
        """恢复配置文件
        
        Args:
            backup_dir: 备份目录
        """
        import shutil
        
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            raise ConfigurationException(f"备份目录不存在: {backup_dir}")
        
        environments_backup = backup_path / "environments"
        if not environments_backup.exists():
            raise ConfigurationException(f"备份中未找到环境配置: {environments_backup}")
        
        # 恢复配置文件
        if self._config_manager:
            shutil.rmtree(self._config_manager.config_dir, ignore_errors=True)
            shutil.copytree(environments_backup, self._config_manager.config_dir)
        
        logging.info(f"配置文件已从备份恢复: {backup_dir}")


# 全局配置工厂实例
config_factory = ConfigurationFactory()


def create_config(environment: Optional[str] = None,
                 config_file: Optional[str] = None,
                 config_dir: Optional[str] = None,
                 env_file: Optional[str] = None,
                 validate: bool = True) -> EnvironmentSettings:
    """创建配置的便捷函数
    
    Args:
        environment: 环境名称
        config_file: 配置文件路径
        config_dir: 配置目录
        env_file: 环境变量文件路径
        validate: 是否验证配置
        
    Returns:
        EnvironmentSettings: 环境配置对象
    """
    return config_factory.create_configuration(
        environment=environment,
        config_file=config_file,
        config_dir=config_dir,
        load_env_file=env_file,
        validate=validate
    )


def get_config_info() -> Dict[str, Any]:
    """获取配置信息的便捷函数
    
    Returns:
        dict: 配置信息
    """
    return config_factory.get_configuration_info()