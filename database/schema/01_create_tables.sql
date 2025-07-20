-- 医保接口SDK数据库表结构
-- 创建时间: 2024-01-15
-- 版本: 1.0.0

-- 设置字符集和排序规则
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. 接口配置表 (medical_interface_config)
-- 用途：配置不同医保接口的参数和字段映射
-- =====================================================
CREATE TABLE `medical_interface_config` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 接口基本信息
    `api_code` VARCHAR(10) NOT NULL COMMENT '接口编码（如1101、2207等）',
    `api_name` VARCHAR(200) NOT NULL COMMENT '接口名称',
    `api_description` TEXT COMMENT '接口描述',
    `business_category` VARCHAR(50) NOT NULL COMMENT '业务分类',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    
    -- 接口参数配置
    `required_params` JSON NOT NULL DEFAULT ('{}') COMMENT '必填参数配置',
    `optional_params` JSON DEFAULT ('{}') COMMENT '可选参数配置',
    `default_values` JSON DEFAULT ('{}') COMMENT '默认值配置',
    
    -- 请求配置
    `request_template` JSON DEFAULT ('{}') COMMENT '请求模板',
    `param_mapping` JSON DEFAULT ('{}') COMMENT '参数映射规则',
    `validation_rules` JSON DEFAULT ('{}') COMMENT '数据验证规则',
    
    -- 响应配置
    `response_mapping` JSON DEFAULT ('{}') COMMENT '响应字段映射',
    `success_condition` VARCHAR(200) DEFAULT 'infcode=0' COMMENT '成功条件',
    `error_handling` JSON DEFAULT ('{}') COMMENT '错误处理配置',
    
    -- 地区差异配置
    `region_specific` JSON DEFAULT ('{}') COMMENT '地区特殊配置',
    `province_overrides` JSON DEFAULT ('{}') COMMENT '省份级别覆盖配置',
    
    -- 接口特性
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `requires_auth` BOOLEAN DEFAULT TRUE COMMENT '是否需要认证',
    `supports_batch` BOOLEAN DEFAULT FALSE COMMENT '是否支持批量',
    `max_retry_times` INT DEFAULT 3 COMMENT '最大重试次数',
    `timeout_seconds` INT DEFAULT 30 COMMENT '超时时间（秒）',
    
    -- 版本和同步
    `config_version` VARCHAR(50) DEFAULT '1.0' COMMENT '配置版本',
    `last_updated_by` VARCHAR(100) COMMENT '最后更新人',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_api_code` (`api_code`),
    KEY `idx_business_category` (`business_category`),
    KEY `idx_business_type` (`business_type`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口配置表';

-- =====================================================
-- 2. 机构配置表 (medical_organization_config)
-- 用途：存储不同医院的接入配置信息
-- =====================================================
CREATE TABLE `medical_organization_config` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 机构基本信息
    `org_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    `org_name` VARCHAR(200) NOT NULL COMMENT '机构名称',
    `org_type` VARCHAR(10) NOT NULL COMMENT '机构类型',
    `province_code` VARCHAR(6) NOT NULL COMMENT '省份代码',
    `city_code` VARCHAR(6) NOT NULL COMMENT '城市代码',
    `area_code` VARCHAR(6) DEFAULT NULL COMMENT '地区代码',
    
    -- 接入配置
    `app_id` VARCHAR(100) NOT NULL COMMENT '应用ID',
    `app_secret` VARCHAR(200) NOT NULL COMMENT '应用密钥',
    `base_url` VARCHAR(500) NOT NULL COMMENT '接口基础URL',
    
    -- 安全配置
    `crypto_type` VARCHAR(20) DEFAULT 'SM4' COMMENT '加密方式',
    `sign_type` VARCHAR(20) DEFAULT 'SM3' COMMENT '签名算法',
    `cert_path` VARCHAR(500) DEFAULT NULL COMMENT '证书路径',
    `private_key_path` VARCHAR(500) DEFAULT NULL COMMENT '私钥路径',
    
    -- 超时配置
    `default_timeout` INT DEFAULT 30 COMMENT '默认超时时间（秒）',
    `connect_timeout` INT DEFAULT 10 COMMENT '连接超时时间（秒）',
    `read_timeout` INT DEFAULT 30 COMMENT '读取超时时间（秒）',
    
    -- 重试配置
    `max_retry_times` INT DEFAULT 3 COMMENT '最大重试次数',
    `retry_interval` INT DEFAULT 1000 COMMENT '重试间隔（毫秒）',
    
    -- 扩展配置
    `extra_config` JSON DEFAULT ('{}') COMMENT '扩展配置',
    `gateway_config` JSON DEFAULT ('{}') COMMENT '网关配置',
    
    -- 状态管理
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `is_test_env` BOOLEAN DEFAULT FALSE COMMENT '是否测试环境',
    `last_health_check` TIMESTAMP NULL COMMENT '最后健康检查时间',
    `health_status` VARCHAR(20) DEFAULT 'unknown' COMMENT '健康状态',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by` VARCHAR(100) COMMENT '创建人',
    `updated_by` VARCHAR(100) COMMENT '更新人',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_org_code` (`org_code`),
    KEY `idx_org_name` (`org_name`),
    KEY `idx_province_city` (`province_code`, `city_code`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_health_status` (`health_status`),
    KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构配置表';

-- =====================================================
-- 3. 通用业务操作日志表 (business_operation_logs)
-- 用途：存储所有174个医保接口的调用记录和响应数据，支持分区存储
-- =====================================================
CREATE TABLE `business_operation_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 主键和唯一标识
    `operation_id` VARCHAR(50) NOT NULL COMMENT '唯一操作ID',
    
    -- 接口信息
    `api_code` VARCHAR(10) NOT NULL COMMENT '接口编码',
    `api_name` VARCHAR(200) NOT NULL COMMENT '接口名称',
    
    -- 业务分类
    `business_category` VARCHAR(50) NOT NULL COMMENT '业务分类（结算/备案/查询等）',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型（门诊/住院/药房等）',
    
    -- 机构和人员
    `institution_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    `psn_no` VARCHAR(30) DEFAULT NULL COMMENT '人员编号',
    `mdtrt_id` VARCHAR(30) DEFAULT NULL COMMENT '就医登记号',
    
    -- 数据存储
    `request_data` JSON NOT NULL COMMENT '请求数据（JSONB格式）',
    `response_data` JSON DEFAULT NULL COMMENT '响应数据（JSONB格式）',
    
    -- 状态管理
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态（success/failed/pending/processing）',
    `error_code` VARCHAR(50) DEFAULT NULL COMMENT '错误代码',
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    
    -- 时间信息
    `operation_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    `complete_time` TIMESTAMP NULL COMMENT '完成时间',
    `response_time_ms` INT DEFAULT NULL COMMENT '响应时间（毫秒）',
    
    -- 操作员信息
    `operator_id` VARCHAR(50) DEFAULT NULL COMMENT '操作员ID',
    `operator_name` VARCHAR(100) DEFAULT NULL COMMENT '操作员姓名',
    
    -- 系统信息
    `trace_id` VARCHAR(50) NOT NULL COMMENT '链路追踪ID',
    `client_ip` VARCHAR(45) DEFAULT NULL COMMENT '客户端IP',
    `user_agent` VARCHAR(500) DEFAULT NULL COMMENT '用户代理',
    `request_id` VARCHAR(50) DEFAULT NULL COMMENT '请求ID',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`, `operation_time`),
    UNIQUE KEY `uk_operation_id` (`operation_id`),
    KEY `idx_api_code_time` (`api_code`, `operation_time` DESC),
    KEY `idx_institution_time` (`institution_code`, `operation_time` DESC),
    KEY `idx_business_category` (`business_category`),
    KEY `idx_business_type` (`business_type`),
    KEY `idx_status_time` (`status`, `operation_time` DESC),
    KEY `idx_psn_time` (`psn_no`, `operation_time` DESC),
    KEY `idx_mdtrt_time` (`mdtrt_id`, `operation_time` DESC),
    KEY `idx_trace_id` (`trace_id`),
    KEY `idx_complete_time` (`complete_time`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用业务操作日志表'
PARTITION BY RANGE (UNIX_TIMESTAMP(`operation_time`)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01 00:00:00')),
    PARTITION p202402 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01 00:00:00')),
    PARTITION p202403 VALUES LESS THAN (UNIX_TIMESTAMP('2024-04-01 00:00:00')),
    PARTITION p202404 VALUES LESS THAN (UNIX_TIMESTAMP('2024-05-01 00:00:00')),
    PARTITION p202405 VALUES LESS THAN (UNIX_TIMESTAMP('2024-06-01 00:00:00')),
    PARTITION p202406 VALUES LESS THAN (UNIX_TIMESTAMP('2024-07-01 00:00:00')),
    PARTITION p202407 VALUES LESS THAN (UNIX_TIMESTAMP('2024-08-01 00:00:00')),
    PARTITION p202408 VALUES LESS THAN (UNIX_TIMESTAMP('2024-09-01 00:00:00')),
    PARTITION p202409 VALUES LESS THAN (UNIX_TIMESTAMP('2024-10-01 00:00:00')),
    PARTITION p202410 VALUES LESS THAN (UNIX_TIMESTAMP('2024-11-01 00:00:00')),
    PARTITION p202411 VALUES LESS THAN (UNIX_TIMESTAMP('2024-12-01 00:00:00')),
    PARTITION p202412 VALUES LESS THAN (UNIX_TIMESTAMP('2025-01-01 00:00:00')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- =====================================================
-- 4. 医药机构信息表 (medical_institution_info)
-- 用途：存储1201接口获取的医药机构详细信息
-- =====================================================
CREATE TABLE `medical_institution_info` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 机构基本信息（完全对应接口输出字段）
    `fixmedins_code` VARCHAR(12) NOT NULL COMMENT '定点医药机构编号',
    `fixmedins_name` VARCHAR(200) NOT NULL COMMENT '定点医药机构名称',
    `uscc` VARCHAR(50) NOT NULL COMMENT '统一社会信用代码',
    `fixmedins_type` VARCHAR(6) NOT NULL COMMENT '定点医疗服务机构类型',
    `hosp_lv` VARCHAR(6) DEFAULT NULL COMMENT '医院等级',
    `exp_content` VARCHAR(4000) DEFAULT NULL COMMENT '扩展字段',
    
    -- 同步相关字段
    `sync_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '同步时间',
    `data_version` VARCHAR(50) DEFAULT NULL COMMENT '数据版本号',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_fixmedins_code` (`fixmedins_code`),
    KEY `idx_fixmedins_name` (`fixmedins_name`),
    KEY `idx_uscc` (`uscc`),
    KEY `idx_fixmedins_type` (`fixmedins_type`),
    KEY `idx_hosp_lv` (`hosp_lv`),
    KEY `idx_sync_time` (`sync_time`),
    FULLTEXT KEY `ft_fixmedins_name` (`fixmedins_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='医药机构信息表';

-- =====================================================
-- 5. 接口调用统计表 (medical_interface_stats)
-- 用途：存储接口调用的统计数据
-- =====================================================
CREATE TABLE `medical_interface_stats` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    
    -- 统计维度
    `stat_date` DATE NOT NULL COMMENT '统计日期',
    `institution_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    `api_code` VARCHAR(10) NOT NULL COMMENT '接口编码',
    `business_category` VARCHAR(50) NOT NULL COMMENT '业务分类',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    
    -- 调用统计
    `total_calls` INT DEFAULT 0 COMMENT '调用总数',
    `success_calls` INT DEFAULT 0 COMMENT '成功数量',
    `failed_calls` INT DEFAULT 0 COMMENT '失败数量',
    `pending_calls` INT DEFAULT 0 COMMENT '处理中数量',
    
    -- 性能统计
    `avg_response_time` DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均响应时间（毫秒）',
    `max_response_time` INT DEFAULT 0 COMMENT '最大响应时间（毫秒）',
    `min_response_time` INT DEFAULT 0 COMMENT '最小响应时间（毫秒）',
    
    -- 错误统计
    `error_types` JSON DEFAULT ('{}') COMMENT '错误类型统计',
    `top_errors` JSON DEFAULT ('{}') COMMENT 'TOP错误信息',
    
    -- 趋势数据
    `hourly_distribution` JSON DEFAULT ('{}') COMMENT '小时分布统计',
    `success_rate` DECIMAL(5,2) DEFAULT 0.00 COMMENT '成功率（%）',
    
    -- 审计字段
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_stat_date_inst_api` (`stat_date`, `institution_code`, `api_code`),
    KEY `idx_stat_date` (`stat_date`),
    KEY `idx_institution_code` (`institution_code`),
    KEY `idx_api_code` (`api_code`),
    KEY `idx_business_category` (`business_category`),
    KEY `idx_success_rate` (`success_rate`),
    KEY `idx_total_calls` (`total_calls`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口调用统计表';

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;