#!/usr/bin/env python3
"""
连接池优化功能测试脚本
测试ConnectionPoolManager的优化功能和监控能力
"""

import time
import threading
import logging
from datetime import datetime
from medical_insurance_sdk.core.connection_pool_manager import (
    ConnectionPoolManager, MySQLPoolConfig, RedisPoolConfig
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_mysql_pool_optimization():
    """测试MySQL连接池优化功能"""
    print("=" * 60)
    print("测试MySQL连接池优化功能")
    print("=" * 60)
    
    # 创建连接池管理器
    manager = ConnectionPoolManager()
    
    # 从配置文件获取数据库配置
    from medical_insurance_sdk.core.database import DatabaseConfig
    db_config = DatabaseConfig.from_env()
    
    # 创建MySQL连接池配置（使用环境配置，但调整连接数以便测试）
    mysql_config = MySQLPoolConfig(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        database=db_config.database,
        charset=db_config.charset,
        maxconnections=5,  # 小连接数便于测试
        mincached=2,
        maxcached=5,
        enable_monitoring=True,
        slow_query_threshold=0.1,
        connect_timeout=db_config.connect_timeout,
        read_timeout=db_config.read_timeout,
        write_timeout=db_config.write_timeout
    )
    
    try:
        # 创建MySQL连接池
        mysql_pool = manager.create_mysql_pool('test_mysql', mysql_config)
        print(f"✓ 创建MySQL连接池成功: {mysql_pool.pool_name}")
        
        # 获取初始统计信息
        initial_stats = mysql_pool.get_stats()
        print(f"✓ 初始连接池状态: 最大连接={initial_stats.max_connections}, 当前连接={initial_stats.current_connections}")
        
        # 模拟并发连接请求
        def simulate_connections():
            for i in range(10):
                try:
                    conn = mysql_pool.get_connection()
                    time.sleep(0.2)  # 模拟查询时间
                    conn.close()
                except Exception as e:
                    print(f"连接失败: {e}")
        
        # 启动多个线程模拟并发
        threads = []
        for i in range(3):
            thread = threading.Thread(target=simulate_connections)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 获取详细统计信息
        detailed_stats = mysql_pool.get_detailed_stats()
        print(f"✓ 详细统计信息:")
        print(f"  - 总请求数: {detailed_stats['performance_metrics']['total_requests']}")
        print(f"  - 失败请求数: {detailed_stats['performance_metrics']['failed_requests']}")
        print(f"  - 峰值连接数: {detailed_stats['current_status']['peak_connections']}")
        print(f"  - 平均响应时间: {detailed_stats['performance_metrics']['average_response_time']:.3f}s")
        
        # 获取优化建议
        suggestions = manager.get_optimization_suggestions()
        print(f"✓ 优化建议数量: {len(suggestions)}")
        for suggestion in suggestions:
            print(f"  - {suggestion['type']}: {suggestion['description']}")
        
        print("✓ MySQL连接池优化测试完成")
        
    except Exception as e:
        print(f"✗ MySQL连接池测试失败: {e}")
    
    finally:
        manager.close_all()

def test_redis_pool_optimization():
    """测试Redis连接池优化功能"""
    print("=" * 60)
    print("测试Redis连接池优化功能")
    print("=" * 60)
    
    # 创建连接池管理器
    manager = ConnectionPoolManager()
    
    # 从环境变量获取Redis配置
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    # 创建Redis连接池配置
    redis_config = RedisPoolConfig(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0')),
        password=os.getenv('REDIS_PASSWORD'),
        max_connections=10,
        enable_monitoring=True,
        slow_command_threshold=0.05,
        health_check_interval=5
    )
    
    try:
        # 创建Redis连接池
        redis_pool = manager.create_redis_pool('test_redis', redis_config)
        print(f"✓ 创建Redis连接池成功: {redis_pool.pool_name}")
        
        # 获取初始统计信息
        initial_stats = redis_pool.get_stats()
        print(f"✓ 初始连接池状态: 最大连接={initial_stats.max_connections}, 当前连接={initial_stats.current_connections}")
        
        # 模拟Redis操作
        def simulate_redis_operations():
            for i in range(20):
                try:
                    client = redis_pool.get_connection()
                    # 模拟各种Redis命令
                    client.set(f'test_key_{i}', f'test_value_{i}')
                    client.get(f'test_key_{i}')
                    client.delete(f'test_key_{i}')
                    time.sleep(0.01)  # 短暂延迟
                except Exception as e:
                    print(f"Redis操作失败: {e}")
        
        # 启动多个线程模拟并发
        threads = []
        for i in range(5):
            thread = threading.Thread(target=simulate_redis_operations)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 等待一段时间让监控收集数据
        time.sleep(2)
        
        # 获取统计信息
        final_stats = redis_pool.get_stats()
        print(f"✓ 最终统计信息:")
        print(f"  - 总请求数: {final_stats.total_requests}")
        print(f"  - 失败请求数: {final_stats.failed_requests}")
        print(f"  - 平均响应时间: {final_stats.average_response_time:.3f}s")
        print(f"  - 连接池健康状态: {redis_pool.is_healthy()}")
        
        print("✓ Redis连接池优化测试完成")
        
    except Exception as e:
        print(f"✗ Redis连接池测试失败: {e}")
    
    finally:
        manager.close_all()

def test_pool_manager_monitoring():
    """测试连接池管理器的监控功能"""
    print("=" * 60)
    print("测试连接池管理器监控功能")
    print("=" * 60)
    
    # 创建连接池管理器
    manager = ConnectionPoolManager()
    
    try:
        # 从配置文件获取数据库配置
        from medical_insurance_sdk.core.database import DatabaseConfig
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        db_config = DatabaseConfig.from_env()
        
        # 创建多个连接池
        mysql_config = MySQLPoolConfig(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset=db_config.charset,
            maxconnections=10,
            enable_monitoring=True
        )
        
        redis_config = RedisPoolConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            max_connections=10,
            enable_monitoring=True
        )
        
        # 创建连接池
        manager.create_mysql_pool('monitor_mysql', mysql_config)
        manager.create_redis_pool('monitor_redis', redis_config)
        
        print("✓ 创建测试连接池完成")
        
        # 启动监控
        manager.start_monitoring()
        print("✓ 启动连接池监控")
        
        # 等待监控收集数据
        time.sleep(3)
        
        # 获取所有统计信息
        all_stats = manager.get_all_stats()
        print(f"✓ 连接池统计信息:")
        print(f"  - MySQL连接池数量: {all_stats['summary']['total_mysql_pools']}")
        print(f"  - Redis连接池数量: {all_stats['summary']['total_redis_pools']}")
        print(f"  - 健康的Redis连接池: {all_stats['summary']['healthy_redis_pools']}")
        print(f"  - 总连接数: {all_stats['summary']['total_connections']}")
        
        # 获取性能报告
        performance_report = manager.get_performance_report()
        print(f"✓ 性能报告:")
        print(f"  - 优化建议数量: {performance_report['optimization_suggestions']}")
        print(f"  - 性能问题数量: {performance_report['performance_issues']}")
        
        # 停止监控
        manager.stop_monitoring()
        print("✓ 停止连接池监控")
        
        print("✓ 连接池管理器监控测试完成")
        
    except Exception as e:
        print(f"✗ 连接池管理器监控测试失败: {e}")
    
    finally:
        manager.close_all()

def test_optimization_suggestions():
    """测试优化建议功能"""
    print("=" * 60)
    print("测试优化建议功能")
    print("=" * 60)
    
    # 创建连接池管理器
    manager = ConnectionPoolManager()
    
    try:
        # 从配置文件获取数据库配置
        from medical_insurance_sdk.core.database import DatabaseConfig
        db_config = DatabaseConfig.from_env()
        
        # 创建一个小容量的连接池以触发优化建议
        mysql_config = MySQLPoolConfig(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset=db_config.charset,
            maxconnections=2,  # 很小的连接数
            mincached=1,
            maxcached=2,
            enable_monitoring=True,
            slow_query_threshold=0.01  # 很低的慢查询阈值
        )
        
        mysql_pool = manager.create_mysql_pool('small_mysql', mysql_config)
        
        # 模拟高负载以触发优化建议
        def high_load_simulation():
            for i in range(50):
                try:
                    conn = mysql_pool.get_connection()
                    time.sleep(0.1)  # 模拟慢查询
                    conn.close()
                except Exception as e:
                    pass  # 忽略连接失败，这正是我们想要的
        
        # 启动高负载
        threads = []
        for i in range(5):
            thread = threading.Thread(target=high_load_simulation)
            threads.append(thread)
            thread.start()
        
        # 等待部分完成
        time.sleep(2)
        
        # 获取优化建议
        suggestions = manager.get_optimization_suggestions()
        print(f"✓ 获取到 {len(suggestions)} 条优化建议:")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. 类型: {suggestion['type']}")
            print(f"     严重程度: {suggestion['severity']}")
            print(f"     描述: {suggestion['description']}")
            print(f"     建议: {suggestion['suggestion']}")
            print()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 获取性能报告
        report = manager.get_performance_report()
        print(f"✓ 性能报告摘要:")
        print(f"  - 时间戳: {report['timestamp']}")
        print(f"  - 连接池详情: {report['pool_details']}")
        print(f"  - 优化建议数: {report['optimization_suggestions']}")
        
        print("✓ 优化建议功能测试完成")
        
    except Exception as e:
        print(f"✗ 优化建议功能测试失败: {e}")
    
    finally:
        manager.close_all()

def main():
    """主测试函数"""
    print("开始连接池优化功能测试")
    print("=" * 80)
    
    try:
        # 测试MySQL连接池优化
        test_mysql_pool_optimization()
        print()
        
        # 测试Redis连接池优化
        test_redis_pool_optimization()
        print()
        
        # 测试连接池管理器监控
        test_pool_manager_monitoring()
        print()
        
        # 测试优化建议
        test_optimization_suggestions()
        print()
        
        print("=" * 80)
        print("✓ 所有连接池优化功能测试完成")
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()