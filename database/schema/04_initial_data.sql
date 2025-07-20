-- 医保接口SDK初始化数据
-- 创建时间: 2024-01-15
-- 版本: 1.0.0

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- 1. 接口配置表初始数据
-- =====================================================

-- 1101 人员基本信息获取接口配置
INSERT INTO `medical_interface_config` (
    `api_code`, `api_name`, `api_description`, `business_category`, `business_type`,
    `required_params`, `optional_params`, `default_values`,
    `request_template`, `response_mapping`, `validation_rules`,
    `region_specific`, `is_active`, `timeout_seconds`, `max_retry_times`
) VALUES (
    '1101', 
    '人员基本信息获取', 
    '通过人员编号获取参保人员基本信息',
    '基础信息业务',
    'query',
    JSON_OBJECT(
        'mdtrt_cert_type', JSON_OBJECT('display_name', '就诊凭证类型', 'description', '01-电子凭证；02-身份证；03-社保卡'),
        'mdtrt_cert_no', JSON_OBJECT('display_name', '就诊凭证编号', 'description', '凭证对应的编号'),
        'psn_cert_type', JSON_OBJECT('display_name', '人员证件类型', 'description', '01-身份证'),
        'certno', JSON_OBJECT('display_name', '证件号码', 'description', '身份证号码'),
        'psn_name', JSON_OBJECT('display_name', '人员姓名', 'description', '参保人姓名')
    ),
    JSON_OBJECT(
        'card_sn', JSON_OBJECT('display_name', '卡识别码', 'description', '社保卡识别码'),
        'begntime', JSON_OBJECT('display_name', '开始时间', 'description', '查询开始时间')
    ),
    JSON_OBJECT(
        'psn_cert_type', '01',
        'begntime', ''
    ),
    JSON_OBJECT(
        'data', JSON_OBJECT(
            'mdtrt_cert_type', '${mdtrt_cert_type}',
            'mdtrt_cert_no', '${mdtrt_cert_no}',
            'card_sn', '${card_sn}',
            'begntime', '${begntime}',
            'psn_cert_type', '${psn_cert_type}',
            'certno', '${certno}',
            'psn_name', '${psn_name}'
        )
    ),
    JSON_OBJECT(
        'person_info', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo'),
        'person_name', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo.psn_name'),
        'person_id', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo.psn_no'),
        'id_card', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo.certno'),
        'gender', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo.gend'),
        'birth_date', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo.brdy'),
        'age', JSON_OBJECT('type', 'direct', 'source_path', 'baseinfo.age'),
        'insurance_list', JSON_OBJECT(
            'type', 'array_mapping',
            'source_path', 'insuinfo',
            'item_mapping', JSON_OBJECT(
                'insurance_type', 'insutype',
                'person_type', 'psn_type',
                'balance', 'balc',
                'status', 'psn_insu_stas',
                'start_date', 'psn_insu_date'
            )
        ),
        'identity_list', JSON_OBJECT(
            'type', 'array_mapping',
            'source_path', 'idetinfo',
            'item_mapping', JSON_OBJECT(
                'identity_type', 'psn_idet_type',
                'level', 'psn_type_lv',
                'start_time', 'begntime',
                'end_time', 'endtime'
            )
        ),
        'total_balance', JSON_OBJECT(
            'type', 'computed',
            'expression', 'sum([item.get("balc", 0) for item in ${insuinfo}])'
        )
    ),
    JSON_OBJECT(
        'mdtrt_cert_type', JSON_OBJECT(
            'enum_values', JSON_ARRAY('01', '02', '03'),
            'pattern_error', '就诊凭证类型必须是01、02或03'
        ),
        'mdtrt_cert_no', JSON_OBJECT(
            'max_length', 50,
            'pattern', '^[A-Za-z0-9]+$',
            'pattern_error', '就诊凭证编号只能包含字母和数字'
        ),
        'certno', JSON_OBJECT(
            'max_length', 18,
            'pattern', '^[0-9]{17}[0-9Xx]$',
            'pattern_error', '身份证号码格式不正确'
        ),
        'psn_name', JSON_OBJECT(
            'max_length', 50,
            'pattern', '^[\\u4e00-\\u9fa5·]+$',
            'pattern_error', '人员姓名只能包含中文字符和·'
        ),
        'conditional_rules', JSON_ARRAY(
            JSON_OBJECT(
                'condition', JSON_OBJECT('field', 'mdtrt_cert_type', 'operator', 'eq', 'value', '03'),
                'required_fields', JSON_ARRAY('card_sn'),
                'error_message', '使用社保卡时卡识别码不能为空'
            )
        ),
        'data_transforms', JSON_OBJECT(
            'psn_name', JSON_OBJECT('type', 'remove_spaces'),
            'certno', JSON_OBJECT('type', 'string_upper')
        )
    ),
    JSON_OBJECT(
        'hunan', JSON_OBJECT(
            'special_params', JSON_OBJECT(
                'recer_sys_code', 'HIS_HN'
            )
        ),
        'guangdong', JSON_OBJECT(
            'special_params', JSON_OBJECT(
                'recer_sys_code', 'HIS_GD'
            ),
            'encryption', 'SM4'
        )
    ),
    1, 30, 3
);

-- 2201 门诊结算接口配置
INSERT INTO `medical_interface_config` (
    `api_code`, `api_name`, `api_description`, `business_category`, `business_type`,
    `required_params`, `optional_params`, `default_values`,
    `request_template`, `response_mapping`, `validation_rules`,
    `region_specific`, `is_active`, `timeout_seconds`, `max_retry_times`
) VALUES (
    '2201', 
    '门诊结算', 
    '门诊费用结算处理',
    '医保服务业务',
    'settlement',
    JSON_OBJECT(
        'mdtrt_id', JSON_OBJECT('display_name', '就诊ID', 'description', '医疗机构就诊ID'),
        'psn_no', JSON_OBJECT('display_name', '人员编号', 'description', '医保人员编号'),
        'chrg_bchno', JSON_OBJECT('display_name', '收费批次号', 'description', '收费批次号'),
        'acct_used_flag', JSON_OBJECT('display_name', '个人账户使用标志', 'description', '0-不使用，1-使用')
    ),
    JSON_OBJECT(
        'insutype', JSON_OBJECT('display_name', '险种类型', 'description', '险种类型代码'),
        'invono', JSON_OBJECT('display_name', '发票号', 'description', '发票号码'),
        'fulamt_ownpay_amt', JSON_OBJECT('display_name', '全自费金额', 'description', '全自费金额'),
        'overlmt_selfpay', JSON_OBJECT('display_name', '超限价自费费用', 'description', '超限价自费费用'),
        'preselfpay_amt', JSON_OBJECT('display_name', '先行自付金额', 'description', '先行自付金额')
    ),
    JSON_OBJECT(
        'acct_used_flag', '0',
        'insutype', '310',
        'fulamt_ownpay_amt', '0',
        'overlmt_selfpay', '0',
        'preselfpay_amt', '0'
    ),
    JSON_OBJECT(
        'data', JSON_OBJECT(
            'mdtrt_id', '${mdtrt_id}',
            'psn_no', '${psn_no}',
            'chrg_bchno', '${chrg_bchno}',
            'acct_used_flag', '${acct_used_flag}',
            'insutype', '${insutype}',
            'invono', '${invono}',
            'fulamt_ownpay_amt', '${fulamt_ownpay_amt}',
            'overlmt_selfpay', '${overlmt_selfpay}',
            'preselfpay_amt', '${preselfpay_amt}'
        )
    ),
    JSON_OBJECT(
        'settlement_result', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo'),
        'settlement_id', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.setl_id'),
        'settlement_time', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.setl_time'),
        'total_amount', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.medfee_sumamt'),
        'insurance_amount', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.hifp_pay'),
        'personal_amount', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.psn_pay_sumamt'),
        'account_pay', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.acct_pay'),
        'cash_pay', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.psn_cash_pay'),
        'fund_pay_sumamt', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.fund_pay_sumamt'),
        'ownpay_amt', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.ownpay_amt'),
        'other_pay', JSON_OBJECT('type', 'direct', 'source_path', 'setlinfo.oth_pay'),
        'settlement_summary', JSON_OBJECT(
            'type', 'computed',
            'expression', '{"total": ${setlinfo.medfee_sumamt}, "insurance": ${setlinfo.hifp_pay}, "personal": ${setlinfo.psn_pay_sumamt}}'
        )
    ),
    JSON_OBJECT(
        'mdtrt_id', JSON_OBJECT(
            'max_length', 30,
            'pattern', '^[A-Za-z0-9]+$',
            'pattern_error', '就诊ID格式不正确'
        ),
        'psn_no', JSON_OBJECT(
            'max_length', 30,
            'pattern', '^[0-9]+$',
            'pattern_error', '人员编号只能包含数字'
        ),
        'chrg_bchno', JSON_OBJECT(
            'max_length', 30,
            'pattern', '^[A-Za-z0-9]+$',
            'pattern_error', '收费批次号格式不正确'
        ),
        'acct_used_flag', JSON_OBJECT(
            'enum_values', JSON_ARRAY('0', '1'),
            'pattern_error', '个人账户使用标志必须是0或1'
        ),
        'insutype', JSON_OBJECT(
            'enum_values', JSON_ARRAY('310', '390', '410'),
            'pattern_error', '险种类型不正确'
        )
    ),
    JSON_OBJECT(
        'hunan', JSON_OBJECT(
            'special_params', JSON_OBJECT(
                'recer_sys_code', 'HIS_HN'
            ),
            'timeout_seconds', 60
        ),
        'guangdong', JSON_OBJECT(
            'special_params', JSON_OBJECT(
                'recer_sys_code', 'HIS_GD'
            ),
            'encryption', 'SM4',
            'timeout_seconds', 45
        )
    ),
    1, 60, 3
);

-- 1201 医药机构信息获取接口配置
INSERT INTO `medical_interface_config` (
    `api_code`, `api_name`, `api_description`, `business_category`, `business_type`,
    `required_params`, `optional_params`, `default_values`,
    `request_template`, `response_mapping`, `validation_rules`,
    `is_active`, `timeout_seconds`, `max_retry_times`
) VALUES (
    '1201', 
    '医药机构信息获取', 
    '获取定点医药机构信息',
    '基础信息业务',
    'query',
    JSON_OBJECT(
        'fixmedins_code', JSON_OBJECT('display_name', '定点医药机构编号', 'description', '12位机构编号'),
        'fixmedins_name', JSON_OBJECT('display_name', '定点医药机构名称', 'description', '机构名称')
    ),
    JSON_OBJECT(
        'fixmedins_type', JSON_OBJECT('display_name', '机构类型', 'description', '机构类型代码'),
        'hosp_lv', JSON_OBJECT('display_name', '医院等级', 'description', '医院等级代码')
    ),
    JSON_OBJECT(),
    JSON_OBJECT(
        'data', JSON_OBJECT(
            'fixmedins_code', '${fixmedins_code}',
            'fixmedins_name', '${fixmedins_name}',
            'fixmedins_type', '${fixmedins_type}',
            'hosp_lv', '${hosp_lv}'
        )
    ),
    JSON_OBJECT(
        'institution_info', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo'),
        'institution_code', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo.fixmedins_code'),
        'institution_name', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo.fixmedins_name'),
        'credit_code', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo.uscc'),
        'institution_type', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo.fixmedins_type'),
        'hospital_level', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo.hosp_lv'),
        'extension_content', JSON_OBJECT('type', 'direct', 'source_path', 'medinsinfo.exp_content')
    ),
    JSON_OBJECT(
        'fixmedins_code', JSON_OBJECT(
            'max_length', 12,
            'pattern', '^[A-Z0-9]{12}$',
            'pattern_error', '机构编号必须是12位字母数字组合'
        ),
        'fixmedins_name', JSON_OBJECT(
            'max_length', 200,
            'pattern', '^[\\u4e00-\\u9fa5A-Za-z0-9\\(\\)（）\\-_\\s]+$',
            'pattern_error', '机构名称格式不正确'
        )
    ),
    1, 30, 3
);

-- =====================================================
-- 2. 机构配置表初始数据
-- =====================================================

-- 测试机构配置
INSERT INTO `medical_organization_config` (
    `org_code`, `org_name`, `org_type`, `province_code`, `city_code`, `area_code`,
    `app_id`, `app_secret`, `base_url`,
    `crypto_type`, `sign_type`,
    `default_timeout`, `connect_timeout`, `read_timeout`,
    `max_retry_times`, `retry_interval`,
    `extra_config`, `gateway_config`,
    `is_active`, `is_test_env`, `health_status`,
    `created_by`, `updated_by`
) VALUES (
    'TEST001', 
    '测试医院', 
    '01', 
    '430000', 
    '430100', 
    '430102',
    'test_app_id_001',
    'test_app_secret_001',
    'https://test-api.medical.gov.cn',
    'SM4',
    'SM3',
    30, 10, 30,
    3, 1000,
    JSON_OBJECT(
        'recer_sys_code', 'HIS_TEST',
        'dev_no', 'TEST_DEVICE_001',
        'opter', 'TEST_OPERATOR',
        'opter_name', '测试操作员',
        'fixmedins_code', 'TEST00000001',
        'fixmedins_name', '测试医院',
        'mdtrtarea_admvs', '430100',
        'insuplc_admdvs', '430100'
    ),
    JSON_OBJECT(
        'api_name', 'yb_api',
        'api_version', '1.0.0'
    ),
    1, 1, 'unknown',
    'system', 'system'
);

-- 湖南省人民医院配置示例
INSERT INTO `medical_organization_config` (
    `org_code`, `org_name`, `org_type`, `province_code`, `city_code`, `area_code`,
    `app_id`, `app_secret`, `base_url`,
    `crypto_type`, `sign_type`,
    `default_timeout`, `connect_timeout`, `read_timeout`,
    `max_retry_times`, `retry_interval`,
    `extra_config`, `gateway_config`,
    `is_active`, `is_test_env`, `health_status`,
    `created_by`, `updated_by`
) VALUES (
    'H43010001', 
    '湖南省人民医院', 
    '01', 
    '430000', 
    '430100', 
    '430102',
    'hn_hospital_001',
    'hn_hospital_secret_001',
    'https://api.hnybj.gov.cn',
    'SM4',
    'SM3',
    45, 15, 45,
    3, 2000,
    JSON_OBJECT(
        'recer_sys_code', 'HIS_HN',
        'dev_no', 'HN_DEVICE_001',
        'opter', 'HN_OPERATOR_001',
        'opter_name', '湖南操作员',
        'fixmedins_code', 'H43010001001',
        'fixmedins_name', '湖南省人民医院',
        'mdtrtarea_admvs', '430100',
        'insuplc_admdvs', '430100'
    ),
    JSON_OBJECT(
        'api_name', 'yb_api',
        'api_version', '1.0.0'
    ),
    1, 0, 'unknown',
    'admin', 'admin'
);

-- 中南大学湘雅医院配置示例
INSERT INTO `medical_organization_config` (
    `org_code`, `org_name`, `org_type`, `province_code`, `city_code`, `area_code`,
    `app_id`, `app_secret`, `base_url`,
    `crypto_type`, `sign_type`,
    `default_timeout`, `connect_timeout`, `read_timeout`,
    `max_retry_times`, `retry_interval`,
    `extra_config`, `gateway_config`,
    `is_active`, `is_test_env`, `health_status`,
    `created_by`, `updated_by`
) VALUES (
    'H43010002', 
    '中南大学湘雅医院', 
    '01', 
    '430000', 
    '430100', 
    '430102',
    'xy_hospital_001',
    'xy_hospital_secret_001',
    'https://api.hnybj.gov.cn',
    'SM4',
    'SM3',
    45, 15, 45,
    3, 2000,
    JSON_OBJECT(
        'recer_sys_code', 'HIS_XY',
        'dev_no', 'XY_DEVICE_001',
        'opter', 'XY_OPERATOR_001',
        'opter_name', '湘雅操作员',
        'fixmedins_code', 'H43010002001',
        'fixmedins_name', '中南大学湘雅医院',
        'mdtrtarea_admvs', '430100',
        'insuplc_admdvs', '430100'
    ),
    JSON_OBJECT(
        'api_name', 'yb_api',
        'api_version', '1.0.0'
    ),
    1, 0, 'unknown',
    'admin', 'admin'
);

-- =====================================================
-- 3. 医药机构信息表初始数据
-- =====================================================

-- 测试机构信息
INSERT INTO `medical_institution_info` (
    `fixmedins_code`, `fixmedins_name`, `uscc`, `fixmedins_type`, `hosp_lv`, `exp_content`,
    `sync_time`, `data_version`
) VALUES (
    'TEST00000001', 
    '测试医院', 
    '12430000000000000X', 
    '101001', 
    '301001', 
    '测试用医院，仅用于开发和测试',
    CURRENT_TIMESTAMP,
    '1.0.0'
);

INSERT INTO `medical_institution_info` (
    `fixmedins_code`, `fixmedins_name`, `uscc`, `fixmedins_type`, `hosp_lv`, `exp_content`,
    `sync_time`, `data_version`
) VALUES (
    'H43010001001', 
    '湖南省人民医院', 
    '12430000123456789X', 
    '101001', 
    '301001', 
    '三级甲等综合医院',
    CURRENT_TIMESTAMP,
    '1.0.0'
);

INSERT INTO `medical_institution_info` (
    `fixmedins_code`, `fixmedins_name`, `uscc`, `fixmedins_type`, `hosp_lv`, `exp_content`,
    `sync_time`, `data_version`
) VALUES (
    'H43010002001', 
    '中南大学湘雅医院', 
    '12430000234567890X', 
    '101001', 
    '301001', 
    '三级甲等综合医院，教学医院',
    CURRENT_TIMESTAMP,
    '1.0.0'
);

INSERT INTO `medical_institution_info` (
    `fixmedins_code`, `fixmedins_name`, `uscc`, `fixmedins_type`, `hosp_lv`, `exp_content`,
    `sync_time`, `data_version`
) VALUES (
    'Y43010001001', 
    '湖南省中医药大学第一附属医院', 
    '12430000345678901X', 
    '102001', 
    '301001', 
    '三级甲等中医医院',
    CURRENT_TIMESTAMP,
    '1.0.0'
);

-- =====================================================
-- 4. 接口调用统计表初始数据（可选）
-- =====================================================

-- 创建当前月份的初始统计记录
INSERT INTO `medical_interface_stats` (
    `stat_date`, `institution_code`, `api_code`, `business_category`, `business_type`,
    `total_calls`, `success_calls`, `failed_calls`, `pending_calls`,
    `avg_response_time`, `max_response_time`, `min_response_time`, `success_rate`
) VALUES 
(CURDATE(), 'TEST001', '1101', '基础信息业务', 'query', 0, 0, 0, 0, 0.00, 0, 0, 0.00),
(CURDATE(), 'TEST001', '2201', '医保服务业务', 'settlement', 0, 0, 0, 0, 0.00, 0, 0, 0.00),
(CURDATE(), 'TEST001', '1201', '基础信息业务', 'query', 0, 0, 0, 0, 0.00, 0, 0, 0.00),
(CURDATE(), 'H43010001', '1101', '基础信息业务', 'query', 0, 0, 0, 0, 0.00, 0, 0, 0.00),
(CURDATE(), 'H43010001', '2201', '医保服务业务', 'settlement', 0, 0, 0, 0, 0.00, 0, 0, 0.00),
(CURDATE(), 'H43010002', '1101', '基础信息业务', 'query', 0, 0, 0, 0, 0.00, 0, 0, 0.00),
(CURDATE(), 'H43010002', '2201', '医保服务业务', 'settlement', 0, 0, 0, 0, 0.00, 0, 0, 0.00);

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 5. 验证初始化数据
-- =====================================================

-- 验证接口配置数据
SELECT 
    api_code as '接口编码',
    api_name as '接口名称',
    business_category as '业务分类',
    business_type as '业务类型',
    is_active as '是否启用',
    timeout_seconds as '超时时间',
    created_at as '创建时间'
FROM medical_interface_config 
ORDER BY api_code;

-- 验证机构配置数据
SELECT 
    org_code as '机构编码',
    org_name as '机构名称',
    province_code as '省份代码',
    city_code as '城市代码',
    is_active as '是否启用',
    is_test_env as '是否测试环境',
    created_at as '创建时间'
FROM medical_organization_config 
ORDER BY org_code;

-- 验证机构信息数据
SELECT 
    fixmedins_code as '机构编号',
    fixmedins_name as '机构名称',
    fixmedins_type as '机构类型',
    hosp_lv as '医院等级',
    sync_time as '同步时间'
FROM medical_institution_info 
ORDER BY fixmedins_code;

-- 验证统计数据
SELECT 
    stat_date as '统计日期',
    institution_code as '机构编码',
    api_code as '接口编码',
    business_category as '业务分类',
    total_calls as '总调用数'
FROM medical_interface_stats 
ORDER BY institution_code, api_code;

-- 显示初始化完成信息
SELECT '配置数据初始化完成！' as status;
SELECT CONCAT('接口配置数量: ', COUNT(*)) as interface_config_count FROM medical_interface_config;
SELECT CONCAT('机构配置数量: ', COUNT(*)) as organization_config_count FROM medical_organization_config;
SELECT CONCAT('机构信息数量: ', COUNT(*)) as institution_info_count FROM medical_institution_info;
SELECT CONCAT('统计记录数量: ', COUNT(*)) as stats_count FROM medical_interface_stats;