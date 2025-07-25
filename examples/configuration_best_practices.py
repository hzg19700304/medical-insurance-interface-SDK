#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK配置管理最佳实践

本文档提供了医保接口SDK配置管理的最佳实践，包括：
- 环境配置管理
- 接口配置管理
- 机构配置管理
- 安全配置管理
- 性能配置优化

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import json
import yaml
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str
    port: int
    database: str
    username: str
    password: str
    charset: str = "utf8mb4"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str
    port: int
    database: int = 0
    password: str = ""
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/medical_insurance_sdk.log"
    max_file_size: str = "100MB"
    backup_count: int = 5
    enable_console: bool = True


@dataclass
class SecurityConfig:
    """安全配置"""
    encrypt_sensitive_data: bool = True
    secret_key: str = ""
    token_expire_hours: int = 24
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30


@dataclass
class PerformanceConfig:
    """性能配置"""
    enable_cache: bool = True
    cache_ttl_seconds: int = 300
    max_concurrent_requests: int = 100
    request_timeout_seconds: int = 30
    retry_max_attempts: int = 3
    retry_delay_seconds: int = 1


class ConfigurationManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
    def create_environment_configs(self):
        """创建不同环境的配置文件"""
        
        environments = {
            "development": {
                "database": DatabaseConfig(
                    host="localhost",
                    port=3306,
                    database="medical_insurance_dev",
                    username="dev_user",
                    password="dev_password",
                    pool_size=5
                ),
                "redis": RedisConfig(
                    host="localhost",
                    port=6379,
                    database=0,
                    max_connections=20
                ),
                "log": LogConfig(
                    level="DEBUG",
                    enable_console=True
                ),
                "security": SecurityConfig(
                    encrypt_sensitive_data=False,
                    secret_key="dev_secret_key_change_in_production"
                ),
                "performance": PerformanceConfig(
                    enable_cache=True,
                    cache_ttl_seconds=60,
                    max_concurrent_requests=50
                )
            },
            
            "testing": {
                "database": DatabaseConfig(
                    host="test-db-server",
                    port=3306,
                    database="medical_insurance_test",
                    username="test_user",
                    password="test_password",
                    pool_size=3
                ),
                "redis": RedisConfig(
                    host="test-redis-server",
                    port=6379,
                    database=1,
                    max_connections=10
                ),
                "log": LogConfig(
                    level="INFO",
                    enable_console=False
                ),
                "security": SecurityConfig(
                    encrypt_sensitive_data=True,
                    secret_key="test_secret_key"
                ),
                "performance": PerformanceConfig(
                    enable_cache=False,
                    max_concurrent_requests=20
                )
            },
            
            "production": {
                "database": DatabaseConfig(
                    host="prod-db-cluster",
                    port=3306,
                    database="medical_insurance_prod",
                    username="prod_user",
                    password="${DB_PASSWORD}",  # 从环境变量获取
                    pool_size=20,
                    max_overflow=50
                ),
                "redis": RedisConfig(
                    host="prod-redis-cluster",
                    port=6379,
                    database=0,
                    password="${REDIS_PASSWORD}",
                    max_connections=100
                ),
                "log": LogConfig(
                    level="WARNING",
                    enable_console=False,
                    file_path="/var/log/medical_insurance_sdk.log"
                ),
                "security": SecurityConfig(
                    encrypt_sensitive_data=True,
                    secret_key="${SECRET_KEY}",
                    token_expire_hours=8,
                    max_login_attempts=3
                ),
                "performance": PerformanceConfig(
                    enable_cache=True,
                    cache_ttl_seconds=600,
                    max_concurrent_requests=200,
                    request_timeout_seconds=60
                )
            }
        }
        
        # 生成配置文件
        for env_name, config in environments.items():
            config_data = {}
            for section_name, section_config in config.items():
                config_data[section_name] = asdict(section_config)
            
            # 保存为JSON格式
            json_file = self.config_dir / f"{env_name}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # 保存为YAML格式
            yaml_file = self.config_dir / f"{env_name}.yaml"
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✓ 创建{env_name}环境配置: {json_file}, {yaml_file}")

    def create_interface_config_template(self):
        """创建接口配置模板"""
        
        interface_config_template = {
            "1101": {
                "api_name": "人员信息获取",
                "business_category": "查询类",
                "business_type": "人员查询",
                "required_params": {
                    "mdtrt_cert_type": {
                        "display_name": "就诊凭证类型",
                        "description": "01-电子凭证；02-身份证；03-社保卡",
                        "type": "string",
                        "enum_values": ["01", "02", "03"]
                    },
                    "mdtrt_cert_no": {
                        "display_name": "就诊凭证编号",
                        "description": "凭证对应的编号",
                        "type": "string",
                        "max_length": 50
                    },
                    "psn_cert_type": {
                        "display_name": "人员证件类型",
                        "description": "01-身份证",
                        "type": "string",
                        "enum_values": ["01"]
                    },
                    "certno": {
                        "display_name": "证件号码",
                        "description": "身份证号码",
                        "type": "string",
                        "pattern": "^[0-9]{17}[0-9Xx]$"
                    },
                    "psn_name": {
                        "display_name": "人员姓名",
                        "description": "参保人姓名",
                        "type": "string",
                        "max_length": 50
                    }
                },
                "optional_params": {
                    "card_sn": {
                        "display_name": "卡识别码",
                        "description": "社保卡识别码",
                        "type": "string",
                        "max_length": 32
                    },
                    "begntime": {
                        "display_name": "开始时间",
                        "description": "查询开始时间",
                        "type": "string",
                        "format": "datetime"
                    }
                },
                "default_values": {
                    "psn_cert_type": "01",
                    "begntime": ""
                },
                "validation_rules": {
                    "conditional_rules": [
                        {
                            "condition": {
                                "field": "mdtrt_cert_type",
                                "operator": "eq",
                                "value": "03"
                            },
                            "required_fields": ["card_sn"],
                            "error_message": "使用社保卡时卡识别码不能为空"
                        }
                    ]
                },
                "response_mapping": {
                    "person_info": {
                        "type": "direct",
                        "source_path": "baseinfo"
                    },
                    "insurance_list": {
                        "type": "array_mapping",
                        "source_path": "insuinfo",
                        "item_mapping": {
                            "insurance_type": "insutype",
                            "balance": "balc",
                            "status": "psn_insu_stas"
                        }
                    }
                },
                "timeout_seconds": 30,
                "max_retry_times": 3,
                "is_active": True
            },
            
            "2201": {
                "api_name": "门诊结算",
                "business_category": "结算类",
                "business_type": "门诊结算",
                "required_params": {
                    "mdtrt_id": {
                        "display_name": "就医登记号",
                        "description": "医疗机构就医登记号",
                        "type": "string",
                        "max_length": 30
                    },
                    "psn_no": {
                        "display_name": "人员编号",
                        "description": "医保人员编号",
                        "type": "string",
                        "max_length": 30
                    },
                    "chrg_bchno": {
                        "display_name": "收费批次号",
                        "description": "收费批次号",
                        "type": "string",
                        "max_length": 30
                    }
                },
                "optional_params": {
                    "acct_used_flag": {
                        "display_name": "个人账户使用标志",
                        "description": "0-不使用，1-使用",
                        "type": "string",
                        "enum_values": ["0", "1"]
                    },
                    "insutype": {
                        "display_name": "险种类型",
                        "description": "险种类型编码",
                        "type": "string"
                    }
                },
                "default_values": {
                    "acct_used_flag": "0",
                    "insutype": "310"
                },
                "response_mapping": {
                    "settlement_result": {
                        "type": "direct",
                        "source_path": "setlinfo"
                    },
                    "settlement_id": {
                        "type": "direct",
                        "source_path": "setlinfo.setl_id"
                    },
                    "total_amount": {
                        "type": "direct",
                        "source_path": "setlinfo.setl_totlnum"
                    }
                },
                "timeout_seconds": 60,
                "max_retry_times": 2,
                "is_active": True
            }
        }
        
        template_file = self.config_dir / "interface_config_template.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(interface_config_template, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建接口配置模板: {template_file}")

    def create_organization_config_template(self):
        """创建机构配置模板"""
        
        organization_config_template = {
            "H43010000001": {
                "org_name": "湖南省人民医院",
                "org_type": "综合医院",
                "province_code": "43",
                "city_code": "4301",
                "region_code": "430100",
                "app_id": "HNRMYY001",
                "app_secret": "${ORG_H43010000001_SECRET}",
                "base_url": "https://api.hnybj.gov.cn/gateway",
                "crypto_type": "SM4",
                "sign_type": "SM3",
                "timeout_config": {
                    "default": 30,
                    "query": 15,
                    "settlement": 60,
                    "upload": 120
                },
                "retry_config": {
                    "max_attempts": 3,
                    "delay_seconds": 1,
                    "backoff_factor": 2
                },
                "special_config": {
                    "enable_cache": True,
                    "cache_ttl": 300,
                    "enable_async": True
                }
            },
            
            "H44010000001": {
                "org_name": "广东省人民医院",
                "org_type": "综合医院",
                "province_code": "44",
                "city_code": "4401",
                "region_code": "440100",
                "app_id": "GDRMYY001",
                "app_secret": "${ORG_H44010000001_SECRET}",
                "base_url": "https://api.gdybj.gov.cn/gateway",
                "crypto_type": "AES",
                "sign_type": "SHA256",
                "timeout_config": {
                    "default": 30,
                    "query": 20,
                    "settlement": 90
                },
                "retry_config": {
                    "max_attempts": 2,
                    "delay_seconds": 2
                },
                "special_config": {
                    "enable_cache": False,
                    "enable_async": False
                }
            },
            
            "H31010000001": {
                "org_name": "上海市第一人民医院",
                "org_type": "综合医院",
                "province_code": "31",
                "city_code": "3101",
                "region_code": "310100",
                "app_id": "SHDYRMYY001",
                "app_secret": "${ORG_H31010000001_SECRET}",
                "base_url": "https://api.shybj.gov.cn/gateway",
                "crypto_type": "SM4",
                "sign_type": "SM3",
                "timeout_config": {
                    "default": 25,
                    "query": 10,
                    "settlement": 45
                },
                "retry_config": {
                    "max_attempts": 3,
                    "delay_seconds": 0.5
                },
                "special_config": {
                    "enable_cache": True,
                    "cache_ttl": 600,
                    "enable_async": True,
                    "custom_headers": {
                        "X-Region": "Shanghai",
                        "X-Version": "2.0"
                    }
                }
            }
        }
        
        template_file = self.config_dir / "organization_config_template.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(organization_config_template, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建机构配置模板: {template_file}")

    def create_security_config_guide(self):
        """创建安全配置指南"""
        
        security_guide = {
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True,
                "forbidden_patterns": [
                    "123456",
                    "password",
                    "admin",
                    "root"
                ]
            },
            
            "encryption_settings": {
                "algorithm": "AES-256-GCM",
                "key_rotation_days": 90,
                "salt_length": 32,
                "iteration_count": 100000
            },
            
            "access_control": {
                "session_timeout_minutes": 30,
                "max_concurrent_sessions": 5,
                "ip_whitelist": [
                    "192.168.1.0/24",
                    "10.0.0.0/8"
                ],
                "rate_limiting": {
                    "requests_per_minute": 60,
                    "burst_size": 10
                }
            },
            
            "audit_settings": {
                "log_all_requests": True,
                "log_sensitive_data": False,
                "retention_days": 365,
                "alert_on_failures": True
            },
            
            "ssl_tls_settings": {
                "min_tls_version": "1.2",
                "cipher_suites": [
                    "ECDHE-RSA-AES256-GCM-SHA384",
                    "ECDHE-RSA-AES128-GCM-SHA256"
                ],
                "certificate_validation": True
            }
        }
        
        guide_file = self.config_dir / "security_config_guide.json"
        with open(guide_file, 'w', encoding='utf-8') as f:
            json.dump(security_guide, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建安全配置指南: {guide_file}")

    def create_performance_tuning_guide(self):
        """创建性能调优指南"""
        
        performance_guide = {
            "database_optimization": {
                "connection_pool": {
                    "initial_size": 5,
                    "max_size": 20,
                    "increment": 2,
                    "timeout_seconds": 30,
                    "validation_query": "SELECT 1",
                    "test_on_borrow": True,
                    "test_while_idle": True
                },
                "query_optimization": {
                    "enable_query_cache": True,
                    "cache_size_mb": 256,
                    "slow_query_threshold_ms": 1000,
                    "explain_slow_queries": True
                },
                "indexing_strategy": {
                    "auto_create_indexes": False,
                    "index_maintenance_schedule": "0 2 * * 0",
                    "statistics_update_frequency": "daily"
                }
            },
            
            "cache_optimization": {
                "redis_settings": {
                    "max_memory": "512mb",
                    "eviction_policy": "allkeys-lru",
                    "persistence": "rdb",
                    "save_frequency": "900 1 300 10 60 10000"
                },
                "cache_strategies": {
                    "interface_config": {
                        "ttl_seconds": 3600,
                        "max_size": 1000,
                        "eviction_policy": "lru"
                    },
                    "organization_config": {
                        "ttl_seconds": 7200,
                        "max_size": 500,
                        "eviction_policy": "lru"
                    },
                    "user_sessions": {
                        "ttl_seconds": 1800,
                        "max_size": 10000,
                        "eviction_policy": "ttl"
                    }
                }
            },
            
            "application_optimization": {
                "thread_pool": {
                    "core_size": 10,
                    "max_size": 50,
                    "queue_capacity": 1000,
                    "keep_alive_seconds": 60
                },
                "request_processing": {
                    "max_request_size_mb": 10,
                    "request_timeout_seconds": 30,
                    "enable_compression": True,
                    "compression_threshold": 1024
                },
                "memory_management": {
                    "initial_heap_size": "512m",
                    "max_heap_size": "2g",
                    "gc_algorithm": "G1GC",
                    "enable_gc_logging": True
                }
            },
            
            "monitoring_settings": {
                "metrics_collection": {
                    "enable_jvm_metrics": True,
                    "enable_database_metrics": True,
                    "enable_cache_metrics": True,
                    "collection_interval_seconds": 30
                },
                "alerting_thresholds": {
                    "cpu_usage_percent": 80,
                    "memory_usage_percent": 85,
                    "response_time_ms": 5000,
                    "error_rate_percent": 5
                }
            }
        }
        
        guide_file = self.config_dir / "performance_tuning_guide.json"
        with open(guide_file, 'w', encoding='utf-8') as f:
            json.dump(performance_guide, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建性能调优指南: {guide_file}")

    def create_deployment_configs(self):
        """创建部署配置"""
        
        # Docker配置
        docker_compose = {
            "version": "3.8",
            "services": {
                "medical-insurance-sdk": {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile"
                    },
                    "ports": ["8080:8080"],
                    "environment": [
                        "ENVIRONMENT=production",
                        "DB_HOST=mysql",
                        "DB_PORT=3306",
                        "DB_NAME=medical_insurance",
                        "DB_USER=app_user",
                        "DB_PASSWORD=${DB_PASSWORD}",
                        "REDIS_HOST=redis",
                        "REDIS_PORT=6379",
                        "SECRET_KEY=${SECRET_KEY}"
                    ],
                    "depends_on": ["mysql", "redis"],
                    "volumes": [
                        "./logs:/app/logs",
                        "./config:/app/config"
                    ],
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                
                "mysql": {
                    "image": "mysql:8.0",
                    "environment": [
                        "MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}",
                        "MYSQL_DATABASE=medical_insurance",
                        "MYSQL_USER=app_user",
                        "MYSQL_PASSWORD=${DB_PASSWORD}"
                    ],
                    "ports": ["3306:3306"],
                    "volumes": [
                        "mysql_data:/var/lib/mysql",
                        "./database/init.sql:/docker-entrypoint-initdb.d/init.sql"
                    ],
                    "restart": "unless-stopped"
                },
                
                "redis": {
                    "image": "redis:7-alpine",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"],
                    "restart": "unless-stopped",
                    "command": "redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}"
                }
            },
            
            "volumes": {
                "mysql_data": {},
                "redis_data": {}
            }
        }
        
        compose_file = self.config_dir / "docker-compose.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            yaml.dump(docker_compose, f, default_flow_style=False)
        
        # 环境变量模板
        env_template = """# 医保接口SDK环境变量配置
# 复制此文件为 .env 并填入实际值

# 数据库配置
DB_PASSWORD=your_database_password_here
MYSQL_ROOT_PASSWORD=your_mysql_root_password_here

# Redis配置
REDIS_PASSWORD=your_redis_password_here

# 应用配置
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production

# 医保接口配置
ORG_H43010000001_SECRET=your_org_secret_here
ORG_H44010000001_SECRET=your_org_secret_here
ORG_H31010000001_SECRET=your_org_secret_here

# 监控配置
ENABLE_MONITORING=true
METRICS_PORT=9090

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/logs/medical_insurance_sdk.log
"""
        
        env_file = self.config_dir / ".env.template"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        print(f"✓ 创建Docker部署配置: {compose_file}")
        print(f"✓ 创建环境变量模板: {env_file}")

    def create_configuration_validation_script(self):
        """创建配置验证脚本"""
        
        validation_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证脚本
用于验证医保接口SDK的配置文件是否正确
"""

import json
import os
import sys
from pathlib import Path


def validate_database_config(config):
    """验证数据库配置"""
    required_fields = ['host', 'port', 'database', 'username', 'password']
    errors = []
    
    for field in required_fields:
        if field not in config:
            errors.append(f"数据库配置缺少必填字段: {field}")
    
    if 'port' in config and not isinstance(config['port'], int):
        errors.append("数据库端口必须是整数")
    
    if 'pool_size' in config and config['pool_size'] < 1:
        errors.append("数据库连接池大小必须大于0")
    
    return errors


def validate_redis_config(config):
    """验证Redis配置"""
    errors = []
    
    if 'host' not in config:
        errors.append("Redis配置缺少host字段")
    
    if 'port' in config and not isinstance(config['port'], int):
        errors.append("Redis端口必须是整数")
    
    if 'database' in config and not isinstance(config['database'], int):
        errors.append("Redis数据库编号必须是整数")
    
    return errors


def validate_log_config(config):
    """验证日志配置"""
    errors = []
    
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if 'level' in config and config['level'] not in valid_levels:
        errors.append(f"日志级别必须是以下之一: {', '.join(valid_levels)}")
    
    if 'file_path' in config:
        log_dir = Path(config['file_path']).parent
        if not log_dir.exists():
            errors.append(f"日志目录不存在: {log_dir}")
    
    return errors


def validate_security_config(config):
    """验证安全配置"""
    errors = []
    
    if 'secret_key' in config:
        if len(config['secret_key']) < 32:
            errors.append("密钥长度至少32个字符")
        if config['secret_key'] in ['dev_secret_key_change_in_production', 'test_secret_key']:
            errors.append("生产环境不能使用默认密钥")
    
    if 'token_expire_hours' in config and config['token_expire_hours'] < 1:
        errors.append("令牌过期时间必须大于0小时")
    
    return errors


def validate_performance_config(config):
    """验证性能配置"""
    errors = []
    
    if 'max_concurrent_requests' in config and config['max_concurrent_requests'] < 1:
        errors.append("最大并发请求数必须大于0")
    
    if 'request_timeout_seconds' in config and config['request_timeout_seconds'] < 1:
        errors.append("请求超时时间必须大于0秒")
    
    if 'cache_ttl_seconds' in config and config['cache_ttl_seconds'] < 0:
        errors.append("缓存TTL不能为负数")
    
    return errors


def validate_config_file(config_file):
    """验证配置文件"""
    print(f"验证配置文件: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"✗ 配置文件不存在: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ 配置文件JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 读取配置文件失败: {e}")
        return False
    
    all_errors = []
    
    # 验证各个配置段
    if 'database' in config:
        errors = validate_database_config(config['database'])
        all_errors.extend([f"数据库配置: {error}" for error in errors])
    
    if 'redis' in config:
        errors = validate_redis_config(config['redis'])
        all_errors.extend([f"Redis配置: {error}" for error in errors])
    
    if 'log' in config:
        errors = validate_log_config(config['log'])
        all_errors.extend([f"日志配置: {error}" for error in errors])
    
    if 'security' in config:
        errors = validate_security_config(config['security'])
        all_errors.extend([f"安全配置: {error}" for error in errors])
    
    if 'performance' in config:
        errors = validate_performance_config(config['performance'])
        all_errors.extend([f"性能配置: {error}" for error in errors])
    
    if all_errors:
        print("✗ 配置验证失败:")
        for error in all_errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ 配置验证通过")
        return True


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python validate_config.py <config_file>")
        print("示例: python validate_config.py config/production.json")
        sys.exit(1)
    
    config_file = sys.argv[1]
    success = validate_config_file(config_file)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        
        script_file = self.config_dir / "validate_config.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(validation_script)
        
        # 设置执行权限
        os.chmod(script_file, 0o755)
        
        print(f"✓ 创建配置验证脚本: {script_file}")

    def generate_all_configs(self):
        """生成所有配置文件和指南"""
        print("生成医保接口SDK配置管理文件...")
        print("="*60)
        
        self.create_environment_configs()
        self.create_interface_config_template()
        self.create_organization_config_template()
        self.create_security_config_guide()
        self.create_performance_tuning_guide()
        self.create_deployment_configs()
        self.create_configuration_validation_script()
        
        print("\n" + "="*60)
        print("配置文件生成完成！")
        print("\n生成的文件:")
        for file_path in sorted(self.config_dir.glob("*")):
            print(f"  - {file_path}")
        
        print("\n使用说明:")
        print("1. 根据环境选择对应的配置文件 (development.json, testing.json, production.json)")
        print("2. 复制 .env.template 为 .env 并填入实际配置值")
        print("3. 使用 validate_config.py 验证配置文件正确性")
        print("4. 参考各种指南文件进行配置优化")
        print("5. 使用 docker-compose.yml 进行容器化部署")


        return config_file


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python validate_config.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    is_valid = validate_config_file(config_file)
    
    if is_valid:
        print("\\n配置文件验证通过！")
        sys.exit(0)
    else:
        print("\\n配置文件验证失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        
        script_file = self.config_dir / "validate_config.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(validation_script)
        
        # 设置执行权限
        import stat
        os.chmod(script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✓ 创建配置验证脚本: {script_file}")

    def create_migration_scripts(self):
        """创建数据库迁移脚本"""
        
        # 创建初始化脚本
        init_script = '''-- 医保接口SDK数据库初始化脚本
-- 版本: 1.0.0
-- 创建时间: 2024-01-15

-- 创建数据库
CREATE DATABASE IF NOT EXISTS medical_insurance DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medical_insurance;

-- 创建接口配置表
CREATE TABLE IF NOT EXISTS medical_interface_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    api_code VARCHAR(10) NOT NULL UNIQUE COMMENT '接口编码',
    api_name VARCHAR(200) NOT NULL COMMENT '接口名称',
    api_description TEXT COMMENT '接口描述',
    business_category VARCHAR(50) NOT NULL COMMENT '业务分类',
    business_type VARCHAR(50) NOT NULL COMMENT '业务类型',
    
    required_params JSON NOT NULL DEFAULT '{}' COMMENT '必填参数配置',
    optional_params JSON DEFAULT '{}' COMMENT '可选参数配置',
    default_values JSON DEFAULT '{}' COMMENT '默认值配置',
    
    request_template JSON DEFAULT '{}' COMMENT '请求模板',
    param_mapping JSON DEFAULT '{}' COMMENT '参数映射规则',
    validation_rules JSON DEFAULT '{}' COMMENT '数据验证规则',
    
    response_mapping JSON DEFAULT '{}' COMMENT '响应字段映射',
    success_condition VARCHAR(200) DEFAULT 'infcode=0' COMMENT '成功条件',
    error_handling JSON DEFAULT '{}' COMMENT '错误处理配置',
    
    region_specific JSON DEFAULT '{}' COMMENT '地区特殊配置',
    province_overrides JSON DEFAULT '{}' COMMENT '省份级别覆盖配置',
    
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    requires_auth BOOLEAN DEFAULT TRUE COMMENT '是否需要认证',
    supports_batch BOOLEAN DEFAULT FALSE COMMENT '是否支持批量',
    max_retry_times INTEGER DEFAULT 3 COMMENT '最大重试次数',
    timeout_seconds INTEGER DEFAULT 30 COMMENT '超时时间（秒）',
    
    config_version VARCHAR(50) DEFAULT '1.0' COMMENT '配置版本',
    last_updated_by VARCHAR(100) COMMENT '最后更新人',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_api_code (api_code),
    INDEX idx_business_category (business_category),
    INDEX idx_business_type (business_type),
    INDEX idx_is_active (is_active),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口配置表';

-- 插入初始接口配置数据
INSERT INTO medical_interface_config (
    api_code, api_name, business_category, business_type,
    required_params, validation_rules, response_mapping, is_active
) VALUES 
(
    '1101', '人员信息获取', '查询类', '人员查询',
    '{"mdtrt_cert_type": {"display_name": "就诊凭证类型"}, "mdtrt_cert_no": {"display_name": "就诊凭证编号"}, "psn_cert_type": {"display_name": "人员证件类型"}, "certno": {"display_name": "证件号码"}, "psn_name": {"display_name": "人员姓名"}}',
    '{"certno": {"pattern": "^[0-9]{17}[0-9Xx]$", "pattern_error": "身份证号码格式不正确"}}',
    '{"person_name": "output.baseinfo.psn_name", "person_id": "output.baseinfo.psn_no", "gender": "output.baseinfo.gend"}',
    TRUE
),
(
    '2201', '门诊结算', '结算类', '门诊结算',
    '{"mdtrt_id": {"display_name": "就医登记号"}, "psn_no": {"display_name": "人员编号"}, "chrg_bchno": {"display_name": "收费批次号"}}',
    '{"mdtrt_id": {"max_length": 30}, "psn_no": {"max_length": 30}}',
    '{"settlement_id": "output.setlinfo.setl_id", "total_amount": "output.setlinfo.setl_totlnum"}',
    TRUE
);

COMMIT;
'''
        
        init_file = self.config_dir / "database_init.sql"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_script)
        
        print(f"✓ 创建数据库初始化脚本: {init_file}")

    def generate_all_configurations(self):
        """生成所有配置文件"""
        print("开始生成医保接口SDK配置文件...")
        print("=" * 60)
        
        try:
            # 创建环境配置
            self.create_environment_configs()
            
            # 创建接口配置模板
            self.create_interface_config_template()
            
            # 创建机构配置模板
            self.create_organization_config_template()
            
            # 创建安全配置指南
            self.create_security_config_guide()
            
            # 创建性能调优指南
            self.create_performance_tuning_guide()
            
            # 创建部署配置
            self.create_deployment_configs()
            
            # 创建配置验证脚本
            self.create_configuration_validation_script()
            
            # 创建数据库迁移脚本
            self.create_migration_scripts()
            
            print("\n" + "=" * 60)
            print("✓ 所有配置文件生成完成！")
            print(f"配置文件目录: {self.config_dir.absolute()}")
            
            # 显示生成的文件列表
            print("\n生成的文件列表:")
            for file_path in sorted(self.config_dir.glob("*")):
                if file_path.is_file():
                    print(f"  - {file_path.name}")
            
            print("\n使用说明:")
            print("1. 复制 .env.template 为 .env 并填入实际配置值")
            print("2. 根据环境选择对应的配置文件 (development.json, testing.json, production.json)")
            print("3. 使用 validate_config.py 验证配置文件正确性")
            print("4. 使用 database_init.sql 初始化数据库")
            print("5. 使用 docker-compose.yml 进行容器化部署")
            
        except Exception as e:
            print(f"✗ 配置文件生成失败: {str(e)}")


class ConfigurationBestPractices:
    """配置管理最佳实践指南"""
    
    @staticmethod
    def print_best_practices():
        """打印配置管理最佳实践"""
        print("\n医保接口SDK配置管理最佳实践")
        print("=" * 80)
        
        practices = [
            {
                "category": "环境管理",
                "practices": [
                    "为不同环境（开发、测试、生产）创建独立的配置文件",
                    "使用环境变量管理敏感信息，避免硬编码",
                    "生产环境配置文件不应包含默认密码或密钥",
                    "定期轮换密钥和证书",
                    "使用配置管理工具（如Ansible、Terraform）自动化配置部署"
                ]
            },
            {
                "category": "安全配置",
                "practices": [
                    "所有敏感数据必须加密存储",
                    "使用强密码策略，密码长度至少8位",
                    "启用SSL/TLS加密传输",
                    "配置IP白名单限制访问",
                    "启用审计日志记录所有配置变更",
                    "定期进行安全扫描和漏洞评估"
                ]
            },
            {
                "category": "性能优化",
                "practices": [
                    "合理配置数据库连接池大小",
                    "启用Redis缓存提升查询性能",
                    "设置合适的超时时间和重试策略",
                    "配置请求限流防止系统过载",
                    "定期监控和调优性能参数",
                    "使用连接池复用减少连接开销"
                ]
            },
            {
                "category": "监控告警",
                "practices": [
                    "配置系统健康检查和存活探针",
                    "设置关键指标的告警阈值",
                    "启用详细的日志记录和分析",
                    "配置性能监控和报表",
                    "建立故障恢复和应急响应机制",
                    "定期备份配置文件和数据"
                ]
            },
            {
                "category": "部署运维",
                "practices": [
                    "使用容器化部署提高一致性",
                    "实施蓝绿部署或滚动更新策略",
                    "配置自动化的健康检查",
                    "建立配置版本控制和回滚机制",
                    "定期进行灾难恢复演练",
                    "文档化所有配置变更和操作流程"
                ]
            }
        ]
        
        for category_info in practices:
            print(f"\n{category_info['category']}:")
            for idx, practice in enumerate(category_info['practices'], 1):
                print(f"  {idx}. {practice}")
        
        print("\n配置文件管理建议:")
        print("1. 使用版本控制系统管理配置文件")
        print("2. 配置文件应该有清晰的注释说明")
        print("3. 定期审查和更新配置文件")
        print("4. 建立配置变更的审批流程")
        print("5. 保持配置文件的简洁和可读性")
        
        print("\n故障排除指南:")
        print("1. 检查配置文件语法是否正确")
        print("2. 验证数据库连接参数")
        print("3. 确认网络连接和防火墙设置")
        print("4. 查看应用日志和错误信息")
        print("5. 使用配置验证工具检查配置")


def main():
    """主函数"""
    print("医保接口SDK配置管理最佳实践")
    print("=" * 80)
    
    # 创建配置管理器
    config_manager = ConfigurationManager()
    
    # 生成所有配置文件
    config_manager.generate_all_configurations()
    
    # 显示最佳实践
    ConfigurationBestPractices.print_best_practices()


if __name__ == "__main__":
    main()
   
 def create_monitoring_config(self):
        """创建监控配置"""
        
        # Prometheus配置
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "medical-insurance-sdk",
                    "static_configs": [
                        {
                            "targets": ["localhost:8080"]
                        }
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "30s"
                }
            ]
        }
        
        # Grafana仪表板配置
        grafana_dashboard = {
            "dashboard": {
                "title": "医保接口SDK监控",
                "panels": [
                    {
                        "title": "接口调用量",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(api_requests_total[5m])",
                                "legendFormat": "{{api_code}}"
                            }
                        ]
                    },
                    {
                        "title": "响应时间",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, api_request_duration_seconds_bucket)",
                                "legendFormat": "95th percentile"
                            }
                        ]
                    }
                ]
            }
        }
        
        # 保存监控配置
        monitoring_dir = self.config_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        with open(monitoring_dir / "prometheus.yml", 'w', encoding='utf-8') as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        with open(monitoring_dir / "grafana-dashboard.json", 'w', encoding='utf-8') as f:
            json.dump(grafana_dashboard, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建监控配置: {monitoring_dir}")

    def create_backup_strategy_guide(self):
        """创建备份策略指南"""
        
        backup_guide = {
            "database_backup": {
                "strategy": "定期全量备份 + 增量备份",
                "full_backup": {
                    "frequency": "每日凌晨2点",
                    "retention": "30天",
                    "command": "mysqldump --single-transaction medical_insurance > backup_$(date +%Y%m%d).sql"
                },
                "incremental_backup": {
                    "frequency": "每小时",
                    "retention": "7天",
                    "method": "binlog备份"
                }
            },
            "configuration_backup": {
                "strategy": "版本控制 + 定期归档",
                "version_control": {
                    "tool": "Git",
                    "frequency": "每次变更"
                }
            }
        }
        
        guide_file = self.config_dir / "backup_strategy_guide.json"
        with open(guide_file, 'w', encoding='utf-8') as f:
            json.dump(backup_guide, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建备份策略指南: {guide_file}")

    def run_extended_configuration_guide(self):
        """运行扩展配置指南"""
        print("\n" + "="*60)
        print("扩展配置管理功能")
        print("="*60)
        
        self.create_monitoring_config()
        self.create_backup_strategy_guide()
        
        print("\n✓ 扩展配置管理功能创建完成!")


# 扩展ConfigurationManager类
def extended_main():
    """扩展主函数"""
    config_manager = ConfigurationManager()
    
    # 运行原有功能
    config_manager.generate_all_configurations()
    
    # 运行扩展功能
    config_manager.run_extended_configuration_guide()
    
    # 显示最佳实践
    ConfigurationBestPractices.print_best_practices()
    
    print("\n🎉 医保接口SDK配置管理最佳实践指南完成!")
    print("\n📚 相关文档:")
    print("  • 配置文件模板已生成")
    print("  • 安全配置指南已创建")
    print("  • 性能调优指南已创建")
    print("  • 部署配置已准备")
    print("  • 监控配置已设置")
    print("  • 备份策略已制定")


# 为ConfigurationManager类添加扩展方法
ConfigurationManager.create_monitoring_config = create_monitoring_config
ConfigurationManager.create_backup_strategy_guide = create_backup_strategy_guide
ConfigurationManager.run_extended_configuration_guide = run_extended_configuration_guide