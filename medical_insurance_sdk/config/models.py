"""配置数据模型"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import json


@dataclass
class InterfaceConfig:
    """接口配置模型"""

    api_code: str
    api_name: str
    business_category: str
    business_type: str
    required_params: Dict[str, Any]
    optional_params: Dict[str, Any]
    default_values: Dict[str, Any]
    request_template: Dict[str, Any]
    response_mapping: Dict[str, Any]
    validation_rules: Dict[str, Any]
    region_specific: Dict[str, Any]
    is_active: bool
    timeout_seconds: int
    max_retry_times: int

    @classmethod
    def from_db_record(cls, record: dict) -> "InterfaceConfig":
        """从数据库记录创建配置对象"""
        return cls(
            api_code=record["api_code"],
            api_name=record["api_name"],
            business_category=record["business_category"],
            business_type=record["business_type"],
            required_params=(
                json.loads(record["required_params"])
                if record["required_params"]
                else {}
            ),
            optional_params=(
                json.loads(record["optional_params"])
                if record["optional_params"]
                else {}
            ),
            default_values=(
                json.loads(record["default_values"]) if record["default_values"] else {}
            ),
            request_template=(
                json.loads(record["request_template"])
                if record["request_template"]
                else {}
            ),
            response_mapping=(
                json.loads(record["response_mapping"])
                if record["response_mapping"]
                else {}
            ),
            validation_rules=(
                json.loads(record["validation_rules"])
                if record["validation_rules"]
                else {}
            ),
            region_specific=(
                json.loads(record["region_specific"])
                if record["region_specific"]
                else {}
            ),
            is_active=record["is_active"],
            timeout_seconds=record["timeout_seconds"],
            max_retry_times=record["max_retry_times"],
        )


@dataclass
class OrganizationConfig:
    """机构配置模型"""

    org_code: str
    org_name: str
    org_type: str
    province_code: str
    city_code: str
    app_id: str
    app_secret: str
    base_url: str
    crypto_type: str
    sign_type: str
    timeout_config: Dict[str, int]
    is_active: bool

    @classmethod
    def from_db_record(cls, record: dict) -> "OrganizationConfig":
        """从数据库记录创建配置对象"""
        return cls(
            org_code=record["org_code"],
            org_name=record["org_name"],
            org_type=record["org_type"],
            province_code=record["province_code"],
            city_code=record["city_code"],
            app_id=record["app_id"],
            app_secret=record["app_secret"],
            base_url=record["base_url"],
            crypto_type=record["crypto_type"],
            sign_type=record["sign_type"],
            timeout_config=(
                json.loads(record["timeout_config"]) if record["timeout_config"] else {}
            ),
            is_active=record["is_active"],
        )


@dataclass
class SDKConfig:
    """SDK总体配置"""

    database_config: Any  # DatabaseConfig type will be imported when needed
    redis_config: Optional[Dict[str, Any]] = None
    log_config: Optional[Dict[str, Any]] = None
    crypto_config: Optional[Dict[str, Any]] = None
    http_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.redis_config is None:
            self.redis_config = {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
            }

        if self.log_config is None:
            self.log_config = {
                "level": "INFO",
                "file": "logs/medical_insurance_sdk.log",
                "max_size": "10MB",
                "backup_count": 5,
            }

        if self.crypto_config is None:
            self.crypto_config = {
                "default_crypto_type": "SM4",
                "default_sign_type": "SM3",
            }

        if self.http_config is None:
            self.http_config = {
                "timeout": 30,
                "max_retries": 3,
                "pool_connections": 10,
                "pool_maxsize": 10,
            }
