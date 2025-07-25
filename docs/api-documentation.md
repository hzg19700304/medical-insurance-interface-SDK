# 医保接口SDK API文档

## 概述

医保接口SDK是一个通用的医保接口调用工具，支持所有174个医保接口的统一调用。SDK采用配置驱动的设计，通过数据库配置管理接口参数、验证规则和数据映射，无需为每个接口编写专门的代码。

## 快速开始

### 安装和配置

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置数据库**
```bash
# 初始化数据库
python init_database_fixed.py

# 插入测试数据
python insert_test_organization.py
python insert_test_interfaces.py
```

3. **配置环境变量**
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
# 设置数据库连接、Redis配置等
```

### 基本使用

```python
from medical_insurance_sdk import MedicalInsuranceClient

# 创建客户端
client = MedicalInsuranceClient()

# 调用人员信息查询接口(1101)
result = client.call_interface(
    api_code="1101",
    input_data={
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    },
    org_code="H43010300001"
)

print("查询结果:", result)
```

## 核心API

### MedicalInsuranceClient

主要的客户端类，提供统一的接口调用方法。

#### 初始化

```python
from medical_insurance_sdk import MedicalInsuranceClient

# 使用默认配置
client = MedicalInsuranceClient()

# 使用自定义配置
from medical_insurance_sdk.config import SDKConfig
config = SDKConfig(
    database_url="mysql://user:pass@localhost/medical_insurance",
    redis_url="redis://localhost:6379/0"
)
client = MedicalInsuranceClient(config)
```

#### call_interface() - 同步接口调用

**方法签名**
```python
def call_interface(self, api_code: str, input_data: dict, org_code: str, **kwargs) -> dict
```

**参数说明**
- `api_code` (str): 医保接口编码，如"1101"、"2201"等
- `input_data` (dict): 接口输入数据，具体字段根据接口而定
- `org_code` (str): 机构编码，用于获取机构配置
- `**kwargs`: 其他可选参数

**返回值**
- `dict`: 解析后的接口响应数据

**示例**
```python
# 人员信息查询
result = client.call_interface(
    api_code="1101",
    input_data={
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01", 
        "certno": "430123199001011234",
        "psn_name": "张三"
    },
    org_code="H43010300001"
)

# 门诊结算
result = client.call_interface(
    api_code="2201", 
    input_data={
        "mdtrt_id": "MDT20240115001",
        "psn_no": "430123199001011234",
        "chrg_bchno": "CHG20240115001",
        "acct_used_flag": "0"
    },
    org_code="H43010300001"
)
```

#### call_interface_async() - 异步接口调用

**方法签名**
```python
def call_interface_async(self, api_code: str, input_data: dict, org_code: str, **kwargs) -> str
```

**参数说明**
- 参数与同步方法相同

**返回值**
- `str`: 异步任务ID，可用于查询任务状态

**示例**
```python
# 提交异步任务
task_id = client.call_interface_async(
    api_code="1101",
    input_data={...},
    org_code="H43010300001"
)

# 查询任务状态
status = client.get_async_task_status(task_id)
print(f"任务状态: {status}")

# 获取任务结果
if status == "completed":
    result = client.get_async_task_result(task_id)
    print("任务结果:", result)
```

### 数据处理工具

#### DataHelper - 数据处理辅助类

提供常用的数据提取和格式化方法。

```python
from medical_insurance_sdk.utils import DataHelper

# 提取人员基本信息
person_info = DataHelper.extract_person_basic_info(response_data)
# 返回: {'name': '张三', 'id': '123456', 'gender': '1', ...}

# 提取参保信息
insurance_list = DataHelper.extract_insurance_info(response_data)
# 返回: [{'type': '310', 'balance': 1000.0, 'status': '1'}, ...]

# 计算总余额
total_balance = DataHelper.calculate_total_balance(insurance_list)
# 返回: 1000.0

# 格式化结算摘要
settlement = DataHelper.format_settlement_summary(response_data)
# 返回: {'settlement_id': 'S123', 'total': 500.0, 'insurance_pay': 400.0, ...}
```

## 接口配置

### 配置驱动的设计

SDK采用配置驱动的设计，所有接口的参数验证、数据转换和响应解析都通过数据库配置管理。

### 接口配置表结构

接口配置存储在`medical_interface_config`表中，主要字段包括：

- `api_code`: 接口编码
- `api_name`: 接口名称
- `required_params`: 必填参数配置
- `optional_params`: 可选参数配置
- `validation_rules`: 验证规则
- `response_mapping`: 响应数据映射
- `default_values`: 默认值配置

### 配置示例

#### 人员信息查询接口(1101)配置

```json
{
  "api_code": "1101",
  "api_name": "人员信息获取",
  "required_params": {
    "mdtrt_cert_type": {"display_name": "就诊凭证类型"},
    "mdtrt_cert_no": {"display_name": "就诊凭证编号"},
    "psn_cert_type": {"display_name": "人员证件类型"},
    "certno": {"display_name": "证件号码"},
    "psn_name": {"display_name": "人员姓名"}
  },
  "validation_rules": {
    "mdtrt_cert_type": {
      "enum_values": ["01", "02", "03"]
    },
    "certno": {
      "pattern": "^[0-9]{17}[0-9Xx]$",
      "pattern_error": "身份证号码格式不正确"
    }
  },
  "response_mapping": {
    "person_info": {"type": "direct", "source_path": "baseinfo"},
    "insurance_list": {"type": "array_mapping", "source_path": "insuinfo"}
  }
}
```

### 机构配置

机构配置存储在`medical_organization_config`表中，包含：

- 机构基本信息（编码、名称、地区）
- 接口认证信息（app_id、app_secret、base_url）
- 加密配置（crypto_type、sign_type）
- 超时配置

## 数据验证

### 验证规则

SDK支持多种验证规则：

1. **必填字段验证**
```json
{
  "required_params": {
    "psn_name": {"display_name": "人员姓名"}
  }
}
```

2. **格式验证**
```json
{
  "validation_rules": {
    "certno": {
      "pattern": "^[0-9]{17}[0-9Xx]$",
      "pattern_error": "身份证号码格式不正确"
    }
  }
}
```

3. **枚举值验证**
```json
{
  "validation_rules": {
    "mdtrt_cert_type": {
      "enum_values": ["01", "02", "03"]
    }
  }
}
```

4. **条件依赖验证**
```json
{
  "validation_rules": {
    "conditional_rules": [
      {
        "condition": {"field": "mdtrt_cert_type", "operator": "eq", "value": "03"},
        "required_fields": ["card_sn"],
        "error_message": "使用社保卡时卡识别码不能为空"
      }
    ]
  }
}
```

### 验证错误处理

当数据验证失败时，SDK会抛出`ValidationException`异常：

```python
from medical_insurance_sdk.exceptions import ValidationException

try:
    result = client.call_interface("1101", invalid_data, "H43010300001")
except ValidationException as e:
    print("验证失败:", e.message)
    print("错误详情:", e.details)
    # 输出: {'certno': ['身份证号码格式不正确']}
```

## 响应数据处理

### 数据映射规则

SDK支持多种响应数据映射类型：

1. **直接映射**
```json
{
  "person_info": {
    "type": "direct",
    "source_path": "baseinfo"
  }
}
```

2. **数组映射**
```json
{
  "insurance_list": {
    "type": "array_mapping",
    "source_path": "insuinfo",
    "item_mapping": {
      "insurance_type": "insutype",
      "balance": "balc"
    }
  }
}
```

3. **计算字段**
```json
{
  "total_balance": {
    "type": "computed",
    "expression": "sum([item.get('balc', 0) for item in ${insuinfo}])"
  }
}
```

4. **条件映射**
```json
{
  "has_insurance": {
    "type": "conditional",
    "condition": {"field": "insuinfo", "operator": "not_empty"},
    "true_rule": {"type": "direct", "source_path": "true"},
    "false_rule": {"type": "direct", "source_path": "false"}
  }
}
```

## 错误处理

### 异常类型

SDK定义了完整的异常体系：

```python
from medical_insurance_sdk.exceptions import (
    MedicalInsuranceException,    # 基础异常
    ValidationException,          # 数据验证异常
    ConfigurationException,       # 配置异常
    NetworkException,            # 网络异常
    AuthenticationException,     # 认证异常
    BusinessException           # 业务异常
)
```

### 错误处理示例

```python
try:
    result = client.call_interface("1101", data, "H43010300001")
except ValidationException as e:
    # 数据验证错误
    print(f"数据验证失败: {e.message}")
    print(f"错误详情: {e.details}")
except AuthenticationException as e:
    # 认证错误
    print(f"认证失败: {e.message}")
except NetworkException as e:
    # 网络错误
    print(f"网络异常: {e.message}")
    print(f"是否可重试: {e.retryable}")
except BusinessException as e:
    # 业务错误
    print(f"业务异常: {e.message}")
    print(f"错误代码: {e.error_code}")
except MedicalInsuranceException as e:
    # 其他异常
    print(f"SDK异常: {e.message}")
```

## 日志和监控

### 日志配置

SDK使用结构化日志记录所有接口调用：

```python
import logging
from medical_insurance_sdk.utils.logger import setup_logging

# 配置日志
setup_logging(
    level=logging.INFO,
    log_file="logs/medical_insurance_sdk.log",
    max_file_size="10MB",
    backup_count=5
)
```

### 日志格式

```json
{
  "timestamp": "2024-01-15 10:30:00",
  "level": "INFO",
  "api_code": "1101",
  "org_code": "H43010300001",
  "operation_id": "OP20240115103000001",
  "trace_id": "TR20240115103000001",
  "duration_ms": 1500,
  "status": "success",
  "message": "接口调用成功"
}
```

### 监控指标

SDK提供丰富的监控指标：

```python
from medical_insurance_sdk.core.metrics_collector import MetricsCollector

# 获取监控指标
metrics = MetricsCollector()
stats = metrics.get_interface_stats("1101", "H43010300001")

print(f"调用次数: {stats['call_count']}")
print(f"成功率: {stats['success_rate']}")
print(f"平均响应时间: {stats['avg_response_time']}ms")
```

## 性能优化

### 连接池配置

```python
from medical_insurance_sdk.config import SDKConfig

config = SDKConfig(
    database_pool_size=20,
    database_max_overflow=30,
    redis_pool_size=10,
    http_pool_connections=20,
    http_pool_maxsize=20
)
```

### 缓存配置

```python
# 配置缓存
config = SDKConfig(
    cache_enabled=True,
    cache_ttl=300,  # 5分钟
    cache_interface_config=True,
    cache_org_config=True
)
```

### 异步处理

对于耗时较长的接口调用，建议使用异步处理：

```python
# 异步调用
task_id = client.call_interface_async("1101", data, "H43010300001")

# 轮询结果
import time
while True:
    status = client.get_async_task_status(task_id)
    if status in ["completed", "failed"]:
        break
    time.sleep(1)

if status == "completed":
    result = client.get_async_task_result(task_id)
```

## 常见问题

### Q: 如何添加新的医保接口？

A: 只需在`medical_interface_config`表中添加新接口的配置即可，无需修改代码：

```sql
INSERT INTO medical_interface_config (
    api_code, api_name, business_category, business_type,
    required_params, validation_rules, response_mapping, is_active
) VALUES (
    '1102', '新接口名称', '查询类', '人员查询',
    '{"param1": {"display_name": "参数1"}}',
    '{"param1": {"pattern": "^[0-9]+$"}}',
    '{"result": {"type": "direct", "source_path": "output"}}',
    1
);
```

### Q: 如何处理不同地区的接口差异？

A: 在接口配置的`region_specific`字段中配置地区特殊规则：

```json
{
  "region_specific": {
    "hunan": {
      "special_params": {"recer_sys_code": "HIS_HN"}
    },
    "guangdong": {
      "special_params": {"recer_sys_code": "HIS_GD"},
      "encryption": "SM4"
    }
  }
}
```

### Q: 如何调试接口调用问题？

A: 1. 检查日志文件中的详细调用记录
   2. 查看数据库中的`business_operation_logs`表
   3. 使用调试模式获取更详细的信息：

```python
import logging
logging.getLogger('medical_insurance_sdk').setLevel(logging.DEBUG)

# 启用详细日志
client = MedicalInsuranceClient(debug=True)
```

### Q: 如何优化接口调用性能？

A: 1. 启用缓存减少配置查询
   2. 使用连接池复用数据库连接
   3. 对于批量操作使用异步处理
   4. 合理配置超时时间

```python
config = SDKConfig(
    cache_enabled=True,
    database_pool_size=20,
    http_timeout=30
)
```

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持配置驱动的通用接口处理
- 实现完整的数据验证和映射功能
- 支持异步处理和监控统计

---

更多详细信息请参考：
- [接口配置说明](interface-configuration-guide.md)
- [故障排除指南](troubleshooting-guide.md)
- [最佳实践](best-practices.md)