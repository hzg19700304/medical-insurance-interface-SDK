"""
配置管理器模块
提供接口配置和机构配置的动态加载、缓存和热更新功能
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .database import DatabaseManager, DatabaseConfig
from .cache_manager import RedisCacheManager, HybridCacheManager
from ..models.config import InterfaceConfig, OrganizationConfig
from ..exceptions import ConfigurationException


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = 300):  # 默认5分钟过期
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                cache_item = self._cache[key]
                if cache_item['expires_at'] > datetime.now():
                    return cache_item['value']
                else:
                    # 缓存过期，删除
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now()
            }
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理的数量"""
        with self._lock:
            expired_keys = []
            now = datetime.now()
            
            for key, cache_item in self._cache.items():
                if cache_item['expires_at'] <= now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            now = datetime.now()
            active_count = 0
            expired_count = 0
            
            for cache_item in self._cache.values():
                if cache_item['expires_at'] > now:
                    active_count += 1
                else:
                    expired_count += 1
            
            return {
                'total_items': len(self._cache),
                'active_items': active_count,
                'expired_items': expired_count,
                'default_ttl': self.default_ttl
            }


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, db_config: DatabaseConfig, cache_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager(db_config)
        
        # 初始化缓存管理器
        if cache_config and cache_config.get('type') == 'redis':
            # 使用Redis缓存
            redis_config = cache_config.get('redis', {})
            self.cache_manager = RedisCacheManager(**redis_config)
            self.logger.info("使用Redis缓存管理器")
        elif cache_config and cache_config.get('type') == 'hybrid':
            # 使用混合缓存
            hybrid_config = cache_config.get('hybrid', {})
            self.cache_manager = HybridCacheManager(**hybrid_config)
            self.logger.info("使用混合缓存管理器")
        else:
            # 使用内存缓存（默认）
            cache_ttl = cache_config.get('ttl', 300) if cache_config else 300
            self.cache_manager = CacheManager(cache_ttl)
            self.logger.info("使用内存缓存管理器")
        
        self._lock = threading.RLock()
        
        # 配置更新监控
        self._last_config_check = {}
        self._config_check_interval = 60  # 秒
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()
        
        # 启动配置监控线程
        self._start_config_monitor()
    
    def get_interface_config(self, api_code: str, region: str = None) -> InterfaceConfig:
        """获取接口配置"""
        cache_key = f"interface_config:{api_code}:{region or 'default'}"
        
        # 尝试从缓存获取
        cached_config = self.cache_manager.get(cache_key)
        if cached_config:
            return cached_config
        
        try:
            # 从数据库查询
            sql = """
                SELECT * FROM medical_interface_config 
                WHERE api_code = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            record = self.db_manager.execute_query_one(sql, (api_code,))
            if not record:
                raise ConfigurationException(f"接口配置不存在: {api_code}")
            
            # 创建配置对象
            config = InterfaceConfig.from_db_record(record)
            
            # 应用地区特殊配置
            if region and config.region_specific.get(region):
                region_config = config.region_specific[region]
                self._apply_region_config(config, region_config)
            
            # 缓存配置
            self.cache_manager.set(cache_key, config)
            
            self.logger.debug(f"加载接口配置: {api_code}, 地区: {region}")
            return config
            
        except Exception as e:
            self.logger.error(f"获取接口配置失败: {api_code}, 错误: {e}")
            raise ConfigurationException(f"获取接口配置失败: {e}")
    
    def get_organization_config(self, org_code: str) -> OrganizationConfig:
        """获取机构配置"""
        cache_key = f"org_config:{org_code}"
        
        # 尝试从缓存获取
        cached_config = self.cache_manager.get(cache_key)
        if cached_config:
            return cached_config
        
        try:
            # 从数据库查询
            sql = """
                SELECT * FROM medical_organization_config 
                WHERE org_code = %s AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            record = self.db_manager.execute_query_one(sql, (org_code,))
            if not record:
                raise ConfigurationException(f"机构配置不存在: {org_code}")
            
            # 创建配置对象
            config = OrganizationConfig.from_db_record(record)
            
            # 缓存配置
            self.cache_manager.set(cache_key, config)
            
            self.logger.debug(f"加载机构配置: {org_code}")
            return config
            
        except Exception as e:
            self.logger.error(f"获取机构配置失败: {org_code}, 错误: {e}")
            raise ConfigurationException(f"获取机构配置失败: {e}")
    
    def get_all_interface_configs(self, business_category: str = None) -> List[InterfaceConfig]:
        """获取所有接口配置"""
        try:
            if business_category:
                sql = """
                    SELECT * FROM medical_interface_config 
                    WHERE business_category = %s AND is_active = 1
                    ORDER BY api_code
                """
                records = self.db_manager.execute_query(sql, (business_category,))
            else:
                sql = """
                    SELECT * FROM medical_interface_config 
                    WHERE is_active = 1
                    ORDER BY api_code
                """
                records = self.db_manager.execute_query(sql)
            
            configs = []
            for record in records:
                config = InterfaceConfig.from_db_record(record)
                configs.append(config)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"获取所有接口配置失败: {e}")
            raise ConfigurationException(f"获取所有接口配置失败: {e}")
    
    def get_all_organization_configs(self, province_code: str = None) -> List[OrganizationConfig]:
        """获取所有机构配置"""
        try:
            if province_code:
                sql = """
                    SELECT * FROM medical_organization_config 
                    WHERE province_code = %s AND is_active = 1
                    ORDER BY org_code
                """
                records = self.db_manager.execute_query(sql, (province_code,))
            else:
                sql = """
                    SELECT * FROM medical_organization_config 
                    WHERE is_active = 1
                    ORDER BY org_code
                """
                records = self.db_manager.execute_query(sql)
            
            configs = []
            for record in records:
                config = OrganizationConfig.from_db_record(record)
                configs.append(config)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"获取所有机构配置失败: {e}")
            raise ConfigurationException(f"获取所有机构配置失败: {e}")
    
    def reload_config(self, config_type: str = None, config_key: str = None):
        """重新加载配置"""
        with self._lock:
            if config_type == "interface" and config_key:
                # 重新加载特定接口配置
                cache_pattern = f"interface_config:{config_key}:"
                self._clear_cache_by_pattern(cache_pattern)
                self.logger.info(f"重新加载接口配置: {config_key}")
                
            elif config_type == "organization" and config_key:
                # 重新加载特定机构配置
                cache_key = f"org_config:{config_key}"
                self.cache_manager.delete(cache_key)
                self.logger.info(f"重新加载机构配置: {config_key}")
                
            elif config_type == "interface":
                # 重新加载所有接口配置
                self._clear_cache_by_pattern("interface_config:")
                self.logger.info("重新加载所有接口配置")
                
            elif config_type == "organization":
                # 重新加载所有机构配置
                self._clear_cache_by_pattern("org_config:")
                self.logger.info("重新加载所有机构配置")
                
            else:
                # 重新加载所有配置
                self.cache_manager.clear()
                self.logger.info("重新加载所有配置")
    
    def _apply_region_config(self, config: InterfaceConfig, region_config: Dict[str, Any]):
        """应用地区特殊配置"""
        # 合并特殊参数
        if 'special_params' in region_config:
            config.default_values.update(region_config['special_params'])
        
        # 覆盖加密配置
        if 'encryption' in region_config:
            if 'encryption_config' not in config.region_specific:
                config.region_specific['encryption_config'] = {}
            config.region_specific['encryption_config'].update({
                'type': region_config['encryption']
            })
        
        # 覆盖超时配置
        if 'timeout' in region_config:
            config.timeout_seconds = region_config['timeout']
    
    def _clear_cache_by_pattern(self, pattern: str):
        """根据模式清理缓存"""
        if hasattr(self.cache_manager, 'delete_pattern'):
            # Redis或混合缓存管理器支持模式删除
            self.cache_manager.delete_pattern(pattern + '*')
        else:
            # 内存缓存管理器需要手动遍历
            keys_to_delete = []
            for key in self.cache_manager._cache.keys():
                if key.startswith(pattern):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.cache_manager.delete(key)
    
    def _start_config_monitor(self):
        """启动配置监控线程"""
        self._monitor_thread = threading.Thread(
            target=self._config_monitor_worker,
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("配置监控线程已启动")
    
    def _config_monitor_worker(self):
        """配置监控工作线程"""
        while not self._stop_monitor.wait(self._config_check_interval):
            try:
                self._check_config_updates()
                self.cache_manager.cleanup_expired()
            except Exception as e:
                self.logger.error(f"配置监控过程中发生错误: {e}")
    
    def _check_config_updates(self):
        """检查配置更新"""
        try:
            # 检查接口配置更新
            sql = """
                SELECT api_code, MAX(updated_at) as last_updated 
                FROM medical_interface_config 
                WHERE is_active = 1 
                GROUP BY api_code
            """
            
            interface_updates = self.db_manager.execute_query(sql)
            for update in interface_updates:
                api_code = update['api_code']
                last_updated = update['last_updated']
                
                if api_code in self._last_config_check:
                    if last_updated > self._last_config_check[api_code]:
                        # 配置有更新，清理相关缓存
                        self._clear_cache_by_pattern(f"interface_config:{api_code}:")
                        self.logger.info(f"检测到接口配置更新: {api_code}")
                
                self._last_config_check[api_code] = last_updated
            
            # 检查机构配置更新
            sql = """
                SELECT org_code, MAX(updated_at) as last_updated 
                FROM medical_organization_config 
                WHERE is_active = 1 
                GROUP BY org_code
            """
            
            org_updates = self.db_manager.execute_query(sql)
            for update in org_updates:
                org_code = update['org_code']
                last_updated = update['last_updated']
                
                cache_key = f"org_config_check:{org_code}"
                if cache_key in self._last_config_check:
                    if last_updated > self._last_config_check[cache_key]:
                        # 配置有更新，清理相关缓存
                        self.cache_manager.delete(f"org_config:{org_code}")
                        self.logger.info(f"检测到机构配置更新: {org_code}")
                
                self._last_config_check[cache_key] = last_updated
                
        except Exception as e:
            self.logger.error(f"检查配置更新失败: {e}")
    
    def get_config_stats(self) -> Dict[str, Any]:
        """获取配置管理器统计信息"""
        try:
            # 获取接口配置统计
            interface_sql = """
                SELECT 
                    COUNT(*) as total_interfaces,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_interfaces,
                    COUNT(DISTINCT business_category) as categories
                FROM medical_interface_config
            """
            interface_stats = self.db_manager.execute_query_one(interface_sql)
            
            # 获取机构配置统计
            org_sql = """
                SELECT 
                    COUNT(*) as total_organizations,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_organizations,
                    COUNT(DISTINCT province_code) as provinces
                FROM medical_organization_config
            """
            org_stats = self.db_manager.execute_query_one(org_sql)
            
            # 获取缓存统计
            cache_stats = self.cache_manager.get_stats()
            
            return {
                'interface_config': interface_stats or {},
                'organization_config': org_stats or {},
                'cache': cache_stats,
                'monitor_status': {
                    'running': self._monitor_thread and self._monitor_thread.is_alive(),
                    'check_interval': self._config_check_interval,
                    'last_check_count': len(self._last_config_check)
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取配置统计信息失败: {e}")
            return {'error': str(e)}
    
    def close(self):
        """关闭配置管理器"""
        # 停止监控线程
        if self._monitor_thread:
            self._stop_monitor.set()
            self._monitor_thread.join(timeout=5)
        
        # 关闭数据库连接
        if self.db_manager:
            self.db_manager.close()
        
        # 清理缓存
        self.cache_manager.clear()
        
        self.logger.info("配置管理器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()