#!/usr/bin/env python3
"""
医保接口SDK Docker健康检查脚本
用于检查各个服务的健康状态
"""

import sys
import time
import requests
import pymysql
import redis
import json
from typing import Dict, List, Tuple


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.results = {}
    
    def check_mysql(self, host: str = 'localhost', port: int = 3306, 
                   user: str = 'medical_user', password: str = 'wodemima',
                   database: str = 'medical_insurance_sdk') -> Tuple[bool, str]:
        """检查MySQL连接"""
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=5
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            connection.close()
            
            if result and result[0] == 1:
                return True, "MySQL连接正常"
            else:
                return False, "MySQL查询失败"
                
        except Exception as e:
            return False, f"MySQL连接失败: {str(e)}"
    
    def check_redis(self, host: str = 'localhost', port: int = 6379,
                   password: str = 'wodemima') -> Tuple[bool, str]:
        """检查Redis连接"""
        try:
            r = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            pong = r.ping()
            if pong:
                # 测试读写
                r.set('health_check', 'ok', ex=10)
                value = r.get('health_check')
                if value and value.decode() == 'ok':
                    return True, "Redis连接正常"
                else:
                    return False, "Redis读写测试失败"
            else:
                return False, "Redis ping失败"
                
        except Exception as e:
            return False, f"Redis连接失败: {str(e)}"
    
    def check_api_service(self, url: str = 'http://localhost:8000') -> Tuple[bool, str]:
        """检查API服务"""
        try:
            # 检查健康检查端点
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True, "API服务正常"
                else:
                    return False, f"API服务状态异常: {data.get('status', 'unknown')}"
            else:
                return False, f"API服务响应异常: HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "API服务连接失败"
        except requests.exceptions.Timeout:
            return False, "API服务响应超时"
        except Exception as e:
            return False, f"API服务检查失败: {str(e)}"
    
    def check_celery_worker(self, redis_host: str = 'localhost', redis_port: int = 6379,
                           redis_password: str = 'wodemima') -> Tuple[bool, str]:
        """检查Celery Worker"""
        try:
            from celery import Celery
            
            # 创建Celery应用
            app = Celery('health_check')
            app.conf.update(
                broker_url=f'redis://:{redis_password}@{redis_host}:{redis_port}/0',
                result_backend=f'redis://:{redis_password}@{redis_host}:{redis_port}/0'
            )
            
            # 检查活跃的worker
            inspect = app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                worker_count = len(active_workers)
                return True, f"Celery Worker正常 ({worker_count}个worker)"
            else:
                return False, "没有活跃的Celery Worker"
                
        except Exception as e:
            return False, f"Celery Worker检查失败: {str(e)}"
    
    def check_all_services(self, config: Dict = None) -> Dict[str, Dict]:
        """检查所有服务"""
        if config is None:
            config = {
                'mysql': {'host': 'localhost', 'port': 3306, 'user': 'medical_user', 'password': 'wodemima'},
                'redis': {'host': 'localhost', 'port': 6379, 'password': 'wodemima'},
                'api': {'url': 'http://localhost:8000'},
                'celery': {'redis_host': 'localhost', 'redis_port': 6379, 'redis_password': 'wodemima'}
            }
        
        results = {}
        
        # 检查MySQL
        print("检查MySQL服务...")
        mysql_ok, mysql_msg = self.check_mysql(**config['mysql'])
        results['mysql'] = {'status': 'healthy' if mysql_ok else 'unhealthy', 'message': mysql_msg}
        print(f"  MySQL: {'✓' if mysql_ok else '✗'} {mysql_msg}")
        
        # 检查Redis
        print("检查Redis服务...")
        redis_ok, redis_msg = self.check_redis(**config['redis'])
        results['redis'] = {'status': 'healthy' if redis_ok else 'unhealthy', 'message': redis_msg}
        print(f"  Redis: {'✓' if redis_ok else '✗'} {redis_msg}")
        
        # 检查API服务
        print("检查API服务...")
        api_ok, api_msg = self.check_api_service(**config['api'])
        results['api'] = {'status': 'healthy' if api_ok else 'unhealthy', 'message': api_msg}
        print(f"  API: {'✓' if api_ok else '✗'} {api_msg}")
        
        # 检查Celery Worker
        print("检查Celery Worker...")
        celery_ok, celery_msg = self.check_celery_worker(**config['celery'])
        results['celery'] = {'status': 'healthy' if celery_ok else 'unhealthy', 'message': celery_msg}
        print(f"  Celery: {'✓' if celery_ok else '✗'} {celery_msg}")
        
        # 计算总体状态
        all_healthy = all(result['status'] == 'healthy' for result in results.values())
        results['overall'] = {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'message': '所有服务正常' if all_healthy else '部分服务异常'
        }
        
        return results
    
    def wait_for_services(self, config: Dict = None, max_wait: int = 300, check_interval: int = 5) -> bool:
        """等待服务启动"""
        print(f"等待服务启动，最大等待时间: {max_wait}秒")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            results = self.check_all_services(config)
            
            if results['overall']['status'] == 'healthy':
                print("所有服务已启动完成！")
                return True
            
            print(f"等待中... ({int(time.time() - start_time)}s)")
            time.sleep(check_interval)
        
        print("服务启动超时！")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='医保接口SDK健康检查')
    parser.add_argument('--wait', action='store_true', help='等待服务启动')
    parser.add_argument('--max-wait', type=int, default=300, help='最大等待时间（秒）')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    parser.add_argument('--mysql-host', default='localhost', help='MySQL主机')
    parser.add_argument('--mysql-port', type=int, default=3306, help='MySQL端口')
    parser.add_argument('--redis-host', default='localhost', help='Redis主机')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis端口')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API服务URL')
    
    args = parser.parse_args()
    
    # 构建配置
    config = {
        'mysql': {
            'host': args.mysql_host,
            'port': args.mysql_port,
            'user': 'medical_user',
            'password': 'wodemima'
        },
        'redis': {
            'host': args.redis_host,
            'port': args.redis_port,
            'password': 'wodemima'
        },
        'api': {
            'url': args.api_url
        },
        'celery': {
            'redis_host': args.redis_host,
            'redis_port': args.redis_port,
            'redis_password': 'wodemima'
        }
    }
    
    checker = HealthChecker()
    
    if args.wait:
        # 等待服务启动
        success = checker.wait_for_services(config, args.max_wait)
        sys.exit(0 if success else 1)
    else:
        # 执行健康检查
        results = checker.check_all_services(config)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\n总体状态: {'✓' if results['overall']['status'] == 'healthy' else '✗'} {results['overall']['message']}")
        
        # 根据总体状态设置退出码
        sys.exit(0 if results['overall']['status'] == 'healthy' else 1)


if __name__ == '__main__':
    main()