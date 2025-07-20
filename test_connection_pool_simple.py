"""
连接池管理器简单测试
测试连接池管理器的基本功能，不需要实际的数据库连接
"""

from medical_insurance_sdk.core.connection_pool_manager import (
    ConnectionPoolManager, MySQLPoolConfig, RedisPoolConfig,
    get_global_pool_manager, close_global_pool_manager
)


def test_pool_config_creation():
    """测试连接池配置创建"""
    print("=== 测试连接池配置创建 ===")
    
    try:
        # 测试MySQL配置
        mysql_config = MySQLPoolConfig(
            host='localhost',
            port=3306,
            user='test_user',
            password='test_password',
            database='test_db',
            mincached=2,
            maxcached=10,
            maxconnections=20
        )
        
        print(f"✓ MySQL配置创建成功: {mysql_config.host}:{mysql_config.port}")
        print(f"  连接池配置: min={mysql_config.mincached}, max={mysql_config.maxconnections}")
        
        # 测试Redis配置
        redis_config = RedisPoolConfig(
            host='localhost',
            port=6379,
            db=0,
            max_connections=50,
            socket_timeout=5
        )
        
        print(f"✓ Redis配置创建成功: {redis_config.host}:{redis_config.port}")
        print(f"  连接池配置: max_connections={redis_config.max_connections}")
        
        return True
        
    except Exception as e:
        print(f"✗ 连接池配置创建失败: {e}")
        return False


def test_pool_manager_creation():
    """测试连接池管理器创建"""
    print("\n=== 测试连接池管理器创建 ===")
    
    try:
        # 创建连接池管理器
        pool_manager = ConnectionPoolManager()
        print("✓ 连接池管理器创建成功")
        
        # 测试获取统计信息（空状态）
        stats = pool_manager.get_all_stats()
        print(f"✓ 初始统计信息: MySQL池={stats['summary']['total_mysql_pools']}, Redis池={stats['summary']['total_redis_pools']}")
        
        # 测试监控功能
        pool_manager.start_monitoring()
        print("✓ 监控线程启动成功")
        
        pool_manager.stop_monitoring()
        print("✓ 监控线程停止成功")
        
        pool_manager.close_all()
        print("✓ 连接池管理器关闭成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 连接池管理器测试失败: {e}")
        return False


def test_global_pool_manager():
    """测试全局连接池管理器"""
    print("\n=== 测试全局连接池管理器 ===")
    
    try:
        # 获取全局连接池管理器
        global_manager1 = get_global_pool_manager()
        global_manager2 = get_global_pool_manager()
        
        # 验证是同一个实例
        if global_manager1 is global_manager2:
            print("✓ 全局连接池管理器单例模式正常")
        else:
            print("✗ 全局连接池管理器单例模式异常")
            return False
        
        # 获取统计信息
        stats = global_manager1.get_all_stats()
        print(f"✓ 全局管理器统计: {stats['summary']}")
        
        # 关闭全局连接池管理器
        close_global_pool_manager()
        print("✓ 全局连接池管理器关闭成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 全局连接池管理器测试失败: {e}")
        return False


def test_connection_pool_stats():
    """测试连接池统计信息"""
    print("\n=== 测试连接池统计信息 ===")
    
    try:
        from medical_insurance_sdk.core.connection_pool_manager import ConnectionPoolStats
        from datetime import datetime
        
        # 创建统计信息对象
        stats = ConnectionPoolStats(
            pool_name="test_pool",
            pool_type="mysql",
            max_connections=20,
            current_connections=5,
            active_connections=3,
            idle_connections=2,
            total_requests=100,
            failed_requests=2,
            average_response_time=0.05,
            last_check_time=datetime.now()
        )
        
        print("✓ 连接池统计信息对象创建成功")
        
        # 转换为字典
        stats_dict = stats.to_dict()
        print(f"✓ 统计信息字典: {stats_dict}")
        
        # 验证关键字段
        expected_fields = ['pool_name', 'pool_type', 'max_connections', 'total_requests']
        for field in expected_fields:
            if field in stats_dict:
                print(f"  ✓ 字段 {field}: {stats_dict[field]}")
            else:
                print(f"  ✗ 缺少字段: {field}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 连接池统计信息测试失败: {e}")
        return False


def test_config_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    try:
        # 测试MySQL配置的默认值
        mysql_config = MySQLPoolConfig()
        print(f"✓ MySQL默认配置: host={mysql_config.host}, port={mysql_config.port}")
        print(f"  连接池默认值: mincached={mysql_config.mincached}, maxconnections={mysql_config.maxconnections}")
        
        # 测试Redis配置的默认值
        redis_config = RedisPoolConfig()
        print(f"✓ Redis默认配置: host={redis_config.host}, port={redis_config.port}")
        print(f"  连接池默认值: max_connections={redis_config.max_connections}")
        
        # 测试配置修改
        mysql_config.host = "192.168.1.100"
        mysql_config.maxconnections = 50
        print(f"✓ MySQL配置修改: host={mysql_config.host}, maxconnections={mysql_config.maxconnections}")
        
        redis_config.host = "redis.example.com"
        redis_config.max_connections = 100
        print(f"✓ Redis配置修改: host={redis_config.host}, max_connections={redis_config.max_connections}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置验证测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    try:
        pool_manager = ConnectionPoolManager()
        
        # 测试获取不存在的连接池
        mysql_pool = pool_manager.get_mysql_pool("nonexistent")
        if mysql_pool is None:
            print("✓ 获取不存在的MySQL连接池返回None")
        else:
            print("✗ 获取不存在的MySQL连接池应该返回None")
            return False
        
        redis_pool = pool_manager.get_redis_pool("nonexistent")
        if redis_pool is None:
            print("✓ 获取不存在的Redis连接池返回None")
        else:
            print("✗ 获取不存在的Redis连接池应该返回None")
            return False
        
        # 测试获取不存在连接池的连接
        try:
            pool_manager.get_mysql_connection("nonexistent")
            print("✗ 获取不存在连接池的连接应该抛出异常")
            return False
        except Exception as e:
            print(f"✓ 获取不存在连接池的连接正确抛出异常: {type(e).__name__}")
        
        try:
            pool_manager.get_redis_connection("nonexistent")
            print("✗ 获取不存在连接池的连接应该抛出异常")
            return False
        except Exception as e:
            print(f"✓ 获取不存在连接池的连接正确抛出异常: {type(e).__name__}")
        
        pool_manager.close_all()
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始连接池管理器简单测试...")
    
    # 运行所有测试
    tests = [
        test_pool_config_creation,
        test_pool_manager_creation,
        test_global_pool_manager,
        test_connection_pool_stats,
        test_config_validation,
        test_error_handling
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
        print("⚠️  部分测试失败")