-- 医保接口SDK数据库索引优化
-- 创建时间: 2024-01-15
-- 版本: 1.0.0

-- 设置字符集
SET NAMES utf8mb4;

-- =====================================================
-- 1. 接口配置表 (medical_interface_config) 索引优化
-- =====================================================

-- 为JSON字段创建虚拟列和索引以提高查询性能
ALTER TABLE `medical_interface_config` 
ADD COLUMN `has_required_params` BOOLEAN GENERATED ALWAYS AS (JSON_LENGTH(`required_params`) > 0) STORED,
ADD COLUMN `has_region_specific` BOOLEAN GENERATED ALWAYS AS (JSON_LENGTH(`region_specific`) > 0) STORED;

-- 为虚拟列创建索引
CREATE INDEX `idx_has_required_params` ON `medical_interface_config` (`has_required_params`);
CREATE INDEX `idx_has_region_specific` ON `medical_interface_config` (`has_region_specific`);

-- 复合索引优化
CREATE INDEX `idx_category_type_active` ON `medical_interface_config` (`business_category`, `business_type`, `is_active`);
CREATE INDEX `idx_active_updated` ON `medical_interface_config` (`is_active`, `updated_at` DESC);

-- =====================================================
-- 2. 机构配置表 (medical_organization_config) 索引优化
-- =====================================================

-- 地区相关复合索引
CREATE INDEX `idx_province_city_area` ON `medical_organization_config` (`province_code`, `city_code`, `area_code`);
CREATE INDEX `idx_active_health` ON `medical_organization_config` (`is_active`, `health_status`);
CREATE INDEX `idx_test_env` ON `medical_organization_config` (`is_test_env`, `is_active`);

-- 健康检查相关索引
CREATE INDEX `idx_health_check_time` ON `medical_organization_config` (`last_health_check` DESC);

-- =====================================================
-- 3. 业务操作日志表 (business_operation_logs) 索引优化
-- =====================================================

-- 复合索引优化（考虑分区表特性）
CREATE INDEX `idx_inst_api_time_status` ON `business_operation_logs` 
(`institution_code`, `api_code`, `operation_time` DESC, `status`);

CREATE INDEX `idx_business_time_status` ON `business_operation_logs` 
(`business_category`, `business_type`, `operation_time` DESC, `status`);

-- 人员相关复合索引
CREATE INDEX `idx_psn_inst_time` ON `business_operation_logs` 
(`psn_no`, `institution_code`, `operation_time` DESC) 
WHERE `psn_no` IS NOT NULL;

CREATE INDEX `idx_mdtrt_inst_time` ON `business_operation_logs` 
(`mdtrt_id`, `institution_code`, `operation_time` DESC) 
WHERE `mdtrt_id` IS NOT NULL;

-- 错误分析索引
CREATE INDEX `idx_error_code_time` ON `business_operation_logs` 
(`error_code`, `operation_time` DESC) 
WHERE `error_code` IS NOT NULL;

-- 性能分析索引
CREATE INDEX `idx_response_time` ON `business_operation_logs` (`response_time_ms` DESC) 
WHERE `response_time_ms` IS NOT NULL;

-- 操作员相关索引
CREATE INDEX `idx_operator_time` ON `business_operation_logs` 
(`operator_id`, `operation_time` DESC) 
WHERE `operator_id` IS NOT NULL;

-- =====================================================
-- 4. 医药机构信息表 (medical_institution_info) 索引优化
-- =====================================================

-- 复合查询索引
CREATE INDEX `idx_type_level` ON `medical_institution_info` (`fixmedins_type`, `hosp_lv`);
CREATE INDEX `idx_name_type` ON `medical_institution_info` (`fixmedins_name`, `fixmedins_type`);

-- 同步相关索引
CREATE INDEX `idx_version_sync_time` ON `medical_institution_info` (`data_version`, `sync_time` DESC);

-- =====================================================
-- 5. 接口调用统计表 (medical_interface_stats) 索引优化
-- =====================================================

-- 时间范围查询优化
CREATE INDEX `idx_date_range_inst` ON `medical_interface_stats` 
(`stat_date` DESC, `institution_code`);

CREATE INDEX `idx_date_range_api` ON `medical_interface_stats` 
(`stat_date` DESC, `api_code`);

-- 性能分析索引
CREATE INDEX `idx_avg_response_time` ON `medical_interface_stats` (`avg_response_time` DESC);
CREATE INDEX `idx_calls_success_rate` ON `medical_interface_stats` (`total_calls` DESC, `success_rate` DESC);

-- 业务分析索引
CREATE INDEX `idx_category_date_calls` ON `medical_interface_stats` 
(`business_category`, `stat_date` DESC, `total_calls` DESC);

CREATE INDEX `idx_type_date_success` ON `medical_interface_stats` 
(`business_type`, `stat_date` DESC, `success_rate` DESC);

-- =====================================================
-- 6. 分区表管理索引
-- =====================================================

-- 为分区表创建本地索引（每个分区都会有这些索引）
-- 注意：MySQL的分区表索引必须包含分区键

-- 创建分区管理存储过程
DELIMITER $$

CREATE PROCEDURE `CreateMonthlyPartition`(IN target_date DATE)
BEGIN
    DECLARE partition_name VARCHAR(20);
    DECLARE next_month_start DATE;
    DECLARE sql_stmt TEXT;
    
    -- 生成分区名称
    SET partition_name = CONCAT('p', DATE_FORMAT(target_date, '%Y%m'));
    
    -- 计算下个月的开始时间
    SET next_month_start = DATE_ADD(DATE_FORMAT(target_date, '%Y-%m-01'), INTERVAL 1 MONTH);
    
    -- 构建SQL语句
    SET sql_stmt = CONCAT(
        'ALTER TABLE business_operation_logs ADD PARTITION (',
        'PARTITION ', partition_name, 
        ' VALUES LESS THAN (UNIX_TIMESTAMP(''', next_month_start, ' 00:00:00'')))'
    );
    
    -- 执行SQL
    SET @sql = sql_stmt;
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
END$$

CREATE PROCEDURE `DropOldPartitions`(IN months_to_keep INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE partition_name VARCHAR(64);
    DECLARE partition_date DATE;
    DECLARE cutoff_date DATE;
    DECLARE sql_stmt TEXT;
    
    -- 计算截止日期
    SET cutoff_date = DATE_SUB(CURDATE(), INTERVAL months_to_keep MONTH);
    
    -- 游标声明
    DECLARE partition_cursor CURSOR FOR
        SELECT PARTITION_NAME 
        FROM INFORMATION_SCHEMA.PARTITIONS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'business_operation_logs'
        AND PARTITION_NAME IS NOT NULL
        AND PARTITION_NAME REGEXP '^p[0-9]{6}$';
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN partition_cursor;
    
    read_loop: LOOP
        FETCH partition_cursor INTO partition_name;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- 从分区名称提取日期
        SET partition_date = STR_TO_DATE(SUBSTRING(partition_name, 2), '%Y%m');
        
        -- 如果分区日期早于截止日期，则删除
        IF partition_date < cutoff_date THEN
            SET sql_stmt = CONCAT('ALTER TABLE business_operation_logs DROP PARTITION ', partition_name);
            SET @sql = sql_stmt;
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
        END IF;
        
    END LOOP;
    
    CLOSE partition_cursor;
END$$

DELIMITER ;

-- =====================================================
-- 7. 性能监控视图
-- =====================================================

-- 创建接口性能监控视图
CREATE VIEW `v_interface_performance` AS
SELECT 
    mic.api_code,
    mic.api_name,
    mic.business_category,
    mic.business_type,
    COUNT(bol.id) as total_calls,
    COUNT(CASE WHEN bol.status = 'success' THEN 1 END) as success_calls,
    COUNT(CASE WHEN bol.status = 'failed' THEN 1 END) as failed_calls,
    ROUND(COUNT(CASE WHEN bol.status = 'success' THEN 1 END) * 100.0 / COUNT(bol.id), 2) as success_rate,
    ROUND(AVG(bol.response_time_ms), 2) as avg_response_time,
    MAX(bol.response_time_ms) as max_response_time,
    MIN(bol.response_time_ms) as min_response_time
FROM medical_interface_config mic
LEFT JOIN business_operation_logs bol ON mic.api_code = bol.api_code
WHERE bol.operation_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY mic.api_code, mic.api_name, mic.business_category, mic.business_type
ORDER BY total_calls DESC;

-- 创建机构调用统计视图
CREATE VIEW `v_organization_stats` AS
SELECT 
    moc.org_code,
    moc.org_name,
    moc.province_code,
    moc.city_code,
    COUNT(bol.id) as total_calls,
    COUNT(CASE WHEN bol.status = 'success' THEN 1 END) as success_calls,
    COUNT(CASE WHEN bol.status = 'failed' THEN 1 END) as failed_calls,
    ROUND(COUNT(CASE WHEN bol.status = 'success' THEN 1 END) * 100.0 / COUNT(bol.id), 2) as success_rate,
    ROUND(AVG(bol.response_time_ms), 2) as avg_response_time
FROM medical_organization_config moc
LEFT JOIN business_operation_logs bol ON moc.org_code = bol.institution_code
WHERE bol.operation_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY moc.org_code, moc.org_name, moc.province_code, moc.city_code
ORDER BY total_calls DESC;

-- 创建错误分析视图
CREATE VIEW `v_error_analysis` AS
SELECT 
    error_code,
    COUNT(*) as error_count,
    COUNT(DISTINCT api_code) as affected_apis,
    COUNT(DISTINCT institution_code) as affected_orgs,
    MIN(operation_time) as first_occurrence,
    MAX(operation_time) as last_occurrence,
    SUBSTRING(error_message, 1, 200) as sample_message
FROM business_operation_logs
WHERE status = 'failed' 
AND error_code IS NOT NULL
AND operation_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY error_code, SUBSTRING(error_message, 1, 200)
ORDER BY error_count DESC;