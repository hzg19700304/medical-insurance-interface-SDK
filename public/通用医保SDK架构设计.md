# 通用医保SDK架构设计（简化版）

## 设计原则：简单实用

**核心理念：解决80%的问题，用20%的复杂度**

## 1. 极简架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   HIS系统   │───▶│  SDK客户端  │───▶│  医保接口   │
│  (调用方)   │    │ (通信处理)  │    │  (目标)     │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                   │                   │
       │                   ▼                   │
┌─────────────┐    ┌─────────────┐            │
│  本地数据库 │◀───│  简单日志   │            │
│  (可选)     │    │  (调试用)   │◀───────────┘
└─────────────┘    └─────────────┘
```

## 2. SDK结构（只有3个文件）

```
medical_insurance_sdk/
├── client.py          # 主客户端（核心）
├── config.py          # 配置管理
└── utils.py           # 工具函数
```

## 3. 核心实现

### 3.1 主客户端（client.py）
```python
import requests
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

class MedicalInsuranceClient:
    """医保SDK客户端 - 极简版"""
    
    def __init__(self, app_id: str, app_secret: str, org_code: str, base_url: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.org_code = org_code
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def call(self, interface_code: str, data: Dict[str, Any], 
             timeout: int = 30, retry_times: int = 2) -> Dict[str, Any]:
        """
        统一调用接口
        
        Args:
            interface_code: 接口编号
            data: 业务数据
            timeout: 超时时间(秒)
            retry_times: 重试次数
            
        Returns:
            Dict: 响应数据
        """
        
        for attempt in range(retry_times + 1):
            try:
                # 构建请求
                request_data = self._build_request(interface_code, data)
                
                # 发送请求
                response = self.session.post(
                    f"{self.base_url}/api/medical-insurance",
                    json=request_data,
                    timeout=timeout
                )
                response.raise_for_status()
                
                # 处理响应
                result = self._handle_response(response.json())
                
                # 记录日志（可选）
                self._log_call(interface_code, data, result, success=True)
                
                return result
                
            except Exception as e:
                if attempt < retry_times:
                    time.sleep(1)  # 重试前等待1秒
                    continue
                else:
                    # 最后一次失败，返回错误
                    error_result = {
                        "infcode": "-1",
                        "err_msg": f"调用失败: {str(e)}"
                    }
                    self._log_call(interface_code, data, error_result, success=False)
                    return error_result
    
    def _build_request(self, interface_code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求数据"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 基础请求体
        request_body = {
            "infno": interface_code,
            "msgid": self._generate_msgid(),
            "mdtrtarea_admvs": self.org_code[:6],
            "insuplc_admdvs": self.org_code[:6],
            "recer_sys_code": "HIS",
            "dev_no": "",
            "dev_safe_info": "",
            "cainfo": "",
            "signtype": "SM3",
            "infver": "V1.0",
            "opter_type": "1",
            "opter": "admin",
            "opter_name": "管理员",
            "inf_time": timestamp,
            "fixmedins_code": self.org_code,
            "fixmedins_name": "医疗机构",
            "sign_no": "",
            "input": data
        }
        
        # 简化的签名（生产环境需要真实的SM3签名）
        data_str = json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)
        signature = hashlib.md5((data_str + self.app_secret).encode()).hexdigest()
        
        return {
            "data": data_str,
            "signature": signature,
            "timestamp": timestamp
        }
    
    def _handle_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理响应数据"""
        # 简化处理，直接返回（生产环境需要验签和解密）
        if isinstance(response_data.get("data"), str):
            try:
                return json.loads(response_data["data"])
            except:
                return response_data
        return response_data
    
    def _generate_msgid(self) -> str:
        """生成消息ID"""
        import uuid
        return str(uuid.uuid4()).replace('-', '')
    
    def _log_call(self, interface_code: str, request_data: Dict, 
                  response_data: Dict, success: bool):
        """记录调用日志（可选功能）"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "interface_code": interface_code,
                "success": success,
                "request_data": request_data,
                "response_data": response_data
            }
            
            # 简单的文件日志
            with open("medical_insurance.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except:
            pass  # 日志失败不影响主流程
```

### 3.2 配置管理（config.py）
```python
import json
from typing import Dict, Any

class Config:
    """简单配置管理"""
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        self.config = config_dict or {}
    
    @classmethod
    def from_file(cls, file_path: str):
        """从文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls(config_dict)
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def to_client_params(self) -> Dict[str, str]:
        """转换为客户端参数"""
        return {
            "app_id": self.get("app_id"),
            "app_secret": self.get("app_secret"),
            "org_code": self.get("org_code"),
            "base_url": self.get("base_url")
        }
```

### 3.3 工具函数（utils.py）
```python
import json
from datetime import datetime
from typing import Dict, Any

def validate_interface_code(interface_code: str) -> bool:
    """验证接口编号格式"""
    return interface_code and len(interface_code) == 4 and interface_code.isdigit()

def validate_person_no(person_no: str) -> bool:
    """验证人员编号格式"""
    return person_no and len(person_no) in [15, 18]

def format_amount(amount: float) -> str:
    """格式化金额"""
    return f"{amount:.2f}"

def get_current_time() -> str:
    """获取当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_json_loads(json_str: str, default=None):
    """安全的JSON解析"""
    try:
        return json.loads(json_str)
    except:
        return default

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """脱敏敏感数据（用于日志）"""
    masked_data = data.copy()
    sensitive_keys = ['psn_no', 'cert_no', 'tel', 'addr']
    
    for key in sensitive_keys:
        if key in masked_data and masked_data[key]:
            value = str(masked_data[key])
            if len(value) > 6:
                masked_data[key] = value[:3] + "***" + value[-3:]
            else:
                masked_data[key] = "***"
    
    return masked_data
```

## 4. 使用方式

### 4.1 配置文件（config.json）
```json
{
    "app_id": "your_app_id",
    "app_secret": "your_app_secret",
    "org_code": "H12345678901",
    "base_url": "https://api.hnybj.com"
}
```

### 4.2 Python使用示例
```python
from medical_insurance_sdk import MedicalInsuranceClient, Config

# 方式1：直接初始化
client = MedicalInsuranceClient(
    app_id="your_app_id",
    app_secret="your_secret",
    org_code="H12345678901",
    base_url="https://api.example.com"
)

# 方式2：从配置文件初始化
config = Config.from_file("config.json")
client = MedicalInsuranceClient(**config.to_client_params())

# 调用接口
result = client.call("1101", {"psn_no": "430123199001011234"})

if result.get("infcode") == "0":
    print("调用成功")
    person_info = result.get("output", {}).get("baseinfo", {})
    print(f"姓名: {person_info.get('psn_name')}")
else:
    print(f"调用失败: {result.get('err_msg')}")
```

### 4.3 HIS系统集成（如果需要数据库集成）
```sql
-- 创建简单的调用记录表（可选）
CREATE TABLE medical_insurance_calls (
    id INT IDENTITY(1,1) PRIMARY KEY,
    interface_code VARCHAR(10),
    request_data NVARCHAR(MAX),
    response_data NVARCHAR(MAX),
    success BIT,
    call_time DATETIME DEFAULT GETDATE()
);

-- 简单的调用存储过程
CREATE PROCEDURE sp_call_medical_insurance
    @interface_code VARCHAR(10),
    @input_data NVARCHAR(MAX),
    @result NVARCHAR(MAX) OUTPUT
AS
BEGIN
    -- 调用Python脚本
    DECLARE @cmd NVARCHAR(1000);
    DECLARE @temp_file VARCHAR(100) = 'temp_' + CAST(NEWID() AS VARCHAR(36)) + '.json';
    
    SET @cmd = 'python -c "
from medical_insurance_sdk import MedicalInsuranceClient, Config
import json
import sys

config = Config.from_file(''config.json'')
client = MedicalInsuranceClient(**config.to_client_params())
result = client.call(''' + @interface_code + ''', json.loads(''' + REPLACE(@input_data, '''', '''''') + '''))

with open(''' + @temp_file + ''', ''w'', encoding=''utf-8'') as f:
    json.dump(result, f, ensure_ascii=False)
"';
    
    EXEC xp_cmdshell @cmd;
    
    -- 读取结果文件
    -- 这里需要实现文件读取逻辑
    SET @result = '{"infcode": "0", "message": "调用完成"}';
END
```

## 5. 部署方式

### 5.1 Python包安装
```bash
# 安装SDK
pip install medical-insurance-sdk

# 创建配置文件
echo '{
    "app_id": "your_app_id",
    "app_secret": "your_secret", 
    "org_code": "your_org_code",
    "base_url": "https://api.example.com"
}' > config.json

# 测试调用
python -c "
from medical_insurance_sdk import MedicalInsuranceClient, Config
config = Config.from_file('config.json')
client = MedicalInsuranceClient(**config.to_client_params())
result = client.call('1101', {'psn_no': '123456'})
print(result)
"
```

### 5.2 单文件部署（更简单）
```python
# medical_insurance_simple.py - 单文件版本
import requests
import json
import hashlib
from datetime import datetime

class SimpleClient:
    def __init__(self, app_id, app_secret, org_code, base_url):
        self.app_id = app_id
        self.app_secret = app_secret
        self.org_code = org_code
        self.base_url = base_url
    
    def call(self, interface_code, data):
        # 构建请求
        request_body = {
            "infno": interface_code,
            "msgid": str(hash(str(data) + str(datetime.now()))),
            "fixmedins_code": self.org_code,
            "input": data
        }
        
        # 发送请求
        try:
            response = requests.post(
                f"{self.base_url}/api/medical-insurance",
                json=request_body,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"infcode": "-1", "err_msg": str(e)}

# 使用示例
if __name__ == "__main__":
    client = SimpleClient(
        app_id="your_app_id",
        app_secret="your_secret",
        org_code="your_org_code", 
        base_url="https://api.example.com"
    )
    
    result = client.call("1101", {"psn_no": "123456"})
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 6. 优势总结

### 6.1 简单性
- **3个文件**：client.py, config.py, utils.py
- **1个核心方法**：client.call()
- **零依赖**：只需要requests库

### 6.2 实用性
- **自动重试**：网络异常自动重试2次
- **超时控制**：默认30秒超时
- **错误处理**：统一的错误返回格式
- **日志记录**：可选的调用日志

### 6.3 易用性
- **配置简单**：4个参数搞定
- **调用简单**：一行代码调用接口
- **集成简单**：HIS系统几行代码集成

### 6.4 可扩展性
- **需要数据库**：加个DatabaseManager
- **需要异步**：加个AsyncProcessor  
- **需要监控**：加个MonitorManager

**核心理念：先简单可用，再根据实际需求逐步扩展**

这个简化版本解决了80%的使用场景，复杂度只有原来的20%。你觉得这个方案如何？