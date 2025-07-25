# 医保接口配置指南

## 概述

本文档详细说明如何配置医保接口，包括接口参数配置、验证规则设置、数据映射规则等。通过配置驱动的设计，可以在不修改代码的情况下支持所有174个医保接口。

## 配置表结构

### medical_interface_config 表

接口配置的核心表，包含以下主要字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| api_code | VARCHAR(10) | 接口编码，如"1101" |
| api_name | VARCHAR(200) | 接口名称 |
| business_category | VARCHAR(50) | 业务分类 |
| business_type | VARCHAR(50) | 业务类型 |
| required_params | JSONB | 必填参数配置 |
| optional_params | JSONB | 可选参数配置 |
| validation_rules | JSONB | 验证规则 |
| response_mapping | JSONB | 响应数据映射 |
| default_values | JSONB | 默认值配置 |
| region_specific | JSONB | 地区特殊配置 |

## 参数配置

### required_params - 必填参数

定义接口的必填参数及其描述信息：

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
  "psn_name": {
    "display_name": "人员姓名",
    "description": "参保人姓名"
  }
}
```

### optional_params - 可选参数

定义接口的可选参数：

```json
{
  "card_sn": {
    "display_name": "卡识别码",
    "description": "社保卡识别码，使用社保卡时必填"
  },
  "begntime": {
    "display_name": "开始时间",
    "description": "查询开始时间，格式：yyyy-MM-dd"
  }
}
```

### default_values - 默认值

为参数设置默认值：

```json
{
  "psn_cert_type": "01",
  "begntime": "",
  "acct_used_flag": "0"
}
```

## 验证规则配置

### 基础验证规则

#### 1. 长度验证

```json
{
  "validation_rules": {
    "psn_name": {
      "max_length": 50,
      "min_length": 2
    }
  }
}
```

#### 2. 正则表达式验证

```json
{
  "validation_rules": {
    "certno": {
      "pattern": "^[0-9]{17}[0-9Xx]$",
      "pattern_error": "身份证号码格式不正确"
    },
    "mobile": {
      "pattern": "^1[3-9]\\d{9}$",
      "pattern_error": "手机号码格式不正确"
    }
  }
}
```

#### 3. 枚举值验证

```json
{
  "validation_rules": {
    "mdtrt_cert_type": {
      "enum_values": ["01", "02", "03"],
      "enum_error": "就诊凭证类型必须是01、02或03"
    },
    "gend": {
      "enum_values": ["1", "2"],
      "enum_error": "性别必须是1（男）或2（女）"
    }
  }
}
```

#### 4. 数值范围验证

```json
{
  "validation_rules": {
    "age": {
      "min_value": 0,
      "max_value": 150,
      "value_error": "年龄必须在0-150之间"
    },
    "amount": {
      "min_value": 0.01,
      "decimal_places": 2,
      "value_error": "金额必须大于0且最多2位小数"
    }
  }
}
```

### 高级验证规则

#### 1. 条件依赖验证

当某个字段的值满足特定条件时，其他字段变为必填：

```json
{
  "validation_rules": {
    "conditional_rules": [
      {
        "condition": {
          "field": "mdtrt_cert_type",
          "operator": "eq",
          "value": "03"
        },
        "required_fields": ["card_sn"],
        "error_message": "使用社保卡时卡识别码不能为空"
      },
      {
        "condition": {
          "field": "psn_type",
          "operator": "in",
          "value": ["1", "2"]
        },
        "required_fields": ["work_unit"],
        "error_message": "在职人员必须填写工作单位"
      }
    ]
  }
}
```

#### 2. 字段关联验证

验证多个字段之间的关系：

```json
{
  "validation_rules": {
    "field_relations": [
      {
        "type": "date_range",
        "start_field": "begntime",
        "end_field": "endtime",
        "error_message": "开始时间不能晚于结束时间"
      },
      {
        "type": "mutual_exclusive",
        "fields": ["certno", "card_no"],
        "error_message": "身份证号和卡号不能同时为空"
      }
    ]
  }
}
```

#### 3. 数据转换规则

在验证前对数据进行预处理：

```json
{
  "validation_rules": {
    "data_transforms": {
      "psn_name": {"type": "trim_spaces"},
      "certno": {"type": "string_upper"},
      "mobile": {"type": "remove_spaces"},
      "amount": {"type": "round_decimal", "places": 2}
    }
  }
}
```

## 响应数据映射

### 映射类型

#### 1. 直接映射 (direct)

直接从响应数据中提取字段：

```json
{
  "response_mapping": {
    "person_info": {
      "type": "direct",
      "source_path": "baseinfo"
    },
    "person_name": {
      "type": "direct", 
      "source_path": "baseinfo.psn_name"
    }
  }
}
```

#### 2. 数组映射 (array_mapping)

处理数组类型的响应数据：

```json
{
  "response_mapping": {
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
    }
  }
}
```

#### 3. 计算字段 (computed)

通过表达式计算得出的字段：

```json
{
  "response_mapping": {
    "total_balance": {
      "type": "computed",
      "expression": "sum([float(item.get('balc', 0)) for item in ${insuinfo}])"
    },
    "age_group": {
      "type": "computed", 
      "expression": "'儿童' if int(${baseinfo.age}) < 18 else ('青年' if int(${baseinfo.age}) < 35 else ('中年' if int(${baseinfo.age}) < 60 else '老年'))"
    }
  }
}
```

#### 4. 条件映射 (conditional)

根据条件选择不同的映射规则：

```json
{
  "response_mapping": {
    "has_insurance": {
      "type": "conditional",
      "condition": {
        "field": "insuinfo",
        "operator": "not_empty"
      },
      "true_rule": {
        "type": "direct",
        "source_path": "true"
      },
      "false_rule": {
        "type": "direct", 
        "source_path": "false"
      }
    },
    "insurance_status": {
      "type": "conditional",
      "condition": {
        "field": "baseinfo.psn_insu_stas",
        "operator": "eq",
        "value": "1"
      },
      "true_rule": {
        "type": "direct",
        "source_path": "'正常参保'"
      },
      "false_rule": {
        "type": "direct",
        "source_path": "'非正常参保'"
      }
    }
  }
}
```

#### 5. 嵌套映射 (nested)

处理嵌套结构的数据：

```json
{
  "response_mapping": {
    "settlement_detail": {
      "type": "nested",
      "source_path": "setlinfo",
      "mapping": {
        "settlement_id": "setl_id",
        "total_amount": "setl_totlnum",
        "payment_info": {
          "type": "nested",
          "source_path": "payinfo",
          "mapping": {
            "insurance_pay": "hifp_pay",
            "personal_pay": "psn_pay",
            "account_pay": "acct_pay"
          }
        }
      }
    }
  }
}
```

### 表达式语法

在计算字段中可以使用以下语法：

#### 变量引用
- `${field_name}`: 引用响应数据中的字段
- `${parent.child}`: 引用嵌套字段

#### 常用函数
- `sum(list)`: 求和
- `len(list)`: 获取长度
- `max(list)`: 最大值
- `min(list)`: 最小值
- `float(value)`: 转换为浮点数
- `int(value)`: 转换为整数
- `str(value)`: 转换为字符串

#### 示例表达式
```json
{
  "total_count": "len(${insuinfo})",
  "max_balance": "max([float(item.get('balc', 0)) for item in ${insuinfo}])",
  "formatted_name": "str(${baseinfo.psn_name}).strip().upper()",
  "is_adult": "int(${baseinfo.age}) >= 18"
}
```

## 地区差异配置

### region_specific 配置

不同地区的医保接口可能存在差异，通过`region_specific`字段配置：

```json
{
  "region_specific": {
    "hunan": {
      "special_params": {
        "recer_sys_code": "HIS_HN"
      },
      "validation_overrides": {
        "certno": {
          "pattern": "^43[0-9]{16}[0-9Xx]$",
          "pattern_error": "湖南省身份证号码必须以43开头"
        }
      }
    },
    "guangdong": {
      "special_params": {
        "recer_sys_code": "HIS_GD"
      },
      "encryption": "SM4",
      "timeout_seconds": 60
    },
    "beijing": {
      "special_params": {
        "recer_sys_code": "HIS_BJ",
        "extra_header": "X-Region: BJ"
      },
      "response_mapping_overrides": {
        "person_name": {
          "type": "direct",
          "source_path": "baseinfo.name"
        }
      }
    }
  }
}
```

### 地区配置的应用

SDK会根据机构配置中的地区信息自动应用相应的地区配置：

```python
# 机构配置中指定地区
org_config = {
    "org_code": "H43010300001",
    "province_code": "430000",
    "region": "hunan"  # 指定地区
}

# SDK会自动应用湖南地区的特殊配置
result = client.call_interface("1101", data, "H43010300001")
```

## 配置示例

### 完整的接口配置示例

以下是人员信息查询接口(1101)的完整配置：

```sql
INSERT INTO medical_interface_config (
    api_code, api_name, business_category, business_type,
    required_params, optional_params, default_values,
    validation_rules, response_mapping, region_specific, is_active
) VALUES (
    '1101',
    '人员信息获取',
    '查询类',
    '人员查询',
    -- required_params
    '{
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
    }',
    -- optional_params
    '{
        "card_sn": {
            "display_name": "卡识别码",
            "description": "社保卡识别码，使用社保卡时必填"
        },
        "begntime": {
            "display_name": "开始时间",
            "description": "查询开始时间，格式：yyyy-MM-dd"
        }
    }',
    -- default_values
    '{
        "psn_cert_type": "01",
        "begntime": ""
    }',
    -- validation_rules
    '{
        "mdtrt_cert_type": {
            "enum_values": ["01", "02", "03"],
            "enum_error": "就诊凭证类型必须是01、02或03"
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
        ],
        "data_transforms": {
            "psn_name": {"type": "trim_spaces"},
            "certno": {"type": "string_upper"}
        }
    }',
    -- response_mapping
    '{
        "person_info": {
            "type": "direct",
            "source_path": "baseinfo"
        },
        "person_name": {
            "type": "direct",
            "source_path": "baseinfo.psn_name"
        },
        "person_id": {
            "type": "direct",
            "source_path": "baseinfo.psn_no"
        },
        "id_card": {
            "type": "direct",
            "source_path": "baseinfo.certno"
        },
        "gender": {
            "type": "direct",
            "source_path": "baseinfo.gend"
        },
        "birth_date": {
            "type": "direct",
            "source_path": "baseinfo.brdy"
        },
        "age": {
            "type": "direct",
            "source_path": "baseinfo.age"
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
        "identity_list": {
            "type": "array_mapping",
            "source_path": "idetinfo",
            "item_mapping": {
                "identity_type": "psn_idet_type",
                "level": "psn_type_lv",
                "start_time": "begntime",
                "end_time": "endtime"
            }
        },
        "total_balance": {
            "type": "computed",
            "expression": "sum([float(item.get(\"balc\", 0)) for item in ${insuinfo}])"
        },
        "has_insurance": {
            "type": "conditional",
            "condition": {
                "field": "insuinfo",
                "operator": "not_empty"
            },
            "true_rule": {
                "type": "direct",
                "source_path": "true"
            },
            "false_rule": {
                "type": "direct",
                "source_path": "false"
            }
        },
        "age_group": {
            "type": "computed",
            "expression": "\"儿童\" if int(${baseinfo.age}) < 18 else (\"青年\" if int(${baseinfo.age}) < 35 else (\"中年\" if int(${baseinfo.age}) < 60 else \"老年\"))"
        }
    }',
    -- region_specific
    '{
        "hunan": {
            "special_params": {
                "recer_sys_code": "HIS_HN"
            },
            "validation_overrides": {
                "certno": {
                    "pattern": "^43[0-9]{16}[0-9Xx]$",
                    "pattern_error": "湖南省身份证号码必须以43开头"
                }
            }
        },
        "guangdong": {
            "special_params": {
                "recer_sys_code": "HIS_GD"
            },
            "encryption": "SM4"
        }
    }',
    1
);
```

## 配置管理工具

### 配置验证脚本

创建配置验证脚本来检查配置的正确性：

```python
# scripts/validate_interface_config.py
import json
import sys
from medical_insurance_sdk.config import ConfigManager

def validate_config(api_code):
    """验证接口配置"""
    config_manager = ConfigManager()
    
    try:
        config = config_manager.get_interface_config(api_code)
        print(f"✓ 接口 {api_code} 配置加载成功")
        
        # 验证必填参数
        if not config.required_params:
            print("⚠ 警告: 未配置必填参数")
        
        # 验证响应映射
        if not config.response_mapping:
            print("⚠ 警告: 未配置响应映射")
            
        # 验证JSON格式
        for field in ['required_params', 'validation_rules', 'response_mapping']:
            value = getattr(config, field)
            if value:
                try:
                    json.dumps(value)
                except Exception as e:
                    print(f"✗ 错误: {field} JSON格式无效: {e}")
                    return False
        
        print(f"✓ 接口 {api_code} 配置验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 错误: 接口 {api_code} 配置验证失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python validate_interface_config.py <api_code>")
        sys.exit(1)
    
    api_code = sys.argv[1]
    success = validate_config(api_code)
    sys.exit(0 if success else 1)
```

### 配置导入导出工具

```python
# scripts/config_manager.py
import json
import sys
from medical_insurance_sdk.config import ConfigManager

def export_config(api_code, output_file):
    """导出接口配置"""
    config_manager = ConfigManager()
    config = config_manager.get_interface_config(api_code)
    
    config_data = {
        'api_code': config.api_code,
        'api_name': config.api_name,
        'business_category': config.business_category,
        'business_type': config.business_type,
        'required_params': config.required_params,
        'optional_params': config.optional_params,
        'validation_rules': config.validation_rules,
        'response_mapping': config.response_mapping,
        'default_values': config.default_values,
        'region_specific': config.region_specific
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    print(f"配置已导出到: {output_file}")

def import_config(input_file):
    """导入接口配置"""
    with open(input_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 这里需要实现数据库插入逻辑
    print(f"配置已从 {input_file} 导入")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法:")
        print("  导出: python config_manager.py export <api_code> <output_file>")
        print("  导入: python config_manager.py import <input_file>")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "export":
        export_config(sys.argv[2], sys.argv[3])
    elif action == "import":
        import_config(sys.argv[2])
    else:
        print("未知操作:", action)
        sys.exit(1)
```

## 最佳实践

### 1. 配置设计原则

- **完整性**: 确保所有必要的参数和验证规则都已配置
- **一致性**: 相同类型的接口使用一致的配置模式
- **可维护性**: 使用清晰的字段名和详细的描述信息
- **可扩展性**: 预留扩展字段，便于后续功能增强

### 2. 验证规则设计

- **渐进式验证**: 从基础验证到复杂验证逐步配置
- **友好的错误信息**: 提供清晰、具体的错误提示
- **性能考虑**: 避免过于复杂的正则表达式和计算

### 3. 响应映射设计

- **结构化输出**: 设计清晰的输出数据结构
- **字段命名**: 使用有意义的字段名，便于理解和使用
- **数据类型**: 确保映射后的数据类型正确

### 4. 地区配置管理

- **最小化差异**: 尽量减少地区间的配置差异
- **文档记录**: 详细记录各地区的特殊配置和原因
- **版本控制**: 对配置变更进行版本控制和审核

---

更多信息请参考：
- [API文档](api-documentation.md)
- [故障排除指南](troubleshooting-guide.md)
- [最佳实践](best-practices.md)