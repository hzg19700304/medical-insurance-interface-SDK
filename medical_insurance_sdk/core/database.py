"""
数据库连接管理模块
提供MySQL连接池配置、连接健康检查和重连机制
"""

import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dataclasses import dataclass
import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
import threading

from .connection_pool_manager import (
    ConnectionPoolManager, MySQLPoolConfig, MySQLConnectionPool,
    get_global_pool_manager
)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""
    charset: str = "utf8mb4"
    
    # 连接池配置
    min_connections: int = 5
    max_connections: int = 20
    max_shared: int = 10
    max_usage: int = 1000
    
    # 连接超时配置
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30
    
    # 健康检查配置
    health_check_interval: int = 60  # 秒
    max_retry_times: int = 3
    retry_delay: int = 5  # 秒
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量创建配置"""
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        # 首先尝试从当前目录加载
        load_dotenv()
        # 然后尝试从medical_insurance_sdk目录加载
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_path)
        
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", os.getenv("DB_USERNAME", "root")),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_DATABASE", "medical_insurance"),
            charset=os.getenv("DB_CHARSET", "utf8mb4"),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
            max_shared=int(os.getenv("DB_MAX_SHARED", "10")),
            max_usage=int(os.getenv("DB_MAX_USAGE", "1000")),
            connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
            read_timeout=int(os.getenv("DB_READ_TIMEOUT", "30")),
            write_timeout=int(os.getenv("DB_WRITE_TIMEOUT", "30")),
            health_check_interval=int(os.getenv("DB_HEALTH_CHECK_INTERVAL", "60")),
            max_retry_times=int(os.getenv("DB_MAX_RETRY_TIMES", "3")),
            retry_delay=int(os.getenv("DB_RETRY_DELAY", "5"))
        )


class DatabaseManager:
    """数据库连接管理器 - 集成连接池管理器"""
    
    def __init__(self, config: DatabaseConfig, pool_name: str = "default", use_global_pool: bool = True):
        self.config = config
        self.pool_name = pool_name
        self.use_global_pool = use_global_pool
        self.logger = logging.getLogger(__name__)
        
        # 使用连接池管理器
        if use_global_pool:
            self.pool_manager = get_global_pool_manager()
        else:
            self.pool_manager = ConnectionPoolManager()
        
        # 创建MySQL连接池配置
        mysql_config = MySQLPoolConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset=config.charset,
            mincached=config.min_connections,
            maxcached=config.max_connections,
            maxconnections=config.max_connections,
            maxusage=config.max_usage,
            connect_timeout=config.connect_timeout,
            read_timeout=config.read_timeout,
            write_timeout=config.write_timeout
        )
        
        # 创建连接池
        self.mysql_pool = self.pool_manager.create_mysql_pool(pool_name, mysql_config)
        
        # 兼容性：保留原有的连接池引用
        self._pool = self.mysql_pool.pool
        
        # 初始化健康检查相关属性（兼容性）
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        
        # 启动健康检查（如果配置了）
        if config.health_check_interval > 0:
            self._start_health_check()
        
        self.logger.info(f"数据库管理器初始化完成，使用连接池: {pool_name}")
    
    def _initialize_pool(self):
        """初始化连接池"""
        try:
            self._pool = PooledDB(
                creator=pymysql,
                maxconnections=self.config.max_connections,
                mincached=self.config.min_connections,
                maxcached=self.config.max_connections,
                maxshared=self.config.max_shared,
                maxusage=self.config.max_usage,
                blocking=True,
                setsession=[],
                ping=1,  # 自动ping检查连接
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                cursorclass=DictCursor,
                connect_timeout=self.config.connect_timeout,
                read_timeout=self.config.read_timeout,
                write_timeout=self.config.write_timeout,
                autocommit=True
            )
            self.logger.info(f"数据库连接池初始化成功: {self.config.host}:{self.config.port}/{self.config.database}")
        except Exception as e:
            self.logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        connection = None
        try:
            connection = self.mysql_pool.get_connection()
            yield connection
        except Exception as e:
            self.logger.error(f"获取数据库连接失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行查询SQL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()
    
    def execute_query_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """执行查询SQL，返回单条记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchone()
            finally:
                cursor.close()
    
    def execute_update(self, sql: str, params: tuple = None) -> int:
        """执行更新SQL，返回影响行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                affected_rows = cursor.execute(sql, params)
                conn.commit()
                return affected_rows
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_batch_update(self, sql: str, params_list: List[tuple]) -> int:
        """批量执行更新SQL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                affected_rows = cursor.executemany(sql, params_list)
                conn.commit()
                return affected_rows
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                conn.begin()
                for operation in operations:
                    sql = operation.get('sql')
                    params = operation.get('params')
                    cursor.execute(sql, params)
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                self.logger.error(f"事务执行失败: {e}")
                raise
            finally:
                cursor.close()
    
    def check_connection_health(self) -> bool:
        """检查连接健康状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
        except Exception as e:
            self.logger.warning(f"数据库连接健康检查失败: {e}")
            return False
    
    def _start_health_check(self):
        """启动健康检查线程"""
        if self.config.health_check_interval > 0:
            self._health_check_thread = threading.Thread(
                target=self._health_check_worker,
                daemon=True
            )
            self._health_check_thread.start()
            self.logger.info("数据库健康检查线程已启动")
    
    def _health_check_worker(self):
        """健康检查工作线程"""
        while not self._stop_health_check.wait(self.config.health_check_interval):
            try:
                if not self.check_connection_health():
                    self.logger.warning("数据库连接健康检查失败，尝试重新初始化连接池")
                    self._reconnect_with_retry()
            except Exception as e:
                self.logger.error(f"健康检查过程中发生错误: {e}")
    
    def _reconnect_with_retry(self):
        """带重试的重连机制"""
        for attempt in range(self.config.max_retry_times):
            try:
                with self._lock:
                    # 关闭现有连接池
                    if self._pool:
                        self._pool.close()
                    
                    # 重新初始化连接池
                    self._initialize_pool()
                    
                    # 验证连接
                    if self.check_connection_health():
                        self.logger.info(f"数据库重连成功 (尝试 {attempt + 1}/{self.config.max_retry_times})")
                        return True
                        
            except Exception as e:
                self.logger.error(f"数据库重连失败 (尝试 {attempt + 1}/{self.config.max_retry_times}): {e}")
                
                if attempt < self.config.max_retry_times - 1:
                    time.sleep(self.config.retry_delay)
        
        self.logger.error("数据库重连失败，已达到最大重试次数")
        return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态信息"""
        try:
            # 获取连接池统计信息
            pool_stats = self.mysql_pool.get_stats()
            return {
                "status": "active",
                "pool_name": self.pool_name,
                "pool_stats": pool_stats.to_dict(),
                "health_check_enabled": self.config.health_check_interval > 0,
                "last_health_check": self.check_connection_health()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def close(self):
        """关闭数据库连接管理器"""
        # 停止健康检查线程
        if self._health_check_thread:
            self._stop_health_check.set()
            self._health_check_thread.join(timeout=5)
        
        # 如果不使用全局连接池管理器，则关闭本地管理器
        if not self.use_global_pool and self.pool_manager:
            self.pool_manager.close_all()
        
        self.logger.info("数据库连接管理器已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DatabaseConnectionError(Exception):
    """数据库连接错误"""
    pass


class DatabaseQueryError(Exception):
    """数据库查询错误"""
    pass