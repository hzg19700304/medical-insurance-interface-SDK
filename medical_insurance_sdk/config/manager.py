"""配置管理器"""

from typing import Optional
from ..core.database import DatabaseConfig, DatabaseManager
from .models import InterfaceConfig, OrganizationConfig
from ..exceptions import ConfigurationException


class ConfigManager:
    """配置管理器"""

    def __init__(self, db_config: DatabaseConfig):
        """初始化配置管理器

        Args:
            db_config: 数据库配置
        """
        self.db_manager = DatabaseManager(db_config)
        self._interface_config_cache = {}
        self._org_config_cache = {}

    def get_interface_config(
        self, api_code: str, region: Optional[str] = None
    ) -> InterfaceConfig:
        """获取接口配置

        Args:
            api_code: 接口编码
            region: 地区代码

        Returns:
            InterfaceConfig: 接口配置

        Raises:
            ConfigurationException: 配置不存在或无效时抛出异常
        """
        # TODO: 实现从数据库加载接口配置的逻辑
        # 这里先返回一个基础的配置对象，实际实现将在后续任务中完成

        cache_key = f"{api_code}_{region or 'default'}"
        if cache_key in self._interface_config_cache:
            return self._interface_config_cache[cache_key]

        # 临时返回默认配置
        config = InterfaceConfig(
            api_code=api_code,
            api_name=f"接口{api_code}",
            business_category="查询类",
            business_type="基础查询",
            required_params={},
            optional_params={},
            default_values={},
            request_template={},
            response_mapping={},
            validation_rules={},
            region_specific={},
            is_active=True,
            timeout_seconds=30,
            max_retry_times=3,
        )

        self._interface_config_cache[cache_key] = config
        return config

    def get_organization_config(self, org_code: str) -> OrganizationConfig:
        """获取机构配置

        Args:
            org_code: 机构编码

        Returns:
            OrganizationConfig: 机构配置

        Raises:
            ConfigurationException: 配置不存在或无效时抛出异常
        """
        # TODO: 实现从数据库加载机构配置的逻辑
        # 这里先返回一个基础的配置对象，实际实现将在后续任务中完成

        if org_code in self._org_config_cache:
            return self._org_config_cache[org_code]

        # 临时返回默认配置
        config = OrganizationConfig(
            org_code=org_code,
            org_name=f"机构{org_code}",
            org_type="医院",
            province_code="430000",
            city_code="430100",
            app_id="test_app_id",
            app_secret="test_app_secret",
            base_url="http://localhost:8080/api",
            crypto_type="SM4",
            sign_type="SM3",
            timeout_config={"default": 30},
            is_active=True,
        )

        self._org_config_cache[org_code] = config
        return config

    def reload_config(self, config_type: Optional[str] = None):
        """重新加载配置

        Args:
            config_type: 配置类型，None表示重新加载所有配置
        """
        if config_type is None or config_type == "interface":
            self._interface_config_cache.clear()

        if config_type is None or config_type == "organization":
            self._org_config_cache.clear()

    def test_database_connection(self) -> bool:
        """测试数据库连接

        Returns:
            bool: 连接是否正常
        """
        return self.db_manager.test_connection()
