# 医保接口SDK数据库设计

## 概述

本目录包含医保接口SDK的完整数据库设计，包括表结构、索引、约束、初始数据和管理工具。

## 目录结构

```
database/
├── README.md                    # 本文档
├── setup_database.sql          # 完整数据库安装脚本
├── db_manager.py              # Python数据库管理工具
└── schema/                    # 数据库架构文件
    ├── 01_create_tables.sql   # 创建表结构
    ├── 02_create_indexes.sql  # 创建索引
    ├── 03_create_constraints.sql # 创建约束和触发器
    └── 04_initial_data.sql    # 初始数据
```

## 数据库表结构

### 核心表

1. **medical_interface_config** - 接口配置表
   - 存储174个医保接口的配置信息
   - 支持配置驱动的参数验证和数据映射
   - 支持地区差异化配置

2. **medical_organization_config** - 机构配置表
   - 存储不同医院的接入配置
   - 包含认证信息、超时配置、重试策略等

3. **business_operation_logs** - 通用业务操作日志表
   - 存储所有接口调用记录和响应数据
   - 支持按时间分区，提高查询性能
   - 使用JSONB格式存储请求和响应数据

4. **medical_institution_info** - 医药机构信息表
   - 存储1201接口获取的机构详细信息
   - 支持全文检索和模糊查询

5. **medical_interface_stats** - 接口调用统计表
   - 存储接口调用的统计数据
   - 支持性能分析和监控

### 特性

- **分区表**: business_operation_logs表按月分区，提高查询性能
- **JSON支持**: 使用JSON字段存储复杂配置和数据
- **全文检索**: 机构名称支持全文检索
- **自动统计**: 通过触发器自动更新统计数据
- **数据完整性**: 完善的约束和检查机制

## 安装方法

### 方法一：使用MySQL客户端

```bash
# 1. 连接到MySQL
mysql -u root -p

# 2. 执行安装脚本
source /path/to/database/setup_database.sql
```

### 方法二：使用Python管理工具

```bash
# 1. 安装依赖
pip install pymysql

# 2. 初始化数据库（会自动创建数据库）
python database/db_manager.py --host localhost --user root --password your_password init --create-db

# 3. 检查数据库状态
python database/db_manager.py --host localhost --user root --password your_password status
```

### 方法三：分步执行

```bash
# 1. 创建数据库
CREATE DATABASE medical_insurance_sdk DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
USE medical_insurance_sdk;

# 2. 依次执行架构文件
source schema/01_create_tables.sql
source schema/02_create_indexes.sql
source schema/03_create_constraints.sql
source schema/04_initial_data.sql
```

## 配置说明

### 数据库连接配置

```python
# 默认配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'wodemima',
    'database': 'medical_insurance_sdk',
    'charset': 'utf8mb4'
}
```

### 环境变量配置

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=medical_sdk
export DB_PASSWORD=your_password
export DB_NAME=medical_insurance_sdk
```

## 数据库管理

### 分区管理

```bash
# 创建新的月度分区
python db_manager.py partition --create 2024-07

# 清理旧分区（保留12个月）
python db_manager.py partition --cleanup 12
```

### 数据维护

```sql
-- 检查数据完整性
CALL CheckDataIntegrity();

-- 修复统计数据
CALL RepairStatistics('2024-01-15');

-- 创建月度分区
CALL CreateMonthlyPartition('2024-07-01');

-- 清理旧分区
CALL DropOldPartitions(12);
```

### 性能监控

```sql
-- 查看接口性能
SELECT * FROM v_interface_performance;

-- 查看机构统计
SELECT * FROM v_organization_stats;

-- 查看错误分析
SELECT * FROM v_error_analysis;
```

## 索引策略

### 主要索引

1. **业务查询索引**
   - 按机构+时间+接口查询
   - 按人员+时间查询
   - 按就医登记号+时间查询

2. **统计分析索引**
   - 按业务分类+时间统计
   - 按错误类型分析
   - 按响应时间分析

3. **配置查询索引**
   - 接口配置按编码查询
   - 机构配置按地区查询
   - 机构信息全文检索

### 索引优化建议

- 定期分析表统计信息：`ANALYZE TABLE table_name`
- 监控慢查询日志
- 根据实际查询模式调整索引

## 数据备份

### 备份策略

```bash
# 完整备份
mysqldump -u root -p --single-transaction --routines --triggers medical_insurance_sdk > backup_full.sql

# 仅结构备份
mysqldump -u root -p --no-data --routines --triggers medical_insurance_sdk > backup_schema.sql

# 仅数据备份
mysqldump -u root -p --no-create-info medical_insurance_sdk > backup_data.sql
```

### 恢复数据

```bash
# 恢复完整备份
mysql -u root -p medical_insurance_sdk < backup_full.sql

# 恢复结构
mysql -u root -p medical_insurance_sdk < backup_schema.sql

# 恢复数据
mysql -u root -p medical_insurance_sdk < backup_data.sql
```

## 安全配置

### 用户权限

```sql
-- 创建应用用户
CREATE USER 'medical_sdk'@'%' IDENTIFIED BY 'strong_password_2024';
GRANT SELECT, INSERT, UPDATE, DELETE ON medical_insurance_sdk.* TO 'medical_sdk'@'%';

-- 创建只读用户
CREATE USER 'medical_sdk_readonly'@'%' IDENTIFIED BY 'readonly_password_2024';
GRANT SELECT ON medical_insurance_sdk.* TO 'medical_sdk_readonly'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 安全建议

1. 使用强密码
2. 限制网络访问
3. 定期更新密码
4. 启用SSL连接
5. 监控异常访问

## 故障排除

### 常见问题

1. **连接失败**
   - 检查MySQL服务状态
   - 验证连接参数
   - 检查防火墙设置

2. **权限错误**
   - 确认用户权限
   - 检查数据库存在性
   - 验证密码正确性

3. **性能问题**
   - 检查索引使用情况
   - 分析慢查询日志
   - 考虑分区优化

4. **空间不足**
   - 清理旧分区数据
   - 压缩表空间
   - 增加存储容量

### 日志查看

```sql
-- 查看错误日志
SHOW VARIABLES LIKE 'log_error';

-- 查看慢查询日志
SHOW VARIABLES LIKE 'slow_query_log%';

-- 查看二进制日志
SHOW BINARY LOGS;
```

## 版本升级

### 升级步骤

1. 备份现有数据
2. 测试升级脚本
3. 执行升级操作
4. 验证数据完整性
5. 更新应用配置

### 版本兼容性

- MySQL 5.7+
- MySQL 8.0+ (推荐)
- MariaDB 10.3+

## 联系支持

如有问题，请联系开发团队或查看项目文档。