"""
Redis缓存功能测试
测试Redis缓存管理器的基本功能
"""

import time
import json
from medical_insurance_sdk.core.cache_manager import RedisCacheManager, HybridCacheManager
from medical_insurance_sdk.config.cache_config import get_cache_config


def test_redis_cache_basic():
    """测试Redis缓存基本功能"""
    print("=== 测试Redis缓存基本功能 ===")
    
    try:
        # 创建Redis缓存管理器
        cache_manager = RedisCacheManager(
            host='localhost',
            port=6379,
            db=0,
            default_ttl=60,
            key_prefix='test_medical_sdk:'
        )
        
        print("✓ Redis缓存管理器创建成功")
        
        # 测试设置和获取
        test_key = "interface_config:1101"
        test_value = {
            "api_code": "1101",
            "api_name": "人员信息获取",
            "required_params": {"psn_no": "人员编号"},
            "default_values": {"psn_cert_type": "01"}
        }
        
        # 设置缓存
        success = cache_manager.set(test_key, test_value, ttl=30)
        print(f"✓ 设置缓存: {success}")
        
        # 获取缓存
        cached_value = cache_manager.get(test_key)
        print(f"✓ 获取缓存: {cached_value is not None}")
        print(f"  缓存内容: {json.dumps(cached_value, ensure_ascii=False, indent=2)}")
        
        # 检查键是否存在
        exists = cache_manager.exists(test_key)
        print(f"✓ 键存在检查: {exists}")
        
        # 获取TTL
        ttl = cache_manager.ttl(test_key)
        print(f"✓ 剩余TTL: {ttl}秒")
        
        # 测试模式删除
        cache_manager.set("interface_config:1102", {"api_code": "1102"})
        cache_manager.set("interface_config:1103", {"api_code": "1103"})
        
        deleted_count = cache_manager.delete_pattern("interface_config:*")
        print(f"✓ 模式删除: 删除了{deleted_count}个键")
        
        # 获取统计信息
        stats = cache_manager.get_stats()
        print(f"✓ 缓存统计: 命中率{stats['hit_rate']}%, 总请求{stats['total_requests']}")
        
        # 获取Redis信息
        redis_info = cache_manager.get_info()
        print(f"✓ Redis信息: 版本{redis_info.get('redis_version', 'N/A')}")
        
        cache_manager.close()
        print("✓ Redis缓存管理器关闭成功")
        
    except Exception as e:
        print(f"✗ Redis缓存测试失败: {e}")
        return False
    
    return True


def test_hybrid_cache():
    """测试混合缓存功能"""
    print("\n=== 测试混合缓存功能 ===")
    
    try:
        # 创建混合缓存管理器
        redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'default_ttl': 300,
            'key_prefix': 'test_hybrid:'
        }
        
        cache_manager = HybridCacheManager(
            redis_config=redis_config,
            memory_cache_size=100,
            memory_ttl=60,
            use_memory_fallback=True
        )
        
        print("✓ 混合缓存管理器创建成功")
        
        # 测试缓存设置和获取
        test_key = "org_config:TEST001"
        test_value = {
            "org_code": "TEST001",
            "org_name": "测试医院",
            "app_id": "test_app_id",
            "base_url": "https://test.medical.gov.cn"
        }
        
        # 设置缓存
        success = cache_manager.set(test_key, test_value, ttl=120)
        print(f"✓ 设置混合缓存: {success}")
        
        # 第一次获取（从Redis）
        cached_value = cache_manager.get(test_key)
        print(f"✓ 第一次获取: {cached_value is not None}")
        
        # 第二次获取（从内存缓存）
        cached_value = cache_manager.get(test_key)
        print(f"✓ 第二次获取: {cached_value is not None}")
        
        # 获取统计信息
        stats = cache_manager.get_stats()
        print(f"✓ 混合缓存统计:")
        print(f"  内存缓存: {stats['memory_cache']}")
        print(f"  Redis可用: {stats['hybrid_config']['redis_available']}")
        
        cache_manager.close()
        print("✓ 混合缓存管理器关闭成功")
        
    except Exception as e:
        print(f"✗ 混合缓存测试失败: {e}")
        return False
    
    return True


def test_cache_config():
    """测试缓存配置"""
    print("\n=== 测试缓存配置 ===")
    
    try:
        # 测试不同环境的配置
        environments = ['development', 'testing', 'production']
        
        for env in environments:
            config = get_cache_config(env)
            print(f"✓ {env}环境配置: {config['type']}")
        
        print("✓ 缓存配置测试成功")
        
    except Exception as e:
        print(f"✗ 缓存配置测试失败: {e}")
        return False
    
    return True


def test_cache_performance():
    """测试缓存性能"""
    print("\n=== 测试缓存性能 ===")
    
    try:
        cache_manager = RedisCacheManager(
            host='localhost',
            port=6379,
            db=0,
            key_prefix='perf_test:'
        )
        
        # 批量设置测试
        start_time = time.time()
        for i in range(100):
            cache_manager.set(f"perf_key_{i}", {"id": i, "data": f"test_data_{i}"})
        set_time = time.time() - start_time
        
        print(f"✓ 批量设置100个键耗时: {set_time:.3f}秒")
        
        # 批量获取测试
        start_time = time.time()
        hit_count = 0
        for i in range(100):
            value = cache_manager.get(f"perf_key_{i}")
            if value is not None:
                hit_count += 1
        get_time = time.time() - start_time
        
        print(f"✓ 批量获取100个键耗时: {get_time:.3f}秒, 命中{hit_count}个")
        
        # 清理测试数据
        deleted_count = cache_manager.delete_pattern("perf_key_*")
        print(f"✓ 清理测试数据: 删除{deleted_count}个键")
        
        cache_manager.close()
        print("✓ 性能测试完成")
        
    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("开始Redis缓存功能测试...")
    
    # 运行所有测试
    tests = [
        test_redis_cache_basic,
        test_hybrid_cache,
        test_cache_config,
        test_cache_performance
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
        print("⚠️  部分测试失败，请检查Redis连接和配置")