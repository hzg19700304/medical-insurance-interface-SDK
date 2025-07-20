-- 医保接口SDK数据库完整安装脚本
-- 创建时间: 2024-01-15
-- 版本: 1.0.0
-- 说明: 此脚本将创建完整的医保接口SDK数据库结构

-- 设置字符集和SQL模式
SET NAMES utf8mb4;
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `medical_insurance_sdk` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `medical_insurance_sdk`;

-- 显示安装进度
SELECT '开始安装医保接口SDK数据库...' AS status;

-- =====================================================
-- 第一步：创建表结构
-- =====================================================
SELECT '第一步：创建表结构...' AS status;

-- 执行表创建脚本
SOURCE schema/01_create_tables.sql;

SELECT '表结构创建完成' AS status;

-- =====================================================
-- 第二步：创建索引
-- =====================================================
SELECT '第二步：创建索引...' AS status;

-- 执行索引创建脚本
SOURCE schema/02_create_indexes.sql;

SELECT '索引创建完成' AS status;

-- =====================================================
-- 第三步：创建约束
-- =====================================================
SELECT '第三步：创建约束和触发器...' AS status;

-- 执行约束创建脚本
SOURCE schema/03_create_constraints.sql;

SELECT '约束和触发器创建完成' AS status;

-- =====================================================
-- 第四步：插入初始数据
-- =====================================================
SELECT '第四步：插入初始数据...' AS status;

-- 执行初始数据插入脚本
SOURCE schema/04_initial_data.sql;

SELECT '初始数据插入完成' AS status;

-- =====================================================
-- 第五步：验证安装
-- =====================================================
SELECT '第五步：验证安装...' AS status;

-- 检查表是否创建成功
SELECT 
    TABLE_NAME as '表名',
    TABLE_ROWS as '行数',
    DATA_LENGTH as '数据大小',
    INDEX_LENGTH as '索引大小',
    TABLE_COMMENT as '表注释'
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'medical_insurance_sdk'
ORDER BY TABLE_NAME;

-- 检查索引是否创建成功
SELECT 
    TABLE_NAME as '表名',
    INDEX_NAME as '索引名',
    COLUMN_NAME as '列名',
    INDEX_TYPE as '索引类型'
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = 'medical_insurance_sdk'
AND INDEX_NAME != 'PRIMARY'
ORDER BY TABLE_NAME, INDEX_NAME;

-- 检查约束是否创建成功
SELECT 
    TABLE_NAME as '表名',
    CONSTRAINT_NAME as '约束名',
    CONSTRAINT_TYPE as '约束类型'
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE TABLE_SCHEMA = 'medical_insurance_sdk'
ORDER BY TABLE_NAME, CONSTRAINT_TYPE;

-- 检查触发器是否创建成功
SELECT 
    TRIGGER_NAME as '触发器名',
    EVENT_MANIPULATION as '事件类型',
    EVENT_OBJECT_TABLE as '表名',
    ACTION_TIMING as '触发时机'
FROM INFORMATION_SCHEMA.TRIGGERS 
WHERE TRIGGER_SCHEMA = 'medical_insurance_sdk'
ORDER BY EVENT_OBJECT_TABLE;

-- 检查存储过程是否创建成功
SELECT 
    ROUTINE_NAME as '存储过程名',
    ROUTINE_TYPE as '类型',
    ROUTINE_COMMENT as '注释'
FROM INFORMATION_SCHEMA.ROUTINES 
WHERE ROUTINE_SCHEMA = 'medical_insurance_sdk'
ORDER BY ROUTINE_NAME;

-- 检查视图是否创建成功
SELECT 
    TABLE_NAME as '视图名',
    TABLE_COMMENT as '视图注释'
FROM INFORMATION_SCHEMA.VIEWS 
WHERE TABLE_SCHEMA = 'medical_insurance_sdk'
ORDER BY TABLE_NAME;

-- 检查分区是否创建成功
SELECT 
    TABLE_NAME as '表名',
    PARTITION_NAME as '分区名',
    PARTITION_METHOD as '分区方法',
    PARTITION_EXPRESSION as '分区表达式'
FROM INFORMATION_SCHEMA.PARTITIONS 
WHERE TABLE_SCHEMA = 'medical_insurance_sdk'
AND PARTITION_NAME IS NOT NULL
ORDER BY TABLE_NAME, PARTITION_NAME;

-- 检查初始数据是否插入成功
SELECT '接口配置数量' as '数据类型', COUNT(*) as '记录数' FROM medical_interface_config
UNION ALL
SELECT '机构配置数量', COUNT(*) FROM medical_organization_config
UNION ALL
SELECT '机构信息数量', COUNT(*) FROM medical_institution_info
UNION ALL
SELECT '统计记录数量', COUNT(*) FROM medical_interface_stats;

-- =====================================================
-- 安装完成
-- =====================================================
SELECT '医保接口SDK数据库安装完成！' AS status;
SELECT CONCAT('数据库版本: ', VERSION()) AS database_version;
SELECT CONCAT('字符集: ', @@character_set_database) AS charset;
SELECT CONCAT('排序规则: ', @@collation_database) AS collation;
SELECT NOW() AS installation_time;