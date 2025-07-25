# 医保接口SDK故障排除指南

## 概述

本文档提供医保接口SDK常见问题的诊断和解决方案，帮助开发者快速定位和解决问题。

## 常见问题分类

### 1. 配置相关问题
### 2. 网络连接问题
### 3. 数据验证问题
### 4. 接口调用问题
### 5. 性能问题
### 6. 数据库问题

---

## 1. 配置相关问题

### 问题1.1: 找不到接口配置

**错误信息**:
```
ConfigurationException: 接口配置不存在: api_code=1101
```

**可能原因**:
- 数据库中没有对应接口的配置记录
- 接口配置被禁用 (is_active=false)
- 数据库连接问题

**解决方案**:

1. **检查数据库配置**:
```sql
SELECT * FROM medical_interface_config WHERE api_code = '1101';
```

2. **检查配置状态**:
```sql
SELECT api_code, api_name, is_active FROM medical_interface_config WHERE api_code = '1101';
```

3. **重新插入配置**:
```bash
python insert_test_interfaces.py
```

4. **验证配置加载**:
```python
from medical_insurance_sdk.config import ConfigManager
config_manager = ConfigManager()
config = config_manager.get_interface_config('1101')
print(config)
```

### 问题1.2: 机构配置不存在

**错误信息**:
```
ConfigurationException: 机构配置不存在: org_code=H43010300001
```

**解决方案**:

1. **检查机构配置**:
```sql
SELECT * FROM medical_organization_config WHERE org_code = 'H43010300001';
```

2. **插入测试机构配置**:
```bash
python insert_test_organization.py
```

### 问题1.3: JSON配置格式错误

**错误信息**:
```
json.JSONDecodeError: Expecting ',' delimiter: line 5 column 10
```

**解决方案**:

1. **验证JSON格式**:
```python
import json
config_str = '{"field": "value"}'  # 从数据库获取的配置
try:
    config = json.loads(config_str)
    print("JSON格式正确")
except json.JSONDecodeError as e:
    print(f"JSON格式错误: {e}")
```

2. **使用配置验证脚本**:
```bash
python scripts/validate_config_data.py
```

---

## 2. 网络连接问题

### 问题2.1: 连接超时

**错误信息**:
```
NetworkException: 连接超时: Read timeout
```

**解决方案**:

1. **检查网络连接**:
```bash
ping api.example.com
telnet api.example.com 80
```

2. **调整超时配置**:
```python
from medical_insurance_sdk.config import SDKConfig
config = SDKConfig(http_timeout=60)  # 增加到60秒
client = MedicalInsuranceClient(config)
```

3. **检查防火墙设置**:
```bash
# Windows
netsh advfirewall show allprofiles

# Linux
iptables -L
```

### 问题2.2: SSL证书验证失败

**错误信息**:
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**解决方案**:

1. **临时禁用SSL验证** (仅用于测试):
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

2. **配置证书路径**:
```python
config = SDKConfig(
    ssl_verify=True,
    ssl_cert_path="/path/to/cert.pem"
)
```

### 问题2.3: 代理配置问题

**解决方案**:

1. **配置HTTP代理**:
```python
config = SDKConfig(
    http_proxy="http://proxy.company.com:8080",
    https_proxy="https://proxy.company.com:8080"
)
```

2. **环境变量配置**:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
```

---

## 3. 数据验证问题

### 问题3.1: 必填字段验证失败

**错误信息**:
```
ValidationException: 数据验证失败
Details: {'psn_name': ['人员姓名不能为空']}
```

**解决方案**:

1. **检查输入数据**:
```python
input_data = {
    "mdtrt_cert_type": "02",
    "mdtrt_cert_no": "430123199001011234",
    "psn_cert_type": "01",
    "certno": "430123199001011234",
    "psn_name": "张三"  # 确保必填字段不为空
}
```

2. **查看接口配置的必填字段**:
```sql
SELECT required_params FROM medical_interface_config WHERE api_code = '1101';
```

### 问题3.2: 格式验证失败

**错误信息**:
```
ValidationException: 身份证号码格式不正确
```

**解决方案**:

1. **检查数据格式**:
```python
import re
certno = "430123199001011234"
pattern = r"^[0-9]{17}[0-9Xx]$"
if re.match(pattern, certno):
    print("格式正确")
else:
    print("格式错误")
```

2. **查看验证规则配置**:
```sql
SELECT validation_rules FROM medical_interface_config WHERE api_code = '1101';
```

### 问题3.3: 条件依赖验证失败

**错误信息**:
```
ValidationException: 使用社保卡时卡识别码不能为空
```

**解决方案**:

1. **检查条件依赖**:
```python
# 当mdtrt_cert_type为"03"时，card_sn为必填
input_data = {
    "mdtrt_cert_type": "03",  # 社保卡
    "card_sn": "1234567890",  # 必须提供卡识别码
    # ... 其他字段
}
```

---

## 4. 接口调用问题

### 问题4.1: 网关认证失败

**错误信息**:
```
AuthenticationException: 签名验证失败
```

**解决方案**:

1. **检查AK/SK配置**:
```sql
SELECT app_id, app_secret FROM medical_organization_config WHERE org_code = 'H43010300001';
```

2. **验证签名算法**:
```python
from medical_insurance_sdk.core.protocol_processor import GatewayHeaders
headers = GatewayHeaders("api_name", "1.0", "your_ak", "your_sk")
print(headers.generate_headers())
```

3. **检查时间戳**:
```python
import time
current_timestamp = int(time.time() * 1000)
print(f"当前时间戳: {current_timestamp}")
```

### 问题4.2: 接口返回业务错误

**错误信息**:
```
BusinessException: 人员信息不存在
Error Code: -1
```

**解决方案**:

1. **检查输入参数**:
   - 确认身份证号码正确
   - 确认人员在医保系统中存在
   - 检查参保状态

2. **查看完整的请求响应日志**:
```python
import logging
logging.getLogger('medical_insurance_sdk').setLevel(logging.DEBUG)
```

3. **使用测试数据**:
```python
# 使用已知存在的测试数据
test_data = {
    "mdtrt_cert_type": "02",
    "mdtrt_cert_no": "430123199001011234",  # 测试身份证号
    "psn_cert_type": "01",
    "certno": "430123199001011234",
    "psn_name": "测试用户"
}
```

### 问题4.3: 响应数据解析失败

**错误信息**:
```
DataParsingException: 响应数据解析失败: 'baseinfo' key not found
```

**解决方案**:

1. **检查响应数据结构**:
```python
# 查看原始响应数据
print("原始响应:", response.output)
```

2. **验证响应映射配置**:
```sql
SELECT response_mapping FROM medical_interface_config WHERE api_code = '1101';
```

3. **调试数据解析**:
```python
from medical_insurance_sdk.core.data_parser import DataParser
parser = DataParser(config_manager)
result = parser.parse_response_data(response_data, interface_config)
```

---

## 5. 性能问题

### 问题5.1: 接口调用缓慢

**症状**: 接口调用响应时间超过5秒

**诊断步骤**:

1. **检查网络延迟**:
```bash
ping api.example.com
```

2. **分析调用链路**:
```python
import time
start_time = time.time()
result = client.call_interface("1101", data, "H43010300001")
end_time = time.time()
print(f"调用耗时: {end_time - start_time:.2f}秒")
```

3. **查看性能指标**:
```python
from medical_insurance_sdk.core.metrics_collector import MetricsCollector
metrics = MetricsCollector()
stats = metrics.get_interface_stats("1101", "H43010300001")
print(f"平均响应时间: {stats['avg_response_time']}ms")
```

**优化方案**:

1. **启用缓存**:
```python
config = SDKConfig(
    cache_enabled=True,
    cache_ttl=300  # 5分钟缓存
)
```

2. **调整连接池**:
```python
config = SDKConfig(
    database_pool_size=20,
    http_pool_connections=20
)
```

3. **使用异步调用**:
```python
task_id = client.call_interface_async("1101", data, "H43010300001")
```

### 问题5.2: 内存使用过高

**诊断工具**:

1. **内存监控**:
```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f"内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")
```

2. **对象引用分析**:
```python
import gc
print(f"对象数量: {len(gc.get_objects())}")
```

**优化方案**:

1. **及时释放资源**:
```python
# 使用上下文管理器
with MedicalInsuranceClient() as client:
    result = client.call_interface("1101", data, "H43010300001")
```

2. **调整缓存大小**:
```python
config = SDKConfig(
    cache_max_size=1000,  # 限制缓存条目数量
    cache_ttl=300
)
```

---

## 6. 数据库问题

### 问题6.1: 数据库连接失败

**错误信息**:
```
DatabaseException: (2003, "Can't connect to MySQL server on 'localhost'")
```

**解决方案**:

1. **检查数据库服务状态**:
```bash
# Windows
net start mysql

# Linux
systemctl status mysql
```

2. **验证连接参数**:
```python
import pymysql
try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='password',
        database='medical_insurance'
    )
    print("数据库连接成功")
    connection.close()
except Exception as e:
    print(f"连接失败: {e}")
```

3. **检查防火墙和端口**:
```bash
netstat -an | grep 3306
```

### 问题6.2: 数据库表不存在

**错误信息**:
```
ProgrammingError: (1146, "Table 'medical_insurance.medical_interface_config' doesn't exist")
```

**解决方案**:

1. **重新初始化数据库**:
```bash
python init_database_fixed.py
```

2. **检查表结构**:
```sql
SHOW TABLES;
DESCRIBE medical_interface_config;
```

### 问题6.3: 数据库连接池耗尽

**错误信息**:
```
TimeoutError: QueuePool limit of size 20 overflow 30 reached
```

**解决方案**:

1. **调整连接池配置**:
```python
config = SDKConfig(
    database_pool_size=50,
    database_max_overflow=100,
    database_pool_timeout=30
)
```

2. **检查连接泄漏**:
```python
# 确保连接正确关闭
with database_manager.get_connection() as conn:
    # 执行数据库操作
    pass  # 连接会自动关闭
```

---

## 调试工具和技巧

### 1. 日志配置

**启用详细日志**:
```python
import logging

# 配置根日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 配置SDK日志
sdk_logger = logging.getLogger('medical_insurance_sdk')
sdk_logger.setLevel(logging.DEBUG)

# 配置数据库日志
db_logger = logging.getLogger('sqlalchemy.engine')
db_logger.setLevel(logging.INFO)
```

**查看日志文件**:
```bash
tail -f logs/medical_insurance_sdk.log
```

### 2. 数据库调试

**查看SQL执行**:
```python
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**手动执行SQL**:
```sql
-- 查看最近的接口调用记录
SELECT * FROM business_operation_logs 
ORDER BY operation_time DESC 
LIMIT 10;

-- 查看失败的调用记录
SELECT api_code, error_message, operation_time 
FROM business_operation_logs 
WHERE status = 'failed' 
ORDER BY operation_time DESC;
```

### 3. 网络调试

**抓包分析**:
```bash
# 使用tcpdump抓包
tcpdump -i any -w capture.pcap host api.example.com

# 使用Wireshark分析
wireshark capture.pcap
```

**HTTP请求调试**:
```python
import requests
import json

# 手动构造请求
headers = {
    'Content-Type': 'application/json',
    '_api_name': 'api_name',
    '_api_version': '1.0',
    # ... 其他头部
}

data = {
    "infno": "1101",
    "input": {...}
}

response = requests.post(
    'http://api.example.com/api',
    headers=headers,
    json=data,
    timeout=30
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
```

### 4. 性能分析

**使用cProfile**:
```python
import cProfile
import pstats

def profile_interface_call():
    client = MedicalInsuranceClient()
    result = client.call_interface("1101", data, "H43010300001")
    return result

# 性能分析
cProfile.run('profile_interface_call()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(10)
```

**内存分析**:
```python
from memory_profiler import profile

@profile
def memory_test():
    client = MedicalInsuranceClient()
    for i in range(100):
        result = client.call_interface("1101", data, "H43010300001")

memory_test()
```

---

## 常用诊断命令

### 系统环境检查
```bash
# Python版本
python --version

# 依赖包版本
pip list | grep -E "(mysql|redis|requests)"

# 系统资源
free -h  # Linux
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory  # Windows
```

### 数据库检查
```sql
-- 检查表结构
SHOW CREATE TABLE medical_interface_config;

-- 检查数据量
SELECT COUNT(*) FROM business_operation_logs;

-- 检查索引
SHOW INDEX FROM business_operation_logs;

-- 检查连接数
SHOW PROCESSLIST;
```

### 网络检查
```bash
# 端口连通性
telnet api.example.com 80

# DNS解析
nslookup api.example.com

# 路由跟踪
traceroute api.example.com  # Linux
tracert api.example.com     # Windows
```

---

## 联系支持

如果以上方法无法解决问题，请收集以下信息并联系技术支持：

### 必要信息
1. **错误信息**: 完整的错误堆栈信息
2. **环境信息**: 操作系统、Python版本、依赖包版本
3. **配置信息**: 相关的配置文件内容（隐藏敏感信息）
4. **日志文件**: 相关的日志文件片段
5. **重现步骤**: 详细的问题重现步骤

### 日志收集脚本
```python
# scripts/collect_debug_info.py
import sys
import json
import platform
from medical_insurance_sdk.config import ConfigManager

def collect_debug_info():
    info = {
        'system': {
            'platform': platform.platform(),
            'python_version': sys.version,
        },
        'config': {},
        'recent_logs': []
    }
    
    try:
        config_manager = ConfigManager()
        # 收集配置信息（隐藏敏感数据）
        # 收集最近的日志
    except Exception as e:
        info['error'] = str(e)
    
    with open('debug_info.json', 'w') as f:
        json.dump(info, f, indent=2)
    
    print("调试信息已保存到 debug_info.json")

if __name__ == "__main__":
    collect_debug_info()
```

---

更多信息请参考：
- [API文档](api-documentation.md)
- [接口配置指南](interface-configuration-guide.md)
- [最佳实践](best-practices.md)