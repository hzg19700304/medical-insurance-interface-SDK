# 医保接口Python SDK技术规范文档

## 一、SDK总体架构

### 1.1 架构设计原则

#### 1.1.1 设计原则
- **简单易用**：提供简洁直观的API接口
- **健壮可靠**：完善的错误处理和重试机制
- **高性能**：支持异步操作和连接池
- **可扩展**：模块化设计，易于添加新功能
- **标准化**：遵循Python开发最佳实践

#### 1.1.2 架构层次
```
医保接口Python SDK架构
├── 用户接口层 (Public API)
│   ├── MedicalInsuranceSDK (主入口类)
│   ├── AsyncMedicalInsuranceSDK (异步版本)
│   └── 数据模型类 (Pydantic Models)
├── 业务逻辑层 (Business Logic)
│   ├── PatientService (患者服务)
│   ├── CatalogService (目录服务)
│   ├── UploadService (上传服务)
│   └── FileService (文件服务)
├── 协议适配层 (Protocol Adapter)
│   ├── MedicalInsuranceProtocol (医保协议)
│   ├── SignatureGenerator (签名生成器)
│   └── MessageBuilder (报文构建器)
├── 网络通信层 (Network Layer)
│   ├── HttpClient (HTTP客户端)
│   ├── AsyncHttpClient (异步HTTP客户端)
│   └── RetryHandler (重试处理器)
└── 基础设施层 (Infrastructure)
    ├── ConfigManager (配置管理)
    ├── Logger (日志管理)
    ├── CacheManager (缓存管理)
    └── ExceptionHandler (异常处理)
```

### 1.2 目录结构规范

#### 1.2.1 项目目录结构
```
medical_insurance_sdk/
├── README.md                           # 项目说明文档
├── CHANGELOG.md                        # 变更日志
├── LICENSE                             # 许可证
├── setup.py                           # 安装脚本
├── requirements.txt                    # 依赖清单
├── pyproject.toml                     # 项目配置
├── medical_insurance_sdk/              # 主包目录
│   ├── __init__.py                    # 包初始化
│   ├── version.py                     # 版本信息
│   ├── client.py                      # 主要客户端类
│   ├── async_client.py                # 异步客户端类
│   ├── config/                        # 配置管理模块
│   │   ├── __init__.py
│   │   ├── config_manager.py          # 配置管理器
│   │   └── default_config.py          # 默认配置
│   ├── models/                        # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py                    # 基础模型
│   │   ├── request.py                 # 请求模型
│   │   ├── response.py                # 响应模型
│   │   └── exceptions.py              # 异常模型
│   ├── services/                      # 业务服务
│   │   ├── __init__.py
│   │   ├── base_service.py            # 基础服务类
│   │   ├── patient_service.py         # 患者服务
│   │   ├── catalog_service.py         # 目录服务
│   │   ├── upload_service.py          # 上传服务
│   │   └── file_service.py            # 文件服务
│   ├── protocol/                      # 协议层
│   │   ├── __init__.py
│   │   ├── medical_insurance.py       # 医保协议
│   │   ├── signature.py               # 签名处理
│   │   └── message_builder.py         # 报文构建
│   ├── network/                       # 网络层
│   │   ├── __init__.py
│   │   ├── http_client.py             # HTTP客户端
│   │   ├── async_http_client.py       # 异步HTTP客户端
│   │   └── retry_handler.py           # 重试处理
│   └── utils/                         # 工具模块
│       ├── __init__.py
│       ├── logger.py                  # 日志工具
│       ├── cache.py                   # 缓存工具
│       ├── validators.py              # 验证工具
│       └── helpers.py                 # 辅助工具
├── tests/                             # 测试目录
│   ├── __init__.py
│   ├── conftest.py                    # pytest配置
│   ├── unit/                          # 单元测试
│   │   ├── test_client.py
│   │   ├── test_services.py
│   │   └── test_protocol.py
│   ├── integration/                   # 集成测试
│   │   ├── test_patient_query.py
│   │   └── test_file_download.py
│   └── fixtures/                      # 测试数据
│       ├── config_sample.json
│       └── response_samples.json
├── examples/                          # 示例代码
│   ├── basic_usage.py                 # 基础使用示例
│   ├── async_usage.py                 # 异步使用示例
│   ├── file_operations.py             # 文件操作示例
│   └── error_handling.py              # 错误处理示例
└── docs/                              # 文档目录
    ├── api_reference.md               # API参考文档
    ├── user_guide.md                  # 用户指南
    └── developer_guide.md             # 开发者指南
```

## 二、技术选型和依赖管理

### 2.1 Python版本兼容性

#### 2.1.1 支持的Python版本
```python
# setup.py
python_requires=">=3.8"

# 支持版本列表
SUPPORTED_PYTHON_VERSIONS = [
    "3.8",   # 最低支持版本
    "3.9",   # 稳定版本
    "3.10",  # 推荐版本
    "3.11",  # 最新版本
    "3.12"   # 未来版本
]
```

#### 2.1.2 版本兼容性矩阵
| Python版本 | 支持状态 | 备注 |
|-----------|---------|------|
| 3.7 | ❌ 不支持 | 生命周期已结束 |
| 3.8 | ✅ 支持 | 最低版本要求 |
| 3.9 | ✅ 完全支持 | 稳定版本 |
| 3.10 | ✅ 完全支持 | 推荐版本 |
| 3.11 | ✅ 完全支持 | 性能优化版本 |
| 3.12 | ✅ 实验支持 | 最新版本 |

### 2.2 核心依赖库

#### 2.2.1 必需依赖 (requirements.txt)
```txt
# HTTP客户端
httpx>=0.24.0,<1.0.0          # 现代HTTP客户端，支持异步
requests>=2.28.0,<3.0.0       # 传统HTTP客户端，向下兼容

# 数据验证和序列化
pydantic>=1.10.0,<3.0.0       # 数据验证和模型定义
typing-extensions>=4.0.0      # 类型提示扩展

# 日期时间处理
python-dateutil>=2.8.0        # 日期时间工具

# 配置管理
python-dotenv>=0.19.0         # 环境变量管理
PyYAML>=6.0                   # YAML配置支持

# 加密和签名
cryptography>=3.4.0           # 加密库（用于签名）

# 日志
structlog>=22.0.0             # 结构化日志

# 缓存（可选）
cachetools>=5.0.0             # 内存缓存工具
```

#### 2.2.2 开发依赖 (requirements-dev.txt)
```txt
# 测试框架
pytest>=7.0.0                 # 测试框架
pytest-asyncio>=0.21.0        # 异步测试支持
pytest-cov>=4.0.0             # 覆盖率测试
pytest-mock>=3.10.0           # Mock测试

# 代码质量
black>=22.0.0                 # 代码格式化
isort>=5.10.0                 # 导入排序
flake8>=5.0.0                 # 代码检查
mypy>=1.0.0                   # 类型检查
pre-commit>=2.20.0            # Git钩子

# 文档生成
sphinx>=5.0.0                 # 文档生成
sphinx-rtd-theme>=1.0.0       # 文档主题

# 性能分析
memory-profiler>=0.60.0       # 内存分析
line-profiler>=4.0.0          # 性能分析
```

#### 2.2.3 依赖版本策略
```python
# 版本固定策略
VERSION_STRATEGY = {
    "major_dependencies": "^x.y.z",    # 主要依赖使用语义化版本
    "critical_dependencies": "~x.y.z", # 关键依赖使用补丁版本
    "development_dependencies": ">=x.y.z", # 开发依赖使用最低版本
}

# 依赖更新策略
UPDATE_STRATEGY = {
    "security_updates": "immediate",    # 安全更新立即应用
    "major_updates": "quarterly",       # 主版本更新季度评估
    "minor_updates": "monthly",         # 次版本更新月度评估
    "patch_updates": "weekly",          # 补丁更新周更新
}
```

### 2.3 可选依赖

#### 2.3.1 性能优化依赖
```txt
# 可选的性能优化依赖
ujson>=5.0.0                  # 快速JSON解析
orjson>=3.8.0                 # 更快的JSON库
uvloop>=0.17.0                # 快速事件循环(仅Unix)
```

#### 2.3.2 额外功能依赖
```txt
# 可选的额外功能
redis>=4.5.0                  # Redis缓存支持
sqlalchemy>=1.4.0            # 数据库ORM支持
prometheus-client>=0.15.0     # 监控指标支持
```

## 三、代码规范和最佳实践

### 3.1 代码风格规范

#### 3.1.1 PEP 8 扩展规范
```python
# .flake8 配置
[flake8]
max-line-length = 88
select = E,W,F
ignore = E203,E501,W503
exclude = __pycache__,*.egg-info,.git,.tox,build,dist

# black 配置
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

# isort 配置
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
```

#### 3.1.2 命名规范
```python
# 模块命名：小写字母，下划线分隔
# ✅ 正确
medical_insurance_client.py
patient_service.py
config_manager.py

# ❌ 错误
MedicalInsuranceClient.py
patientService.py
ConfigManager.py

# 类命名：大驼峰命名法
# ✅ 正确
class MedicalInsuranceSDK:
    pass

class PatientQueryRequest:
    pass

# ❌ 错误
class medical_insurance_sdk:
    pass

class patient_query_request:
    pass

# 函数和变量命名：小写字母，下划线分隔
# ✅ 正确
def query_patient_info():
    patient_name = "张三"
    medical_record_id = "123456"

# ❌ 错误
def queryPatientInfo():
    patientName = "张三"
    medicalRecordID = "123456"

# 常量命名：大写字母，下划线分隔
# ✅ 正确
DEFAULT_TIMEOUT = 30
MAX_RETRY_COUNT = 3
API_VERSION = "1.0.0"

# 私有属性和方法：单下划线前缀
class MedicalInsuranceSDK:
    def __init__(self):
        self._config = None
        self._client = None
    
    def _build_headers(self):
        pass

# 特殊用途：双下划线前缀（谨慎使用）
class BaseModel:
    def __init__(self):
        self.__internal_state = {}
```

#### 3.1.3 文档字符串规范
```python
def query_patient(
    self, 
    cert_type: str, 
    cert_no: str, 
    name: str = ""
) -> PatientInfo:
    """查询患者医保信息.
    
    通过证件信息查询患者的基本信息、参保状态和医保余额等信息。
    支持身份证、社保卡等多种证件类型。
    
    Args:
        cert_type: 证件类型。支持的值：
            - "01": 电子凭证
            - "02": 身份证  
            - "03": 社保卡
        cert_no: 证件号码，如身份证号或社保卡号
        name: 患者姓名，可选参数，用于辅助验证
        
    Returns:
        PatientInfo: 患者信息对象，包含以下属性：
            - person_no: 人员编号
            - name: 姓名
            - gender: 性别
            - birthday: 出生日期
            - insurance_info: 参保信息列表
            
    Raises:
        AuthenticationError: 认证失败，检查AK/SK配置
        ValidationError: 参数验证失败，检查证件号格式
        PatientNotFoundError: 患者信息不存在
        NetworkError: 网络连接失败
        MedicalInsuranceError: 其他医保接口错误
        
    Example:
        >>> sdk = MedicalInsuranceSDK("config.json")
        >>> patient = sdk.query_patient("02", "430281199001010001", "张三")
        >>> print(f"患者姓名: {patient.name}")
        >>> print(f"医保余额: {patient.insurance_info[0].balance}")
        
    Note:
        - 证件号码需要符合相应的格式要求
        - 查询结果会自动缓存5分钟
        - 异地就医患者可能返回多个参保信息
        
    See Also:
        - query_patient_async: 异步版本
        - validate_patient_data: 数据验证方法
    """
```

### 3.2 类型提示规范

#### 3.2.1 基础类型提示
```python
from typing import (
    List, Dict, Optional, Union, Any, Callable, 
    TypeVar, Generic, Protocol, Literal, Final
)
from typing_extensions import TypedDict, NotRequired
from datetime import datetime, date
from decimal import Decimal

# 基础类型
patient_name: str = "张三"
patient_age: int = 35
account_balance: Decimal = Decimal("1500.00")
birth_date: date = date(1990, 1, 1)
query_time: datetime = datetime.now()

# 容器类型
insurance_types: List[str] = ["310", "390"]
patient_data: Dict[str, Any] = {"name": "张三", "age": 35}
optional_name: Optional[str] = None
cert_type: Union[str, int] = "02"

# 字面量类型
CertType = Literal["01", "02", "03"]
Gender = Literal["1", "2", "9"]

def query_patient(cert_type: CertType, gender: Gender) -> PatientInfo:
    pass

# TypedDict 用于结构化数据
class PatientInfoDict(TypedDict):
    person_no: str
    name: str
    gender: Gender
    birthday: date
    insurance_info: List[Dict[str, Any]]
    
class ConfigDict(TypedDict):
    base_url: str
    ak: str
    sk: str
    timeout: NotRequired[int]  # 可选字段
```

#### 3.2.2 泛型和协议
```python
from typing import TypeVar, Generic, Protocol

# 泛型定义
T = TypeVar('T')
ResponseT = TypeVar('ResponseT', bound='BaseResponse')

class APIResponse(Generic[T]):
    """泛型API响应类"""
    def __init__(self, success: bool, data: T, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

# 使用泛型
def query_patient(cert_no: str) -> APIResponse[PatientInfo]:
    pass

def download_catalog() -> APIResponse[List[DrugInfo]]:
    pass

# 协议定义
class Serializable(Protocol):
    """可序列化协议"""
    def to_dict(self) -> Dict[str, Any]:
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        ...

# 使用协议
def serialize_data(obj: Serializable) -> Dict[str, Any]:
    return obj.to_dict()
```

#### 3.2.3 高级类型提示
```python
from typing import Awaitable, Coroutine, AsyncIterator
from collections.abc import Sequence, Mapping

# 异步类型
async def query_patient_async(cert_no: str) -> PatientInfo:
    pass

def get_async_query() -> Awaitable[PatientInfo]:
    return query_patient_async("123456")

# 生成器类型
def iter_patients() -> AsyncIterator[PatientInfo]:
    async for patient in get_all_patients():
        yield patient

# 回调函数类型
ProgressCallback = Callable[[int, int], None]
ErrorHandler = Callable[[Exception], bool]

def download_file(
    url: str, 
    progress_callback: Optional[ProgressCallback] = None,
    error_handler: Optional[ErrorHandler] = None
) -> bytes:
    pass

# 类型别名
JSONData = Dict[str, Any]
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, bool]]

# Final 类型（常量）
API_VERSION: Final[str] = "1.0.0"
DEFAULT_TIMEOUT: Final[int] = 30
```

### 3.3 异常处理规范

#### 3.3.1 异常层次结构
```python
# exceptions.py
class MedicalInsuranceError(Exception):
    """医保接口SDK基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retry: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.retry = retry

class AuthenticationError(MedicalInsuranceError):
    """认证相关错误"""
    pass

class SignatureError(AuthenticationError):
    """签名错误"""
    pass

class TimestampExpiredError(AuthenticationError):
    """时间戳过期错误"""
    pass

class ValidationError(MedicalInsuranceError):
    """数据验证错误"""
    
    def __init__(
        self, 
        message: str, 
        field_errors: Optional[Dict[str, List[str]]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field_errors = field_errors or {}

class NetworkError(MedicalInsuranceError):
    """网络相关错误"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, retry=True, **kwargs)
        self.status_code = status_code

class TimeoutError(NetworkError):
    """超时错误"""
    pass

class ConnectionError(NetworkError):
    """连接错误"""
    pass

class BusinessError(MedicalInsuranceError):
    """业务逻辑错误"""
    pass

class PatientNotFoundError(BusinessError):
    """患者不存在错误"""
    pass

class FileDownloadError(MedicalInsuranceError):
    """文件下载错误"""
    pass

class FileNotFoundError(FileDownloadError):
    """文件不存在错误"""
    pass

class FileExpiredError(FileDownloadError):
    """文件过期错误"""
    pass

class ConfigurationError(MedicalInsuranceError):
    """配置错误"""
    pass
```

#### 3.3.2 异常处理最佳实践
```python
from typing import Type, Union, Optional
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def handle_exceptions(
    *exception_types: Type[Exception],
    default_return: Any = None,
    log_error: bool = True
):
    """异常处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_error:
                    logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
                
                if isinstance(e, MedicalInsuranceError):
                    # 重新抛出业务异常
                    raise
                else:
                    # 包装系统异常
                    raise MedicalInsuranceError(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        error_code="SYSTEM_ERROR"
                    ) from e
            except Exception as e:
                if log_error:
                    logger.error(f"Unexpected exception in {func.__name__}: {e}", exc_info=True)
                
                if default_return is not None:
                    return default_return
                
                raise MedicalInsuranceError(
                    f"Unexpected error: {str(e)}",
                    error_code="UNKNOWN_ERROR"
                ) from e
        return wrapper
    return decorator

# 使用示例
class PatientService:
    @handle_exceptions(requests.RequestException, ValueError)
    def query_patient(self, cert_no: str) -> PatientInfo:
        if not cert_no:
            raise ValidationError("证件号不能为空")
        
        try:
            response = self._call_api("1101", {"cert_no": cert_no})
            return self._parse_patient_info(response)
        except requests.Timeout:
            raise TimeoutError("请求超时，请稍后重试")
        except requests.ConnectionError:
            raise ConnectionError("网络连接失败")
        except Exception as e:
            # 转换为业务异常
            raise BusinessError(f"查询患者信息失败: {str(e)}") from e
```

## 四、异步编程规范

### 4.1 异步架构设计

#### 4.1.1 异步客户端设计
```python
import asyncio
import aiohttp
from typing import AsyncIterator, AsyncContextManager
from contextlib import asynccontextmanager

class AsyncMedicalInsuranceSDK:
    """异步医保接口SDK"""
    
    def __init__(self, config_path: str):
        self.config = ConfigManager.load(config_path)
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(10)  # 限制并发数
    
    async def __aenter__(self) -> 'AsyncMedicalInsuranceSDK':
        """异步上下文管理器入口"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def _ensure_session(self):
        """确保HTTP会话已创建"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,  # 连接池大小
                limit_per_host=10,
                keepalive_timeout=30
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": f"MedicalInsurance-SDK/{__version__}"}
            )
    
    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def query_patient(
        self, 
        cert_type: str, 
        cert_no: str, 
        name: str = ""
    ) -> PatientInfo:
        """异步查询患者信息"""
        async with self._semaphore:  # 控制并发
            return await self._query_patient_impl(cert_type, cert_no, name)
    
    async def _query_patient_impl(
        self, 
        cert_type: str, 
        cert_no: str, 
        name: str
    ) -> PatientInfo:
        """查询患者信息的具体实现"""
        await self._ensure_session()
        
        # 构建请求
        request_data = self._build_patient_query_request(cert_type, cert_no, name)
        
        # 发送异步请求
        try:
            async with self._session.post(
                self.config.base_url,
                json=request_data,
                headers=self._build_headers("1101")
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return self._parse_patient_info(data)
        
        except asyncio.TimeoutError:
            raise TimeoutError("请求超时")
        except aiohttp.ClientError as e:
            raise NetworkError(f"网络请求失败: {str(e)}")

# 使用示例
async def main():
    config_path = "config.json"
    
    # 方式1：使用异步上下文管理器（推荐）
    async with AsyncMedicalInsuranceSDK(config_path) as sdk:
        patient = await sdk.query_patient("02", "430281199001010001")
        print(f"患者姓名: {patient.name}")
    
    # 方式2：手动管理
    sdk = AsyncMedicalInsuranceSDK(config_path)
    try:
        patient = await sdk.query_patient("02", "430281199001010001")
        print(f"患者姓名: {patient.name}")
    finally:
        await sdk.close()

# 运行异步代码
if __name__ == "__main__":
    asyncio.run(main())
```

#### 4.1.2 批量异步操作
```python
import asyncio
from typing import List, Tuple, Union

class BatchOperations:
    """批量异步操作工具"""
    
    def __init__(self, sdk: AsyncMedicalInsuranceSDK, max_concurrent: int = 10):
        self.sdk = sdk
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def query_patients_batch(
        self, 
        patient_requests: List[Tuple[str, str, str]]
    ) -> List[Union[PatientInfo, Exception]]:
        """批量查询患者信息"""
        
        async def query_single(cert_type: str, cert_no: str, name: str):
            async with self.semaphore:
                try:
                    return await self.sdk.query_patient(cert_type, cert_no, name)
                except Exception as e:
                    return e
        
        tasks = [
            query_single(cert_type, cert_no, name)
            for cert_type, cert_no, name in patient_requests
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def download_catalogs_batch(
        self, 
        catalog_types: List[str]
    ) -> List[Union[bytes, Exception]]:
        """批量下载目录文件"""
        
        async def download_single(catalog_type: str):
            async with self.semaphore:
                try:
                    file_info = await self.sdk.get_file_info(catalog_type, {"ver": "1.0.0"})
                    return await self.sdk.download_file(
                        file_info.file_query_no, 
                        file_info.filename
                    )
                except Exception as e:
                    return e
        
        tasks = [download_single(catalog_type) for catalog_type in catalog_types]
        return await asyncio.gather(*tasks, return_exceptions=True)

# 使用示例
async def batch_example():
    async with AsyncMedicalInsuranceSDK("config.json") as sdk:
        batch_ops = BatchOperations(sdk, max_concurrent=5)
        
        # 批量查询患者
        patient_requests = [
            ("02", "430281199001010001", "张三"),
            ("02", "430281199001010002", "李四"),
            ("02", "430281199001010003", "王五"),
        ]
        
        results = await batch_ops.query_patients_batch(patient_requests)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"第{i+1}个患者查询失败: {result}")
            else:
                print(f"第{i+1}个患者: {result.name}")
```

#### 4.1.3 异步流处理
```python
import asyncio
from typing import AsyncIterator, Optional

class AsyncStreamProcessor:
    """异步流处理器"""
    
    def __init__(self, sdk: AsyncMedicalInsuranceSDK):
        self.sdk = sdk
    
    async def process_patient_stream(
        self, 
        cert_numbers: AsyncIterator[str]
    ) -> AsyncIterator[PatientInfo]:
        """处理患者信息流"""
        
        async for cert_no in cert_numbers:
            try:
                patient = await self.sdk.query_patient("02", cert_no)
                yield patient
            except Exception as e:
                # 记录错误但继续处理
                logger.error(f"处理证件号 {cert_no} 失败: {e}")
                continue
    
    async def parse_file_stream(
        self, 
        file_content: bytes,
        chunk_size: int = 1000
    ) -> AsyncIterator[List[Dict[str, str]]]:
        """异步解析大文件"""
        
        lines = file_content.decode('utf-8').split('\n')
        
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            parsed_chunk = []
            
            for line in chunk:
                if line.strip():
                    fields = line.split('\t')
                    if len(fields) >= 5:  # 假设至少需要5个字段
                        parsed_chunk.append({
                            'drug_code': fields[0],
                            'drug_name': fields[1],
                            'generic_name': fields[3],
                            'specification': fields[13],
                            'price': fields[48] if len(fields) > 48 else ''
                        })
            
            if parsed_chunk:
                yield parsed_chunk
            
            # 让出控制权，避免阻塞事件循环
            await asyncio.sleep(0)

# 使用示例
async def stream_example():
    async def cert_number_generator():
        """证件号生成器"""
        cert_numbers = [
            "430281199001010001",
            "430281199001010002", 
            "430281199001010003"
        ]
        for cert_no in cert_numbers:
            yield cert_no
            await asyncio.sleep(0.1)  # 模拟间隔
    
    async with AsyncMedicalInsuranceSDK("config.json") as sdk:
        processor = AsyncStreamProcessor(sdk)
        
        # 处理患者流
        async for patient in processor.process_patient_stream(cert_number_generator()):
            print(f"处理患者: {patient.name}")
```

### 4.2 同步异步兼容性

#### 4.2.1 同步异步API统一
```python
from typing import Union, overload
import asyncio
from functools import wraps

class UnifiedMedicalInsuranceSDK:
    """统一的同步/异步SDK"""
    
    def __init__(self, config_path: str, async_mode: bool = False):
        self.config_path = config_path
        self.async_mode = async_mode
        
        if async_mode:
            self._async_sdk: Optional[AsyncMedicalInsuranceSDK] = None
        else:
            self._sync_sdk = MedicalInsuranceSDK(config_path)
    
    @property
    async def async_sdk(self) -> AsyncMedicalInsuranceSDK:
        """获取异步SDK实例"""
        if self._async_sdk is None:
            self._async_sdk = AsyncMedicalInsuranceSDK(self.config_path)
        return self._async_sdk
    
    @overload
    def query_patient(
        self, 
        cert_type: str, 
        cert_no: str, 
        name: str = ""
    ) -> PatientInfo:
        ...
    
    @overload
    async def query_patient(
        self, 
        cert_type: str, 
        cert_no: str, 
        name: str = ""
    ) -> PatientInfo:
        ...
    
    def query_patient(
        self, 
        cert_type: str, 
        cert_no: str, 
        name: str = ""
    ) -> Union[PatientInfo, Awaitable[PatientInfo]]:
        """统一的患者查询方法"""
        if self.async_mode:
            return self._query_patient_async(cert_type, cert_no, name)
        else:
            return self._sync_sdk.query_patient(cert_type, cert_no, name)
    
    async def _query_patient_async(
        self, 
        cert_type: str, 
        cert_no: str, 
        name: str = ""
    ) -> PatientInfo:
        """异步查询实现"""
        sdk = await self.async_sdk
        return await sdk.query_patient(cert_type, cert_no, name)

# 同步转异步装饰器
def make_async(sync_func):
    """将同步函数转换为异步函数"""
    @wraps(sync_func)
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_func, *args, **kwargs)
    return async_wrapper

# 异步转同步装饰器  
def make_sync(async_func):
    """将异步函数转换为同步函数"""
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            return asyncio.run(async_func(*args, **kwargs))
        else:
            # 已有运行中的事件循环，使用 run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func(*args, **kwargs))
                return future.result()
    return sync_wrapper
```

## 五、配置管理规范

### 5.1 配置文件格式

#### 5.1.1 支持的配置格式
```python
# config_manager.py
import json
import yaml
import os
from typing import Dict, Any, Union, Optional
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class MedicalInsuranceConfig:
    """医保接口配置类"""
    
    # 基础配置
    base_url: str
    ak: str
    sk: str
    
    # 机构信息
    fixmedins_code: str
    fixmedins_name: str
    mdtrtarea_admvs: str
    insuplc_admdvs: Optional[str] = None
    
    # 经办人信息
    opter: str = "0001"
    opter_name: str = "系统管理员"
    opter_type: str = "1"
    
    # 网络配置
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5分钟
    cache_max_size: int = 1000
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 高级配置
    verify_ssl: bool = True
    user_agent: str = field(default_factory=lambda: f"MedicalInsurance-SDK/{__version__}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MedicalInsuranceConfig':
        """从字典创建配置"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def validate(self) -> None:
        """验证配置有效性"""
        required_fields = ['base_url', 'ak', 'sk', 'fixmedins_code', 'fixmedins_name']
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not isinstance(value, str) or not value.strip():
                raise ConfigurationError(f"配置字段 {field_name} 不能为空")
        
        if self.timeout <= 0:
            raise ConfigurationError("timeout 必须大于0")
        
        if self.retry_count < 0:
            raise ConfigurationError("retry_count 不能小于0")

class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def load_from_file(config_path: Union[str, Path]) -> MedicalInsuranceConfig:
        """从文件加载配置"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise ConfigurationError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(f"不支持的配置文件格式: {config_path.suffix}")
            
            config = MedicalInsuranceConfig.from_dict(data)
            config.validate()
            return config
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigurationError(f"加载配置文件失败: {e}")
    
    @staticmethod
    def load_from_env() -> MedicalInsuranceConfig:
        """从环境变量加载配置"""
        env_mapping = {
            'base_url': 'MI_BASE_URL',
            'ak': 'MI_ACCESS_KEY',
            'sk': 'MI_SECRET_KEY',
            'fixmedins_code': 'MI_FIXMEDINS_CODE',
            'fixmedins_name': 'MI_FIXMEDINS_NAME',
            'mdtrtarea_admvs': 'MI_MDTRTAREA_ADMVS',
            'insuplc_admdvs': 'MI_INSUPLC_ADMDVS',
            'opter': 'MI_OPTER',
            'opter_name': 'MI_OPTER_NAME',
            'timeout': 'MI_TIMEOUT',
            'retry_count': 'MI_RETRY_COUNT',
        }
        
        config_data = {}
        for config_key, env_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value:
                # 类型转换
                if config_key in ['timeout', 'retry_count']:
                    config_data[config_key] = int(env_value)
                elif config_key in ['cache_enabled', 'verify_ssl']:
                    config_data[config_key] = env_value.lower() in ['true', '1', 'yes']
                else:
                    config_data[config_key] = env_value
        
        if not config_data:
            raise ConfigurationError("未找到环境变量配置")
        
        config = MedicalInsuranceConfig.from_dict(config_data)
        config.validate()
        return config
    
    @staticmethod
    def load(config_source: Union[str, Path, Dict[str, Any]]) -> MedicalInsuranceConfig:
        """通用配置加载方法"""
        if isinstance(config_source, (str, Path)):
            # 文件路径
            if str(config_source) == "ENV":
                return ConfigManager.load_from_env()
            else:
                return ConfigManager.load_from_file(config_source)
        elif isinstance(config_source, dict):
            # 字典配置
            config = MedicalInsuranceConfig.from_dict(config_source)
            config.validate()
            return config
        else:
            raise ConfigurationError(f"不支持的配置源类型: {type(config_source)}")
```

#### 5.1.2 配置文件示例

**JSON格式配置 (config.json)**:
```json
{
  "base_url": "https://dms.hun.hsip.gov.cn/fsi/api/rsfComIfsService/callService",
  "ak": "yRV6rnHYEa2clmx1MCWb4HjlOcwhS8gLbW6O4o",
  "sk": "SK8Z8G7jSm2023T1jn6EgRweJ0Fy1JpeielmJnBe",
  "fixmedins_code": "H43111100255",
  "fixmedins_name": "某某医院",
  "mdtrtarea_admvs": "431199",
  "insuplc_admdvs": "431199",
  "opter": "0153",
  "opter_name": "系统管理员",
  "timeout": 30,
  "retry_count": 3,
  "retry_delay": 1.0,
  "cache_enabled": true,
  "cache_ttl": 300,
  "log_level": "INFO"
}
```

**YAML格式配置 (config.yaml)**:
```yaml
# 医保接口配置
medical_insurance:
  # 基础配置
  base_url: "https://dms.hun.hsip.gov.cn/fsi/api/rsfComIfsService/callService"
  ak: "yRV6rnHYEa2clmx1MCWb4HjlOcwhS8gLbW6O4o"
  sk: "SK8Z8G7jSm2023T1jn6EgRweJ0Fy1JpeielmJnBe"
  
  # 机构信息
  institution:
    code: "H43111100255"
    name: "某某医院"
    area_code: "431199"
    insurance_area_code: "431199"
  
  # 经办人信息
  operator:
    code: "0153"
    name: "系统管理员"
    type: "1"
  
  # 网络配置
  network:
    timeout: 30
    retry_count: 3
    retry_delay: 1.0
    verify_ssl: true
  
  # 缓存配置
  cache:
    enabled: true
    ttl: 300
    max_size: 1000
  
  # 日志配置
  logging:
    level: "INFO"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**环境变量配置 (.env)**:
```bash
# 医保接口环境变量
MI_BASE_URL=https://dms.hun.hsip.gov.cn/fsi/api/rsfComIfsService/callService
MI_ACCESS_KEY=yRV6rnHYEa2clmx1MCWb4HjlOcwhS8gLbW6O4o
MI_SECRET_KEY=SK8Z8G7jSm2023T1jn6EgRweJ0Fy1JpeielmJnBe
MI_FIXMEDINS_CODE=H43111100255
MI_FIXMEDINS_NAME=某某医院
MI_MDTRTAREA_ADMVS=431199
MI_INSUPLC_ADMDVS=431199
MI_OPTER=0153
MI_OPTER_NAME=系统管理员
MI_TIMEOUT=30
MI_RETRY_COUNT=3
```

### 5.2 配置验证和安全

#### 5.2.1 配置验证器
```python
import re
from typing import List, Callable

class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        url_pattern = re.compile(
            r'^https?://'  # http:// 或 https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
            r'(?::\d+)?'  # 端口
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_fixmedins_code(code: str) -> bool:
        """验证机构编号格式"""
        # 格式：H + 11位数字
        pattern = re.compile(r'^H\d{11}$')
        return bool(pattern.match(code))
    
    @staticmethod
    def validate_area_code(code: str) -> bool:
        """验证区划代码格式"""
        # 6位数字
        pattern = re.compile(r'^\d{6}$')
        return bool(pattern.match(code))
    
    @staticmethod
    def validate_ak_sk(key: str) -> bool:
        """验证AK/SK格式"""
        # 30-50位字母数字组合
        pattern = re.compile(r'^[A-Za-z0-9]{30,50}$')
        return bool(pattern.match(key))

class SecureConfigManager:
    """安全配置管理器"""
    
    def __init__(self):
        self.validators: Dict[str, Callable[[str], bool]] = {
            'base_url': ConfigValidator.validate_url,
            'fixmedins_code': ConfigValidator.validate_fixmedins_code,
            'mdtrtarea_admvs': ConfigValidator.validate_area_code,
            'insuplc_admdvs': ConfigValidator.validate_area_code,
            'ak': ConfigValidator.validate_ak_sk,
            'sk': ConfigValidator.validate_ak_sk,
        }
    
    def validate_config(self, config: MedicalInsuranceConfig) -> List[str]:
        """验证配置并返回错误列表"""
        errors = []
        
        for field_name, validator in self.validators.items():
            value = getattr(config, field_name, None)
            if value and not validator(value):
                errors.append(f"{field_name} 格式不正确: {value}")
        
        return errors
    
    def mask_sensitive_data(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏敏感配置数据"""
        sensitive_fields = ['ak', 'sk', 'secret_key', 'password']
        masked_config = config_dict.copy()
        
        for field in sensitive_fields:
            if field in masked_config and masked_config[field]:
                value = str(masked_config[field])
                if len(value) > 8:
                    masked_config[field] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                else:
                    masked_config[field] = "*" * len(value)
        
        return masked_config
```

## 六、测试规范

### 6.1 测试架构

#### 6.1.1 测试分层结构
```python
# conftest.py - pytest配置
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from medical_insurance_sdk import MedicalInsuranceSDK
from medical_insurance_sdk.config import MedicalInsuranceConfig

@pytest.fixture
def sample_config():
    """示例配置"""
    return MedicalInsuranceConfig(
        base_url="http://test.example.com",
        ak="test_access_key_12345678901234567890",
        sk="test_secret_key_12345678901234567890",
        fixmedins_code="H43111100255",
        fixmedins_name="测试医院",
        mdtrtarea_admvs="431199",
        opter="0001",
        opter_name="测试用户"
    )

@pytest.fixture
def mock_http_client():
    """Mock HTTP客户端"""
    with patch('medical_insurance_sdk.network.HttpClient') as mock:
        yield mock

@pytest.fixture
def sample_patient_response():
    """示例患者查询响应"""
    return {
        "infcode": 0,
        "inf_refmsgid": "430000002507141030120130589177",
        "output": {
            "baseinfo": {
                "psn_no": "43000030281000120001",
                "psn_name": "张三",
                "gend": "1",
                "brdy": "1990-01-01",
                "age": 35.5
            },
            "insuinfo": [{
                "balc": 1500.00,
                "insutype": "310",
                "psn_type": "11",
                "psn_insu_stas": "1"
            }],
            "idetinfo": []
        }
    }

@pytest.fixture
def sdk(sample_config):
    """SDK实例"""
    with patch.object(MedicalInsuranceSDK, '_load_config', return_value=sample_config):
        return MedicalInsuranceSDK("test_config.json")
```

#### 6.1.2 单元测试示例
```python
# tests/unit/test_client.py
import pytest
from unittest.mock import Mock, patch, call
from medical_insurance_sdk import MedicalInsuranceSDK
from medical_insurance_sdk.exceptions import ValidationError, AuthenticationError

class TestMedicalInsuranceSDK:
    """SDK主类测试"""
    
    def test_init_with_valid_config(self, sample_config):
        """测试有效配置初始化"""
        with patch.object(MedicalInsuranceSDK, '_load_config', return_value=sample_config):
            sdk = MedicalInsuranceSDK("config.json")
            assert sdk.config == sample_config
    
    def test_init_with_invalid_config_path(self):
        """测试无效配置路径"""
        with pytest.raises(ConfigurationError):
            MedicalInsuranceSDK("nonexistent.json")
    
    @patch('medical_insurance_sdk.client.requests.post')
    def test_query_patient_success(self, mock_post, sdk, sample_patient_response):
        """测试患者查询成功"""
        # 设置mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_patient_response
        mock_post.return_value = mock_response
        
        # 执行测试
        result = sdk.query_patient("02", "430281199001010001", "张三")
        
        # 验证结果
        assert result.person_no == "43000030281000120001"
        assert result.name == "张三"
        assert result.gender == "1"
        assert len(result.insurance_info) == 1
        assert result.insurance_info[0].balance == 1500.00
        
        # 验证API调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # 验证请求URL
        assert call_args[1]['url'] == sdk.config.base_url
        
        # 验证请求头
        headers = call_args[1]['headers']
        assert '_api_name' in headers
        assert headers['_api_name'] == '1101'
        assert '_api_signature' in headers
    
    def test_query_patient_validation_error(self, sdk):
        """测试患者查询参数验证错误"""
        with pytest.raises(ValidationError):
            sdk.query_patient("", "430281199001010001", "张三")  # 空证件类型
        
        with pytest.raises(ValidationError):
            sdk.query_patient("02", "", "张三")  # 空证件号
    
    @patch('medical_insurance_sdk.client.requests.post')
    def test_query_patient_authentication_error(self, mock_post, sdk):
        """测试认证错误"""
        # 设置mock响应为认证失败
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "code": 401,
            "message": "签名不一致!"
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(AuthenticationError):
            sdk.query_patient("02", "430281199001010001", "张三")
    
    @patch('medical_insurance_sdk.client.requests.post')
    def test_query_patient_business_error(self, mock_post, sdk):
        """测试业务错误"""
        # 设置mock响应为业务失败
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "infcode": -1,
            "err_msg": "该参保人的基本信息为空",
            "output": None
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(PatientNotFoundError):
            sdk.query_patient("02", "430281199001010001", "张三")

class TestSignatureGeneration:
    """签名生成测试"""
    
    def test_generate_signature(self, sdk):
        """测试签名生成"""
        # 固定时间戳用于测试
        timestamp = 1721789415123
        expected_signature = "expected_base64_signature"
        
        with patch('medical_insurance_sdk.protocol.signature.hmac') as mock_hmac, \
             patch('medical_insurance_sdk.protocol.signature.base64') as mock_base64:
            
            mock_hmac.new.return_value.digest.return_value = b'signature_bytes'
            mock_base64.b64encode.return_value.decode.return_value = expected_signature
            
            signature = sdk._generate_signature("1101", "1.0.0", timestamp)
            
            assert signature == expected_signature
            mock_hmac.new.assert_called_once()
            mock_base64.b64encode.assert_called_once()
    
    def test_generate_msgid(self, sdk):
        """测试报文ID生成"""
        with patch('medical_insurance_sdk.protocol.message_builder.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250714103015"
            mock_datetime.now.return_value.microsecond = 123000
            
            msgid = sdk._generate_msgid()
            
            expected_msgid = f"{sdk.config.fixmedins_code}20250714103015123"
            assert msgid == expected_msgid
            assert len(msgid) == 30
```

#### 6.1.3 集成测试示例
```python
# tests/integration/test_patient_query.py
import pytest
import json
from medical_insurance_sdk import MedicalInsuranceSDK

@pytest.mark.integration
class TestPatientQueryIntegration:
    """患者查询集成测试"""
    
    @pytest.fixture(scope="class")
    def real_sdk(self):
        """真实SDK实例（使用测试环境配置）"""
        return MedicalInsuranceSDK("tests/fixtures/test_config.json")
    
    def test_query_existing_patient(self, real_sdk):
        """测试查询存在的患者"""
        # 使用测试环境的真实患者数据
        result = real_sdk.query_patient(
            cert_type="02",
            cert_no="test_cert_no_001",  # 测试环境的有效证件号
            name="测试患者一"
        )
        
        assert result.person_no is not None
        assert result.name == "测试患者一"
        assert len(result.insurance_info) > 0
    
    def test_query_nonexistent_patient(self, real_sdk):
        """测试查询不存在的患者"""
        with pytest.raises(PatientNotFoundError):
            real_sdk.query_patient(
                cert_type="02",
                cert_no="999999999999999999",  # 不存在的证件号
                name="不存在的患者"
            )
    
    @pytest.mark.slow
    def test_query_patient_performance(self, real_sdk):
        """测试查询性能"""
        import time
        
        start_time = time.time()
        result = real_sdk.query_patient(
            cert_type="02",
            cert_no="test_cert_no_001",
            name="测试患者一"
        )
        end_time = time.time()
        
        # 验证响应时间在2秒内
        assert end_time - start_time < 2.0
        assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncPatientQuery:
    """异步患者查询集成测试"""
    
    @pytest.fixture(scope="class")
    async def async_sdk(self):
        """异步SDK实例"""
        from medical_insurance_sdk import AsyncMedicalInsuranceSDK
        sdk = AsyncMedicalInsuranceSDK("tests/fixtures/test_config.json")
        yield sdk
        await sdk.close()
    
    async def test_async_query_patient(self, async_sdk):
        """测试异步查询患者"""
        result = await async_sdk.query_patient(
            cert_type="02",
            cert_no="test_cert_no_001",
            name="测试患者一"
        )
        
        assert result.person_no is not None
        assert result.name == "测试患者一"
    
    async def test_concurrent_queries(self, async_sdk):
        """测试并发查询"""
        import asyncio
        
        tasks = [
            async_sdk.query_patient("02", f"test_cert_no_{i:03d}", f"测试患者{i}")
            for i in range(1, 6)  # 5个并发查询
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证至少有一些成功的查询
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0
```

#### 6.1.4 性能测试
```python
# tests/performance/test_performance.py
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import statistics

@pytest.mark.performance
class TestPerformance:
    """性能测试"""
    
    def test_sync_query_performance(self, sdk):
        """同步查询性能测试"""
        query_times = []
        
        for i in range(10):
            start_time = time.time()
            try:
                result = sdk.query_patient("02", f"test_cert_no_{i:03d}", f"患者{i}")
                end_time = time.time()
                query_times.append(end_time - start_time)
            except Exception:
                pass  # 忽略错误，专注于性能
        
        if query_times:
            avg_time = statistics.mean(query_times)
            max_time = max(query_times)
            
            assert avg_time < 2.0, f"平均响应时间过长: {avg_time:.2f}s"
            assert max_time < 5.0, f"最大响应时间过长: {max_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_async_concurrent_performance(self, async_sdk):
        """异步并发性能测试"""
        concurrent_count = 20
        
        start_time = time.time()
        
        tasks = [
            async_sdk.query_patient("02", f"test_cert_no_{i:03d}", f"患者{i}")
            for i in range(concurrent_count)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_count = len([r for r in results if not isinstance(r, Exception)])
        
        # 验证并发处理能力
        assert total_time < 10.0, f"并发处理时间过长: {total_time:.2f}s"
        assert successful_count > 0, "没有成功的并发查询"
        
        # 计算QPS
        qps = successful_count / total_time
        assert qps > 2, f"QPS过低: {qps:.2f}"
    
    def test_memory_usage(self, sdk):
        """内存使用测试"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 执行多次查询
        for i in range(100):
            try:
                sdk.query_patient("02", f"test_cert_no_{i:03d}", f"患者{i}")
            except Exception:
                pass
        
        gc.collect()  # 强制垃圾回收
        final_memory = process.memory_info().rss
        
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # 验证内存增长合理
        assert memory_increase_mb < 50, f"内存增长过多: {memory_increase_mb:.2f}MB"
```

### 6.2 测试工具和辅助

#### 6.2.1 Mock工具
```python
# tests/utils/mock_helpers.py
from unittest.mock import Mock, patch
from typing import Dict, Any, Optional

class MockHttpResponse:
    """Mock HTTP响应"""
    
    def __init__(
        self, 
        status_code: int = 200, 
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

class MedicalInsuranceMockFactory:
    """医保接口Mock工厂"""
    
    @staticmethod
    def create_success_response(data: Dict[str, Any]) -> MockHttpResponse:
        """创建成功响应"""
        return MockHttpResponse(200, {
            "infcode": 0,
            "inf_refmsgid": "430000002507141030120130589177",
            "output": data
        })
    
    @staticmethod
    def create_error_response(error_msg: str, infcode: int = -1) -> MockHttpResponse:
        """创建错误响应"""
        return MockHttpResponse(200, {
            "infcode": infcode,
            "err_msg": error_msg,
            "output": None
        })
    
    @staticmethod
    def create_network_error() -> MockHttpResponse:
        """创建网络错误响应"""
        return MockHttpResponse(500)
    
    @staticmethod
    def create_patient_response(
        person_no: str = "43000030281000120001",
        name: str = "张三",
        balance: float = 1500.00
    ) -> MockHttpResponse:
        """创建患者查询响应"""
        data = {
            "baseinfo": {
                "psn_no": person_no,
                "psn_name": name,
                "gend": "1",
                "brdy": "1990-01-01",
                "age": 35.5
            },
            "insuinfo": [{
                "balc": balance,
                "insutype": "310",
                "psn_type": "11",
                "psn_insu_stas": "1"
            }],
            "idetinfo": []
        }
        return MedicalInsuranceMockFactory.create_success_response(data)

# 使用示例
@patch('medical_insurance_sdk.client.requests.post')
def test_with_mock_factory(mock_post, sdk):
    """使用Mock工厂的测试"""
    mock_post.return_value = MedicalInsuranceMockFactory.create_patient_response(
        name="李四",
        balance=2000.00
    )
    
    result = sdk.query_patient("02", "430281199001010002", "李四")
    
    assert result.name == "李四"
    assert result.insurance_info[0].balance == 2000.00
```

## 七、日志和监控

### 7.1 结构化日志

#### 7.1.1 日志配置
```python
# utils/logger.py
import logging
import structlog
import sys
from typing import Dict, Any, Optional
from datetime import datetime

def configure_logging(
    level: str = "INFO",
    format_type: str = "json",  # json 或 console
    log_file: Optional[str] = None
) -> None:
    """配置结构化日志"""
    
    # 基础配置
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        stream=sys.stdout
    )
    
    # 配置structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 文件日志
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)

class MedicalInsuranceLogger:
    """医保接口专用日志器"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def log_api_request(
        self,
        api_name: str,
        request_data: Dict[str, Any],
        masked: bool = True
    ) -> None:
        """记录API请求"""
        if masked:
            # 脱敏处理
            safe_data = self._mask_sensitive_data(request_data)
        else:
            safe_data = request_data
        
        self.logger.info(
            "API请求",
            api_name=api_name,
            request_id=safe_data.get("msgid"),
            fixmedins_code=safe_data.get("fixmedins_code"),
            request_size=len(str(request_data))
        )
    
    def log_api_response(
        self,
        api_name: str,
        response_data: Dict[str, Any],
        duration: float
    ) -> None:
        """记录API响应"""
        self.logger.info(
            "API响应",
            api_name=api_name,
            infcode=response_data.get("infcode"),
            success=response_data.get("infcode") == 0,
            duration_ms=round(duration * 1000, 2),
            response_size=len(str(response_data))
        )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录错误"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
        if context:
            error_data.update(context)
        
        if hasattr(error, 'error_code'):
            error_data["error_code"] = error.error_code
        
        if hasattr(error, 'retry'):
            error_data["retryable"] = error.retry
        
        self.logger.error("操作失败", **error_data)
    
    def log_performance_metrics(
        self,
        operation: str,
        duration: float,
        success: bool,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录性能指标"""
        metrics = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_metrics:
            metrics.update(additional_metrics)
        
        self.logger.info("性能指标", **metrics)
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏敏感数据"""
        sensitive_fields = {'ak', 'sk', 'access_key', 'secret_key', 'certno', 'psn_name'}
        
        def mask_recursive(obj):
            if isinstance(obj, dict):
                return {
                    k: mask_recursive(v) if k not in sensitive_fields else self._mask_value(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [mask_recursive(item) for item in obj]
            else:
                return obj
        
        return mask_recursive(data)
    
    def _mask_value(self, value: Any) -> str:
        """脱敏单个值"""
        str_value = str(value)
        if len(str_value) <= 4:
            return "*" * len(str_value)
        elif len(str_value) <= 8:
            return str_value[:2] + "*" * (len(str_value) - 4) + str_value[-2:]
        else:
            return str_value[:4] + "*" * (len(str_value) - 8) + str_value[-4:]

# 装饰器用法
def log_api_call(logger: MedicalInsuranceLogger):
    """API调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.log_performance_metrics(
                    operation=func.__name__,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.log_error(e, {
                    "function": func.__name__,
                    "duration": duration
                })
                
                logger.log_performance_metrics(
                    operation=func.__name__,
                    duration=duration,
                    success=False
                )
                
                raise
        
        return wrapper
    return decorator
```

### 7.2 监控指标

#### 7.2.1 指标收集
```python
# utils/metrics.py
import time
from typing import Dict, Any, Optional, Counter
from dataclasses import dataclass, field
from threading import Lock
import threading

@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics: Dict[str, list] = {}
        self._counters: Dict[str, int] = {}
        self._lock = Lock()
    
    def counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """计数器指标"""
        with self._lock:
            key = f"{name}:{tags or {}}"
            self._counters[key] = self._counters.get(key, 0) + value
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """仪表盘指标"""
        point = MetricPoint(name, value, tags=tags or {})
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(point)
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """直方图指标"""
        self.gauge(f"{name}_duration", value, tags)
        self.counter(f"{name}_count", 1, tags)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                "gauges": dict(self._metrics),
                "counters": dict(self._counters),
                "timestamp": time.time()
            }
    
    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()

class MedicalInsuranceMetrics:
    """医保接口指标"""
    
    def __init__(self):
        self.collector = MetricsCollector()
    
    def record_api_call(
        self, 
        api_name: str, 
        duration: float, 
        success: bool,
        status_code: Optional[int] = None
    ) -> None:
        """记录API调用指标"""
        tags = {
            "api_name": api_name,
            "success": str(success).lower()
        }
        
        if status_code:
            tags["status_code"] = str(status_code)
        
        # 调用次数
        self.collector.counter("medical_insurance_api_calls_total", 1, tags)
        
        # 响应时间
        self.collector.histogram("medical_insurance_api_duration", duration, tags)
        
        # 错误率
        if not success:
            self.collector.counter("medical_insurance_api_errors_total", 1, tags)
    
    def record_cache_operation(self, operation: str, hit: bool) -> None:
        """记录缓存操作指标"""
        tags = {
            "operation": operation,
            "result": "hit" if hit else "miss"
        }
        
        self.collector.counter("medical_insurance_cache_operations_total", 1, tags)
    
    def record_file_operation(
        self, 
        operation: str, 
        file_size: int, 
        duration: float, 
        success: bool
    ) -> None:
        """记录文件操作指标"""
        tags = {
            "operation": operation,
            "success": str(success).lower()
        }
        
        self.collector.counter("medical_insurance_file_operations_total", 1, tags)
        self.collector.gauge("medical_insurance_file_size_bytes", file_size, tags)
        self.collector.histogram("medical_insurance_file_operation_duration", duration, tags)

# 全局指标实例
metrics = MedicalInsuranceMetrics()

def track_metrics(operation: str):
    """指标跟踪装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics.record_api_call(
                    api_name=operation,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                metrics.record_api_call(
                    api_name=operation,
                    duration=duration,
                    success=False
                )
                
                raise
        
        return wrapper
    return decorator
```

## 八、打包和发布

### 8.1 包配置

#### 8.1.1 setup.py配置
```python
# setup.py
from setuptools import setup, find_packages
import re
from pathlib import Path

# 读取版本号
def get_version():
    version_file = Path(__file__).parent / "medical_insurance_sdk" / "version.py"
    version_content = version_file.read_text(encoding="utf-8")
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# 读取README
def get_long_description():
    readme_file = Path(__file__).parent / "README.md"
    return readme_file.read_text(encoding="utf-8")

# 读取依赖
def get_requirements():
    requirements_file = Path(__file__).parent / "requirements.txt"
    return requirements_file.read_text(encoding="utf-8").strip().split('\n')

setup(
    name="medical-insurance-sdk",
    version=get_version(),
    author="Your Organization",
    author_email="contact@yourorg.com",
    description="Python SDK for Medical Insurance Interface",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/medical-insurance-sdk",
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "performance": [
            "orjson>=3.8.0",
            "uvloop>=0.17.0; sys_platform != 'win32'",
        ],
        "monitoring": [
            "prometheus-client>=0.15.0",
            "structlog>=22.0.0",
        ],
        "cache": [
            "redis>=4.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "medical-insurance-cli=medical_insurance_sdk.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "medical_insurance_sdk": [
            "config/*.json",
            "config/*.yaml",
            "py.typed",
        ],
    },
    zip_safe=False,
)
```

#### 8.1.2 pyproject.toml配置
```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "medical-insurance-sdk"
dynamic = ["version"]
description = "Python SDK for Medical Insurance Interface"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Organization", email = "contact@yourorg.com"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.8"
dependencies = [
    "httpx>=0.24.0,<1.0.0",
    "pydantic>=1.10.0,<3.0.0",
    "python-dateutil>=2.8.0",
    "cryptography>=3.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=5.0.0",
    "mypy>=1.0.0",
]
performance = [
    "orjson>=3.8.0",
    "uvloop>=0.17.0; sys_platform != 'win32'",
]

[project.urls]
Homepage = "https://github.com/yourorg/medical-insurance-sdk"
Documentation = "https://medical-insurance-sdk.readthedocs.io"
Repository = "https://github.com/yourorg/medical-insurance-sdk.git"
Changelog = "https://github.com/yourorg/medical-insurance-sdk/blob/main/CHANGELOG.md"

[project.scripts]
medical-insurance-cli = "medical_insurance_sdk.cli:main"

[tool.setuptools.dynamic]
version = {attr = "medical_insurance_sdk.__version__"}

[tool.setuptools.packages.find]
exclude = ["tests*", "examples*", "docs*"]

[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "performance: marks tests as performance tests",
]

[tool.coverage.run]
source = ["medical_insurance_sdk"]
omit = ["*/tests/*", "*/examples/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### 8.2 版本管理

#### 8.2.1 版本号规范
```python
# medical_insurance_sdk/version.py
"""版本信息模块"""

# 语义化版本控制
# MAJOR.MINOR.PATCH[-PRE_RELEASE][+BUILD_METADATA]
__version__ = "1.0.0"

# 版本信息
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "pre_release": None,
    "build_metadata": None,
}

# API版本
API_VERSION = "1.0.0"

# 最低支持的Python版本
MIN_PYTHON_VERSION = (3, 8)

def get_version_info() -> dict:
    """获取详细版本信息"""
    import sys
    import platform
    
    return {
        "sdk_version": __version__,
        "api_version": API_VERSION,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
    }

def check_python_version() -> bool:
    """检查Python版本兼容性"""
    import sys
    return sys.version_info >= MIN_PYTHON_VERSION
```

#### 8.2.2 变更日志规范
```markdown
# CHANGELOG.md

# 变更日志

本项目的所有重要变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- 

### 变更
- 

### 废弃
- 

### 移除
- 

### 修复
- 

### 安全
- 

## [1.0.0] - 2025-07-14

### 新增
- 初始版本发布
- 支持患者信息查询接口（1101）