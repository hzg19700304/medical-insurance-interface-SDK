# 医保接口SDK架构设计（简化版）

## 设计原则：功能单一，专注通信

SDK只负责：**发送请求 + 接收响应**，不处理业务逻辑

## 1. SDK整体架构

### 1.1 简化分层架构
```
┌─────────────────────────────────────┐
│           HIS系统业务层              │  ← HIS处理业务逻辑
├─────────────────────────────────────┤
│           SDK通信接口层              │  ← SDK提供统一调用接口
├─────────────────────────────────────┤
│          协议处理层                  │  ← 加密、签名、格式化
├─────────────────────────────────────┤
│          HTTP通信层                  │  ← 网络请求/响应
└─────────────────────────────────────┘
```

### 1.2 极简模块划分
```
MedicalInsuranceSDK/
├── client.py               # 主客户端（唯一入口）
├── config.py               # 配置管理
├── crypto.py               # 加密解密
├── exceptions.py           # 异常定义
└── utils.py                # 工具函数
```

**核心理念：只做4件事**
1. **接收参数** - 接收HIS传入的接口编号和数据
2. **协议处理** - 加密、签名、格式化
3. **发送请求** - HTTP通信
4. **返回响应** - 解密、验签、返回原始数据

## 2. 极简API设计

### 2.1 唯一入口：统一调用方法
```python
from medical_insurance_sdk import MedicalInsuranceClient

# 初始化（只需要基本配置）
client = MedicalInsuranceClient(
    app_id="your_app_id",
    app_secret="your_app_secret", 
    org_code="医疗机构编码",
    base_url="https://api.example.com"
)

# 统一调用接口 - 这是SDK的核心，只有一个方法
response = client.call(
    interface_code="1101",  # 接口编号
    data={                  # 业务数据（由HIS系统准备）
        "psn_no": "身份证号",
        "cert_no": "证件号码"
    }
)

# 返回原始响应数据，由HIS系统自己解析
print(response)  # {"infcode": "0", "output": {...}, ...}
```

### 2.2 SDK职责边界
```
┌─────────────────────────────────────┐
│  HIS系统负责：                       │
│  - 业务逻辑处理                      │
│  - 数据组装和解析                    │
│  - 业务流程控制                      │
│  - 错误处理和重试策略                │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│  SDK只负责：                        │
│  - 接收接口编号和数据                │
│  - 加密、签名、格式化                │
│  - HTTP请求/响应                     │
│  - 解密、验签                       │
│  - 返回原始数据                      │
└─────────────────────────────────────┘
```

## 3. 核心实现

### 3.1 主客户端类
```python
import json
import requests
from typing import Dict, Any
from .crypto import encrypt_data, decrypt_data, sign_data, verify_signature
from .exceptions import NetworkException, AuthenticationException

class MedicalInsuranceClient:
    """医保接口SDK主客户端 - 极简设计"""
    
    def __init__(self, app_id: str, app_secret: str, org_code: str, base_url: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.org_code = org_code
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def call(self, interface_code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一调用接口 - SDK的唯一核心方法
        
        Args:
            interface_code: 接口编号 (如: "1101", "2207")
            data: 业务数据字典
            
        Returns:
            Dict: 原始响应数据
            
        Raises:
            NetworkException: 网络异常
            AuthenticationException: 认证异常
        """
        try:
            # 1. 构建请求
            request_data = self._build_request(interface_code, data)
            
            # 2. 发送HTTP请求
            response = self.session.post(
                f"{self.base_url}/api/medical-insurance",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # 3. 处理响应
            return self._handle_response(response.json())
            
        except requests.RequestException as e:
            raise NetworkException(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise AuthenticationException(f"请求处理失败: {str(e)}")
    
    def _build_request(self, interface_code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求数据"""
        # 基础请求结构
        request_body = {
            "infno": interface_code,
            "msgid": self._generate_msgid(),
            "mdtrtarea_admvs": self.org_code[:6],  # 医疗区域代码
            "insuplc_admdvs": self.org_code[:6],   # 参保地代码
            "recer_sys_code": "HIS",
            "dev_no": "",
            "dev_safe_info": "",
            "cainfo": "",
            "signtype": "SM3",
            "infver": "V1.0",
            "opter_type": "1",
            "opter": "admin",
            "opter_name": "管理员",
            "inf_time": self._get_current_time(),
            "fixmedins_code": self.org_code,
            "fixmedins_name": "医疗机构名称",
            "sign_no": "",
            "input": data  # 业务数据
        }
        
        # 加密和签名
        encrypted_data = encrypt_data(json.dumps(request_body), self.app_secret)
        signature = sign_data(encrypted_data, self.app_secret)
        
        return {
            "data": encrypted_data,
            "signature": signature,
            "timestamp": self._get_current_time()
        }
    
    def _handle_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理响应数据"""
        # 验签
        if not verify_signature(response_data.get("data", ""), 
                              response_data.get("signature", ""), 
                              self.app_secret):
            raise AuthenticationException("响应验签失败")
        
        # 解密
        decrypted_data = decrypt_data(response_data.get("data", ""), self.app_secret)
        return json.loads(decrypted_data)
    
    def _generate_msgid(self) -> str:
        """生成消息ID"""
        import uuid
        return str(uuid.uuid4()).replace('-', '')
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### 3.2 使用示例
```python
# 初始化SDK
client = MedicalInsuranceClient(
    app_id="your_app_id",
    app_secret="your_app_secret",
    org_code="医疗机构编码", 
    base_url="https://api.example.com"
)

# HIS系统调用 - 查询人员信息
response = client.call("1101", {
    "psn_no": "身份证号码"
})

# HIS系统处理响应
if response.get("infcode") == "0":
    person_info = response.get("output", {}).get("baseinfo", {})
    print(f"姓名: {person_info.get('psn_name')}")
else:
    print(f"查询失败: {response.get('err_msg')}")

# HIS系统调用 - 门诊挂号
response = client.call("2201", {
    "psn_no": "身份证号码",
    "fixmedins_code": "医疗机构编码",
    "med_type": "11",  # 门诊
    "medfee_sumamt": "0",
    "psn_setlway": "01"
})

# HIS系统调用 - 门诊结算
response = client.call("2207", {
    "mdtrt_id": "就医登记号",
    "psn_no": "身份证号码", 
    "chrg_bchno": "收费批次号",
    "acct_used_flag": "0",
    "insutype": "310",
    "invono": "发票号"
})
```

## 4. 极简配置设计

### 4.1 去掉配置文件，直接传参
```python
# 不需要复杂的配置文件，直接传参即可
client = MedicalInsuranceClient(
    app_id="your_app_id",
    app_secret="your_app_secret",
    org_code="医疗机构编码",
    base_url="https://api.example.com",
    timeout=30  # 可选参数
)
```

### 4.2 如果需要配置文件，保持简单
```json
{
  "app_id": "your_app_id",
  "app_secret": "your_app_secret", 
  "org_code": "医疗机构编码",
  "base_url": "https://api.example.com"
}
```

```python
# 支持配置文件初始化
client = MedicalInsuranceClient.from_config("config.json")
```

## 6. 错误处理设计

### 6.1 异常层次结构
```python
class MedicalInsuranceException(Exception):
    """医保SDK基础异常"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message

class NetworkException(MedicalInsuranceException):
    """网络异常"""
    pass

class AuthenticationException(MedicalInsuranceException):
    """认证异常"""
    pass

class ValidationException(MedicalInsuranceException):
    """数据校验异常"""
    pass

class BusinessException(MedicalInsuranceException):
    """业务异常"""
    
    def __init__(self, message: str, error_code: str, response_data: Dict = None):
        super().__init__(message, error_code)
        self.response_data = response_data
```

### 6.2 错误处理装饰器
```python
from functools import wraps
import logging

def handle_exceptions(func):
    """异常处理装饰器"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NetworkException as e:
            logging.error(f"网络异常: {e.message}")
            raise
        except AuthenticationException as e:
            logging.error(f"认证异常: {e.message}")
            raise
        except ValidationException as e:
            logging.error(f"校验异常: {e.message}")
            raise
        except Exception as e:
            logging.error(f"未知异常: {str(e)}")
            raise MedicalInsuranceException(f"SDK内部错误: {str(e)}")
    
    return wrapper
```

## 7. 日志和监控设计

### 7.1 日志设计
```python
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

class SDKLogger:
    """SDK日志管理"""
    
    def __init__(self, name: str = "medical_insurance_sdk"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志配置"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        file_handler = RotatingFileHandler(
            'logs/sdk.log', 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_request(self, interface_code: str, request_data: dict):
        """记录请求日志"""
        self.logger.info(f"请求接口: {interface_code}, 请求数据: {request_data}")
    
    def log_response(self, interface_code: str, response_data: dict):
        """记录响应日志"""
        self.logger.info(f"接口响应: {interface_code}, 响应数据: {response_data}")
```

### 7.2 性能监控
```python
import time
from functools import wraps
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_api_call(self, interface_code: str, duration: float, success: bool):
        """记录API调用指标"""
        if interface_code not in self.metrics:
            self.metrics[interface_code] = {
                'total_calls': 0,
                'success_calls': 0,
                'total_duration': 0,
                'avg_duration': 0
            }
        
        metric = self.metrics[interface_code]
        metric['total_calls'] += 1
        metric['total_duration'] += duration
        metric['avg_duration'] = metric['total_duration'] / metric['total_calls']
        
        if success:
            metric['success_calls'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics

def monitor_performance(interface_code: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            finally:
                duration = time.time() - start_time
                # 记录性能指标
                monitor = PerformanceMonitor()
                monitor.record_api_call(interface_code, duration, success)
        return wrapper
    return decorator
```

## 8. 使用示例

### 8.1 基础使用
```python
from medical_insurance_sdk import MedicalInsuranceClient

# 初始化客户端
client = MedicalInsuranceClient(
    app_id="your_app_id",
    app_secret="your_app_secret",
    org_code="医疗机构编码",
    config_file="config.json"
)

# 查询人员信息
person_info = client.basic_service().get_person_info("身份证号")
if person_info.is_success:
    print(f"人员姓名: {person_info.person_info['psn_name']}")
else:
    print(f"查询失败: {person_info.error_message}")
```

### 8.2 门诊业务流程
```python
# 门诊挂号
registration = client.outpatient_service().register(
    person_id="身份证号",
    dept_code="内科",
    doctor_code="医生编码"
)

# 上传就诊信息
visit_info = client.outpatient_service().upload_visit_info(
    mdtrt_id=registration.mdtrt_id,
    diagnosis_code="诊断代码",
    diagnosis_name="诊断名称"
)

# 上传费用明细
fee_details = client.outpatient_service().upload_fee_details(
    mdtrt_id=registration.mdtrt_id,
    fee_items=[
        {"item_code": "项目代码", "item_name": "项目名称", "price": 100.00}
    ]
)

# 预结算
pre_settlement = client.settlement_service().pre_settle(
    mdtrt_id=registration.mdtrt_id
)

# 正式结算
settlement = client.settlement_service().settle(
    mdtrt_id=registration.mdtrt_id
)
```

### 8.3 异常处理
```python
try:
    result = client.basic_service().get_person_info("身份证号")
    if result.is_success:
        # 处理成功结果
        pass
    else:
        # 处理业务错误
        print(f"业务错误: {result.error_message}")
        
except NetworkException as e:
    print(f"网络异常: {e.message}")
    # 可以选择重试
    
except AuthenticationException as e:
    print(f"认证失败: {e.message}")
    # 需要检查认证配置
    
except ValidationException as e:
    print(f"参数错误: {e.message}")
    # 需要检查输入参数
```

## 9. 部署和分发

### 9.1 包结构
```
medical-insurance-sdk/
├── setup.py
├── README.md
├── requirements.txt
├── CHANGELOG.md
├── medical_insurance_sdk/
│   ├── __init__.py
│   └── [所有源码文件]
├── examples/
│   ├── basic_usage.py
│   ├── outpatient_flow.py
│   └── inpatient_flow.py
├── docs/
│   ├── api_reference.md
│   ├── user_guide.md
│   └── troubleshooting.md
└── tests/
    └── [所有测试文件]
```

### 9.2 安装方式
```bash
# pip安装
pip install medical-insurance-sdk

# 源码安装
git clone https://github.com/your-org/medical-insurance-sdk.git
cd medical-insurance-sdk
pip install -e .
```

这个SDK架构设计考虑了医院HIS系统的实际需求，提供了简洁易用的API接口，同时保证了系统的稳定性和扩展性。你觉得这个设计方案如何？需要我详细展开某个部分吗？