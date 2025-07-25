#!/usr/bin/env python3
"""
医保接口SDK服务监控脚本
提供服务状态监控、自动重启和告警功能
"""

import os
import sys
import time
import json
import logging
import smtplib
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

import requests
import pymysql
import redis
import psutil


class ServiceMonitor:
    """服务监控器"""
    
    def __init__(self, config_file: str = None):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.alert_history = {}
        
    def load_config(self, config_file: str = None) -> Dict:
        """加载配置"""
        default_config = {
            "services": {
                "api": {
                    "url": "http://localhost:8000/health",
                    "timeout": 10,
                    "retry_count": 3,
                    "restart_command": "docker-compose -f docker-compose.prod.yml restart medical_sdk"
                },
                "mysql": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "medical_user",
                    "password": "wodemima",
                    "database": "medical_insurance_sdk",
                    "restart_command": "docker-compose -f docker-compose.prod.yml restart mysql"
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "password": "wodemima",
                    "restart_command": "docker-compose -f docker-compose.prod.yml restart redis"
                },
                "celery": {
                    "redis_host": "localhost",
                    "redis_port": 6379,
                    "redis_password": "wodemima",
                    "restart_command": "docker-compose -f docker-compose.prod.yml restart celery_worker"
                }
            },
            "monitoring": {
                "check_interval": 60,
                "alert_threshold": 3,
                "alert_cooldown": 300,
                "auto_restart": True,
                "max_restart_attempts": 3
            },
            "alerts": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.example.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "monitor@example.com",
                    "to_emails": ["admin@example.com"]
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/service_monitor.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        
        # 创建日志目录
        log_file = log_config.get('file', 'logs/service_monitor.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def check_api_service(self, config: Dict) -> Tuple[bool, str]:
        """检查API服务"""
        try:
            response = requests.get(
                config['url'],
                timeout=config.get('timeout', 10)
            )
            
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
    
    def check_mysql_service(self, config: Dict) -> Tuple[bool, str]:
        """检查MySQL服务"""
        try:
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                connect_timeout=5
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            connection.close()
            
            if result and result[0] == 1:
                return True, "MySQL服务正常"
            else:
                return False, "MySQL查询失败"
                
        except Exception as e:
            return False, f"MySQL服务检查失败: {str(e)}"
    
    def check_redis_service(self, config: Dict) -> Tuple[bool, str]:
        """检查Redis服务"""
        try:
            r = redis.Redis(
                host=config['host'],
                port=config['port'],
                password=config['password'],
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            pong = r.ping()
            if pong:
                # 测试读写
                test_key = 'monitor_test'
                r.set(test_key, 'ok', ex=10)
                value = r.get(test_key)
                if value and value.decode() == 'ok':
                    return True, "Redis服务正常"
                else:
                    return False, "Redis读写测试失败"
            else:
                return False, "Redis ping失败"
                
        except Exception as e:
            return False, f"Redis服务检查失败: {str(e)}"
    
    def check_celery_service(self, config: Dict) -> Tuple[bool, str]:
        """检查Celery服务"""
        try:
            from celery import Celery
            
            # 创建Celery应用
            app = Celery('monitor')
            redis_url = f"redis://:{config['redis_password']}@{config['redis_host']}:{config['redis_port']}/0"
            app.conf.update(
                broker_url=redis_url,
                result_backend=redis_url
            )
            
            # 检查活跃的worker
            inspect = app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                worker_count = len(active_workers)
                return True, f"Celery服务正常 ({worker_count}个worker)"
            else:
                return False, "没有活跃的Celery Worker"
                
        except Exception as e:
            return False, f"Celery服务检查失败: {str(e)}"
    
    def check_system_resources(self) -> Dict[str, any]:
        """检查系统资源"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            self.logger.error(f"系统资源检查失败: {e}")
            return {}
    
    def restart_service(self, service_name: str, restart_command: str) -> bool:
        """重启服务"""
        try:
            self.logger.info(f"尝试重启服务: {service_name}")
            
            result = subprocess.run(
                restart_command.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.logger.info(f"服务重启成功: {service_name}")
                return True
            else:
                self.logger.error(f"服务重启失败: {service_name}, 错误: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"服务重启超时: {service_name}")
            return False
        except Exception as e:
            self.logger.error(f"服务重启异常: {service_name}, 错误: {str(e)}")
            return False
    
    def send_email_alert(self, subject: str, message: str):
        """发送邮件告警"""
        try:
            email_config = self.config['alerts']['email']
            
            if not email_config.get('enabled', False):
                return
            
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_emails'], text)
            server.quit()
            
            self.logger.info("邮件告警发送成功")
            
        except Exception as e:
            self.logger.error(f"邮件告警发送失败: {e}")
    
    def send_webhook_alert(self, data: Dict):
        """发送Webhook告警"""
        try:
            webhook_config = self.config['alerts']['webhook']
            
            if not webhook_config.get('enabled', False):
                return
            
            response = requests.post(
                webhook_config['url'],
                json=data,
                headers=webhook_config.get('headers', {}),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Webhook告警发送成功")
            else:
                self.logger.error(f"Webhook告警发送失败: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Webhook告警发送失败: {e}")
    
    def should_send_alert(self, service_name: str) -> bool:
        """判断是否应该发送告警"""
        now = datetime.now()
        monitoring_config = self.config['monitoring']
        
        # 检查告警冷却时间
        if service_name in self.alert_history:
            last_alert = self.alert_history[service_name]['last_alert']
            cooldown = timedelta(seconds=monitoring_config.get('alert_cooldown', 300))
            
            if now - last_alert < cooldown:
                return False
        
        return True
    
    def record_alert(self, service_name: str):
        """记录告警历史"""
        self.alert_history[service_name] = {
            'last_alert': datetime.now(),
            'count': self.alert_history.get(service_name, {}).get('count', 0) + 1
        }
    
    def monitor_services(self) -> Dict[str, Dict]:
        """监控所有服务"""
        results = {}
        services_config = self.config['services']
        
        # 检查API服务
        if 'api' in services_config:
            healthy, message = self.check_api_service(services_config['api'])
            results['api'] = {'healthy': healthy, 'message': message}
        
        # 检查MySQL服务
        if 'mysql' in services_config:
            healthy, message = self.check_mysql_service(services_config['mysql'])
            results['mysql'] = {'healthy': healthy, 'message': message}
        
        # 检查Redis服务
        if 'redis' in services_config:
            healthy, message = self.check_redis_service(services_config['redis'])
            results['redis'] = {'healthy': healthy, 'message': message}
        
        # 检查Celery服务
        if 'celery' in services_config:
            healthy, message = self.check_celery_service(services_config['celery'])
            results['celery'] = {'healthy': healthy, 'message': message}
        
        # 检查系统资源
        results['system'] = self.check_system_resources()
        
        return results
    
    def handle_service_failure(self, service_name: str, message: str):
        """处理服务故障"""
        monitoring_config = self.config['monitoring']
        services_config = self.config['services']
        
        self.logger.warning(f"服务异常: {service_name} - {message}")
        
        # 自动重启
        if monitoring_config.get('auto_restart', True):
            restart_command = services_config[service_name].get('restart_command')
            if restart_command:
                success = self.restart_service(service_name, restart_command)
                if success:
                    # 等待服务启动
                    time.sleep(30)
                    return
        
        # 发送告警
        if self.should_send_alert(service_name):
            alert_subject = f"医保SDK服务告警: {service_name}服务异常"
            alert_message = f"""
服务名称: {service_name}
异常信息: {message}
发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
服务器: {os.uname().nodename if hasattr(os, 'uname') else 'Windows'}

请及时处理！
            """
            
            self.send_email_alert(alert_subject, alert_message)
            self.send_webhook_alert({
                'service': service_name,
                'status': 'unhealthy',
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            self.record_alert(service_name)
    
    def run_once(self):
        """执行一次监控检查"""
        self.logger.info("开始服务监控检查...")
        
        results = self.monitor_services()
        
        # 处理服务状态
        for service_name, result in results.items():
            if service_name == 'system':
                continue
                
            if not result['healthy']:
                self.handle_service_failure(service_name, result['message'])
            else:
                self.logger.debug(f"服务正常: {service_name} - {result['message']}")
        
        # 检查系统资源
        system_info = results.get('system', {})
        if system_info:
            cpu_percent = system_info.get('cpu_percent', 0)
            memory_percent = system_info.get('memory_percent', 0)
            disk_percent = system_info.get('disk_percent', 0)
            
            # 资源告警阈值
            if cpu_percent > 80:
                self.logger.warning(f"CPU使用率过高: {cpu_percent}%")
            if memory_percent > 80:
                self.logger.warning(f"内存使用率过高: {memory_percent}%")
            if disk_percent > 80:
                self.logger.warning(f"磁盘使用率过高: {disk_percent}%")
        
        self.logger.info("服务监控检查完成")
    
    def run_daemon(self):
        """以守护进程模式运行"""
        monitoring_config = self.config['monitoring']
        check_interval = monitoring_config.get('check_interval', 60)
        
        self.logger.info(f"启动服务监控守护进程，检查间隔: {check_interval}秒")
        
        try:
            while True:
                self.run_once()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.logger.info("监控服务被用户中断")
        except Exception as e:
            self.logger.error(f"监控服务异常: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='医保接口SDK服务监控')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--once', action='store_true', help='执行一次检查后退出')
    
    args = parser.parse_args()
    
    try:
        monitor = ServiceMonitor(args.config)
        
        if args.once:
            monitor.run_once()
        else:
            monitor.run_daemon()
            
    except KeyboardInterrupt:
        print("\n监控服务被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"监控服务启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()