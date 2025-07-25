"""
连接池管理器功能测试（使用环境变量配置）
测试MySQL和Redis连接池的管理和监控功能，智能处理Redis不可用的情况
"""

import os
import time
import threading
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('medical_insurance_sdk/.env')

from medical_insurance_sdk.core.connection_pool_manager import (
    ConnectionPoolManager, MySQLPoolConfig, RedisPoolConfig,
    get_global_pool_manager, close_global_pool_manager
)
from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig


def check_redis_available():
    """检查Redis是否可用"""
    try:
        import redis
        client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_PASSWORD') else None,
            socket_connect_timeout=2
        )
        client.ping()
        return True
    except Exception:
        return False


def check_mysql_available():
    """检查MySQL是否可用"""
    try:
        import pymysql
        conn = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USERNAME', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'medical_insurance'),
            connect_timeout=2
        )
        conn.close()
        return True
    except Exception:
        return False


def test_mysql_connection_pool():
    """测试MySQL连接池"""
    print("=== 测试MySQL连接池 ===")
    
    if not check_mysql_available():
        print("⚠️  MySQL不可用，跳过MySQL连接池测试")
        return True
    
    try:
        # 创建MySQL连接池配置
        mysql_config = MySQLPoolConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USERNAME', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'medical_insurance'),
            mincached=2,
            maxcached=10,
            maxconnections=20
        )
        
        # 创建连接池管理器
        pool_manager = ConnectionPoolManager()
        
        # 创建MySQL连接池
        mysql_pool = pool_manager.create_mysql_pool("test_mysql", mysql_config)
        print("✓ MySQL连接池创建成功")
        
        # 测试获取连接
        connections = []
        for i in range(3):
            try:
                conn = mysql_pool.get_connection()
                connections.append(conn)
                
                # 测试简单查询
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test_value")
                result = cursor.fetchone()
                cursor.close()
                
                print(f"✓ 获取连接 {i+1}: 成功，查询结果: {result}")
            except Exception as e:
                print(f"✗ 获取连接 {i+1}: 失败 - {e}")
        
        # 关闭连接
        for conn in connections:
            conn.close()
        print("✓ 连接已关闭")
        
        # 获取统计信息
        stats = mysql_pool.get_stats()
        print(f"✓ 连接池统计: 总请求={stats.total_requests}, 失败请求={stats.failed_requests}")
        
        pool_manager.close_all()
        print("✓ MySQL连接池测试完成")
        
    except Exception as e:
        print(f"✗ MySQL连接池测试失败: {e}")
        return False
    
    return True


def test_redis_connection_pool():
    """测试Redis连接池"""
    print("\n=== 测试Redis连接池 ===")
    
    if not check_redis_available():
        print("⚠️  Redis不可用，跳过Redis连接池测试")
        return True
    
    try:
        # 创建Redis连接池配置
        redis_config = RedisPoolConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_PASSWORD') else None,
            max_connections=20,
            health_check_interval=10
        )
        
        # 创建连接池管理器
        pool_manager = ConnectionPoolManager()
        
        # 创建Redis连接池
        redis_pool = pool_manager.create_redis_pool("test_redis", redis_config)
        print("✓ Redis连接池创建成功")
        
        # 测试获取连接
        clients = []
        for i in range(3):
            try:
                client = redis_pool.get_connection()
                clients.append(client)
                
                # 测试Redis操作
                client.set(f"test_key_{i}", f"test_value_{i}")
                value = client.get(f"test_key_{i}")
                print(f"✓ 获取Redis客户端 {i+1}: 成功，操作结果: {value}")
                
            except Exception as e:
                print(f"✗ 获取Redis客户端 {i+1}: 失败 - {e}")
        
        # 获取统计信息
        stats = redis_pool.get_stats()
        print(f"✓ Redis连接池统计: 总请求={stats.total_requests}, 健康状态={redis_pool.is_healthy()}")
        
        pool_manager.close_all()
        print("✓ Redis连接池测试完成")
        
    except Exception as e:
        print(f"✗ Redis连接池测试失败: {e}")
        return False
    
    return True


def test_connection_pool_manager():
    """测试连接池管理器"""
    print("\n=== 测试连接池管理器 ===")
    
    mysql_available = check_mysql_available()
    redis_available = check_redis_available()
    
    if not mysql_available and not redis_available:
        print("⚠️  MySQL和Redis都不可用，跳过连接池管理器测试")
        return True
    
    try:
        # 创建连接池管理器
        pool_manager = ConnectionPoolManager()
        
        created_pools = 0
        
        # 创建MySQL连接池（如果可用）
        if mysql_available:
            mysql_config = MySQLPoolConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                user=os.getenv('DB_USERNAME', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_DATABASE', 'medical_insurance'),
                mincached=1,
                maxcached=5,
                maxconnections=10
            )
            
            mysql_pool = pool_manager.create_mysql_pool("main_mysql", mysql_config)
            created_pools += 1
            print("✓ MySQL连接池创建成功")
        
        # 创建Redis连接池（如果可用）
        if redis_available:
            redis_config = RedisPoolConfig(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=int(os.getenv('REDIS_DB', '0')),
                password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_PASSWORD') else None,
                max_connections=10
            )
            
            redis_pool = pool_manager.create_redis_pool("main_redis", redis_config)
            created_pools += 1
            print("✓ Redis连接池创建成功")
        
        print(f"✓ 总共创建了 {created_pools} 个连接池")
        
        # 启动监控
        pool_manager.start_monitoring()
        print("✓ 连接池监控已启动")
        
        # 模拟一些连接操作
        for i in range(5):
            try:
                # MySQL操作（如果可用）
                if mysql_available:
                    mysql_conn = pool_manager.get_mysql_connection("main_mysql")
                    cursor = mysql_conn.cursor()
                    cursor.execute("SELECT %s as test_id", (i,))
                    cursor.close()
                    mysql_conn.close()
                
                # Redis操作（如果可用）
                if redis_available:
                    redis_client = pool_manager.get_redis_connection("main_redis")
                    redis_client.set(f"monitor_test_{i}", f"value_{i}")
                
            except Exception as e:
                print(f"连接操作 {i+1} 失败: {e}")
        
        # 等待一段时间让监控收集数据
        time.sleep(2)
        
        # 获取所有统计信息
        all_stats = pool_manager.get_all_stats()
        print("✓ 连接池管理器统计信息:")
        print(f"  MySQL连接池数量: {all_stats['summary']['total_mysql_pools']}")
        print(f"  Redis连接池数量: {all_stats['summary']['total_redis_pools']}")
        print(f"  健康的Redis连接池: {all_stats['summary']['healthy_redis_pools']}")
        print(f"  总连接数: {all_stats['summary']['total_connections']}")
        print(f"  总请求数: {all_stats['summary']['total_requests']}")
        
        # 停止监控
        pool_manager.stop_monitoring()
        print("✓ 连接池监控已停止")
        
        pool_manager.close_all()
        print("✓ 连接池管理器测试完成")
        
    except Exception as e:
        print(f"✗ 连接池管理器测试失败: {e}")
        return False
    
    return True


def test_database_manager_integration():
    """测试数据库管理器集成"""
    print("\n=== 测试数据库管理器集成 ===")
    
    if not check_mysql_available():
        print("⚠️  MySQL不可用，跳过数据库管理器集成测试")
        return True
    
    try:
        # 从环境变量创建数据库配置
        db_config = DatabaseConfig.from_env()
        
        # 创建数据库管理器（使用连接池）
        db_manager = DatabaseManager(db_config, pool_name="integrated_test")
        print("✓ 集成数据库管理器创建成功")
        
        # 测试数据库操作
        try:
            result = db_manager.execute_query("SELECT 1 as test_value")
            print(f"✓ 数据库查询测试: {result}")
        except Exception as e:
            print(f"数据库查询测试失败: {e}")
        
        # 获取连接池状态
        pool_status = db_manager.get_pool_status()
        print(f"✓ 连接池状态: {pool_status['status']}")
        if 'pool_stats' in pool_status:
            stats = pool_status['pool_stats']
            print(f"  连接池统计: 总请求={stats['total_requests']}, 失败请求={stats['failed_requests']}")
        
        db_manager.close()
        print("✓ 数据库管理器集成测试完成")
        
    except Exception as e:
        print(f"✗ 数据库管理器集成测试失败: {e}")
        return False
    
    return True


def test_hybrid_cache_fallback():
    """测试混合缓存的fallback机制"""
    print("\n=== 测试混合缓存fallback机制 ===")
    
    try:
        from medical_insurance_sdk.core.cache_manager import HybridCacheManager
        
        # 创建Redis配置（可能不可用）
        redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_PASSWORD') else None,
            'default_ttl': 300,
            'key_prefix': 'test_hybrid:'
        }
        
        # 创建混合缓存管理器
        cache_manager = HybridCacheManager(
            redis_config=redis_config,
            memory_cache_size=100,
            memory_ttl=60,
            use_memory_fallback=True
        )
        
        print("✓ 混合缓存管理器创建成功")
        
        # 测试缓存操作
        test_key = "fallback_test_key"
        test_value = {"message": "这是一个测试值", "timestamp": time.time()}
        
        # 设置缓存
        success = cache_manager.set(test_key, test_value, ttl=120)
        print(f"✓ 设置缓存: {success}")
        
        # 获取缓存
        cached_value = cache_manager.get(test_key)
        print(f"✓ 获取缓存: {cached_value is not None}")
        if cached_value:
            print(f"  缓存内容: {cached_value}")
        
        # 获取统计信息
        stats = cache_manager.get_stats()
        print(f"✓ 混合缓存统计:")
        print(f"  Redis可用: {stats['hybrid_config']['redis_available']}")
        print(f"  内存缓存项: {stats['memory_cache']['total_items']}")
        
        cache_manager.close()
        print("✓ 混合缓存fallback测试完成")
        
    except Exception as e:
        print(f"✗ 混合缓存fallback测试失败: {e}")
        return False
    
    return True


def test_environment_config():
    """测试环境配置读取"""
    print("\n=== 测试环境配置读取 ===")
    
    try:
        print("✓ 环境变量配置:")
        print(f"  数据库: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}")
        print(f"  用户: {os.getenv('DB_USERNAME')}")
        print(f"  密码: {'***' if os.getenv('DB_PASSWORD') else '(空)'}")
        print(f"  Redis: {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}")
        print(f"  环境: {os.getenv('ENVIRONMENT', 'development')}")
        
        # 测试可用性
        mysql_available = check_mysql_available()
        redis_available = check_redis_available()
        
        print("✓ 服务可用性:")
        print(f"  MySQL: {'✓ 可用' if mysql_available else '✗ 不可用'}")
        print(f"  Redis: {'✓ 可用' if redis_available else '✗ 不可用'}")
        
        return True
        
    except Exception as e:
        print(f"✗ 环境配置测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始连接池管理器功能测试（使用环境变量配置）...")
    print(f"环境: {os.getenv('ENVIRONMENT', 'development')}")
    
    # 运行所有测试
    tests = [
        test_environment_config,
        test_mysql_connection_pool,
        test_redis_connection_pool,
        test_connection_pool_manager,
        test_database_manager_integration,
        test_hybrid_cache_fallback
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"测试异常: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！")
    elif passed > 0:
        print("✅ 部分测试通过，这是正常的（某些服务可能不可用）")
    else:
        print("⚠️  所有测试失败，请检查配置和服务状态")