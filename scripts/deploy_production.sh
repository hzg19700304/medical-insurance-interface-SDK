#!/bin/bash
# 医保接口SDK生产环境部署脚本
# 使用方法: ./scripts/deploy_production.sh [--backup] [--no-migrate] [--config-file=path]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
BACKUP_ENABLED=false
MIGRATE_ENABLED=true
CONFIG_FILE=""
DEPLOYMENT_ENV="production"
PROJECT_NAME="medical-insurance-sdk"

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

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup)
                BACKUP_ENABLED=true
                shift
                ;;
            --no-migrate)
                MIGRATE_ENABLED=false
                shift
                ;;
            --config-file=*)
                CONFIG_FILE="${1#*=}"
                shift
                ;;
            --env=*)
                DEPLOYMENT_ENV="${1#*=}"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 显示帮助信息
show_help() {
    cat << EOF
医保接口SDK生产环境部署脚本

使用方法:
    $0 [选项]

选项:
    --backup              部署前备份数据库
    --no-migrate          跳过数据库迁移
    --config-file=PATH    指定配置文件路径
    --env=ENV            指定部署环境 (默认: production)
    -h, --help           显示此帮助信息

示例:
    $0 --backup --config-file=/path/to/config.env
    $0 --no-migrate --env=staging
EOF
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3未安装"
        exit 1
    fi
    
    # 检查必要的文件
    required_files=(
        "docker-compose.prod.yml"
        "Dockerfile.prod"
        "scripts/migrate_database.py"
        "scripts/docker-health-check.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "缺少必要文件: $file"
            exit 1
        fi
    done
    
    log_success "系统要求检查通过"
}

# 加载配置
load_config() {
    log_info "加载配置..."
    
    if [ -n "$CONFIG_FILE" ] && [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        log_info "已加载配置文件: $CONFIG_FILE"
    elif [ -f ".env.production" ]; then
        source ".env.production"
        log_info "已加载默认生产配置: .env.production"
    elif [ -f ".env" ]; then
        source ".env"
        log_warning "使用默认配置文件: .env"
    else
        log_error "未找到配置文件"
        exit 1
    fi
    
    # 验证必要的环境变量
    required_vars=(
        "DB_HOST"
        "DB_USERNAME"
        "DB_PASSWORD"
        "DB_DATABASE"
        "REDIS_HOST"
        "REDIS_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "缺少必要的环境变量: $var"
            exit 1
        fi
    done
    
    log_success "配置加载完成"
}

# 创建必要的目录和文件
prepare_deployment() {
    log_info "准备部署环境..."
    
    # 创建目录
    mkdir -p logs data secrets docker/nginx/ssl
    
    # 生成密钥文件（如果不存在）
    if [ ! -f "secrets/mysql_root_password.txt" ]; then
        openssl rand -base64 32 > secrets/mysql_root_password.txt
        chmod 600 secrets/mysql_root_password.txt
        log_info "已生成MySQL root密码"
    fi
    
    if [ ! -f "secrets/mysql_password.txt" ]; then
        echo "$DB_PASSWORD" > secrets/mysql_password.txt
        chmod 600 secrets/mysql_password.txt
        log_info "已设置MySQL用户密码"
    fi
    
    if [ ! -f "secrets/redis_password.txt" ]; then
        echo "$REDIS_PASSWORD" > secrets/redis_password.txt
        chmod 600 secrets/redis_password.txt
        log_info "已设置Redis密码"
    fi
    
    # 生成SSL证书（如果不存在）
    if [ ! -f "docker/nginx/ssl/server.crt" ]; then
        log_info "生成SSL证书..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout docker/nginx/ssl/server.key \
            -out docker/nginx/ssl/server.crt \
            -subj "/C=CN/ST=Hunan/L=Changsha/O=Medical/OU=IT/CN=localhost"
        log_success "SSL证书生成完成"
    fi
    
    log_success "部署环境准备完成"
}

# 备份数据库
backup_database() {
    if [ "$BACKUP_ENABLED" = true ]; then
        log_info "开始备份数据库..."
        
        backup_file="backup_${DB_DATABASE}_$(date +%Y%m%d_%H%M%S).sql"
        
        python3 scripts/migrate_database.py backup \
            --host="$DB_HOST" \
            --port="${DB_PORT:-3306}" \
            --user="$DB_USERNAME" \
            --password="$DB_PASSWORD" \
            --database="$DB_DATABASE" \
            --backup-file="$backup_file"
        
        if [ $? -eq 0 ]; then
            log_success "数据库备份完成: $backup_file"
        else
            log_error "数据库备份失败"
            exit 1
        fi
    else
        log_info "跳过数据库备份"
    fi
}

# 数据库迁移
migrate_database() {
    if [ "$MIGRATE_ENABLED" = true ]; then
        log_info "开始数据库迁移..."
        
        python3 scripts/migrate_database.py init \
            --host="$DB_HOST" \
            --port="${DB_PORT:-3306}" \
            --user="$DB_USERNAME" \
            --password="$DB_PASSWORD" \
            --database="$DB_DATABASE"
        
        if [ $? -eq 0 ]; then
            log_success "数据库迁移完成"
        else
            log_error "数据库迁移失败"
            exit 1
        fi
    else
        log_info "跳过数据库迁移"
    fi
}

# 构建和部署应用
deploy_application() {
    log_info "开始部署应用..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose -f docker-compose.prod.yml build
    
    if [ $? -ne 0 ]; then
        log_error "Docker镜像构建失败"
        exit 1
    fi
    
    # 启动服务
    log_info "启动服务..."
    docker-compose -f docker-compose.prod.yml up -d
    
    if [ $? -ne 0 ]; then
        log_error "服务启动失败"
        exit 1
    fi
    
    log_success "应用部署完成"
}

# 健康检查
health_check() {
    log_info "开始健康检查..."
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 执行健康检查
    python3 scripts/docker-health-check.py \
        --wait \
        --max-wait=300 \
        --mysql-host="$DB_HOST" \
        --mysql-port="${DB_PORT:-3306}" \
        --redis-host="$REDIS_HOST" \
        --redis-port="${REDIS_PORT:-6379}" \
        --api-url="http://localhost:8000"
    
    if [ $? -eq 0 ]; then
        log_success "健康检查通过"
    else
        log_error "健康检查失败"
        
        # 显示服务状态
        log_info "服务状态:"
        docker-compose -f docker-compose.prod.yml ps
        
        # 显示日志
        log_info "服务日志:"
        docker-compose -f docker-compose.prod.yml logs --tail=50
        
        exit 1
    fi
}

# 验证部署
validate_deployment() {
    log_info "验证部署..."
    
    # 验证数据库
    python3 scripts/migrate_database.py validate \
        --host="$DB_HOST" \
        --port="${DB_PORT:-3306}" \
        --user="$DB_USERNAME" \
        --password="$DB_PASSWORD" \
        --database="$DB_DATABASE"
    
    if [ $? -ne 0 ]; then
        log_error "数据库验证失败"
        exit 1
    fi
    
    # 验证API服务
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$response" = "200" ]; then
        log_success "API服务验证通过"
    else
        log_error "API服务验证失败 (HTTP $response)"
        exit 1
    fi
    
    log_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    
    echo ""
    echo "服务访问地址:"
    echo "  - API服务: https://localhost"
    echo "  - 健康检查: https://localhost/health"
    echo ""
    
    echo "服务状态:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "有用的命令:"
    echo "  - 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  - 重启服务: docker-compose -f docker-compose.prod.yml restart"
    echo "  - 停止服务: docker-compose -f docker-compose.prod.yml down"
    echo "  - 健康检查: python3 scripts/docker-health-check.py"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 错误处理
error_handler() {
    log_error "部署过程中发生错误，正在清理..."
    cleanup
    exit 1
}

# 设置错误处理
trap error_handler ERR

# 主函数
main() {
    log_info "开始生产环境部署..."
    log_info "部署环境: $DEPLOYMENT_ENV"
    
    # 解析参数
    parse_args "$@"
    
    # 执行部署步骤
    check_requirements
    load_config
    prepare_deployment
    backup_database
    migrate_database
    deploy_application
    health_check
    validate_deployment
    show_deployment_info
    
    log_success "生产环境部署完成！"
}

# 执行主函数
main "$@"