@echo off
REM 医保接口SDK Docker环境快速搭建脚本 - Windows版本
REM 使用方法: scripts\docker-setup.bat [dev|prod|status|logs|cleanup]

setlocal enabledelayedexpansion

REM 设置颜色
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 获取环境参数
set "ENVIRONMENT=%1"
if "%ENVIRONMENT%"=="" set "ENVIRONMENT=dev"

echo %BLUE%[INFO]%NC% Medical Insurance SDK Docker Setup Script
echo %BLUE%[INFO]%NC% Environment: %ENVIRONMENT%

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker未安装，请先安装Docker Desktop
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker Compose未安装，请先安装Docker Compose
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Docker环境检查通过

REM 创建必要的目录
echo %BLUE%[INFO]%NC% Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "docker\mysql" mkdir docker\mysql
if not exist "docker\redis" mkdir docker\redis
if not exist "docker\nginx\ssl" mkdir docker\nginx\ssl
if not exist "secrets" mkdir secrets
echo %GREEN%[SUCCESS]%NC% Directories created successfully

REM 创建环境配置文件
if not exist ".env" (
    echo %BLUE%[INFO]%NC% 创建环境配置文件...
    copy .env.example .env >nul
    echo %GREEN%[SUCCESS]%NC% 环境配置文件已创建，请根据需要修改.env文件
) else (
    echo %BLUE%[INFO]%NC% 环境配置文件已存在
)

REM 根据环境类型执行相应操作
if "%ENVIRONMENT%"=="dev" goto :start_dev
if "%ENVIRONMENT%"=="prod" goto :start_prod
if "%ENVIRONMENT%"=="status" goto :show_status
if "%ENVIRONMENT%"=="logs" goto :show_logs
if "%ENVIRONMENT%"=="cleanup" goto :cleanup
goto :usage

:start_dev
echo %BLUE%[INFO]%NC% Starting development environment...
docker-compose down
docker-compose build
docker-compose up -d
echo %GREEN%[SUCCESS]%NC% Development environment started successfully
echo %BLUE%[INFO]%NC% Service access addresses:
echo %BLUE%[INFO]%NC%   - Medical SDK API: http://localhost:8000
echo %BLUE%[INFO]%NC%   - Flower Monitor: http://localhost:5555
echo %BLUE%[INFO]%NC%   - MySQL: localhost:3307
echo %BLUE%[INFO]%NC%   - Redis: localhost:6379
goto :show_status

:start_prod
echo %BLUE%[INFO]%NC% 启动生产环境...
REM 检查密钥文件
if not exist "secrets\mysql_root_password.txt" (
    echo %BLUE%[INFO]%NC% 生成MySQL root密码...
    powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32, 8)" > secrets\mysql_root_password.txt
)
if not exist "secrets\mysql_password.txt" (
    echo %BLUE%[INFO]%NC% 生成MySQL用户密码...
    powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32, 8)" > secrets\mysql_password.txt
)
if not exist "secrets\redis_password.txt" (
    echo %BLUE%[INFO]%NC% 生成Redis密码...
    powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32, 8)" > secrets\redis_password.txt
)

docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
echo %GREEN%[SUCCESS]%NC% 生产环境启动完成
echo %BLUE%[INFO]%NC% 服务访问地址：
echo %BLUE%[INFO]%NC%   - 医保SDK API: https://localhost
echo %BLUE%[INFO]%NC%   - HTTP会自动重定向到HTTPS
docker-compose -f docker-compose.prod.yml ps
goto :end

:show_status
echo %BLUE%[INFO]%NC% Service status:
docker-compose ps
goto :end

:show_logs
echo %BLUE%[INFO]%NC% 显示服务日志：
docker-compose logs -f
goto :end

:cleanup
echo %BLUE%[INFO]%NC% 清理Docker环境...
docker-compose down -v
docker-compose -f docker-compose.prod.yml down -v
for /f "tokens=*" %%i in ('docker images "medical_insurance*" -q 2^>nul') do docker rmi %%i 2>nul
docker system prune -f
echo %GREEN%[SUCCESS]%NC% 环境清理完成
goto :end

:usage
echo %RED%[ERROR]%NC% 未知的环境类型: %ENVIRONMENT%
echo %BLUE%[INFO]%NC% 使用方法: %0 [dev^|prod^|status^|logs^|cleanup]
exit /b 1

:end
endlocal