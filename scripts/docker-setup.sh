#!/bin/bash
# 医保接口SDK Docker环境快速搭建脚本
# 使用方法: ./scripts/docker-setup.sh [dev|prod]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p docker/mysql
    mkdir -p docker/redis
    mkdir -p docker/nginx/ssl
    mkdir -p secrets
    
    log_success "目录创建完成"
}

# 生成SSL证书（自签名，仅用于开发）
generate_ssl_cert() {
    log_info "生成SSL证书..."
    
    if [ ! -f "docker/nginx/ssl/server.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout docker/nginx/ssl/server.key \
            -out docker/nginx/ssl/server.crt \
            -subj "/C=CN/ST=Hunan/L=Changsha/O=Medical/OU=IT/CN=localhost"
        
        log_success "SSL证书生成完成"
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 生成密钥文件
generate_secrets() {
    log_info "生成密钥文件..."
    
    # MySQL root密码
    if [ ! -f "secrets/mysql_root_password.txt" ]; then
        echo "$(openssl rand -base64 32)" > secrets/mysql_root_password.txt
        log_success "MySQL root密码已生成"
    fi
    
    # MySQL用户密码
    if [ ! -f "secrets/mysql_password.txt" ]; then
        echo "$(openssl rand -base64 32)" > secrets/mysql_password.txt
        log_success "MySQL用户密码已生成"
    fi
    
    # Redis密码
    if [ ! -f "secrets/redis_password.txt" ]; then
        echo "$(openssl rand -base64 32)" > secrets/redis_password.txt
        log_success "Redis密码已生成"
    fi
    
    # 设置文件权限
    chmod 600 secrets/*.txt
}

# 创建环境配置文件
create_env_file() {
    log_info "创建环境配置文件..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_success "环境配置文件已创建，请根据需要修改.env文件"
    else
        log_info "环境配置文件已存在"
    fi
}

# 构建和启动开发环境
start_dev_environment() {
    log_info "启动开发环境..."
    
    # 停止现有容器
    docker-compose down
    
    # 构建镜像
    docker-compose build
    
    # 启动服务
    docker-compose up -d
    
    log_success "开发环境启动完成"
    log_info "服务访问地址："
    log_info "  - 医保SDK API: http://localhost:8000"
    log_info "  - Flower监控: http://localhost:5555"
    log_info "  - MySQL: localhost:3306"
    log_info "  - Redis: localhost:6379"
}

# 构建和启动生产环境
start_prod_environment() {
    log_info "启动生产环境..."
    
    # 检查密钥文件
    if [ ! -f "secrets/mysql_root_password.txt" ] || [ ! -f "secrets/mysql_password.txt" ] || [ ! -f "secrets/redis_password.txt" ]; then
        log_error "生产环境需要密钥文件，请先运行生成密钥步骤"
        exit 1
    fi
    
    # 停止现有容器
    docker-compose -f docker-compose.prod.yml down
    
    # 构建镜像
    docker-compose -f docker-compose.prod.yml build
    
    # 启动服务
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "生产环境启动完成"
    log_info "服务访问地址："
    log_info "  - 医保SDK API: https://localhost"
    log_info "  - HTTP会自动重定向到HTTPS"
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    
    if [ "$1" = "prod" ]; then
        docker-compose -f docker-compose.prod.yml ps
    else
        docker-compose ps
    fi
}

# 显示日志
show_logs() {
    log_info "显示服务日志："
    
    if [ "$1" = "prod" ]; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
}

# 清理环境
cleanup() {
    log_info "清理Docker环境..."
    
    # 停止并删除容器
    docker-compose down -v
    docker-compose -f docker-compose.prod.yml down -v
    
    # 删除镜像
    docker rmi $(docker images "medical_insurance*" -q) 2>/dev/null || true
    
    # 清理未使用的资源
    docker system prune -f
    
    log_success "环境清理完成"
}

# 主函数
main() {
    local environment=${1:-dev}
    
    log_info "医保接口SDK Docker环境搭建脚本"
    log_info "环境类型: $environment"
    
    # 检查Docker环境
    check_docker
    
    # 创建目录
    create_directories
    
    # 创建环境配置
    create_env_file
    
    case $environment in
        "dev")
            start_dev_environment
            show_status "dev"
            ;;
        "prod")
            generate_ssl_cert
            generate_secrets
            start_prod_environment
            show_status "prod"
            ;;
        "status")
            show_status "dev"
            ;;
        "logs")
            show_logs "dev"
            ;;
        "logs-prod")
            show_logs "prod"
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            log_error "未知的环境类型: $environment"
            log_info "使用方法: $0 [dev|prod|status|logs|logs-prod|cleanup]"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"