# 医保接口SDK数据库设置指南

## 概述

本指南介绍如何为医保接口SDK设置数据库环境，包括MySQL和测试用SQLite的配置方法。

## 选项1: MySQL数据库设置（推荐用于生产环境）

### 1. 安装MySQL

#### Windows
1. 下载MySQL Installer: https://dev.mysql.com/downloads/installer/
2. 运行安装程序，选择"Developer Default"
3. 设置root密码
4. 完成安装

#### macOS
```bash
# 使用Homebrew安装
brew install mysql

# 启动MySQL服务
brew services start mysql

# 设置root密码
mysql_secure_installation
```

#### Ubuntu/Debian
```bash
# 安装MySQL
sudo apt update
sudo apt install mysql-server

# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置root密码
sudo mysql_secure_installation
```

### 2. 创建数据库和用户

```sql
-- 连接到MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE medical_insurance_sdk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（可选，推荐）
CREATE USER 'medical_sdk'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON medical_insurance_sdk.* TO 'medical_sdk'@'localhost';
FLUSH PRIVILEGES;

-- 退出MySQL
EXIT;
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# 复制示例配置文件
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=medical_sdk          # 或使用 root
DB_PASSWORD=your_secure_password
DB_NAME=medical_insurance_sdk
DB_CHARSET=utf8mb4
```

### 4. 初始化数据库

使用数据库管理工具：

```bash
# 方法1: 使用数据库管理器
python database/db_manager.py init --create-db

# 方法2: 使用初始化脚本
python scripts/initialize_config_data.py

# 方法3: 直接执行SQL脚本
mysql -u medical_sdk -p medical_insurance_sdk < database/setup_database.sql
```

### 5. 验证安装

```bash
# 检查数据库状态
python database/db_manager.py status

# 或者直接查询
mysql -u medical_sdk -p -e "USE medical_insurance_sdk; SHOW TABLES;"
```

## 选项2: SQLite测试数据库（用于开发和测试）

如果你没有MySQL环境或只是想快速测试，可以使用SQLite：

### 1. 运行测试数据库设置

```bash
python scripts/setup_test_database.py
```

### 2. 验证测试数据库

```bash
# 检查生成的数据库文件
ls -la test_database.db

# 使用SQLite命令行工具查看（如果已安装）
sqlite3 test_database.db ".tables"
```

## 数据库结构说明

### 核心表

1. **medical_interface_config** - 接口配置表
   - 存储174个医保接口的配置信息
   - 包含参数验证、响应映射等配置

2. **medical_organization_config** - 机构配置表
   - 存储不同医院的接入配置
   - 包含认证信息、超时配置等

3. **business_operation_logs** - 业务操作日志表
   - 存储所有接口调用记录
   - 支持分区存储，提高查询性能

4. **medical_institution_info** - 医药机构信息表
   - 存储1201接口获取的机构详细信息

5. **medical_interface_stats** - 接口调用统计表
   - 存储接口调用的统计数据

### 初始数据

数据库初始化后会包含：

- **1101接口配置**: 人员基本信息获取接口的完整配置
- **2201接口配置**: 门诊结算接口的配置数据
- **测试机构配置**: 用于开发测试的机构配置
- **示例机构信息**: 湖南省人民医院等示例数据

## 常见问题解决

### 1. 连接被拒绝

```
Error: (1045, "Access denied for user 'root'@'localhost' (using password: NO)")
```

**解决方案:**
- 确保MySQL服务正在运行
- 检查用户名和密码是否正确
- 确保 `.env` 文件中的配置正确

### 2. 数据库不存在

```
Error: (1049, "Unknown database 'medical_insurance_sdk'")
```

**解决方案:**
- 手动创建数据库或使用 `--create-db` 参数
- 检查数据库名称是否正确

### 3. 权限不足

```
Error: (1142, "CREATE command denied to user...")
```

**解决方案:**
- 确保用户有足够的权限
- 使用root用户或授予相应权限

### 4. 字符集问题

**解决方案:**
- 确保数据库使用utf8mb4字符集
- 检查连接配置中的字符集设置

## 性能优化建议

### 1. 索引优化
- 数据库脚本已包含优化的索引
- 根据实际查询模式调整索引

### 2. 分区管理
- business_operation_logs表使用月度分区
- 定期清理旧分区数据

### 3. 连接池配置
```bash
# 在.env中配置连接池
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

## 备份和恢复

### 备份数据库
```bash
# 完整备份
mysqldump -u medical_sdk -p medical_insurance_sdk > backup_$(date +%Y%m%d).sql

# 仅备份结构
mysqldump -u medical_sdk -p --no-data medical_insurance_sdk > schema_backup.sql

# 仅备份数据
mysqldump -u medical_sdk -p --no-create-info medical_insurance_sdk > data_backup.sql
```

### 恢复数据库
```bash
# 恢复完整备份
mysql -u medical_sdk -p medical_insurance_sdk < backup_20240115.sql

# 恢复到新数据库
mysql -u medical_sdk -p -e "CREATE DATABASE medical_insurance_sdk_restore;"
mysql -u medical_sdk -p medical_insurance_sdk_restore < backup_20240115.sql
```

## 监控和维护

### 1. 定期检查
```bash
# 检查数据库状态
python database/db_manager.py status

# 检查数据完整性
mysql -u medical_sdk -p medical_insurance_sdk -e "CALL CheckDataIntegrity();"
```

### 2. 分区维护
```bash
# 创建新月度分区
python database/db_manager.py partition --create 2024-02

# 清理旧分区（保留12个月）
python database/db_manager.py partition --cleanup 12
```

### 3. 性能监控
- 使用内置的性能监控视图
- 定期检查慢查询日志
- 监控数据库连接数和资源使用

## 联系支持

如果遇到数据库设置问题，请：

1. 检查本指南的常见问题部分
2. 查看项目日志文件
3. 在项目仓库提交Issue
4. 联系技术支持团队

---

**注意**: 生产环境请务必：
- 使用强密码
- 定期备份数据
- 监控数据库性能
- 及时更新安全补丁