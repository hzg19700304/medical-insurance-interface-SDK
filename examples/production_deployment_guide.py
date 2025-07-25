#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK生产环境部署指南

本指南提供了医保接口SDK在生产环境中的完整部署方案，包括：
- 环境准备和依赖安装
- 数据库配置和初始化
- 应用配置和部署
- 监控和日志配置
- 安全加固和性能优化
- 故障排除和运维指南

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class DeploymentEnvironment:
    """部署环境配置"""
    name: str
    description: str
    requirements: Dict[str, str]
    services: List[str]
    ports: List[int]
    volumes: List[str]


class ProductionDeploymentGuide:
    """生产环境部署指南"""
    
    def __init__(self, deployment_dir: str = "deployment"):
        """
        初始化部署指南
        
        Args:
            deployment_dir: 部署文件目录
        """
        self.deployment_dir = Path(deployment_dir)
        self.deployment_dir.mkdir(exist_ok=True)
        
    def create_system_requirements_check(self):
        """创建系统要求检查脚本"""
        
        check_script = '''#!/bin/bash
# 医保接口SDK系统要求检查脚本

echo "医保接口SDK系统要求检查"
echo "=========================="

# 检查操作系统
echo "检查操作系统..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✓ 操作系统: Linux"
    OS_VERSION=$(lsb_release -d | cut -f2)
    echo "  版本: $OS_VERSION"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ 操作系统: macOS"
    OS_VERSION=$(sw_vers -productVersion)
    echo "  版本: $OS_VERSION"
else
    echo "✗ 不支持的操作系统: $OSTYPE"
    exit 1
fi

# 检查Python版本
echo "\\n检查Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 8 ]]; then
        echo "✓ Python版本: $PYTHON_VERSION"
    else
        echo "✗ Python版本过低: $PYTHON_VERSION (需要3.8+)"
        exit 1
    fi
else
    echo "✗ 未找到Python3"
    exit 1
fi

# 检查Docker
echo "\\n检查Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo "✓ Docker版本: $DOCKER_VERSION"
    
    # 检查Docker服务状态
    if docker info &> /dev/null; then
        echo "✓ Docker服务运行正常"
    else
        echo "✗ Docker服务未运行"
        exit 1
    fi
else
    echo "✗ 未找到Docker"
    exit 1
fi

# 检查Docker Compose
echo "\\n检查Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    echo "✓ Docker Compose版本: $COMPOSE_VERSION"
else
    echo "✗ 未找到Docker Compose"
    exit 1
fi

# 检查内存
echo "\\n检查系统内存..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
elif [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{printf "%.0f", $1/1024/1024}')
fi

if [[ $TOTAL_MEM -ge 4096 ]]; then
    echo "✓ 系统内存: ${TOTAL_MEM}MB"
else
    echo "⚠ 系统内存较低: ${TOTAL_MEM}MB (建议4GB+)"
fi

# 检查磁盘空间
echo "\\n检查磁盘空间..."
DISK_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "✓ 可用磁盘空间: $DISK_SPACE"

# 检查网络连接
echo "\\n检查网络连接..."
if ping -c 1 google.com &> /dev/null; then
    echo "✓ 网络连接正常"
else
    echo "⚠ 网络连接异常"
fi

# 检查端口占用
echo "\\n检查端口占用..."
PORTS=(3306 6379 8080 9090)
for port in "${PORTS[@]}"; do
    if lsof -i :$port &> /dev/null; then
        echo "⚠ 端口 $port 已被占用"
    else
        echo "✓ 端口 $port 可用"
    fi
done

echo "\\n系统要求检查完成！"
'''
        
        script_file = self.deployment_dir / "check_requirements.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(check_script)
        
        # 设置执行权限
        import stat
        os.chmod(script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✓ 创建系统要求检查脚本: {script_file}")

    def create_docker_deployment_files(self):
        """创建Docker部署文件"""
        
        # 创建生产环境Docker Compose文件
        docker_compose_prod = {
            "version": "3.8",
            "services": {
                "medical-insurance-sdk": {
                    "build": {
                        "context": "..",
                        "dockerfile": "Dockerfile.prod"
                    },
                    "container_name": "medical-insurance-sdk",
                    "restart": "unless-stopped",
                    "ports": ["8080:8080"],
                    "environment": [
                        "ENVIRONMENT=production",
                        "DB_HOST=mysql",
                        "DB_PORT=3306",
                        "DB_NAME=medical_insurance",
                        "DB_USER=medical_app",
                        "DB_PASSWORD=${DB_PASSWORD}",
                        "REDIS_HOST=redis",
                        "REDIS_PORT=6379",
                        "REDIS_PASSWORD=${REDIS_PASSWORD}",
                        "SECRET_KEY=${SECRET_KEY}",
                        "LOG_LEVEL=INFO"
                    ],
                    "depends_on": {
                        "mysql": {"condition": "service_healthy"},
                        "redis": {"condition": "service_healthy"}
                    },
                    "volumes": [
                        "./logs:/app/logs",
                        "./config:/app/config:ro"
                    ],
                    "networks": ["medical-network"],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "60s"
                    },
                    "deploy": {
                        "resources": {
                            "limits": {
                                "cpus": "2.0",
                                "memory": "2G"
                            },
                            "reservations": {
                                "cpus": "0.5",
                                "memory": "512M"
                            }
                        }
                    }
                },
                
                "mysql": {
                    "image": "mysql:8.0",
                    "container_name": "medical-mysql",
                    "restart": "unless-stopped",
                    "environment": [
                        "MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}",
                        "MYSQL_DATABASE=medical_insurance",
                        "MYSQL_USER=medical_app",
                        "MYSQL_PASSWORD=${DB_PASSWORD}",
                        "MYSQL_CHARSET=utf8mb4",
                        "MYSQL_COLLATION=utf8mb4_unicode_ci"
                    ],
                    "ports": ["3306:3306"],
                    "volumes": [
                        "mysql_data:/var/lib/mysql",
                        "./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro",
                        "./database/my.cnf:/etc/mysql/conf.d/my.cnf:ro"
                    ],
                    "networks": ["medical-network"],
                    "healthcheck": {
                        "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 5,
                        "start_period": "60s"
                    },
                    "deploy": {
                        "resources": {
                            "limits": {
                                "cpus": "2.0",
                                "memory": "2G"
                            },
                            "reservations": {
                                "cpus": "0.5",
                                "memory": "1G"
                            }
                        }
                    }
                },
                
                "redis": {
                    "image": "redis:7-alpine",
                    "container_name": "medical-redis",
                    "restart": "unless-stopped",
                    "ports": ["6379:6379"],
                    "volumes": [
                        "redis_data:/data",
                        "./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro"
                    ],
                    "networks": ["medical-network"],
                    "command": "redis-server /usr/local/etc/redis/redis.conf",
                    "healthcheck": {
                        "test": ["CMD", "redis-cli", "ping"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "30s"
                    },
                    "deploy": {
                        "resources": {
                            "limits": {
                                "cpus": "1.0",
                                "memory": "512M"
                            },
                            "reservations": {
                                "cpus": "0.1",
                                "memory": "128M"
                            }
                        }
                    }
                },
                
                "nginx": {
                    "image": "nginx:alpine",
                    "container_name": "medical-nginx",
                    "restart": "unless-stopped",
                    "ports": ["80:80", "443:443"],
                    "volumes": [
                        "./nginx/nginx.conf:/etc/nginx/nginx.conf:ro",
                        "./nginx/ssl:/etc/nginx/ssl:ro",
                        "./logs/nginx:/var/log/nginx"
                    ],
                    "networks": ["medical-network"],
                    "depends_on": ["medical-insurance-sdk"],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "medical-prometheus",
                    "restart": "unless-stopped",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
                        "prometheus_data:/prometheus"
                    ],
                    "networks": ["medical-network"],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=200h",
                        "--web.enable-lifecycle"
                    ]
                },
                
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "medical-grafana",
                    "restart": "unless-stopped",
                    "ports": ["3000:3000"],
                    "environment": [
                        "GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}",
                        "GF_USERS_ALLOW_SIGN_UP=false"
                    ],
                    "volumes": [
                        "grafana_data:/var/lib/grafana",
                        "./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro",
                        "./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro"
                    ],
                    "networks": ["medical-network"],
                    "depends_on": ["prometheus"]
                }
            },
            
            "networks": {
                "medical-network": {
                    "driver": "bridge"
                }
            },
            
            "volumes": {
                "mysql_data": {},
                "redis_data": {},
                "prometheus_data": {},
                "grafana_data": {}
            }
        }
        
        compose_file = self.deployment_dir / "docker-compose.prod.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            yaml.dump(docker_compose_prod, f, default_flow_style=False)
        
        print(f"✓ 创建生产环境Docker Compose文件: {compose_file}")

    def create_nginx_config(self):
        """创建Nginx配置文件"""
        
        nginx_dir = self.deployment_dir / "nginx"
        nginx_dir.mkdir(exist_ok=True)
        
        nginx_config = '''user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    
    # 基本设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # 上游服务器
    upstream medical_backend {
        server medical-insurance-sdk:8080 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    # HTTP服务器（重定向到HTTPS）
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
    
    # HTTPS服务器
    server {
        listen 443 ssl http2;
        server_name your-domain.com;
        
        # SSL配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;
        
        # 现代SSL配置
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;
        
        # 安全头
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy "strict-origin-when-cross-origin";
        
        # 健康检查
        location /health {
            proxy_pass http://medical_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            access_log off;
        }
        
        # API接口
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://medical_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # 登录接口（更严格的限流）
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://medical_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 静态文件
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # 默认位置
        location / {
            return 404;
        }
    }
}
'''
        
        config_file = nginx_dir / "nginx.conf"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(nginx_config)
        
        print(f"✓ 创建Nginx配置文件: {config_file}")

    def create_monitoring_config(self):
        """创建监控配置文件"""
        
        monitoring_dir = self.deployment_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        # Prometheus配置
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [],
            "scrape_configs": [
                {
                    "job_name": "medical-insurance-sdk",
                    "static_configs": [
                        {"targets": ["medical-insurance-sdk:8080"]}
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "30s"
                },
                {
                    "job_name": "mysql",
                    "static_configs": [
                        {"targets": ["mysql:3306"]}
                    ]
                },
                {
                    "job_name": "redis",
                    "static_configs": [
                        {"targets": ["redis:6379"]}
                    ]
                },
                {
                    "job_name": "nginx",
                    "static_configs": [
                        {"targets": ["nginx:80"]}
                    ]
                }
            ]
        }
        
        prometheus_file = monitoring_dir / "prometheus.yml"
        with open(prometheus_file, 'w', encoding='utf-8') as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        # Grafana数据源配置
        grafana_dir = monitoring_dir / "grafana"
        grafana_dir.mkdir(exist_ok=True)
        
        datasources_dir = grafana_dir / "datasources"
        datasources_dir.mkdir(exist_ok=True)
        
        datasource_config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://prometheus:9090",
                    "isDefault": True
                }
            ]
        }
        
        datasource_file = datasources_dir / "prometheus.yml"
        with open(datasource_file, 'w', encoding='utf-8') as f:
            yaml.dump(datasource_config, f, default_flow_style=False)
        
        print(f"✓ 创建监控配置文件: {prometheus_file}, {datasource_file}")

    def create_deployment_scripts(self):
        """创建部署脚本"""
        
        # 创建部署脚本
        deploy_script = '''#!/bin/bash
# 医保接口SDK生产环境部署脚本

set -e

echo "医保接口SDK生产环境部署"
echo "========================"

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "✗ 未找到.env文件，请先创建并配置环境变量"
    exit 1
fi

# 加载环境变量
source .env

# 检查必需的环境变量
required_vars=("DB_PASSWORD" "MYSQL_ROOT_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "✗ 环境变量 $var 未设置"
        exit 1
    fi
done

echo "✓ 环境变量检查通过"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs/nginx
mkdir -p config
mkdir -p database
mkdir -p redis
mkdir -p nginx/ssl

# 检查SSL证书
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    echo "⚠ SSL证书未找到，将生成自签名证书（仅用于测试）"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
        -keyout nginx/ssl/key.pem \\
        -out nginx/ssl/cert.pem \\
        -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
fi

# 构建镜像
echo "构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build

# 启动服务
echo "启动服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 检查服务状态
echo "检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 健康检查
echo "执行健康检查..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✓ 应用健康检查通过"
else
    echo "✗ 应用健康检查失败"
    docker-compose -f docker-compose.prod.yml logs medical-insurance-sdk
    exit 1
fi

echo "✓ 部署完成！"
echo "应用访问地址: https://localhost"
echo "监控面板: http://localhost:3000 (admin/admin)"
echo "Prometheus: http://localhost:9090"
'''
        
        deploy_file = self.deployment_dir / "deploy.sh"
        with open(deploy_file, 'w', encoding='utf-8') as f:
            f.write(deploy_script)
        
        # 设置执行权限
        import stat
        os.chmod(deploy_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        # 创建停止脚本
        stop_script = '''#!/bin/bash
# 医保接口SDK服务停止脚本

echo "停止医保接口SDK服务..."
docker-compose -f docker-compose.prod.yml down

echo "清理未使用的镜像..."
docker image prune -f

echo "✓ 服务已停止"
'''
        
        stop_file = self.deployment_dir / "stop.sh"
        with open(stop_file, 'w', encoding='utf-8') as f:
            f.write(stop_script)
        
        os.chmod(stop_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        # 创建更新脚本
        update_script = '''#!/bin/bash
# 医保接口SDK服务更新脚本

echo "更新医保接口SDK服务..."

# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose -f docker-compose.prod.yml build --no-cache

# 滚动更新
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# 清理旧镜像
docker image prune -f

echo "✓ 服务更新完成"
'''
        
        update_file = self.deployment_dir / "update.sh"
        with open(update_file, 'w', encoding='utf-8') as f:
            f.write(update_script)
        
        os.chmod(update_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✓ 创建部署脚本: {deploy_file}, {stop_file}, {update_file}")

    def create_backup_scripts(self):
        """创建备份脚本"""
        
        backup_script = '''#!/bin/bash
# 医保接口SDK数据备份脚本

BACKUP_DIR="/backup/medical-insurance-sdk"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="medical_insurance_backup_$DATE"

echo "开始数据备份..."

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份MySQL数据库
echo "备份MySQL数据库..."
docker exec medical-mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD medical_insurance > $BACKUP_DIR/${BACKUP_FILE}.sql

# 备份Redis数据
echo "备份Redis数据..."
docker exec medical-redis redis-cli --rdb $BACKUP_DIR/${BACKUP_FILE}.rdb

# 备份配置文件
echo "备份配置文件..."
tar -czf $BACKUP_DIR/${BACKUP_FILE}_config.tar.gz config/ nginx/ monitoring/

# 备份日志文件
echo "备份日志文件..."
tar -czf $BACKUP_DIR/${BACKUP_FILE}_logs.tar.gz logs/

# 清理7天前的备份
find $BACKUP_DIR -name "medical_insurance_backup_*" -mtime +7 -delete

echo "✓ 备份完成: $BACKUP_DIR/${BACKUP_FILE}*"
'''
        
        backup_file = self.deployment_dir / "backup.sh"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(backup_script)
        
        import stat
        os.chmod(backup_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        # 创建恢复脚本
        restore_script = '''#!/bin/bash
# 医保接口SDK数据恢复脚本

if [ $# -ne 1 ]; then
    echo "用法: $0 <backup_date>"
    echo "示例: $0 20240115_143000"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/backup/medical-insurance-sdk"
BACKUP_FILE="medical_insurance_backup_$BACKUP_DATE"

echo "开始数据恢复..."

# 检查备份文件是否存在
if [ ! -f "$BACKUP_DIR/${BACKUP_FILE}.sql" ]; then
    echo "✗ 备份文件不存在: $BACKUP_DIR/${BACKUP_FILE}.sql"
    exit 1
fi

# 停止服务
echo "停止服务..."
docker-compose -f docker-compose.prod.yml stop medical-insurance-sdk

# 恢复MySQL数据库
echo "恢复MySQL数据库..."
docker exec -i medical-mysql mysql -u root -p$MYSQL_ROOT_PASSWORD medical_insurance < $BACKUP_DIR/${BACKUP_FILE}.sql

# 恢复Redis数据
if [ -f "$BACKUP_DIR/${BACKUP_FILE}.rdb" ]; then
    echo "恢复Redis数据..."
    docker-compose -f docker-compose.prod.yml stop redis
    docker cp $BACKUP_DIR/${BACKUP_FILE}.rdb medical-redis:/data/dump.rdb
    docker-compose -f docker-compose.prod.yml start redis
fi

# 恢复配置文件
if [ -f "$BACKUP_DIR/${BACKUP_FILE}_config.tar.gz" ]; then
    echo "恢复配置文件..."
    tar -xzf $BACKUP_DIR/${BACKUP_FILE}_config.tar.gz
fi

# 启动服务
echo "启动服务..."
docker-compose -f docker-compose.prod.yml start medical-insurance-sdk

echo "✓ 数据恢复完成"
'''
        
        restore_file = self.deployment_dir / "restore.sh"
        with open(restore_file, 'w', encoding='utf-8') as f:
            f.write(restore_script)
        
        os.chmod(restore_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✓ 创建备份脚本: {backup_file}, {restore_file}")

    def create_maintenance_scripts(self):
        """创建维护脚本"""
        
        # 创建日志清理脚本
        log_cleanup_script = '''#!/bin/bash
# 日志清理脚本

LOG_DIR="./logs"
RETENTION_DAYS=30

echo "清理${RETENTION_DAYS}天前的日志文件..."

# 清理应用日志
find $LOG_DIR -name "*.log" -mtime +$RETENTION_DAYS -delete
find $LOG_DIR -name "*.log.*" -mtime +$RETENTION_DAYS -delete

# 清理Nginx日志
find $LOG_DIR/nginx -name "*.log" -mtime +$RETENTION_DAYS -delete

# 压缩7天前的日志
find $LOG_DIR -name "*.log" -mtime +7 -exec gzip {} \\;

echo "✓ 日志清理完成"
'''
        
        cleanup_file = self.deployment_dir / "cleanup_logs.sh"
        with open(cleanup_file, 'w', encoding='utf-8') as f:
            f.write(log_cleanup_script)
        
        import stat
        os.chmod(cleanup_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        # 创建健康检查脚本
        health_check_script = '''#!/bin/bash
# 系统健康检查脚本

echo "医保接口SDK系统健康检查"
echo "======================="

# 检查容器状态
echo "检查容器状态..."
docker-compose -f docker-compose.prod.yml ps

# 检查服务健康状态
services=("medical-insurance-sdk" "mysql" "redis" "nginx")
for service in "${services[@]}"; do
    health=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null || echo "no-healthcheck")
    if [ "$health" = "healthy" ] || [ "$health" = "no-healthcheck" ]; then
        echo "✓ $service: $health"
    else
        echo "✗ $service: $health"
    fi
done

# 检查端口连通性
echo "\\n检查端口连通性..."
ports=(80 443 3306 6379 8080)
for port in "${ports[@]}"; do
    if nc -z localhost $port; then
        echo "✓ 端口 $port: 可访问"
    else
        echo "✗ 端口 $port: 不可访问"
    fi
done

# 检查磁盘空间
echo "\\n检查磁盘空间..."
df -h | grep -E "(Filesystem|/dev/)"

# 检查内存使用
echo "\\n检查内存使用..."
free -h

# 检查CPU使用
echo "\\n检查CPU使用..."
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1

echo "\\n健康检查完成"
'''
        
        health_file = self.deployment_dir / "health_check.sh"
        with open(health_file, 'w', encoding='utf-8') as f:
            f.write(health_check_script)
        
        os.chmod(health_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"✓ 创建维护脚本: {cleanup_file}, {health_file}")

    def create_environment_template(self):
        """创建环境变量模板"""
        
        env_template = '''# 医保接口SDK生产环境配置
# 请复制此文件为 .env 并填入实际值

# 数据库配置
DB_PASSWORD=your_secure_database_password_here
MYSQL_ROOT_PASSWORD=your_secure_mysql_root_password_here

# Redis配置
REDIS_PASSWORD=your_secure_redis_password_here

# 应用配置
SECRET_KEY=your_secret_key_at_least_32_characters_long
ENVIRONMENT=production

# 医保接口配置
ORG_H43010000001_SECRET=your_hunan_org_secret_here
ORG_H44010000001_SECRET=your_guangdong_org_secret_here
ORG_H31010000001_SECRET=your_shanghai_org_secret_here

# 监控配置
GRAFANA_PASSWORD=your_grafana_admin_password_here
ENABLE_MONITORING=true
METRICS_PORT=9090

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/logs/medical_insurance_sdk.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# SSL配置
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# 性能配置
MAX_WORKERS=4
WORKER_CONNECTIONS=1000
DB_POOL_SIZE=20
REDIS_POOL_SIZE=50

# 安全配置
ALLOWED_HOSTS=your-domain.com,localhost
CORS_ORIGINS=https://your-domain.com
SESSION_TIMEOUT=1800
MAX_LOGIN_ATTEMPTS=5

# 备份配置
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"
'''
        
        env_file = self.deployment_dir / ".env.template"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        print(f"✓ 创建环境变量模板: {env_file}")

    def create_deployment_guide_document(self):
        """创建部署指南文档"""
        
        guide_content = '''# 医保接口SDK生产环境部署指南

## 概述

本指南提供了医保接口SDK在生产环境中的完整部署方案，包括环境准备、服务配置、部署执行、监控设置和运维管理。

## 系统要求

### 硬件要求
- CPU: 4核心以上
- 内存: 8GB以上
- 磁盘: 100GB以上可用空间
- 网络: 稳定的互联网连接

### 软件要求
- 操作系统: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- Docker: 20.10+
- Docker Compose: 2.0+
- Python: 3.8+

## 部署步骤

### 1. 环境准备

```bash
# 检查系统要求
./check_requirements.sh

# 创建部署用户
sudo useradd -m -s /bin/bash medical
sudo usermod -aG docker medical

# 切换到部署用户
sudo su - medical
```

### 2. 代码部署

```bash
# 克隆代码仓库
git clone https://github.com/your-org/medical-insurance-sdk.git
cd medical-insurance-sdk/deployment

# 配置环境变量
cp .env.template .env
vim .env  # 填入实际配置值
```

### 3. SSL证书配置

```bash
# 方式1: 使用Let's Encrypt（推荐）
sudo certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 方式2: 使用自签名证书（仅测试）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
    -keyout nginx/ssl/key.pem \\
    -out nginx/ssl/cert.pem
```

### 4. 执行部署

```bash
# 执行部署脚本
./deploy.sh

# 检查部署状态
./health_check.sh
```

### 5. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 测试API接口
curl -k https://localhost/health

# 访问监控面板
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

## 配置说明

### 数据库配置

MySQL配置文件位于 `database/my.cnf`，主要配置项：

```ini
[mysqld]
max_connections = 1000
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
slow_query_log = 1
long_query_time = 2
```

### Redis配置

Redis配置文件位于 `redis/redis.conf`，主要配置项：

```
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1 300 10 60 10000
```

### Nginx配置

Nginx配置文件位于 `nginx/nginx.conf`，包含：
- SSL/TLS配置
- 反向代理设置
- 限流配置
- 安全头设置

## 监控和日志

### 监控系统

- **Prometheus**: 指标收集和存储
- **Grafana**: 可视化监控面板
- **健康检查**: 自动服务健康监控

### 日志管理

- 应用日志: `/logs/medical_insurance_sdk.log`
- Nginx日志: `/logs/nginx/`
- 容器日志: `docker-compose logs`

### 日志轮转

```bash
# 手动清理日志
./cleanup_logs.sh

# 设置定时任务
crontab -e
0 2 * * * /path/to/cleanup_logs.sh
```

## 备份和恢复

### 数据备份

```bash
# 手动备份
./backup.sh

# 设置定时备份
crontab -e
0 2 * * * /path/to/backup.sh
```

### 数据恢复

```bash
# 恢复指定日期的备份
./restore.sh 20240115_143000
```

## 运维管理

### 服务管理

```bash
# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 停止服务
./stop.sh

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 更新服务
./update.sh
```

### 扩容和缩容

```bash
# 扩容应用实例
docker-compose -f docker-compose.prod.yml up -d --scale medical-insurance-sdk=3

# 查看实例状态
docker-compose -f docker-compose.prod.yml ps
```

### 故障排除

#### 常见问题

1. **服务启动失败**
   ```bash
   # 查看日志
   docker-compose -f docker-compose.prod.yml logs medical-insurance-sdk
   
   # 检查配置
   docker-compose -f docker-compose.prod.yml config
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker exec medical-mysql mysqladmin ping
   
   # 查看数据库日志
   docker logs medical-mysql
   ```

3. **Redis连接失败**
   ```bash
   # 检查Redis状态
   docker exec medical-redis redis-cli ping
   
   # 查看Redis日志
   docker logs medical-redis
   ```

#### 性能调优

1. **数据库优化**
   - 调整连接池大小
   - 优化查询索引
   - 配置缓存参数

2. **应用优化**
   - 调整工作进程数
   - 配置内存限制
   - 启用缓存机制

3. **网络优化**
   - 配置Nginx缓存
   - 启用Gzip压缩
   - 调整超时参数

## 安全加固

### 系统安全

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 配置防火墙
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 禁用不必要的服务
sudo systemctl disable apache2
sudo systemctl disable sendmail
```

### 应用安全

- 定期更新密钥和证书
- 启用访问日志审计
- 配置IP白名单
- 实施最小权限原则

### 数据安全

- 数据库加密存储
- 传输层加密
- 定期安全扫描
- 备份数据加密

## 维护计划

### 日常维护

- 检查服务状态
- 监控系统资源
- 查看错误日志
- 验证备份完整性

### 定期维护

- 更新系统补丁
- 轮换密钥证书
- 清理历史数据
- 性能调优分析

### 应急响应

- 建立故障响应流程
- 准备回滚方案
- 配置告警通知
- 定期演练恢复

## 联系支持

如有问题，请联系技术支持：
- 邮箱: support@your-org.com
- 电话: 400-xxx-xxxx
- 文档: https://docs.your-org.com
'''
        
        guide_file = self.deployment_dir / "DEPLOYMENT_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✓ 创建部署指南文档: {guide_file}")

    def generate_all_deployment_files(self):
        """生成所有部署文件"""
        print("开始生成医保接口SDK生产环境部署文件...")
        print("=" * 60)
        
        try:
            # 创建系统要求检查脚本
            self.create_system_requirements_check()
            
            # 创建Docker部署文件
            self.create_docker_deployment_files()
            
            # 创建Nginx配置
            self.create_nginx_config()
            
            # 创建监控配置
            self.create_monitoring_config()
            
            # 创建部署脚本
            self.create_deployment_scripts()
            
            # 创建备份脚本
            self.create_backup_scripts()
            
            # 创建维护脚本
            self.create_maintenance_scripts()
            
            # 创建环境变量模板
            self.create_environment_template()
            
            # 创建部署指南文档
            self.create_deployment_guide_document()
            
            print("\n" + "=" * 60)
            print("✓ 所有部署文件生成完成！")
            print(f"部署文件目录: {self.deployment_dir.absolute()}")
            
            # 显示生成的文件列表
            print("\n生成的文件列表:")
            for file_path in sorted(self.deployment_dir.rglob("*")):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.deployment_dir)
                    print(f"  - {relative_path}")
            
            print("\n部署步骤:")
            print("1. 复制 .env.template 为 .env 并填入实际配置值")
            print("2. 配置SSL证书到 nginx/ssl/ 目录")
            print("3. 运行 ./check_requirements.sh 检查系统要求")
            print("4. 运行 ./deploy.sh 执行部署")
            print("5. 运行 ./health_check.sh 验证部署")
            print("6. 访问 https://localhost 测试应用")
            
        except Exception as e:
            print(f"✗ 部署文件生成失败: {str(e)}")


def main():
    """主函数"""
    print("医保接口SDK生产环境部署指南")
    print("=" * 80)
    
    # 创建部署指南
    deployment_guide = ProductionDeploymentGuide()
    
    # 生成所有部署文件
    deployment_guide.generate_all_deployment_files()


if __name__ == "__main__":
    main()