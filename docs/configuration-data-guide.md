# 医保接口SDK配置数据指南

## 概述

本文档详细说明了医保接口SDK的配置数据结构和使用方法，对应任务2.2的实现内容。

## 配置数据结构

### 1. 接口配置表 (medical_interface_config)

#### 1.1 人员信息获取接口 (1101)

**基本信息:**
- 接口编码: `1101`
- 接口名称: `人员基本信息获取`
- 业务分类: `基础信息业务`
- 业务类型: `query`

**必填参数配置:**
```json
{
  "mdtrt_cert_type": {
    "display_name": "就诊凭证类型",
    "description": "01-电子凭证；02-身份证；03-社保卡"
  },
  "mdtrt_cert_no": {
    "display_name": "就诊凭证编号",
    "description": "凭证对应的编号"
  },
  "psn_cert_type": {
    "display_name": "人员证件类型",
    "description": "01-身份证"
  },
  "certno": {
    "display_name": "证件号码",
    "description": "身份证号码"
  },
  "psn_name": {
    "display_name": "人员姓名",
    "description": "参保人姓名"
  }
}
```

**验证规则配置:**
```json
{
  "mdtrt_cert_type": {
    "enum_values": ["01", "02", "03"],
    "pattern_error": "就诊凭证类型必须是01、02或03"
  },
  "mdtrt_cert_no": {
    "max_length": 50,
    "pattern": "^[A-Za-z0-9]+$",
    "pattern_error": "就诊凭证编号只能包含字母和数字"
  },
  "certno": {
    "max_length": 18,
    "pattern": "^[0-9]{17}[0-9Xx]$",
    "pattern_error": "身份证号码格式不正确"
  },
  "psn_name": {
    "max_length": 50,
    "pattern": "^[\\u4e00-\\u9fa5·]+$",
    "pattern_error": "人员姓名只能包含中文字符和·"
  },
  "conditional_rules": [
    {
      "condition": {
        "field": "mdtrt_cert_type",
        "operator": "eq",
        "value": "03"
      },
      "required_fields": ["card_sn"],
      "error_message": "使用社保卡时卡识别码不能为空"
    }
  ]
}
```

**响应数据映射:**
```json
{
  "person_info": {
    "type": "direct",
    "source_path": "baseinfo"
  },
  "person_name": {
    "type": "direct",
    "source_path": "baseinfo.psn_name"
  },
  "insurance_list": {
    "type": "array_mapping",
    "source_path": "insuinfo",
    "item_mapping": {
      "insurance_type": "insutype",
      "person_type": "psn_type",
      "balance": "balc",
      "status": "psn_insu_stas",
      "start_date": "psn_insu_date"
    }
  },
  "total_balance": {
    "type": "computed",
    "expression": "sum([item.get(\"balc\", 0) for item in ${insuinfo}])"
  }
}
```

#### 1.2 门诊结算接口 (2201)

**基本信息:**
- 接口编码: `2201`
- 接口名称: `门诊结算`
- 业务分类: `医保服务业务`
- 业务类型: `settlement`

**必填参数配置:**
```json
{
  "mdtrt_id": {
    "display_name": "就诊ID",
    "description": "医疗机构就诊ID"
  },
  "psn_no": {
    "display_name": "人员编号",
    "description": "医保人员编号"
  },
  "chrg_bchno": {
    "display_name": "收费批次号",
    "description": "收费批次号"
  },
  "acct_used_flag": {
    "display_name": "个人账户使用标志",
    "description": "0-不使用，1-使用"
  }
}
```

**默认值配置:**
```json
{
  "acct_used_flag": "0",
  "insutype": "310",
  "fulamt_ownpay_amt": "0",
  "overlmt_selfpay": "0",
  "preselfpay_amt": "0"
}
```

**响应数据映射:**
```json
{
  "settlement_result": {
    "type": "direct",
    "source_path": "setlinfo"
  },
  "settlement_id": {
    "type": "direct",
    "source_path": "setlinfo.setl_id"
  },
  "total_amount": {
    "type": "direct",
    "source_path": "setlinfo.medfee_sumamt"
  },
  "insurance_amount": {
    "type": "direct",
    "source_path": "setlinfo.hifp_pay"
  },
  "personal_amount": {
    "type": "direct",
    "source_path": "setlinfo.psn_pay_sumamt"
  },
  "settlement_summary": {
    "type": "computed",
    "expression": "{\"total\": ${setlinfo.medfee_sumamt}, \"insurance\": ${setlinfo.hifp_pay}, \"personal\": ${setlinfo.psn_pay_sumamt}}"
  }
}
```

### 2. 机构配置表 (medical_organization_config)

#### 2.1 测试机构配置 (TEST001)

```json
{
  "org_code": "TEST001",
  "org_name": "测试医院",
  "org_type": "01",
  "province_code": "430000",
  "city_code": "430100",
  "area_code": "430102",
  "app_id": "test_app_id_001",
  "app_secret": "test_app_secret_001",
  "base_url": "https://test-api.medical.gov.cn",
  "crypto_type": "SM4",
  "sign_type": "SM3",
  "is_test_env": true,
  "extra_config": {
    "recer_sys_code": "HIS_TEST",
    "dev_no": "TEST_DEVICE_001",
    "opter": "TEST_OPERATOR",
    "opter_name": "测试操作员",
    "fixmedins_code": "TEST00000001",
    "fixmedins_name": "测试医院",
    "mdtrtarea_admvs": "430100",
    "insuplc_admdvs": "430100"
  }
}
```

#### 2.2 生产机构配置示例

**湖南省人民医院 (H43010001):**
```json
{
  "org_code": "H43010001",
  "org_name": "湖南省人民医院",
  "org_type": "01",
  "province_code": "430000",
  "city_code": "430100",
  "base_url": "https://api.hnybj.gov.cn",
  "is_test_env": false,
  "extra_config": {
    "recer_sys_code": "HIS_HN",
    "fixmedins_code": "H43010001001",
    "fixmedins_name": "湖南省人民医院"
  }
}
```

### 3. 机构信息表 (medical_institution_info)

包含4个机构的详细信息：

1. **测试医院** (TEST00000001)
2. **湖南省人民医院** (H43010001001)
3. **中南大学湘雅医院** (H43010002001)
4. **湖南省中医药大学第一附属医院** (Y43010001001)

每个机构包含以下信息：
- 定点医药机构编号 (fixmedins_code)
- 定点医药机构名称 (fixmedins_name)
- 统一社会信用代码 (uscc)
- 定点医疗服务机构类型 (fixmedins_type)
- 医院等级 (hosp_lv)
- 扩展字段 (exp_content)

## 使用方法

### 1. 数据库初始化

执行以下SQL文件来初始化配置数据：

```bash
# 方法1: 直接执行SQL文件
mysql -u username -p database_name < database/schema/04_initial_data.sql

# 方法2: 使用Python脚本
python scripts/initialize_config_data.py
```

### 2. 配置验证

使用验证脚本检查配置数据的完整性：

```bash
python scripts/validate_config_data.py
```

### 3. 配置使用示例

#### 3.1 获取接口配置

```python
from medical_insurance_sdk.config import ConfigManager

config_manager = ConfigManager(db_config)

# 获取1101接口配置
interface_config = config_manager.get_interface_config('1101')

# 获取机构配置
org_config = config_manager.get_organization_config('TEST001')
```

#### 3.2 使用通用接口处理器

```python
from medical_insurance_sdk.core import UniversalInterfaceProcessor

processor = UniversalInterfaceProcessor(sdk)

# 调用1101接口
result = processor.call_interface(
    api_code='1101',
    input_data={
        'mdtrt_cert_type': '02',
        'mdtrt_cert_no': '430123199001011234',
        'psn_cert_type': '01',
        'certno': '430123199001011234',
        'psn_name': '张三'
    },
    org_code='TEST001'
)

# 调用2201接口
settlement_result = processor.call_interface(
    api_code='2201',
    input_data={
        'mdtrt_id': 'MDT20240115001',
        'psn_no': '1234567890',
        'chrg_bchno': 'CHG20240115001',
        'acct_used_flag': '1'
    },
    org_code='TEST001'
)
```

## 配置扩展

### 1. 添加新接口配置

要添加新的接口配置，需要在 `medical_interface_config` 表中插入新记录：

```sql
INSERT INTO medical_interface_config (
    api_code, api_name, business_category, business_type,
    required_params, validation_rules, response_mapping,
    is_active
) VALUES (
    '新接口编码',
    '新接口名称',
    '业务分类',
    '业务类型',
    '必填参数JSON',
    '验证规则JSON',
    '响应映射JSON',
    1
);
```

### 2. 添加新机构配置

要添加新的机构配置，需要在 `medical_organization_config` 表中插入新记录：

```sql
INSERT INTO medical_organization_config (
    org_code, org_name, org_type, province_code, city_code,
    app_id, app_secret, base_url, crypto_type, sign_type,
    extra_config, is_active
) VALUES (
    '新机构编码',
    '新机构名称',
    '机构类型',
    '省份代码',
    '城市代码',
    '应用ID',
    '应用密钥',
    '接口地址',
    '加密方式',
    '签名算法',
    '扩展配置JSON',
    1
);
```

### 3. 地区差异配置

对于不同地区的特殊需求，可以在接口配置的 `region_specific` 字段中添加地区特殊配置：

```json
{
  "hunan": {
    "special_params": {
      "recer_sys_code": "HIS_HN"
    },
    "timeout_seconds": 60
  },
  "guangdong": {
    "special_params": {
      "recer_sys_code": "HIS_GD"
    },
    "encryption": "SM4",
    "timeout_seconds": 45
  }
}
```

## 注意事项

1. **数据安全**: 生产环境中的 `app_secret` 等敏感信息应该加密存储
2. **配置热更新**: 配置修改后可以通过 `ConfigManager.reload_config()` 方法热更新
3. **版本管理**: 每次配置修改都应该更新 `config_version` 和 `last_updated_by` 字段
4. **测试验证**: 新增配置后应该运行验证脚本确保配置正确性

## 总结

任务2.2已成功完成，包含：

- ✅ 人员信息获取接口(1101)的完整配置
- ✅ 门诊结算接口(2201)的配置数据  
- ✅ 测试机构的配置数据
- ✅ 医药机构信息数据
- ✅ 初始统计数据
- ✅ 配置验证和文档

所有配置数据已准备就绪，可以支持SDK的正常运行和扩展。