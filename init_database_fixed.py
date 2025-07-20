#!/usr/bin/env python3
"""
修复版数据库初始化脚本
"""

import pymysql
import os
import re

def execute_sql_statements(connection, sql_content, file_name):
    """正确解析和执行SQL语句"""
    print(f"\n执行SQL文件: {file_name}")
    
    # 移除注释和空行
    lines = sql_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # 跳过注释行和空行
        if line and not line.startswith('--') and not line.startswith('#'):
            cleaned_lines.append(line)
    
    # 重新组合SQL内容
    sql_content = ' '.join(cleaned_lines)
    
    # 处理DELIMITER语句
    if 'DELIMITER' in sql_content:
        # 分割DELIMITER块
        parts = re.split(r'DELIMITER\s+(\S+)', sql_content)
        current_delimiter = ';'
        statements = []
        
        for i, part in enumerate(parts):
            if i % 2 == 0:  # SQL内容
                if part.strip():
                    # 按当前分隔符分割
                    stmts = [s.strip() for s in part.split(current_delimiter) if s.strip()]
                    statements.extend(stmts)
            else:  # 分隔符
                current_delimiter = part.strip()
    else:
        # 简单按分号分割
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    # 执行语句
    success_count = 0
    error_count = 0
    
    with connection.cursor() as cursor:
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                # 跳过一些特殊语句
                if any(skip in statement.upper() for skip in ['SOURCE', 'DELIMITER']):
                    continue
                
                cursor.execute(statement)
                success_count += 1
                print(f"✅ 语句 {i+1}: 执行成功")
                
            except Exception as e:
                error_count += 1
                print(f"❌ 语句 {i+1}: {e}")
                # 对于某些错误，我们继续执行
                if "already exists" in str(e).lower():
                    print("   (表已存在，跳过)")
                    continue
    
    connection.commit()
    print(f"文件执行完成: 成功 {success_count}, 失败 {error_count}")
    return success_count > 0

def init_database():
    """初始化数据库"""
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'wodemima',
        'database': 'medical_insurance',
        'charset': 'utf8mb4'
    }
    
    print("开始初始化医保SDK数据库...")
    print(f"连接配置: {config['host']}:{config['port']}/{config['database']}")
    
    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        print("✅ 数据库连接成功")
        
        # 直接执行表创建SQL
        table_sql = """
-- 设置字符集和排序规则
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 接口配置表
CREATE TABLE IF NOT EXISTS `medical_interface_config` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `api_code` VARCHAR(10) NOT NULL COMMENT '接口编码',
    `api_name` VARCHAR(200) NOT NULL COMMENT '接口名称',
    `api_description` TEXT COMMENT '接口描述',
    `business_category` VARCHAR(50) NOT NULL COMMENT '业务分类',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    `required_params` JSON NOT NULL DEFAULT ('{}') COMMENT '必填参数配置',
    `optional_params` JSON DEFAULT ('{}') COMMENT '可选参数配置',
    `default_values` JSON DEFAULT ('{}') COMMENT '默认值配置',
    `request_template` JSON DEFAULT ('{}') COMMENT '请求模板',
    `param_mapping` JSON DEFAULT ('{}') COMMENT '参数映射规则',
    `validation_rules` JSON DEFAULT ('{}') COMMENT '数据验证规则',
    `response_mapping` JSON DEFAULT ('{}') COMMENT '响应字段映射',
    `success_condition` VARCHAR(200) DEFAULT 'infcode=0' COMMENT '成功条件',
    `error_handling` JSON DEFAULT ('{}') COMMENT '错误处理配置',
    `region_specific` JSON DEFAULT ('{}') COMMENT '地区特殊配置',
    `province_overrides` JSON DEFAULT ('{}') COMMENT '省份级别覆盖配置',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `requires_auth` BOOLEAN DEFAULT TRUE COMMENT '是否需要认证',
    `supports_batch` BOOLEAN DEFAULT FALSE COMMENT '是否支持批量',
    `max_retry_times` INT DEFAULT 3 COMMENT '最大重试次数',
    `timeout_seconds` INT DEFAULT 30 COMMENT '超时时间（秒）',
    `config_version` VARCHAR(50) DEFAULT '1.0' COMMENT '配置版本',
    `last_updated_by` VARCHAR(100) COMMENT '最后更新人',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_api_code` (`api_code`),
    KEY `idx_business_category` (`business_category`),
    KEY `idx_business_type` (`business_type`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口配置表';

-- 2. 机构配置表
CREATE TABLE IF NOT EXISTS `medical_organization_config` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `org_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    `org_name` VARCHAR(200) NOT NULL COMMENT '机构名称',
    `org_type` VARCHAR(10) NOT NULL COMMENT '机构类型',
    `province_code` VARCHAR(6) NOT NULL COMMENT '省份代码',
    `city_code` VARCHAR(6) NOT NULL COMMENT '城市代码',
    `area_code` VARCHAR(6) DEFAULT NULL COMMENT '地区代码',
    `app_id` VARCHAR(100) NOT NULL COMMENT '应用ID',
    `app_secret` VARCHAR(200) NOT NULL COMMENT '应用密钥',
    `base_url` VARCHAR(500) NOT NULL COMMENT '接口基础URL',
    `crypto_type` VARCHAR(20) DEFAULT 'SM4' COMMENT '加密方式',
    `sign_type` VARCHAR(20) DEFAULT 'SM3' COMMENT '签名算法',
    `cert_path` VARCHAR(500) DEFAULT NULL COMMENT '证书路径',
    `private_key_path` VARCHAR(500) DEFAULT NULL COMMENT '私钥路径',
    `default_timeout` INT DEFAULT 30 COMMENT '默认超时时间（秒）',
    `connect_timeout` INT DEFAULT 10 COMMENT '连接超时时间（秒）',
    `read_timeout` INT DEFAULT 30 COMMENT '读取超时时间（秒）',
    `max_retry_times` INT DEFAULT 3 COMMENT '最大重试次数',
    `retry_interval` INT DEFAULT 1000 COMMENT '重试间隔（毫秒）',
    `extra_config` JSON DEFAULT ('{}') COMMENT '扩展配置',
    `gateway_config` JSON DEFAULT ('{}') COMMENT '网关配置',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `is_test_env` BOOLEAN DEFAULT FALSE COMMENT '是否测试环境',
    `last_health_check` TIMESTAMP NULL COMMENT '最后健康检查时间',
    `health_status` VARCHAR(20) DEFAULT 'unknown' COMMENT '健康状态',
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

-- 3. 业务操作日志表（简化版，不使用分区）
CREATE TABLE IF NOT EXISTS `business_operation_logs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `operation_id` VARCHAR(50) NOT NULL COMMENT '唯一操作ID',
    `api_code` VARCHAR(10) NOT NULL COMMENT '接口编码',
    `api_name` VARCHAR(200) NOT NULL COMMENT '接口名称',
    `business_category` VARCHAR(50) NOT NULL COMMENT '业务分类',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    `institution_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    `psn_no` VARCHAR(30) DEFAULT NULL COMMENT '人员编号',
    `mdtrt_id` VARCHAR(30) DEFAULT NULL COMMENT '就医登记号',
    `request_data` JSON NOT NULL COMMENT '请求数据',
    `response_data` JSON DEFAULT NULL COMMENT '响应数据',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
    `error_code` VARCHAR(50) DEFAULT NULL COMMENT '错误代码',
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    `operation_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    `complete_time` TIMESTAMP NULL COMMENT '完成时间',
    `response_time_ms` INT DEFAULT NULL COMMENT '响应时间（毫秒）',
    `operator_id` VARCHAR(50) DEFAULT NULL COMMENT '操作员ID',
    `operator_name` VARCHAR(100) DEFAULT NULL COMMENT '操作员姓名',
    `trace_id` VARCHAR(50) NOT NULL COMMENT '链路追踪ID',
    `client_ip` VARCHAR(45) DEFAULT NULL COMMENT '客户端IP',
    `user_agent` VARCHAR(500) DEFAULT NULL COMMENT '用户代理',
    `request_id` VARCHAR(50) DEFAULT NULL COMMENT '请求ID',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用业务操作日志表';

-- 4. 医药机构信息表
CREATE TABLE IF NOT EXISTS `medical_institution_info` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `fixmedins_code` VARCHAR(12) NOT NULL COMMENT '定点医药机构编号',
    `fixmedins_name` VARCHAR(200) NOT NULL COMMENT '定点医药机构名称',
    `uscc` VARCHAR(50) NOT NULL COMMENT '统一社会信用代码',
    `fixmedins_type` VARCHAR(6) NOT NULL COMMENT '定点医疗服务机构类型',
    `hosp_lv` VARCHAR(6) DEFAULT NULL COMMENT '医院等级',
    `exp_content` VARCHAR(4000) DEFAULT NULL COMMENT '扩展字段',
    `sync_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '同步时间',
    `data_version` VARCHAR(50) DEFAULT NULL COMMENT '数据版本号',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_fixmedins_code` (`fixmedins_code`),
    KEY `idx_fixmedins_name` (`fixmedins_name`),
    KEY `idx_uscc` (`uscc`),
    KEY `idx_fixmedins_type` (`fixmedins_type`),
    KEY `idx_hosp_lv` (`hosp_lv`),
    KEY `idx_sync_time` (`sync_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='医药机构信息表';

-- 5. 接口调用统计表
CREATE TABLE IF NOT EXISTS `medical_interface_stats` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `stat_date` DATE NOT NULL COMMENT '统计日期',
    `institution_code` VARCHAR(20) NOT NULL COMMENT '机构编码',
    `api_code` VARCHAR(10) NOT NULL COMMENT '接口编码',
    `business_category` VARCHAR(50) NOT NULL COMMENT '业务分类',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    `total_calls` INT DEFAULT 0 COMMENT '调用总数',
    `success_calls` INT DEFAULT 0 COMMENT '成功数量',
    `failed_calls` INT DEFAULT 0 COMMENT '失败数量',
    `pending_calls` INT DEFAULT 0 COMMENT '处理中数量',
    `avg_response_time` DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均响应时间（毫秒）',
    `max_response_time` INT DEFAULT 0 COMMENT '最大响应时间（毫秒）',
    `min_response_time` INT DEFAULT 0 COMMENT '最小响应时间（毫秒）',
    `error_types` JSON DEFAULT ('{}') COMMENT '错误类型统计',
    `top_errors` JSON DEFAULT ('{}') COMMENT 'TOP错误信息',
    `hourly_distribution` JSON DEFAULT ('{}') COMMENT '小时分布统计',
    `success_rate` DECIMAL(5,2) DEFAULT 0.00 COMMENT '成功率（%）',
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
"""
        
        # 执行表创建SQL
        execute_sql_statements(connection, table_sql, "表创建脚本")
        
        # 验证表是否创建成功
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print(f"\n✅ 数据库初始化成功！创建了 {len(tables)} 个表:")
                for table in tables:
                    print(f"   - {table[0]}")
                    
                # 检查每个表的结构
                print(f"\n表结构验证:")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"   {table[0]}: {count} 条记录")
                    
            else:
                print("⚠️  数据库初始化完成，但没有创建表")
                return False
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎉 数据库初始化完成！现在可以正常使用医保SDK了。")
    else:
        print("\n❌ 数据库初始化失败，请检查错误信息。")