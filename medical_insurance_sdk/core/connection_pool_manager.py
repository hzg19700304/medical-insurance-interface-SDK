"""
连接池管理器模块
提供MySQL和Redis连接池的优化配置、监控和管理功能
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

import pymysql
from dbutils.pooled_db import PooledDB
import redis

from ..exceptions import DatabaseException, CacheException


@dataclass
class ConnectionPoolStats:
    """连接池统计信息"""
    pool_name: str
    pool_type: str  # 'mysql' or 'redis'
    max_connections: int
    current_connections: int
    active_connections: int
    idle_connections: int
    total_requests: int
    failed_requests: int
    average_response_time: float
    last_check_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['last_check_time'] = self.last_check_time.isoformat()
        return result


@dataclass
class MySQLPoolConfig:
    """MySQL连接池配置"""
    host: str = 'localhost'
    port: int = 3306
    user: str = 'root'
    password: str = ''
    database: str = 'medical_insurance'
    charset: str = 'utf8mb4'
    
    # 连接池配置
    mincached: int = 5          # 最小缓存连接数
    maxcached: int = 20         # 最大缓存连接数
    maxshared: int = 0          # 最大共享连接数
    maxconnections: int = 50    # 最大连接数
    blocking: bool = True       # 连接池满时是否阻塞
    maxusage: int = 1000        # 单个连接最大使用次数
    setsession: List[str] = None  # 会话设置
    
    # 连接参数
    connect_timeout: int = 10   # 连接超时
    read_timeout: int = 30      # 读取超时
    write_timeout: int = 30     # 写入超时
    autocommit: bool = True     # 自动提交
    
    # 优化配置
    ping_interval: int = 7200   # 连接保活检查间隔（秒）
    reset_on_return: bool = True  # 连接归还时重置状态
    failures_before_close: int = 5  # 连接失败多少次后关闭
    
    # 性能优化配置
    use_unicode: bool = True    # 使用Unicode
    sql_mode: str = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
    init_command: str = None    # 初始化命令
    
    # 连接池监控配置
    enable_monitoring: bool = True  # 启用监控
    slow_query_threshold: float = 1.0  # 慢查询阈值（秒）
    connection_lifetime: int = 3600  # 连接最大生存时间（秒）
    
    def __post_init__(self):
        if self.setsession is None:
            self.setsession = [f'SET SESSION sql_mode="{self.sql_mode}"']
            if self.init_command:
                self.setsession.append(self.init_command)


@dataclass
class RedisPoolConfig:
    """Redis连接池配置"""
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    # 连接池配置
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, int] = None
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    # 优化配置
    connection_pool_class_kwargs: Dict[str, Any] = None
    retry_on_error: List[Exception] = None
    
    # 性能优化配置
    encoding: str = 'utf-8'
    encoding_errors: str = 'strict'
    decode_responses: bool = True
    
    # 连接池监控配置
    enable_monitoring: bool = True
    slow_command_threshold: float = 0.1  # 慢命令阈值（秒）
    connection_lifetime: int = 1800  # 连接最大生存时间（秒）
    
    # 高可用配置
    sentinel_service_name: Optional[str] = None
    sentinel_hosts: List[tuple] = None
    master_name: Optional[str] = None
    
    def __post_init__(self):
        if self.socket_keepalive_options is None:
            self.socket_keepalive_options = {
                'TCP_KEEPIDLE': 1,
                'TCP_KEEPINTVL': 3,
                'TCP_KEEPCNT': 5
            }
        
        if self.connection_pool_class_kwargs is None:
            self.connection_pool_class_kwargs = {}
        
        if self.retry_on_error is None:
            self.retry_on_error = []
        
        if self.sentinel_hosts is None:
            self.sentinel_hosts = []


class MySQLConnectionPool:
    """MySQL连接池管理器"""
    
    def __init__(self, config: MySQLPoolConfig, pool_name: str = "default"):
        self.config = config
        self.pool_name = pool_name
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'slow_queries': 0,
            'response_times': [],
            'slow_query_times': [],
            'connection_errors': 0,
            'last_check_time': datetime.now(),
            'peak_connections': 0,
            'total_connections_created': 0
        }
        self._stats_lock = threading.Lock()
        
        # 连接监控
        self._active_connections = 0
        self._connection_monitor_lock = threading.Lock()
        
        # 创建连接池
        self._create_pool()
        
        # 启动监控（如果启用）
        if config.enable_monitoring:
            self._start_connection_monitoring()
        
        self.logger.info(f"MySQL连接池 '{pool_name}' 初始化完成")
    
    def _create_pool(self):
        """创建MySQL连接池"""
        try:
            # 调试：打印配置信息
            print(f"[DEBUG] 创建连接池，配置密码长度: {len(self.config.password)}")
            print(f"[DEBUG] 配置密码前3位: {self.config.password[:3] if self.config.password else '(空)'}")
            
            # 构建连接参数
            connection_kwargs = {
                'host': self.config.host,
                'port': self.config.port,
                'user': self.config.user,
                'password': self.config.password,
                'database': self.config.database,
                'charset': self.config.charset,
                'connect_timeout': self.config.connect_timeout,
                'read_timeout': self.config.read_timeout,
                'write_timeout': self.config.write_timeout,
                'autocommit': self.config.autocommit,
                'cursorclass': pymysql.cursors.DictCursor,
                'use_unicode': self.config.use_unicode
            }
            
            # 调试：打印连接参数中的密码
            print(f"[DEBUG] 连接参数密码长度: {len(connection_kwargs['password'])}")
            print(f"[DEBUG] 连接参数密码前3位: {connection_kwargs['password'][:3] if connection_kwargs['password'] else '(空)'}")
            
            # 添加SSL配置（如果需要）
            if hasattr(self.config, 'ssl_config') and self.config.ssl_config:
                connection_kwargs.update(self.config.ssl_config)
            
            self.pool = PooledDB(
                creator=pymysql,
                mincached=self.config.mincached,
                maxcached=self.config.maxcached,
                maxshared=self.config.maxshared,
                maxconnections=self.config.maxconnections,
                blocking=self.config.blocking,
                maxusage=self.config.maxusage,
                setsession=self.config.setsession,
                ping=1,  # 使用固定值而不是配置值
                reset=self.config.reset_on_return,
                failures=(pymysql.Error, pymysql.OperationalError),
                **connection_kwargs
            )
            
            # 测试连接
            self._test_connection()
            
            with self._stats_lock:
                self._stats['total_connections_created'] += self.config.mincached
            
        except Exception as e:
            self.logger.error(f"创建MySQL连接池失败: {e}")
            raise DatabaseException(f"MySQL连接池创建失败: {e}")
    
    def _test_connection(self):
        """测试连接"""
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            self.logger.info(f"MySQL连接池 '{self.pool_name}' 连接测试成功")
        except Exception as e:
            self.logger.error(f"MySQL连接池 '{self.pool_name}' 连接测试失败: {e}")
            raise DatabaseException(f"MySQL连接测试失败: {e}")
    
    def get_connection(self):
        """获取连接"""
        start_time = time.time()
        try:
            conn = self.pool.connection()
            
            # 更新活跃连接数
            with self._connection_monitor_lock:
                self._active_connections += 1
                with self._stats_lock:
                    if self._active_connections > self._stats['peak_connections']:
                        self._stats['peak_connections'] = self._active_connections
            
            # 记录统计信息
            response_time = time.time() - start_time
            with self._stats_lock:
                self._stats['total_requests'] += 1
                self._stats['response_times'].append(response_time)
                
                # 检查是否为慢连接
                if response_time > self.config.slow_query_threshold:
                    self._stats['slow_queries'] += 1
                    self._stats['slow_query_times'].append(response_time)
                
                # 只保留最近1000次的响应时间
                if len(self._stats['response_times']) > 1000:
                    self._stats['response_times'] = self._stats['response_times'][-1000:]
                if len(self._stats['slow_query_times']) > 100:
                    self._stats['slow_query_times'] = self._stats['slow_query_times'][-100:]
            
            # 包装连接以监控归还
            return self._wrap_connection(conn)
            
        except Exception as e:
            with self._stats_lock:
                self._stats['failed_requests'] += 1
                self._stats['connection_errors'] += 1
            
            self.logger.error(f"获取MySQL连接失败: {e}")
            raise DatabaseException(f"获取MySQL连接失败: {e}")
    
    def _wrap_connection(self, conn):
        """包装连接以监控使用情况"""
        original_close = conn.close
        
        def monitored_close():
            with self._connection_monitor_lock:
                self._active_connections = max(0, self._active_connections - 1)
            return original_close()
        
        conn.close = monitored_close
        return conn
    
    def _start_connection_monitoring(self):
        """启动连接监控"""
        def monitor_worker():
            while True:
                try:
                    time.sleep(60)  # 每分钟检查一次
                    
                    with self._stats_lock:
                        stats = self._stats.copy()
                    
                    # 记录监控信息
                    if stats['total_requests'] > 0:
                        avg_response_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
                        failure_rate = stats['failed_requests'] / stats['total_requests']
                        
                        self.logger.debug(
                            f"MySQL连接池 '{self.pool_name}' 监控: "
                            f"总请求={stats['total_requests']}, "
                            f"失败率={failure_rate:.2%}, "
                            f"平均响应时间={avg_response_time:.3f}s, "
                            f"慢查询={stats['slow_queries']}, "
                            f"峰值连接={stats['peak_connections']}"
                        )
                        
                        # 检查异常情况
                        if failure_rate > 0.1:  # 失败率超过10%
                            self.logger.warning(f"MySQL连接池 '{self.pool_name}' 失败率过高: {failure_rate:.2%}")
                        
                        if avg_response_time > 2.0:  # 平均响应时间超过2秒
                            self.logger.warning(f"MySQL连接池 '{self.pool_name}' 响应时间过长: {avg_response_time:.3f}s")
                
                except Exception as e:
                    self.logger.error(f"MySQL连接池监控异常: {e}")
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        self.logger.info(f"MySQL连接池 '{self.pool_name}' 监控线程已启动")
    
    def get_stats(self) -> ConnectionPoolStats:
        """获取连接池统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        with self._connection_monitor_lock:
            current_active = self._active_connections
        
        # 计算平均响应时间
        avg_response_time = 0
        if stats['response_times']:
            avg_response_time = sum(stats['response_times']) / len(stats['response_times'])
        
        # 获取连接池状态
        max_connections = self.config.maxconnections
        current_connections = self.config.mincached + current_active
        active_connections = current_active
        idle_connections = max(0, current_connections - active_connections)
        
        return ConnectionPoolStats(
            pool_name=self.pool_name,
            pool_type='mysql',
            max_connections=max_connections,
            current_connections=min(current_connections, max_connections),
            active_connections=active_connections,
            idle_connections=idle_connections,
            total_requests=stats['total_requests'],
            failed_requests=stats['failed_requests'],
            average_response_time=avg_response_time,
            last_check_time=datetime.now()
        )
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        with self._connection_monitor_lock:
            current_active = self._active_connections
        
        # 计算各种统计指标
        avg_response_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
        avg_slow_query_time = sum(stats['slow_query_times']) / len(stats['slow_query_times']) if stats['slow_query_times'] else 0
        
        failure_rate = stats['failed_requests'] / stats['total_requests'] if stats['total_requests'] > 0 else 0
        slow_query_rate = stats['slow_queries'] / stats['total_requests'] if stats['total_requests'] > 0 else 0
        
        # 响应时间分布
        response_time_percentiles = {}
        if stats['response_times']:
            sorted_times = sorted(stats['response_times'])
            response_time_percentiles = {
                'p50': sorted_times[int(len(sorted_times) * 0.5)],
                'p90': sorted_times[int(len(sorted_times) * 0.9)],
                'p95': sorted_times[int(len(sorted_times) * 0.95)],
                'p99': sorted_times[int(len(sorted_times) * 0.99)]
            }
        
        return {
            'pool_name': self.pool_name,
            'pool_type': 'mysql',
            'config': {
                'max_connections': self.config.maxconnections,
                'min_cached': self.config.mincached,
                'max_cached': self.config.maxcached,
                'max_usage': self.config.maxusage
            },
            'current_status': {
                'active_connections': current_active,
                'peak_connections': stats['peak_connections'],
                'total_connections_created': stats['total_connections_created']
            },
            'performance_metrics': {
                'total_requests': stats['total_requests'],
                'failed_requests': stats['failed_requests'],
                'connection_errors': stats['connection_errors'],
                'slow_queries': stats['slow_queries'],
                'failure_rate': failure_rate,
                'slow_query_rate': slow_query_rate,
                'average_response_time': avg_response_time,
                'average_slow_query_time': avg_slow_query_time,
                'response_time_percentiles': response_time_percentiles
            },
            'last_check_time': datetime.now().isoformat()
        }
    
    def close(self):
        """关闭连接池"""
        if hasattr(self, 'pool'):
            # DBUtils的PooledDB没有显式的关闭方法
            # 连接会在程序结束时自动关闭
            self.logger.info(f"MySQL连接池 '{self.pool_name}' 已标记关闭")


class RedisConnectionPool:
    """Redis连接池管理器"""
    
    def __init__(self, config: RedisPoolConfig, pool_name: str = "default"):
        self.config = config
        self.pool_name = pool_name
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'slow_commands': 0,
            'response_times': [],
            'slow_command_times': [],
            'connection_errors': 0,
            'last_check_time': datetime.now(),
            'peak_connections': 0,
            'total_connections_created': 0,
            'command_stats': {}  # 命令统计
        }
        self._stats_lock = threading.Lock()
        
        # 连接监控
        self._active_connections = 0
        self._connection_monitor_lock = threading.Lock()
        
        # 创建连接池
        self._create_pool()
        
        # 健康检查
        self._is_healthy = True
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        
        if config.health_check_interval > 0:
            self._start_health_check()
        
        # 启动监控（如果启用）
        if config.enable_monitoring:
            self._start_connection_monitoring()
        
        self.logger.info(f"Redis连接池 '{pool_name}' 初始化完成")
    
    def _create_pool(self):
        """创建Redis连接池"""
        try:
            # 创建连接参数字典
            connection_kwargs = {
                'host': self.config.host,
                'port': self.config.port,
                'db': self.config.db,
                'socket_timeout': self.config.socket_timeout,
                'socket_connect_timeout': self.config.socket_connect_timeout,
                'socket_keepalive': self.config.socket_keepalive,
                'socket_keepalive_options': self.config.socket_keepalive_options,
                'retry_on_timeout': self.config.retry_on_timeout,
                'decode_responses': self.config.decode_responses,
                'encoding': self.config.encoding,
                'encoding_errors': self.config.encoding_errors
            }
            
            # 只有在密码不为空时才添加密码参数
            if self.config.password:
                connection_kwargs['password'] = self.config.password
            
            # 添加自定义连接池参数
            connection_kwargs.update(self.config.connection_pool_class_kwargs)
            
            # 支持Sentinel模式
            if self.config.sentinel_service_name and self.config.sentinel_hosts:
                from redis.sentinel import Sentinel
                sentinel = Sentinel(self.config.sentinel_hosts)
                self.redis_client = sentinel.master_for(
                    self.config.sentinel_service_name,
                    **connection_kwargs
                )
                self.pool = self.redis_client.connection_pool
            else:
                # 使用正确的Redis连接池类
                self.pool = redis.ConnectionPool(
                    max_connections=self.config.max_connections,
                    **connection_kwargs
                )
                
                # 创建Redis客户端用于测试
                self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # 测试连接
            self._test_connection()
            
            with self._stats_lock:
                self._stats['total_connections_created'] += 1
            
        except Exception as e:
            self.logger.error(f"创建Redis连接池失败: {e}")
            raise CacheException(f"Redis连接池创建失败: {e}")
    
    def _test_connection(self):
        """测试连接"""
        try:
            self.redis_client.ping()
            self.logger.info(f"Redis连接池 '{self.pool_name}' 连接测试成功")
        except Exception as e:
            self.logger.error(f"Redis连接池 '{self.pool_name}' 连接测试失败: {e}")
            raise CacheException(f"Redis连接测试失败: {e}")
    
    def get_connection(self):
        """获取Redis客户端"""
        start_time = time.time()
        try:
            # Redis连接池返回的是客户端实例
            client = redis.Redis(connection_pool=self.pool)
            
            # 更新活跃连接数
            with self._connection_monitor_lock:
                self._active_connections += 1
                with self._stats_lock:
                    if self._active_connections > self._stats['peak_connections']:
                        self._stats['peak_connections'] = self._active_connections
            
            # 记录统计信息
            response_time = time.time() - start_time
            with self._stats_lock:
                self._stats['total_requests'] += 1
                self._stats['response_times'].append(response_time)
                
                # 检查是否为慢命令
                if response_time > self.config.slow_command_threshold:
                    self._stats['slow_commands'] += 1
                    self._stats['slow_command_times'].append(response_time)
                
                # 只保留最近1000次的响应时间
                if len(self._stats['response_times']) > 1000:
                    self._stats['response_times'] = self._stats['response_times'][-1000:]
                if len(self._stats['slow_command_times']) > 100:
                    self._stats['slow_command_times'] = self._stats['slow_command_times'][-100:]
            
            # 包装客户端以监控命令执行
            return self._wrap_client(client)
            
        except Exception as e:
            with self._stats_lock:
                self._stats['failed_requests'] += 1
                self._stats['connection_errors'] += 1
            
            self.logger.error(f"获取Redis连接失败: {e}")
            raise CacheException(f"获取Redis连接失败: {e}")
    
    def _wrap_client(self, client):
        """包装Redis客户端以监控命令执行"""
        original_execute_command = client.execute_command
        
        def monitored_execute_command(command_name, *args, **kwargs):
            start_time = time.time()
            try:
                result = original_execute_command(command_name, *args, **kwargs)
                
                # 记录命令统计
                execution_time = time.time() - start_time
                with self._stats_lock:
                    if command_name not in self._stats['command_stats']:
                        self._stats['command_stats'][command_name] = {
                            'count': 0,
                            'total_time': 0,
                            'slow_count': 0
                        }
                    
                    cmd_stats = self._stats['command_stats'][command_name]
                    cmd_stats['count'] += 1
                    cmd_stats['total_time'] += execution_time
                    
                    if execution_time > self.config.slow_command_threshold:
                        cmd_stats['slow_count'] += 1
                
                return result
                
            except Exception as e:
                with self._stats_lock:
                    self._stats['connection_errors'] += 1
                raise
        
        client.execute_command = monitored_execute_command
        return client
    
    def _start_connection_monitoring(self):
        """启动连接监控"""
        def monitor_worker():
            while True:
                try:
                    time.sleep(60)  # 每分钟检查一次
                    
                    with self._stats_lock:
                        stats = self._stats.copy()
                    
                    # 记录监控信息
                    if stats['total_requests'] > 0:
                        avg_response_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
                        failure_rate = stats['failed_requests'] / stats['total_requests']
                        
                        self.logger.debug(
                            f"Redis连接池 '{self.pool_name}' 监控: "
                            f"总请求={stats['total_requests']}, "
                            f"失败率={failure_rate:.2%}, "
                            f"平均响应时间={avg_response_time:.3f}s, "
                            f"慢命令={stats['slow_commands']}, "
                            f"峰值连接={stats['peak_connections']}"
                        )
                        
                        # 检查异常情况
                        if failure_rate > 0.05:  # 失败率超过5%
                            self.logger.warning(f"Redis连接池 '{self.pool_name}' 失败率过高: {failure_rate:.2%}")
                        
                        if avg_response_time > 0.5:  # 平均响应时间超过0.5秒
                            self.logger.warning(f"Redis连接池 '{self.pool_name}' 响应时间过长: {avg_response_time:.3f}s")
                
                except Exception as e:
                    self.logger.error(f"Redis连接池监控异常: {e}")
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        self.logger.info(f"Redis连接池 '{self.pool_name}' 监控线程已启动")
    
    def _start_health_check(self):
        """启动健康检查线程"""
        self._health_check_thread = threading.Thread(
            target=self._health_check_worker,
            daemon=True
        )
        self._health_check_thread.start()
        self.logger.info(f"Redis连接池 '{self.pool_name}' 健康检查线程已启动")
    
    def _health_check_worker(self):
        """健康检查工作线程"""
        while not self._stop_health_check.wait(self.config.health_check_interval):
            try:
                self.redis_client.ping()
                if not self._is_healthy:
                    self.logger.info(f"Redis连接池 '{self.pool_name}' 连接已恢复")
                self._is_healthy = True
            except Exception as e:
                if self._is_healthy:
                    self.logger.error(f"Redis连接池 '{self.pool_name}' 健康检查失败: {e}")
                self._is_healthy = False
    
    def is_healthy(self) -> bool:
        """检查连接池是否健康"""
        return self._is_healthy
    
    def get_stats(self) -> ConnectionPoolStats:
        """获取连接池统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        # 计算平均响应时间
        avg_response_time = 0
        if stats['response_times']:
            avg_response_time = sum(stats['response_times']) / len(stats['response_times'])
        
        # 获取连接池状态
        current_connections = self.pool.created_connections
        max_connections = self.pool.max_connections
        active_connections = min(current_connections, max_connections)
        idle_connections = max(0, current_connections - active_connections)
        
        return ConnectionPoolStats(
            pool_name=self.pool_name,
            pool_type='redis',
            max_connections=max_connections,
            current_connections=current_connections,
            active_connections=active_connections,
            idle_connections=idle_connections,
            total_requests=stats['total_requests'],
            failed_requests=stats['failed_requests'],
            average_response_time=avg_response_time,
            last_check_time=datetime.now()
        )
    
    def close(self):
        """关闭连接池"""
        # 停止健康检查线程
        if self._health_check_thread:
            self._stop_health_check.set()
            self._health_check_thread.join(timeout=5)
        
        # 关闭连接池
        if hasattr(self, 'pool'):
            self.pool.disconnect()
        
        self.logger.info(f"Redis连接池 '{self.pool_name}' 已关闭")


class ConnectionPoolManager:
    """连接池管理器 - 统一管理MySQL和Redis连接池"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mysql_pools: Dict[str, MySQLConnectionPool] = {}
        self.redis_pools: Dict[str, RedisConnectionPool] = {}
        self._lock = threading.RLock()
        
        # 监控线程
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()
        self._monitor_interval = 60  # 监控间隔（秒）
        
        # 性能优化配置
        self._optimization_config = {
            'auto_scaling_enabled': True,  # 自动扩缩容
            'connection_rebalancing': True,  # 连接重平衡
            'performance_tuning': True,  # 性能调优
            'alert_thresholds': {
                'mysql_failure_rate': 0.1,  # MySQL失败率阈值
                'redis_failure_rate': 0.05,  # Redis失败率阈值
                'response_time_threshold': 2.0,  # 响应时间阈值
                'connection_usage_threshold': 0.8  # 连接使用率阈值
            }
        }
        
        # 性能统计
        self._performance_history = []
        self._performance_lock = threading.Lock()
        
        self.logger.info("连接池管理器初始化完成")
    
    def create_mysql_pool(self, pool_name: str, config: MySQLPoolConfig) -> MySQLConnectionPool:
        """创建MySQL连接池"""
        with self._lock:
            if pool_name in self.mysql_pools:
                self.logger.warning(f"MySQL连接池 '{pool_name}' 已存在，将被替换")
                self.mysql_pools[pool_name].close()
            
            pool = MySQLConnectionPool(config, pool_name)
            self.mysql_pools[pool_name] = pool
            
            self.logger.info(f"创建MySQL连接池 '{pool_name}' 成功")
            return pool
    
    def create_redis_pool(self, pool_name: str, config: RedisPoolConfig) -> RedisConnectionPool:
        """创建Redis连接池"""
        with self._lock:
            if pool_name in self.redis_pools:
                self.logger.warning(f"Redis连接池 '{pool_name}' 已存在，将被替换")
                self.redis_pools[pool_name].close()
            
            pool = RedisConnectionPool(config, pool_name)
            self.redis_pools[pool_name] = pool
            
            self.logger.info(f"创建Redis连接池 '{pool_name}' 成功")
            return pool
    
    def get_mysql_pool(self, pool_name: str = "default") -> Optional[MySQLConnectionPool]:
        """获取MySQL连接池"""
        return self.mysql_pools.get(pool_name)
    
    def get_redis_pool(self, pool_name: str = "default") -> Optional[RedisConnectionPool]:
        """获取Redis连接池"""
        return self.redis_pools.get(pool_name)
    
    def get_mysql_connection(self, pool_name: str = "default"):
        """获取MySQL连接"""
        pool = self.get_mysql_pool(pool_name)
        if not pool:
            raise DatabaseException(f"MySQL连接池 '{pool_name}' 不存在")
        return pool.get_connection()
    
    def get_redis_connection(self, pool_name: str = "default"):
        """获取Redis连接"""
        pool = self.get_redis_pool(pool_name)
        if not pool:
            raise CacheException(f"Redis连接池 '{pool_name}' 不存在")
        return pool.get_connection()
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有连接池的统计信息"""
        stats = {
            'mysql_pools': {},
            'redis_pools': {},
            'summary': {
                'total_mysql_pools': len(self.mysql_pools),
                'total_redis_pools': len(self.redis_pools),
                'healthy_redis_pools': 0,
                'total_connections': 0,
                'total_requests': 0,
                'total_failed_requests': 0
            }
        }
        
        # MySQL连接池统计
        for name, pool in self.mysql_pools.items():
            pool_stats = pool.get_stats()
            stats['mysql_pools'][name] = pool_stats.to_dict()
            stats['summary']['total_connections'] += pool_stats.current_connections
            stats['summary']['total_requests'] += pool_stats.total_requests
            stats['summary']['total_failed_requests'] += pool_stats.failed_requests
        
        # Redis连接池统计
        for name, pool in self.redis_pools.items():
            pool_stats = pool.get_stats()
            stats['redis_pools'][name] = pool_stats.to_dict()
            stats['summary']['total_connections'] += pool_stats.current_connections
            stats['summary']['total_requests'] += pool_stats.total_requests
            stats['summary']['total_failed_requests'] += pool_stats.failed_requests
            
            if pool.is_healthy():
                stats['summary']['healthy_redis_pools'] += 1
        
        return stats
    
    def start_monitoring(self):
        """启动连接池监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self.logger.warning("连接池监控线程已在运行")
            return
        
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker,
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("连接池监控线程已启动")
    
    def stop_monitoring(self):
        """停止连接池监控"""
        if self._monitor_thread:
            self._stop_monitor.set()
            self._monitor_thread.join(timeout=5)
            self.logger.info("连接池监控线程已停止")
    
    def _monitor_worker(self):
        """监控工作线程"""
        while not self._stop_monitor.wait(self._monitor_interval):
            try:
                stats = self.get_all_stats()
                
                # 记录关键指标
                summary = stats['summary']
                self.logger.info(
                    f"连接池监控 - "
                    f"MySQL池: {summary['total_mysql_pools']}, "
                    f"Redis池: {summary['total_redis_pools']} (健康: {summary['healthy_redis_pools']}), "
                    f"总连接: {summary['total_connections']}, "
                    f"总请求: {summary['total_requests']}, "
                    f"失败请求: {summary['total_failed_requests']}"
                )
                
                # 检查异常情况
                self._check_pool_health(stats)
                
            except Exception as e:
                self.logger.error(f"连接池监控异常: {e}")
    
    def _check_pool_health(self, stats: Dict[str, Any]):
        """检查连接池健康状况"""
        # 检查失败率
        total_requests = stats['summary']['total_requests']
        total_failed = stats['summary']['total_failed_requests']
        
        if total_requests > 0:
            failure_rate = total_failed / total_requests
            if failure_rate > self._optimization_config['alert_thresholds']['mysql_failure_rate']:
                self.logger.warning(f"连接池失败率过高: {failure_rate:.2%}")
                self._trigger_optimization('high_failure_rate', failure_rate)
        
        # 检查Redis连接池健康状况
        unhealthy_redis_pools = []
        for name, pool in self.redis_pools.items():
            if not pool.is_healthy():
                unhealthy_redis_pools.append(name)
        
        if unhealthy_redis_pools:
            self.logger.warning(f"不健康的Redis连接池: {', '.join(unhealthy_redis_pools)}")
        
        # 检查连接使用率
        self._check_connection_usage(stats)
        
        # 检查响应时间
        self._check_response_times(stats)
    
    def _check_connection_usage(self, stats: Dict[str, Any]):
        """检查连接使用率"""
        threshold = self._optimization_config['alert_thresholds']['connection_usage_threshold']
        
        # 检查MySQL连接池使用率
        for pool_name, pool_stats in stats['mysql_pools'].items():
            if pool_stats['max_connections'] > 0:
                usage_rate = pool_stats['active_connections'] / pool_stats['max_connections']
                if usage_rate > threshold:
                    self.logger.warning(f"MySQL连接池 '{pool_name}' 使用率过高: {usage_rate:.2%}")
                    if self._optimization_config['auto_scaling_enabled']:
                        self._suggest_pool_scaling(pool_name, 'mysql', usage_rate)
        
        # 检查Redis连接池使用率
        for pool_name, pool_stats in stats['redis_pools'].items():
            if pool_stats['max_connections'] > 0:
                usage_rate = pool_stats['active_connections'] / pool_stats['max_connections']
                if usage_rate > threshold:
                    self.logger.warning(f"Redis连接池 '{pool_name}' 使用率过高: {usage_rate:.2%}")
                    if self._optimization_config['auto_scaling_enabled']:
                        self._suggest_pool_scaling(pool_name, 'redis', usage_rate)
    
    def _check_response_times(self, stats: Dict[str, Any]):
        """检查响应时间"""
        threshold = self._optimization_config['alert_thresholds']['response_time_threshold']
        
        # 检查MySQL响应时间
        for pool_name, pool_stats in stats['mysql_pools'].items():
            if pool_stats['average_response_time'] > threshold:
                self.logger.warning(
                    f"MySQL连接池 '{pool_name}' 响应时间过长: {pool_stats['average_response_time']:.3f}s"
                )
        
        # 检查Redis响应时间
        for pool_name, pool_stats in stats['redis_pools'].items():
            if pool_stats['average_response_time'] > threshold / 10:  # Redis阈值更低
                self.logger.warning(
                    f"Redis连接池 '{pool_name}' 响应时间过长: {pool_stats['average_response_time']:.3f}s"
                )
    
    def _suggest_pool_scaling(self, pool_name: str, pool_type: str, usage_rate: float):
        """建议连接池扩容"""
        self.logger.info(
            f"建议扩容 {pool_type} 连接池 '{pool_name}': "
            f"当前使用率 {usage_rate:.2%}, 建议增加 20% 连接数"
        )
    
    def _trigger_optimization(self, issue_type: str, metric_value: float):
        """触发优化措施"""
        if self._optimization_config['performance_tuning']:
            self.logger.info(f"触发性能优化: {issue_type}, 指标值: {metric_value}")
            
            # 记录性能问题
            with self._performance_lock:
                self._performance_history.append({
                    'timestamp': datetime.now(),
                    'issue_type': issue_type,
                    'metric_value': metric_value
                })
                
                # 只保留最近100条记录
                if len(self._performance_history) > 100:
                    self._performance_history = self._performance_history[-100:]
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = []
        stats = self.get_all_stats()
        
        # 分析MySQL连接池
        for pool_name, pool_stats in stats['mysql_pools'].items():
            pool = self.mysql_pools.get(pool_name)
            if pool:
                detailed_stats = pool.get_detailed_stats()
                suggestions.extend(self._analyze_mysql_pool(pool_name, detailed_stats))
        
        # 分析Redis连接池
        for pool_name, pool_stats in stats['redis_pools'].items():
            suggestions.extend(self._analyze_redis_pool(pool_name, pool_stats))
        
        return suggestions
    
    def _analyze_mysql_pool(self, pool_name: str, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析MySQL连接池并提供优化建议"""
        suggestions = []
        
        # 检查失败率
        if stats['performance_metrics']['failure_rate'] > 0.05:
            suggestions.append({
                'type': 'mysql_high_failure_rate',
                'pool_name': pool_name,
                'severity': 'high',
                'description': f"MySQL连接池失败率过高: {stats['performance_metrics']['failure_rate']:.2%}",
                'suggestion': "检查数据库连接配置，增加连接超时时间，或检查数据库服务器状态"
            })
        
        # 检查慢查询率
        if stats['performance_metrics']['slow_query_rate'] > 0.1:
            suggestions.append({
                'type': 'mysql_slow_queries',
                'pool_name': pool_name,
                'severity': 'medium',
                'description': f"慢查询率过高: {stats['performance_metrics']['slow_query_rate']:.2%}",
                'suggestion': "优化SQL查询，添加索引，或调整慢查询阈值"
            })
        
        # 检查连接使用率
        max_conn = stats['config']['max_connections']
        peak_conn = stats['current_status']['peak_connections']
        if max_conn > 0 and peak_conn / max_conn > 0.8:
            suggestions.append({
                'type': 'mysql_high_connection_usage',
                'pool_name': pool_name,
                'severity': 'medium',
                'description': f"连接使用率过高: {peak_conn}/{max_conn} ({peak_conn/max_conn:.2%})",
                'suggestion': "考虑增加最大连接数，或优化连接使用模式"
            })
        
        return suggestions
    
    def _analyze_redis_pool(self, pool_name: str, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析Redis连接池并提供优化建议"""
        suggestions = []
        
        # 检查失败率
        if stats['total_requests'] > 0:
            failure_rate = stats['failed_requests'] / stats['total_requests']
            if failure_rate > 0.02:  # Redis失败率阈值更低
                suggestions.append({
                    'type': 'redis_high_failure_rate',
                    'pool_name': pool_name,
                    'severity': 'high',
                    'description': f"Redis连接池失败率过高: {failure_rate:.2%}",
                    'suggestion': "检查Redis服务器状态，调整连接超时配置，或启用重试机制"
                })
        
        # 检查连接使用率
        if stats['max_connections'] > 0:
            usage_rate = stats['active_connections'] / stats['max_connections']
            if usage_rate > 0.8:
                suggestions.append({
                    'type': 'redis_high_connection_usage',
                    'pool_name': pool_name,
                    'severity': 'medium',
                    'description': f"Redis连接使用率过高: {usage_rate:.2%}",
                    'suggestion': "考虑增加最大连接数，或使用连接复用"
                })
        
        return suggestions
    
    def apply_optimization(self, optimization_type: str, pool_name: str, **kwargs):
        """应用优化措施"""
        try:
            if optimization_type == 'scale_mysql_pool':
                self._scale_mysql_pool(pool_name, **kwargs)
            elif optimization_type == 'scale_redis_pool':
                self._scale_redis_pool(pool_name, **kwargs)
            elif optimization_type == 'tune_mysql_config':
                self._tune_mysql_config(pool_name, **kwargs)
            elif optimization_type == 'tune_redis_config':
                self._tune_redis_config(pool_name, **kwargs)
            else:
                self.logger.warning(f"未知的优化类型: {optimization_type}")
                
        except Exception as e:
            self.logger.error(f"应用优化措施失败: {e}")
    
    def _scale_mysql_pool(self, pool_name: str, scale_factor: float = 1.2):
        """扩容MySQL连接池"""
        pool = self.mysql_pools.get(pool_name)
        if pool:
            current_max = pool.config.maxconnections
            new_max = int(current_max * scale_factor)
            self.logger.info(f"扩容MySQL连接池 '{pool_name}': {current_max} -> {new_max}")
            # 注意：实际扩容需要重新创建连接池，这里只是记录
    
    def _scale_redis_pool(self, pool_name: str, scale_factor: float = 1.2):
        """扩容Redis连接池"""
        pool = self.redis_pools.get(pool_name)
        if pool:
            current_max = pool.config.max_connections
            new_max = int(current_max * scale_factor)
            self.logger.info(f"扩容Redis连接池 '{pool_name}': {current_max} -> {new_max}")
            # 注意：实际扩容需要重新创建连接池，这里只是记录
    
    def _tune_mysql_config(self, pool_name: str, **config_changes):
        """调优MySQL连接池配置"""
        self.logger.info(f"调优MySQL连接池 '{pool_name}' 配置: {config_changes}")
    
    def _tune_redis_config(self, pool_name: str, **config_changes):
        """调优Redis连接池配置"""
        self.logger.info(f"调优Redis连接池 '{pool_name}' 配置: {config_changes}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        stats = self.get_all_stats()
        suggestions = self.get_optimization_suggestions()
        
        with self._performance_lock:
            history = self._performance_history.copy()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': stats['summary'],
            'pool_details': {
                'mysql_pools': len(stats['mysql_pools']),
                'redis_pools': len(stats['redis_pools']),
                'healthy_redis_pools': stats['summary']['healthy_redis_pools']
            },
            'performance_issues': len(history),
            'optimization_suggestions': len(suggestions),
            'suggestions': suggestions,
            'recent_issues': history[-10:] if history else [],
            'optimization_config': self._optimization_config
        }
    
    def close_all(self):
        """关闭所有连接池"""
        # 停止监控
        self.stop_monitoring()
        
        # 关闭所有MySQL连接池
        for name, pool in self.mysql_pools.items():
            try:
                pool.close()
                self.logger.info(f"MySQL连接池 '{name}' 已关闭")
            except Exception as e:
                self.logger.error(f"关闭MySQL连接池 '{name}' 失败: {e}")
        
        # 关闭所有Redis连接池
        for name, pool in self.redis_pools.items():
            try:
                pool.close()
                self.logger.info(f"Redis连接池 '{name}' 已关闭")
            except Exception as e:
                self.logger.error(f"关闭Redis连接池 '{name}' 失败: {e}")
        
        # 清空连接池字典
        self.mysql_pools.clear()
        self.redis_pools.clear()
        
        self.logger.info("所有连接池已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


# 全局连接池管理器实例
_global_pool_manager: Optional[ConnectionPoolManager] = None
_global_pool_manager_lock = threading.Lock()


def get_global_pool_manager() -> ConnectionPoolManager:
    """获取全局连接池管理器实例"""
    global _global_pool_manager
    
    if _global_pool_manager is None:
        with _global_pool_manager_lock:
            if _global_pool_manager is None:
                _global_pool_manager = ConnectionPoolManager()
    
    return _global_pool_manager


def close_global_pool_manager():
    """关闭全局连接池管理器"""
    global _global_pool_manager
    
    if _global_pool_manager is not None:
        with _global_pool_manager_lock:
            if _global_pool_manager is not None:
                _global_pool_manager.close_all()
                _global_pool_manager = None