"""
连接池管理器功能测试
测试MySQL和Redis连接池的管理和监控功能
"""

import time
import threading
from medical_insurance_sdk.core.connection_pool_manager import (
    ConnectionPoolManager, MySQLPoolConfig, RedisPoolConfig,
    get_global_pool_manager, close_global_pool_manager
)
from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig


def test_mysql_connection_pool():
    """测试MySQL连接池"""
    print("=== 测试MySQL连接池 ===")
    
    try:
        # 从环境变量读取数据库配置
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        load_dotenv('medical_insurance_sdk/.env')
        
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
        for i in range(5):
            try:
                conn = mysql_pool.get_connection()
                connections.append(conn)
                print(f"✓ 获取连接 {i+1}: 成功")
            except Exception as e:
                print(f"✗ 获取连接 {i+1}: 失败 - {e}")
        
        # 关闭连接
        for conn in connections:
            conn.close()
        print("✓ 连接已关闭")
        
        # 获取统计信息
        stats = mysql_pool.get_stats()
        print(f"✓ 连接池统计: {stats.to_dict()}")
        
        pool_manager.close_all()
        print("✓ MySQL连接池测试完成")
        
    except Exception as e:
        print(f"✗ MySQL连接池测试失败: {e}")
        return False
    
    return True


def test_redis_connection_pool():
    """测试Redis连接池"""
    print("\n=== 测试Redis连接池 ===")
    
    try:
        # 从环境变量读取Redis配置
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        load_dotenv('medical_insurance_sdk/.env')
        
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
                print(f"✓ 获取Redis客户端 {i+1}: 成功")
                
                # 测试Redis操作
                client.set(f"test_key_{i}", f"test_value_{i}")
                value = client.get(f"test_key_{i}")
                print(f"  Redis操作测试: {value}")
                
            except Exception as e:
                print(f"✗ 获取Redis客户端 {i+1}: 失败 - {e}")
        
        # 获取统计信息
        stats = redis_pool.get_stats()
        print(f"✓ Redis连接池统计: {stats.to_dict()}")
        
        # 检查健康状态
        is_healthy = redis_pool.is_healthy()
        print(f"✓ Redis连接池健康状态: {is_healthy}")
        
        pool_manager.close_all()
        print("✓ Redis连接池测试完成")
        
    except Exception as e:
        print(f"✗ Redis连接池测试失败: {e}")
        return False
    
    return True


def test_connection_pool_manager():
    """测试连接池管理器"""
    print("\n=== 测试连接池管理器 ===")
    
    try:
        # 从环境变量读取数据库配置
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        load_dotenv('medical_insurance_sdk/.env')
        
        # 创建连接池管理器
        pool_manager = ConnectionPoolManager()
        
        # 创建多个连接池
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
        
        redis_config = RedisPoolConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_PASSWORD') else None,
            max_connections=10
        )
        
        # 创建连接池
        mysql_pool = pool_manager.create_mysql_pool("main_mysql", mysql_config)
        redis_pool = pool_manager.create_redis_pool("main_redis", redis_config)
        
        print("✓ 多个连接池创建成功")
        
        # 启动监控
        pool_manager.start_monitoring()
        print("✓ 连接池监控已启动")
        
        # 模拟一些连接操作
        for i in range(10):
            try:
                # MySQL操作
                mysql_conn = pool_manager.get_mysql_connection("main_mysql")
                mysql_conn.close()
                
                # Redis操作
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


def test_global_pool_manager():
    """测试全局连接池管理器"""
    print("\n=== 测试全局连接池管理器 ===")
    
    try:
        # 从环境变量读取数据库配置
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        load_dotenv('medical_insurance_sdk/.env')
        
        # 获取全局连接池管理器
        global_manager = get_global_pool_manager()
        print("✓ 获取全局连接池管理器成功")
        
        # 创建连接池
        mysql_config = MySQLPoolConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USERNAME', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'medical_insurance'),
            mincached=1,
            maxcached=3,
            maxconnections=5
        )
        
        mysql_pool = global_manager.create_mysql_pool("global_mysql", mysql_config)
        print("✓ 全局MySQL连接池创建成功")
        
        # 测试连接
        conn = global_manager.get_mysql_connection("global_mysql")
        conn.close()
        print("✓ 全局连接池连接测试成功")
        
        # 获取统计信息
        stats = global_manager.get_all_stats()
        print(f"✓ 全局连接池统计: MySQL池数量 {stats['summary']['total_mysql_pools']}")
        
        # 关闭全局连接池管理器
        close_global_pool_manager()
        print("✓ 全局连接池管理器已关闭")
        
    except Exception as e:
        print(f"✗ 全局连接池管理器测试失败: {e}")
        return False
    
    return True


def test_database_manager_integration():
    """测试数据库管理器集成"""
    print("\n=== 测试数据库管理器集成 ===")
    
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
        
        db_manager.close()
        print("✓ 数据库管理器集成测试完成")
        
    except Exception as e:
        print(f"✗ 数据库管理器集成测试失败: {e}")
        return False
    
    return True


def test_concurrent_connections():
    """测试并发连接"""
    print("\n=== 测试并发连接 ===")
    
    try:
        # 从环境变量读取数据库配置
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        load_dotenv('medical_insurance_sdk/.env')
        
        pool_manager = ConnectionPoolManager()
        
        # 创建连接池
        mysql_config = MySQLPoolConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USERNAME', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'medical_insurance'),
            mincached=2,
            maxcached=5,
            maxconnections=10
        )
        
        mysql_pool = pool_manager.create_mysql_pool("concurrent_test", mysql_config)
        
        # 并发测试函数
        def worker(worker_id):
            try:
                for i in range(5):
                    conn = mysql_pool.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT %s as worker_id, %s as iteration", (worker_id, i))
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    time.sleep(0.1)  # 模拟处理时间
                print(f"✓ 工作线程 {worker_id} 完成")
            except Exception as e:
                print(f"✗ 工作线程 {worker_id} 失败: {e}")
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 获取统计信息
        stats = mysql_pool.get_stats()
        print(f"✓ 并发测试统计: 总请求 {stats.total_requests}, 失败请求 {stats.failed_requests}")
        
        pool_manager.close_all()
        print("✓ 并发连接测试完成")
        
    except Exception as e:
        print(f"✗ 并发连接测试失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("开始连接池管理器功能测试...")
    
    # 运行所有测试
    tests = [
        test_mysql_connection_pool,
        test_redis_connection_pool,
        test_connection_pool_manager,
        test_global_pool_manager,
        test_database_manager_integration,
        test_concurrent_connections
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
    else:
        print("⚠️  部分测试失败，请检查数据库连接配置")