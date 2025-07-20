"""
缓存配置模块
提供Redis和混合缓存的配置管理
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RedisCacheConfig:
    """Redis缓存配置"""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    default_ttl: int = 300
    key_prefix: str = 'medical_sdk:'
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> 'RedisCacheConfig':
        """从环境变量创建配置"""
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            default_ttl=int(os.getenv('REDIS_DEFAULT_TTL', '300')),
            key_prefix=os.getenv('REDIS_KEY_PREFIX', 'medical_sdk:'),
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            socket_timeout=int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
            socket_connect_timeout=int(os.getenv('REDIS_CONNECT_TIMEOUT', '5')),
            retry_on_timeout=os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true',
            health_check_interval=int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'password': self.password,
            'default_ttl': self.default_ttl,
            'key_prefix': self.key_prefix,
            'max_connections': self.max_connections,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'retry_on_timeout': self.retry_on_timeout,
            'health_check_interval': self.health_check_interval
        }


@dataclass
class HybridCacheConfig:
    """混合缓存配置"""
    redis_config: RedisCacheConfig
    memory_cache_size: int = 1000
    memory_ttl: int = 60
    use_memory_fallback: bool = True
    
    @classmethod
    def from_env(cls) -> 'HybridCacheConfig':
        """从环境变量创建配置"""
        return cls(
            redis_config=RedisCacheConfig.from_env(),
            memory_cache_size=int(os.getenv('MEMORY_CACHE_SIZE', '1000')),
            memory_ttl=int(os.getenv('MEMORY_CACHE_TTL', '60')),
            use_memory_fallback=os.getenv('USE_MEMORY_FALLBACK', 'true').lower() == 'true'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'redis_config': self.redis_config.to_dict(),
            'memory_cache_size': self.memory_cache_size,
            'memory_ttl': self.memory_ttl,
            'use_memory_fallback': self.use_memory_fallback
        }


class CacheConfigFactory:
    """缓存配置工厂"""
    
    @staticmethod
    def create_cache_config(cache_type: str = 'memory') -> Dict[str, Any]:
        """
        创建缓存配置
        
        Args:
            cache_type: 缓存类型 ('memory', 'redis', 'hybrid')
        
        Returns:
            缓存配置字典
        """
        if cache_type == 'redis':
            redis_config = RedisCacheConfig.from_env()
            return {
                'type': 'redis',
                'redis': redis_config.to_dict()
            }
        elif cache_type == 'hybrid':
            hybrid_config = HybridCacheConfig.from_env()
            return {
                'type': 'hybrid',
                'hybrid': hybrid_config.to_dict()
            }
        else:
            # 默认内存缓存
            return {
                'type': 'memory',
                'ttl': int(os.getenv('MEMORY_CACHE_TTL', '300'))
            }
    
    @staticmethod
    def get_recommended_config(environment: str = 'development') -> Dict[str, Any]:
        """
        获取推荐的缓存配置
        
        Args:
            environment: 环境类型 ('development', 'testing', 'production')
        
        Returns:
            推荐的缓存配置
        """
        if environment == 'production':
            # 生产环境推荐使用Redis缓存
            return CacheConfigFactory.create_cache_config('redis')
        elif environment == 'testing':
            # 测试环境使用内存缓存
            return CacheConfigFactory.create_cache_config('memory')
        else:
            # 开发环境使用混合缓存
            return CacheConfigFactory.create_cache_config('hybrid')


# 预定义的缓存配置模板
CACHE_CONFIG_TEMPLATES = {
    'development': {
        'type': 'hybrid',
        'hybrid': {
            'redis_config': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': None,
                'default_ttl': 300,
                'key_prefix': 'medical_sdk_dev:',
                'max_connections': 10,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30
            },
            'memory_cache_size': 500,
            'memory_ttl': 60,
            'use_memory_fallback': True
        }
    },
    'testing': {
        'type': 'memory',
        'ttl': 60
    },
    'production': {
        'type': 'redis',
        'redis': {
            'host': 'redis-cluster.internal',
            'port': 6379,
            'db': 0,
            'password': None,  # 应该从环境变量获取
            'default_ttl': 600,
            'key_prefix': 'medical_sdk_prod:',
            'max_connections': 100,
            'socket_timeout': 10,
            'socket_connect_timeout': 10,
            'retry_on_timeout': True,
            'health_check_interval': 60
        }
    }
}


def get_cache_config(environment: str = None) -> Dict[str, Any]:
    """
    获取缓存配置
    
    Args:
        environment: 环境名称，如果为None则从环境变量获取
    
    Returns:
        缓存配置字典
    """
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    # 首先尝试从环境变量获取配置
    cache_type = os.getenv('CACHE_TYPE')
    if cache_type:
        return CacheConfigFactory.create_cache_config(cache_type)
    
    # 使用预定义模板
    if environment in CACHE_CONFIG_TEMPLATES:
        return CACHE_CONFIG_TEMPLATES[environment].copy()
    
    # 默认配置
    return CacheConfigFactory.get_recommended_config(environment)