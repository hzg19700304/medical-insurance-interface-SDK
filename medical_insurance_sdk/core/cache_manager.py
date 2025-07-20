"""
Redis缓存管理器模块
提供基于Redis的分布式缓存功能，支持配置缓存和失效机制
"""

import json
import logging
import threading
import time
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta

import redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from ..exceptions import CacheException


class RedisCacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 default_ttl: int = 300,
                 key_prefix: str = 'medical_sdk:',
                 max_connections: int = 50,
                 socket_timeout: int = 5,
                 socket_connect_timeout: int = 5,
                 retry_on_timeout: bool = True,
                 health_check_interval: int = 30):
        """
        初始化Redis缓存管理器
        
        Args:
            host: Redis服务器地址
            port: Redis服务器端口
            db: Redis数据库编号
            password: Redis密码
            default_ttl: 默认过期时间（秒）
            key_prefix: 键前缀
            max_connections: 最大连接数
            socket_timeout: Socket超时时间
            socket_connect_timeout: 连接超时时间
            retry_on_timeout: 超时时重试
            health_check_interval: 健康检查间隔
        """
        self.logger = logging.getLogger(__name__)
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.health_check_interval = health_check_interval
        
        # 创建连接池
        self.connection_pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            decode_responses=True
        )
        
        # 创建Redis客户端
        self.redis_client = redis.Redis(connection_pool=self.connection_pool)
        
        # 健康检查相关
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        self._is_healthy = True
        self._last_health_check = datetime.now()
        
        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        self._stats_lock = threading.Lock()
        
        # 启动健康检查
        self._start_health_check()
        
        # 测试连接
        self._test_connection()
    
    def _test_connection(self):
        """测试Redis连接"""
        try:
            self.redis_client.ping()
            self.logger.info("Redis连接测试成功")
        except Exception as e:
            self.logger.error(f"Redis连接测试失败: {e}")
            raise CacheException(f"Redis连接失败: {e}")
    
    def _make_key(self, key: str) -> str:
        """生成完整的缓存键"""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            raise CacheException(f"值序列化失败: {e}")
    
    def _deserialize_value(self, value: str) -> Any:
        """反序列化值"""
        try:
            return json.loads(value)
        except (TypeError, ValueError) as e:
            raise CacheException(f"值反序列化失败: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._is_healthy:
            self.logger.warning("Redis不健康，跳过缓存获取")
            return None
        
        try:
            full_key = self._make_key(key)
            value = self.redis_client.get(full_key)
            
            if value is not None:
                with self._stats_lock:
                    self._stats['hits'] += 1
                return self._deserialize_value(value)
            else:
                with self._stats_lock:
                    self._stats['misses'] += 1
                return None
                
        except RedisError as e:
            self.logger.error(f"Redis获取缓存失败: {key}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return None
        except Exception as e:
            self.logger.error(f"缓存获取异常: {key}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self._is_healthy:
            self.logger.warning("Redis不健康，跳过缓存设置")
            return False
        
        try:
            full_key = self._make_key(key)
            serialized_value = self._serialize_value(value)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = self.redis_client.setex(full_key, ttl, serialized_value)
            
            if result:
                with self._stats_lock:
                    self._stats['sets'] += 1
                return True
            else:
                return False
                
        except RedisError as e:
            self.logger.error(f"Redis设置缓存失败: {key}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return False
        except Exception as e:
            self.logger.error(f"缓存设置异常: {key}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self._is_healthy:
            self.logger.warning("Redis不健康，跳过缓存删除")
            return False
        
        try:
            full_key = self._make_key(key)
            result = self.redis_client.delete(full_key)
            
            if result > 0:
                with self._stats_lock:
                    self._stats['deletes'] += 1
                return True
            else:
                return False
                
        except RedisError as e:
            self.logger.error(f"Redis删除缓存失败: {key}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return False
        except Exception as e:
            self.logger.error(f"缓存删除异常: {key}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """根据模式删除缓存"""
        if not self._is_healthy:
            self.logger.warning("Redis不健康，跳过模式删除")
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                with self._stats_lock:
                    self._stats['deletes'] += deleted_count
                return deleted_count
            else:
                return 0
                
        except RedisError as e:
            self.logger.error(f"Redis模式删除失败: {pattern}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return 0
        except Exception as e:
            self.logger.error(f"模式删除异常: {pattern}, 错误: {e}")
            with self._stats_lock:
                self._stats['errors'] += 1
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._is_healthy:
            return False
        
        try:
            full_key = self._make_key(key)
            return bool(self.redis_client.exists(full_key))
        except RedisError as e:
            self.logger.error(f"Redis检查键存在失败: {key}, 错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"检查键存在异常: {key}, 错误: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置键的过期时间"""
        if not self._is_healthy:
            return False
        
        try:
            full_key = self._make_key(key)
            return bool(self.redis_client.expire(full_key, ttl))
        except RedisError as e:
            self.logger.error(f"Redis设置过期时间失败: {key}, 错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"设置过期时间异常: {key}, 错误: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间"""
        if not self._is_healthy:
            return -1
        
        try:
            full_key = self._make_key(key)
            return self.redis_client.ttl(full_key)
        except RedisError as e:
            self.logger.error(f"Redis获取TTL失败: {key}, 错误: {e}")
            return -1
        except Exception as e:
            self.logger.error(f"获取TTL异常: {key}, 错误: {e}")
            return -1
    
    def clear_all(self) -> bool:
        """清空所有缓存（仅清空带前缀的键）"""
        if not self._is_healthy:
            return False
        
        try:
            pattern = f"{self.key_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self.logger.info(f"清空缓存完成，删除了 {deleted_count} 个键")
                return True
            else:
                self.logger.info("没有找到需要清空的缓存键")
                return True
                
        except RedisError as e:
            self.logger.error(f"Redis清空缓存失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"清空缓存异常: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        if not self._is_healthy:
            return {'error': 'Redis不健康'}
        
        try:
            info = self.redis_client.info()
            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'uptime_in_seconds': info.get('uptime_in_seconds')
            }
        except RedisError as e:
            self.logger.error(f"获取Redis信息失败: {e}")
            return {'error': str(e)}
        except Exception as e:
            self.logger.error(f"获取Redis信息异常: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        # 计算命中率
        total_requests = stats['hits'] + stats['misses']
        hit_rate = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **stats,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'is_healthy': self._is_healthy,
            'last_health_check': self._last_health_check.isoformat(),
            'connection_pool_info': {
                'max_connections': self.connection_pool.max_connections,
                'created_connections': self.connection_pool.created_connections
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        with self._stats_lock:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0,
                'errors': 0
            }
    
    def _start_health_check(self):
        """启动健康检查线程"""
        self._health_check_thread = threading.Thread(
            target=self._health_check_worker,
            daemon=True
        )
        self._health_check_thread.start()
        self.logger.info("Redis健康检查线程已启动")
    
    def _health_check_worker(self):
        """健康检查工作线程"""
        while not self._stop_health_check.wait(self.health_check_interval):
            try:
                # 执行ping测试
                self.redis_client.ping()
                
                if not self._is_healthy:
                    self.logger.info("Redis连接已恢复")
                
                self._is_healthy = True
                self._last_health_check = datetime.now()
                
            except Exception as e:
                if self._is_healthy:
                    self.logger.error(f"Redis健康检查失败: {e}")
                
                self._is_healthy = False
                self._last_health_check = datetime.now()
    
    def is_healthy(self) -> bool:
        """检查Redis是否健康"""
        return self._is_healthy
    
    def close(self):
        """关闭缓存管理器"""
        # 停止健康检查线程
        if self._health_check_thread:
            self._stop_health_check.set()
            self._health_check_thread.join(timeout=5)
        
        # 关闭连接池
        if self.connection_pool:
            self.connection_pool.disconnect()
        
        self.logger.info("Redis缓存管理器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class HybridCacheManager:
    """混合缓存管理器 - 结合内存缓存和Redis缓存"""
    
    def __init__(self, 
                 redis_config: Dict[str, Any],
                 memory_cache_size: int = 1000,
                 memory_ttl: int = 60,
                 use_memory_fallback: bool = True):
        """
        初始化混合缓存管理器
        
        Args:
            redis_config: Redis配置
            memory_cache_size: 内存缓存大小
            memory_ttl: 内存缓存TTL
            use_memory_fallback: Redis不可用时是否使用内存缓存
        """
        self.logger = logging.getLogger(__name__)
        self.use_memory_fallback = use_memory_fallback
        
        # 初始化Redis缓存
        try:
            self.redis_cache = RedisCacheManager(**redis_config)
        except Exception as e:
            self.logger.error(f"Redis缓存初始化失败: {e}")
            self.redis_cache = None
        
        # 初始化内存缓存（作为L1缓存或fallback）
        from .config_manager import CacheManager
        self.memory_cache = CacheManager(memory_ttl)
        self.memory_cache_size = memory_cache_size
        
        self.logger.info("混合缓存管理器初始化完成")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值 - 先查内存缓存，再查Redis"""
        # 先尝试内存缓存
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # 再尝试Redis缓存
        if self.redis_cache and self.redis_cache.is_healthy():
            value = self.redis_cache.get(key)
            if value is not None:
                # 将Redis中的值缓存到内存中
                self.memory_cache.set(key, value, ttl=60)  # 内存缓存较短TTL
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值 - 同时设置内存缓存和Redis"""
        success = True
        
        # 设置内存缓存
        memory_ttl = min(ttl or 300, 300)  # 内存缓存最多5分钟
        self.memory_cache.set(key, value, ttl=memory_ttl)
        
        # 设置Redis缓存
        if self.redis_cache and self.redis_cache.is_healthy():
            redis_success = self.redis_cache.set(key, value, ttl)
            success = success and redis_success
        elif not self.use_memory_fallback:
            success = False
        
        return success
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        success = True
        
        # 删除内存缓存
        self.memory_cache.delete(key)
        
        # 删除Redis缓存
        if self.redis_cache and self.redis_cache.is_healthy():
            redis_success = self.redis_cache.delete(key)
            success = success and redis_success
        
        return success
    
    def delete_pattern(self, pattern: str) -> int:
        """根据模式删除缓存"""
        deleted_count = 0
        
        # 清理内存缓存中匹配的键
        keys_to_delete = []
        for key in self.memory_cache._cache.keys():
            if pattern in key:  # 简单的模式匹配
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            self.memory_cache.delete(key)
            deleted_count += 1
        
        # 清理Redis缓存
        if self.redis_cache and self.redis_cache.is_healthy():
            redis_deleted = self.redis_cache.delete_pattern(pattern)
            deleted_count += redis_deleted
        
        return deleted_count
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        # 清空内存缓存
        self.memory_cache.clear()
        
        # 清空Redis缓存
        if self.redis_cache and self.redis_cache.is_healthy():
            return self.redis_cache.clear_all()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_stats = self.memory_cache.get_stats()
        
        redis_stats = {}
        if self.redis_cache:
            redis_stats = self.redis_cache.get_stats()
        
        return {
            'memory_cache': memory_stats,
            'redis_cache': redis_stats,
            'hybrid_config': {
                'use_memory_fallback': self.use_memory_fallback,
                'memory_cache_size': self.memory_cache_size,
                'redis_available': self.redis_cache is not None and self.redis_cache.is_healthy()
            }
        }
    
    def close(self):
        """关闭缓存管理器"""
        if self.redis_cache:
            self.redis_cache.close()
        
        if self.memory_cache:
            self.memory_cache.clear()
        
        self.logger.info("混合缓存管理器已关闭")