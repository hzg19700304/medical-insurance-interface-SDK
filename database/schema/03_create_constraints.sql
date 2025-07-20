-- 医保接口SDK数据库约束
-- 创建时间: 2024-01-15
-- 版本: 1.0.0

-- 设置字符集
SET NAMES utf8mb4;

-- =====================================================
-- 1. 接口配置表 (medical_interface_config) 约束
-- =====================================================

-- 检查约束
ALTER TABLE `medical_interface_config` 
ADD CONSTRAINT `chk_api_code_format` 
CHECK (REGEXP_LIKE(`api_code`, '^[0-9]{4}$')),

ADD CONSTRAINT `chk_business_category` 
CHECK (`business_category` IN (
    '基础信息业务', '医保服务业务', '机构管理业务', 
    '信息采集业务', '信息查询业务', '线上支付业务', 
    '电子处方业务', '场景监控业务', '其他业务', '电子票据业务'
)),

ADD CONSTRAINT `chk_business_type` 
CHECK (`business_type` IN (
    'outpatient', 'inpatient', 'pharmacy', 'settlement', 
    'registration', 'prescription', 'inventory', 'query', 
    'config', 'monitor'
)),

ADD CONSTRAINT `chk_timeout_range` 
CHECK (`timeout_seconds` BETWEEN 5 AND 300),

ADD CONSTRAINT `chk_retry_times` 
CHECK (`max_retry_times` BETWEEN 0 AND 10);

-- =====================================================
-- 2. 机构配置表 (medical_organization_config) 约束
-- =====================================================

ALTER TABLE `medical_organization_config` 
ADD CONSTRAINT `chk_org_code_format` 
CHECK (LENGTH(`org_code`) >= 6 AND LENGTH(`org_code`) <= 20),

ADD CONSTRAINT `chk_province_code_format` 
CHECK (REGEXP_LIKE(`province_code`, '^[0-9]{6}$')),

ADD CONSTRAINT `chk_city_code_format` 
CHECK (REGEXP_LIKE(`city_code`, '^[0-9]{6}$')),

ADD CONSTRAINT `chk_crypto_type` 
CHECK (`crypto_type` IN ('SM4', 'AES', 'DES', '3DES')),

ADD CONSTRAINT `chk_sign_type` 
CHECK (`sign_type` IN ('SM3', 'SHA1', 'SHA256', 'MD5')),

ADD CONSTRAINT `chk_timeout_values` 
CHECK (`default_timeout` > 0 AND `connect_timeout` > 0 AND `read_timeout` > 0),

ADD CONSTRAINT `chk_retry_config` 
CHECK (`max_retry_times` >= 0 AND `retry_interval` > 0),

ADD CONSTRAINT `chk_health_status` 
CHECK (`health_status` IN ('healthy', 'unhealthy', 'unknown', 'maintenance'));

-- =====================================================
-- 3. 业务操作日志表 (business_operation_logs) 约束
-- =====================================================

ALTER TABLE `business_operation_logs` 
ADD CONSTRAINT `chk_operation_id_format` 
CHECK (LENGTH(`operation_id`) >= 10),

ADD CONSTRAINT `chk_api_code_log_format` 
CHECK (REGEXP_LIKE(`api_code`, '^[0-9]{4}$')),

ADD CONSTRAINT `chk_status_values` 
CHECK (`status` IN ('success', 'failed', 'pending', 'processing', 'timeout', 'cancelled')),

ADD CONSTRAINT `chk_response_time` 
CHECK (`response_time_ms` IS NULL OR `response_time_ms` >= 0),

ADD CONSTRAINT `chk_complete_time_logic` 
CHECK (`complete_time` IS NULL OR `complete_time` >= `operation_time`),

ADD CONSTRAINT `chk_trace_id_format` 
CHECK (LENGTH(`trace_id`) >= 8);

-- =====================================================
-- 4. 医药机构信息表 (medical_institution_info) 约束
-- =====================================================

ALTER TABLE `medical_institution_info` 
ADD CONSTRAINT `chk_fixmedins_code_format` 
CHECK (REGEXP_LIKE(`fixmedins_code`, '^[A-Z0-9]{12}$')),

ADD CONSTRAINT `chk_uscc_format` 
CHECK (LENGTH(`uscc`) >= 15 AND LENGTH(`uscc`) <= 20),

ADD CONSTRAINT `chk_fixmedins_type_format` 
CHECK (REGEXP_LIKE(`fixmedins_type`, '^[0-9]{6}$')),

ADD CONSTRAINT `chk_hosp_lv_format` 
CHECK (`hosp_lv` IS NULL OR REGEXP_LIKE(`hosp_lv`, '^[0-9]{6}$'));

-- =====================================================
-- 5. 接口调用统计表 (medical_interface_stats) 约束
-- =====================================================

ALTER TABLE `medical_interface_stats` 
ADD CONSTRAINT `chk_call_counts` 
CHECK (`total_calls` >= 0 AND `success_calls` >= 0 AND `failed_calls` >= 0 AND `pending_calls` >= 0),

ADD CONSTRAINT `chk_call_count_logic` 
CHECK (`total_calls` = `success_calls` + `failed_calls` + `pending_calls`),

ADD CONSTRAINT `chk_response_times` 
CHECK (`avg_response_time` >= 0 AND `max_response_time` >= 0 AND `min_response_time` >= 0),

ADD CONSTRAINT `chk_response_time_logic` 
CHECK (`max_response_time` >= `avg_response_time` AND `avg_response_time` >= `min_response_time`),

ADD CONSTRAINT `chk_success_rate` 
CHECK (`success_rate` BETWEEN 0 AND 100);

-- =====================================================
-- 6. 触发器 - 自动更新统计数据
-- =====================================================

DELIMITER $$

-- 业务操作日志插入后自动更新统计
CREATE TRIGGER `tr_update_stats_after_log_insert`
AFTER INSERT ON `business_operation_logs`
FOR EACH ROW
BEGIN
    INSERT INTO `medical_interface_stats` (
        `stat_date`, `institution_code`, `api_code`, 
        `business_category`, `business_type`,
        `total_calls`, `success_calls`, `failed_calls`, `pending_calls`,
        `avg_response_time`, `max_response_time`, `min_response_time`
    ) VALUES (
        DATE(NEW.operation_time), NEW.institution_code, NEW.api_code,
        NEW.business_category, NEW.business_type,
        1, 
        CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
        CASE WHEN NEW.status IN ('pending', 'processing') THEN 1 ELSE 0 END,
        COALESCE(NEW.response_time_ms, 0),
        COALESCE(NEW.response_time_ms, 0),
        COALESCE(NEW.response_time_ms, 0)
    ) ON DUPLICATE KEY UPDATE
        `total_calls` = `total_calls` + 1,
        `success_calls` = `success_calls` + CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
        `failed_calls` = `failed_calls` + CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
        `pending_calls` = `pending_calls` + CASE WHEN NEW.status IN ('pending', 'processing') THEN 1 ELSE 0 END,
        `avg_response_time` = CASE 
            WHEN NEW.response_time_ms IS NOT NULL THEN
                (`avg_response_time` * (`total_calls` - 1) + NEW.response_time_ms) / `total_calls`
            ELSE `avg_response_time`
        END,
        `max_response_time` = CASE 
            WHEN NEW.response_time_ms IS NOT NULL THEN
                GREATEST(`max_response_time`, NEW.response_time_ms)
            ELSE `max_response_time`
        END,
        `min_response_time` = CASE 
            WHEN NEW.response_time_ms IS NOT NULL THEN
                CASE WHEN `min_response_time` = 0 THEN NEW.response_time_ms
                     ELSE LEAST(`min_response_time`, NEW.response_time_ms)
                END
            ELSE `min_response_time`
        END,
        `success_rate` = (`success_calls` * 100.0) / `total_calls`,
        `updated_at` = CURRENT_TIMESTAMP;
END$$

-- 业务操作日志更新后重新计算统计
CREATE TRIGGER `tr_update_stats_after_log_update`
AFTER UPDATE ON `business_operation_logs`
FOR EACH ROW
BEGIN
    -- 如果状态发生变化，重新计算统计
    IF OLD.status != NEW.status THEN
        -- 这里可以添加重新计算逻辑，或者标记需要重新计算
        UPDATE `medical_interface_stats` 
        SET `updated_at` = CURRENT_TIMESTAMP
        WHERE `stat_date` = DATE(NEW.operation_time) 
        AND `institution_code` = NEW.institution_code 
        AND `api_code` = NEW.api_code;
    END IF;
END$$

-- 机构配置更新时自动更新健康检查时间
CREATE TRIGGER `tr_update_health_check_time`
BEFORE UPDATE ON `medical_organization_config`
FOR EACH ROW
BEGIN
    IF OLD.health_status != NEW.health_status THEN
        SET NEW.last_health_check = CURRENT_TIMESTAMP;
    END IF;
END$$

DELIMITER ;

-- =====================================================
-- 7. 数据完整性检查存储过程
-- =====================================================

DELIMITER $$

-- 检查数据完整性
CREATE PROCEDURE `CheckDataIntegrity`()
BEGIN
    DECLARE integrity_issues INT DEFAULT 0;
    
    -- 检查孤立的日志记录（没有对应的接口配置）
    SELECT COUNT(*) INTO @orphan_logs
    FROM business_operation_logs bol
    LEFT JOIN medical_interface_config mic ON bol.api_code = mic.api_code
    WHERE mic.api_code IS NULL;
    
    IF @orphan_logs > 0 THEN
        SET integrity_issues = integrity_issues + 1;
        SELECT CONCAT('发现 ', @orphan_logs, ' 条孤立的日志记录（没有对应的接口配置）') AS issue;
    END IF;
    
    -- 检查孤立的日志记录（没有对应的机构配置）
    SELECT COUNT(*) INTO @orphan_org_logs
    FROM business_operation_logs bol
    LEFT JOIN medical_organization_config moc ON bol.institution_code = moc.org_code
    WHERE moc.org_code IS NULL;
    
    IF @orphan_org_logs > 0 THEN
        SET integrity_issues = integrity_issues + 1;
        SELECT CONCAT('发现 ', @orphan_org_logs, ' 条孤立的日志记录（没有对应的机构配置）') AS issue;
    END IF;
    
    -- 检查统计数据一致性
    SELECT COUNT(*) INTO @inconsistent_stats
    FROM medical_interface_stats mis
    WHERE mis.total_calls != (mis.success_calls + mis.failed_calls + mis.pending_calls);
    
    IF @inconsistent_stats > 0 THEN
        SET integrity_issues = integrity_issues + 1;
        SELECT CONCAT('发现 ', @inconsistent_stats, ' 条统计数据不一致的记录') AS issue;
    END IF;
    
    -- 检查响应时间逻辑
    SELECT COUNT(*) INTO @invalid_response_times
    FROM medical_interface_stats
    WHERE max_response_time < avg_response_time OR avg_response_time < min_response_time;
    
    IF @invalid_response_times > 0 THEN
        SET integrity_issues = integrity_issues + 1;
        SELECT CONCAT('发现 ', @invalid_response_times, ' 条响应时间逻辑错误的记录') AS issue;
    END IF;
    
    IF integrity_issues = 0 THEN
        SELECT '数据完整性检查通过，未发现问题' AS result;
    ELSE
        SELECT CONCAT('数据完整性检查完成，发现 ', integrity_issues, ' 类问题') AS result;
    END IF;
    
END$$

-- 修复统计数据
CREATE PROCEDURE `RepairStatistics`(IN target_date DATE)
BEGIN
    -- 重新计算指定日期的统计数据
    DELETE FROM medical_interface_stats WHERE stat_date = target_date;
    
    INSERT INTO medical_interface_stats (
        stat_date, institution_code, api_code, business_category, business_type,
        total_calls, success_calls, failed_calls, pending_calls,
        avg_response_time, max_response_time, min_response_time, success_rate
    )
    SELECT 
        DATE(bol.operation_time) as stat_date,
        bol.institution_code,
        bol.api_code,
        bol.business_category,
        bol.business_type,
        COUNT(*) as total_calls,
        COUNT(CASE WHEN bol.status = 'success' THEN 1 END) as success_calls,
        COUNT(CASE WHEN bol.status = 'failed' THEN 1 END) as failed_calls,
        COUNT(CASE WHEN bol.status IN ('pending', 'processing') THEN 1 END) as pending_calls,
        ROUND(AVG(bol.response_time_ms), 2) as avg_response_time,
        MAX(bol.response_time_ms) as max_response_time,
        MIN(bol.response_time_ms) as min_response_time,
        ROUND(COUNT(CASE WHEN bol.status = 'success' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
    FROM business_operation_logs bol
    WHERE DATE(bol.operation_time) = target_date
    GROUP BY DATE(bol.operation_time), bol.institution_code, bol.api_code, 
             bol.business_category, bol.business_type;
    
    SELECT CONCAT('已重新计算 ', target_date, ' 的统计数据') AS result;
END$$

DELIMITER ;