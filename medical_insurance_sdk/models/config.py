"""配置模型类"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class InterfaceConfig:
    """接口配置模型"""
    
    api_code: str
    api_name: str
    api_description: Optional[str] = None
    business_category: str = ""
    business_type: str = ""
    required_params: Dict[str, Any] = None
    optional_params: Dict[str, Any] = None
    default_values: Dict[str, Any] = None
    request_template: Dict[str, Any] = None
    param_mapping: Dict[str, Any] = None
    validation_rules: Dict[str, Any] = None
    response_mapping: Dict[str, Any] = None
    success_condition: str = "infcode=0"
    error_handling: Dict[str, Any] = None
    region_specific: Dict[str, Any] = None
    province_overrides: Dict[str, Any] = None
    is_active: bool = True
    requires_auth: bool = True
    supports_batch: bool = False
    max_retry_times: int = 3
    timeout_seconds: int = 30
    config_version: str = "1.0"
    last_updated_by: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.required_params is None:
            self.required_params = {}
        if self.optional_params is None:
            self.optional_params = {}
        if self.default_values is None:
            self.default_values = {}
        if self.request_template is None:
            self.request_template = {}
        if self.param_mapping is None:
            self.param_mapping = {}
        if self.validation_rules is None:
            self.validation_rules = {}
        if self.response_mapping is None:
            self.response_mapping = {}
        if self.error_handling is None:
            self.error_handling = {}
        if self.region_specific is None:
            self.region_specific = {}
        if self.province_overrides is None:
            self.province_overrides = {}

    @classmethod
    def from_db_record(cls, record: Dict[str, Any]) -> 'InterfaceConfig':
        """从数据库记录创建配置对象"""
        def safe_json_loads(value: Any) -> Dict[str, Any]:
            """安全的JSON解析"""
            if value is None:
                return {}
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return {}

        return cls(
            api_code=record.get('api_code', ''),
            api_name=record.get('api_name', ''),
            api_description=record.get('api_description'),
            business_category=record.get('business_category', ''),
            business_type=record.get('business_type', ''),
            required_params=safe_json_loads(record.get('required_params')),
            optional_params=safe_json_loads(record.get('optional_params')),
            default_values=safe_json_loads(record.get('default_values')),
            request_template=safe_json_loads(record.get('request_template')),
            param_mapping=safe_json_loads(record.get('param_mapping')),
            validation_rules=safe_json_loads(record.get('validation_rules')),
            response_mapping=safe_json_loads(record.get('response_mapping')),
            success_condition=record.get('success_condition', 'infcode=0'),
            error_handling=safe_json_loads(record.get('error_handling')),
            region_specific=safe_json_loads(record.get('region_specific')),
            province_overrides=safe_json_loads(record.get('province_overrides')),
            is_active=record.get('is_active', True),
            requires_auth=record.get('requires_auth', True),
            supports_batch=record.get('supports_batch', False),
            max_retry_times=record.get('max_retry_times', 3),
            timeout_seconds=record.get('timeout_seconds', 30),
            config_version=record.get('config_version', '1.0'),
            last_updated_by=record.get('last_updated_by')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'api_code': self.api_code,
            'api_name': self.api_name,
            'api_description': self.api_description,
            'business_category': self.business_category,
            'business_type': self.business_type,
            'required_params': self.required_params,
            'optional_params': self.optional_params,
            'default_values': self.default_values,
            'request_template': self.request_template,
            'param_mapping': self.param_mapping,
            'validation_rules': self.validation_rules,
            'response_mapping': self.response_mapping,
            'success_condition': self.success_condition,
            'error_handling': self.error_handling,
            'region_specific': self.region_specific,
            'province_overrides': self.province_overrides,
            'is_active': self.is_active,
            'requires_auth': self.requires_auth,
            'supports_batch': self.supports_batch,
            'max_retry_times': self.max_retry_times,
            'timeout_seconds': self.timeout_seconds,
            'config_version': self.config_version,
            'last_updated_by': self.last_updated_by
        }


@dataclass
class OrganizationConfig:
    """机构配置模型"""
    
    org_code: str
    org_name: str
    org_type: str = ""
    province_code: str = ""
    city_code: str = ""
    region_code: str = ""
    app_id: str = ""
    app_secret: str = ""
    base_url: str = ""
    crypto_type: str = "SM3"
    sign_type: str = "SM2"
    timeout_config: Dict[str, int] = None
    encryption_config: Dict[str, Any] = None
    gateway_config: Dict[str, Any] = None
    is_active: bool = True
    environment: str = "production"
    description: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.timeout_config is None:
            self.timeout_config = {
                'default': 30,
                'query': 15,
                'settlement': 60,
                'upload': 120
            }
        if self.encryption_config is None:
            self.encryption_config = {}
        if self.gateway_config is None:
            self.gateway_config = {}

    @classmethod
    def from_db_record(cls, record: Dict[str, Any]) -> 'OrganizationConfig':
        """从数据库记录创建配置对象"""
        def safe_json_loads(value: Any) -> Dict[str, Any]:
            """安全的JSON解析"""
            if value is None:
                return {}
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return {}

        return cls(
            org_code=record.get('org_code', ''),
            org_name=record.get('org_name', ''),
            org_type=record.get('org_type', ''),
            province_code=record.get('province_code', ''),
            city_code=record.get('city_code', ''),
            region_code=record.get('region_code', ''),
            app_id=record.get('app_id', ''),
            app_secret=record.get('app_secret', ''),
            base_url=record.get('base_url', ''),
            crypto_type=record.get('crypto_type', 'SM3'),
            sign_type=record.get('sign_type', 'SM2'),
            timeout_config=safe_json_loads(record.get('timeout_config')),
            encryption_config=safe_json_loads(record.get('encryption_config')),
            gateway_config=safe_json_loads(record.get('gateway_config')),
            is_active=record.get('is_active', True),
            environment=record.get('environment', 'production'),
            description=record.get('description'),
            contact_person=record.get('contact_person'),
            contact_phone=record.get('contact_phone')
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'org_code': self.org_code,
            'org_name': self.org_name,
            'org_type': self.org_type,
            'province_code': self.province_code,
            'city_code': self.city_code,
            'region_code': self.region_code,
            'app_id': self.app_id,
            'app_secret': self.app_secret,
            'base_url': self.base_url,
            'crypto_type': self.crypto_type,
            'sign_type': self.sign_type,
            'timeout_config': self.timeout_config,
            'encryption_config': self.encryption_config,
            'gateway_config': self.gateway_config,
            'is_active': self.is_active,
            'environment': self.environment,
            'description': self.description,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone
        }

    def get_timeout(self, operation_type: str = 'default') -> int:
        """获取指定操作类型的超时时间"""
        return self.timeout_config.get(operation_type, self.timeout_config.get('default', 30))