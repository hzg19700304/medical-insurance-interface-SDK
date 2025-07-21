-- HIS系统集成相关表结构
-- 创建时间: 2024-01-15
-- 版本: 1.0.0

-- 设置字符集和排序规则
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. HIS患者同步日志表 (his_patient_sync_log)
-- 用途：记录患者信息同步状态和历史，支持多医院部署
-- =====================================================
CREATE TABLE `his_patient_sync_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 患者基本信息
    `patient_id` VARCHAR(50) NOT NULL COMMENT 'HIS系统患者ID',
    `name` VARCHAR(100) NOT NULL COMMENT '患者姓名',
    `id_card` VARCHAR(18) NOT NULL COMMENT '身份证号',
    `gender` VARCHAR(1) NOT NULL COMMENT '性别：1-男，2-女',
    `birth_date` DATE NOT NULL COMMENT '出生日期',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    `address` VARCHAR(500) DEFAULT NULL COMMENT '地址',
    
    -- 医保相关信息
    `psn_no` VARCHAR(30) DEFAULT NULL COMMENT '医保人员编号',
    `insurance_type` VARCHAR(10) DEFAULT NULL COMMENT '参保类型',
    `insurance_status` VARCHAR(10) DEFAULT NULL COMMENT '参保状态',
    
    -- 医院信息（支持多医院部署）
    `org_code` VARCHAR(20) NOT NULL COMMENT '医院机构编码',
    
    -- 同步状态
    `sync_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '同步状态：pending, synced, failed',
    `sync_time` TIMESTAMP NULL COMMENT '同步时间',
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_patient_org` (`patient_id`, `org_code`),
    KEY `idx_id_card` (`id_card`),
    KEY `idx_name` (`name`),
    KEY `idx_psn_no` (`psn_no`),
    KEY `idx_org_code` (`org_code`),
    KEY `idx_sync_status` (`sync_status`),
    KEY `idx_sync_time` (`sync_time`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='HIS患者同步日志表';

-- =====================================================
-- 2. HIS结算回写日志表 (his_settlement_writeback_log)
-- 用途：记录医保结算结果回写到HIS系统的状态和历史
-- =====================================================
CREATE TABLE `his_settlement_writeback_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 结算基本信息
    `settlement_id` VARCHAR(50) NOT NULL COMMENT '结算ID',
    `patient_id` VARCHAR(50) NOT NULL COMMENT '患者ID',
    `mdtrt_id` VARCHAR(30) NOT NULL COMMENT '就医登记号',
    
    -- 费用信息
    `total_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '总费用',
    `insurance_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '医保支付金额',
    `personal_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '个人支付金额',
    `account_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '个人账户支付金额',
    
    -- 结算信息
    `settlement_time` TIMESTAMP NOT NULL COMMENT '结算时间',
    `settlement_status` VARCHAR(20) NOT NULL COMMENT '结算状态',
    
    -- HIS回写状态
    `his_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'HIS回写状态：pending, written, failed',
    `his_write_time` TIMESTAMP NULL COMMENT 'HIS回写时间',
    `his_error_message` TEXT DEFAULT NULL COMMENT 'HIS回写错误信息',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_settlement_id` (`settlement_id`),
    KEY `idx_patient_id` (`patient_id`),
    KEY `idx_mdtrt_id` (`mdtrt_id`),
    KEY `idx_settlement_time` (`settlement_time`),
    KEY `idx_his_status` (`his_status`),
    KEY `idx_his_write_time` (`his_write_time`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='HIS结算回写日志表';

-- =====================================================
-- 3. 数据同步任务表 (data_sync_tasks)
-- 用途：记录数据同步任务的执行状态和结果
-- =====================================================
CREATE TABLE `data_sync_tasks` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 任务基本信息
    `task_id` VARCHAR(50) NOT NULL COMMENT '任务ID',
    `table_name` VARCHAR(100) NOT NULL COMMENT '同步表名',
    `sync_direction` VARCHAR(20) NOT NULL COMMENT '同步方向：bidirectional, to_his, from_his',
    `sync_type` VARCHAR(20) NOT NULL COMMENT '同步类型：full, incremental',
    
    -- 任务状态
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending, running, success, failed, conflict',
    
    -- 同步条件
    `where_condition` TEXT DEFAULT NULL COMMENT '同步条件',
    `sync_fields` JSON DEFAULT NULL COMMENT '同步字段列表',
    
    -- 时间戳
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `started_at` TIMESTAMP NULL COMMENT '开始时间',
    `completed_at` TIMESTAMP NULL COMMENT '完成时间',
    
    -- 结果统计
    `total_records` INT DEFAULT 0 COMMENT '总记录数',
    `synced_records` INT DEFAULT 0 COMMENT '已同步记录数',
    `failed_records` INT DEFAULT 0 COMMENT '失败记录数',
    `conflict_records` INT DEFAULT 0 COMMENT '冲突记录数',
    
    -- 错误信息
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    
    -- 审计字段
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_task_id` (`task_id`),
    KEY `idx_table_name` (`table_name`),
    KEY `idx_sync_direction` (`sync_direction`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_completed_at` (`completed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据同步任务表';

-- =====================================================
-- 4. 数据同步冲突表 (data_sync_conflicts)
-- 用途：记录数据同步过程中发现的冲突及其解决状态
-- =====================================================
CREATE TABLE `data_sync_conflicts` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 冲突基本信息
    `conflict_id` VARCHAR(50) NOT NULL COMMENT '冲突ID',
    `table_name` VARCHAR(100) NOT NULL COMMENT '表名',
    `primary_key` VARCHAR(100) NOT NULL COMMENT '主键值',
    
    -- 冲突数据
    `his_data` JSON NOT NULL COMMENT 'HIS系统数据',
    `medical_data` JSON NOT NULL COMMENT '医保系统数据',
    `conflict_fields` JSON NOT NULL COMMENT '冲突字段列表',
    
    -- 冲突状态
    `resolved` BOOLEAN DEFAULT FALSE COMMENT '是否已解决',
    `resolution_strategy` VARCHAR(50) DEFAULT NULL COMMENT '解决策略',
    `resolved_at` TIMESTAMP NULL COMMENT '解决时间',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_conflict_id` (`conflict_id`),
    KEY `idx_table_name` (`table_name`),
    KEY `idx_primary_key` (`primary_key`),
    KEY `idx_resolved` (`resolved`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_resolved_at` (`resolved_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据同步冲突表';

-- =====================================================
-- 5. 数据同步状态表 (data_sync_status)
-- 用途：记录各表的最后同步时间和状态
-- =====================================================
CREATE TABLE `data_sync_status` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 同步状态信息
    `table_name` VARCHAR(100) NOT NULL COMMENT '表名',
    `last_sync_time` TIMESTAMP NOT NULL COMMENT '最后同步时间',
    `sync_direction` VARCHAR(20) DEFAULT 'bidirectional' COMMENT '同步方向',
    `sync_status` VARCHAR(20) DEFAULT 'active' COMMENT '同步状态：active, paused, error',
    
    -- 统计信息
    `total_synced` BIGINT DEFAULT 0 COMMENT '累计同步记录数',
    `last_sync_count` INT DEFAULT 0 COMMENT '最后一次同步记录数',
    `error_count` INT DEFAULT 0 COMMENT '错误次数',
    `last_error_message` TEXT DEFAULT NULL COMMENT '最后错误信息',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_table_name` (`table_name`),
    KEY `idx_last_sync_time` (`last_sync_time`),
    KEY `idx_sync_status` (`sync_status`),
    KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据同步状态表';

-- =====================================================
-- 6. 医保人员信息表 (medical_person_info)
-- 用途：存储从医保接口查询到的人员信息，用于HIS集成时的数据关联
-- =====================================================
CREATE TABLE `medical_person_info` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 人员基本信息
    `psn_no` VARCHAR(30) NOT NULL COMMENT '医保人员编号',
    `psn_name` VARCHAR(100) NOT NULL COMMENT '人员姓名',
    `certno` VARCHAR(18) NOT NULL COMMENT '证件号码',
    `gend` VARCHAR(1) DEFAULT NULL COMMENT '性别',
    `brdy` DATE DEFAULT NULL COMMENT '出生日期',
    `age` INT DEFAULT NULL COMMENT '年龄',
    
    -- 参保信息
    `insurance_type` VARCHAR(10) DEFAULT NULL COMMENT '参保类型',
    `insurance_status` VARCHAR(10) DEFAULT NULL COMMENT '参保状态',
    `psn_insu_date` DATE DEFAULT NULL COMMENT '参保日期',
    `psn_insu_stas` VARCHAR(10) DEFAULT NULL COMMENT '人员参保状态',
    
    -- 扩展信息
    `extra_info` JSON DEFAULT ('{}') COMMENT '扩展信息',
    
    -- 数据来源
    `data_source` VARCHAR(20) DEFAULT 'medical_api' COMMENT '数据来源',
    `last_query_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最后查询时间',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_psn_no` (`psn_no`),
    UNIQUE KEY `uk_certno` (`certno`),
    KEY `idx_psn_name` (`psn_name`),
    KEY `idx_insurance_type` (`insurance_type`),
    KEY `idx_insurance_status` (`insurance_status`),
    KEY `idx_last_query_time` (`last_query_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='医保人员信息表';

-- =====================================================
-- 7. HIS数据同步日志表 (his_data_sync_log)
-- 用途：记录通用HIS数据同步操作的详细日志
-- =====================================================
CREATE TABLE `his_data_sync_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 同步基本信息
    `sync_id` VARCHAR(50) NOT NULL COMMENT '同步ID',
    `api_code` VARCHAR(10) NOT NULL COMMENT '医保接口编码',
    `org_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    
    -- 同步方向和类型
    `sync_direction` VARCHAR(20) NOT NULL DEFAULT 'to_his' COMMENT '同步方向：to_his, from_his, bidirectional',
    `sync_type` VARCHAR(20) NOT NULL DEFAULT 'incremental' COMMENT '同步类型：full, incremental',
    
    -- 数据内容
    `medical_data` JSON NOT NULL COMMENT '医保系统数据',
    `his_data` JSON NOT NULL COMMENT 'HIS系统数据',
    
    -- 同步状态和结果
    `sync_status` VARCHAR(20) NOT NULL COMMENT '同步状态：success, failed, partial',
    `synced_records` INT DEFAULT 0 COMMENT '成功同步记录数',
    `failed_records` INT DEFAULT 0 COMMENT '失败记录数',
    `conflict_records` INT DEFAULT 0 COMMENT '冲突记录数',
    
    -- 错误信息
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    `error_details` JSON DEFAULT NULL COMMENT '详细错误信息',
    
    -- 时间信息
    `sync_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '同步时间',
    `duration_ms` INT DEFAULT NULL COMMENT '同步耗时（毫秒）',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_sync_id` (`sync_id`),
    KEY `idx_api_code` (`api_code`),
    KEY `idx_org_code` (`org_code`),
    KEY `idx_sync_direction` (`sync_direction`),
    KEY `idx_sync_status` (`sync_status`),
    KEY `idx_sync_time` (`sync_time`),
    KEY `idx_api_org_time` (`api_code`, `org_code`, `sync_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='HIS数据同步日志表';

-- =====================================================
-- 8. HIS回写日志表 (his_writeback_log)
-- 用途：记录医保接口结果回写到HIS系统的操作日志
-- =====================================================
CREATE TABLE `his_writeback_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 回写基本信息
    `writeback_id` VARCHAR(50) NOT NULL COMMENT '回写ID',
    `api_code` VARCHAR(10) NOT NULL COMMENT '医保接口编码',
    `org_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    
    -- 数据内容
    `medical_result` JSON NOT NULL COMMENT '医保接口处理结果',
    `his_data` JSON NOT NULL COMMENT 'HIS回写数据',
    
    -- 回写状态和结果
    `writeback_status` VARCHAR(20) NOT NULL COMMENT '回写状态：success, failed, partial',
    `written_records` INT DEFAULT 0 COMMENT '成功回写记录数',
    `failed_records` INT DEFAULT 0 COMMENT '失败记录数',
    
    -- 错误信息
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    `error_details` JSON DEFAULT NULL COMMENT '详细错误信息',
    
    -- 时间信息
    `writeback_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '回写时间',
    `duration_ms` INT DEFAULT NULL COMMENT '回写耗时（毫秒）',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_writeback_id` (`writeback_id`),
    KEY `idx_api_code` (`api_code`),
    KEY `idx_org_code` (`org_code`),
    KEY `idx_writeback_status` (`writeback_status`),
    KEY `idx_writeback_time` (`writeback_time`),
    KEY `idx_api_org_time` (`api_code`, `org_code`, `writeback_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='HIS回写日志表';

-- =====================================================
-- 9. 数据一致性检查表 (data_consistency_checks)
-- 用途：记录医保系统与HIS系统的数据一致性检查结果
-- =====================================================
CREATE TABLE `data_consistency_checks` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 检查基本信息
    `check_id` VARCHAR(50) NOT NULL COMMENT '检查ID',
    `api_code` VARCHAR(10) NOT NULL COMMENT '医保接口编码',
    `org_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    
    -- 检查结果
    `check_result` JSON NOT NULL COMMENT '检查结果详情',
    `total_medical_records` INT DEFAULT 0 COMMENT '医保系统记录总数',
    `total_his_records` INT DEFAULT 0 COMMENT 'HIS系统记录总数',
    `consistent_count` INT DEFAULT 0 COMMENT '一致记录数',
    `inconsistent_count` INT DEFAULT 0 COMMENT '不一致记录数',
    `medical_only_count` INT DEFAULT 0 COMMENT '仅医保系统有的记录数',
    `his_only_count` INT DEFAULT 0 COMMENT '仅HIS系统有的记录数',
    
    -- 检查状态
    `check_status` VARCHAR(20) NOT NULL DEFAULT 'completed' COMMENT '检查状态：running, completed, failed',
    `consistency_rate` DECIMAL(5,2) DEFAULT 0.00 COMMENT '一致性比率（%）',
    
    -- 时间信息
    `check_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',
    `check_period_start` TIMESTAMP NOT NULL COMMENT '检查时间范围开始',
    `check_period_end` TIMESTAMP NOT NULL COMMENT '检查时间范围结束',
    `duration_ms` INT DEFAULT NULL COMMENT '检查耗时（毫秒）',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_check_id` (`check_id`),
    KEY `idx_api_code` (`api_code`),
    KEY `idx_org_code` (`org_code`),
    KEY `idx_check_status` (`check_status`),
    KEY `idx_check_time` (`check_time`),
    KEY `idx_consistency_rate` (`consistency_rate`),
    KEY `idx_api_org_time` (`api_code`, `org_code`, `check_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据一致性检查表';

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;