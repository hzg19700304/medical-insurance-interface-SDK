# 医保SDK完整架构图

## 最终SDK包结构

```
medical-insurance-sdk/
├── setup.py                    # 安装配置
├── README.md                   # 使用说明
├── requirements.txt            # 依赖包
├── medical_insurance_sdk/      # 主包
│   ├── __init__.py            # 包初始化
│   ├── client.py              # 主客户端（统一入口）
│   ├── communication/         # 通讯模块
│   │   ├── __init__.py
│   │   ├── http_client.py     # HTTP通信
│   │   ├── crypto.py          # 加密解密
│   │   └── protocol.py        # 协议处理
│   ├── database/              # 数据库操作模块
│   │   ├── __init__.py
│   │   ├── manager.py         # 数据库管理器
│   │   ├── models.py          # 数据模型
│   │   └── migrations.sql     # 数据库脚本
│   ├── async_processor/       # 异步处理模块
│   │   ├── __init__.py
│   │   ├── worker.py          # 后台工作进程
│   │   ├── queue_manager.py   # 队列管理
│   │   └── scheduler.py       # 任务调度
│   ├── scripts/               # Python脚本模块
│   │   ├── __init__.py
│   │   ├── service.py         # 后台服务脚本
│   │   ├── installer.py       # 安装脚本
│   │   └── monitor.py         # 监控脚本
│   ├── config/                # 配置模块
│   │   ├── __init__.py
│   │   ├── settings.py        # 配置管理
│   │   └── defaults.json      # 默认配置
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── logger.py          # 日志工具
│       ├── validator.py       # 数据校验
│       └── exceptions.py      # 异常定义
├── examples/                   # 使用示例
│   ├── basic_usage.py
│   ├── his_integration.py
│   └── batch_processing.py
├── tests/                      # 测试用例
│   ├── test_communication.py
│   ├── test_database.py
│   └── test_async_processor.py
└── docs/                       # 文档
    ├── installation.md
    ├── api_reference.md
    └── troubleshooting.md
```

## 各模块详细功能

### 1. 通讯模块 (communication/)
```python
# http_client.py - HTTP通信核心
class HTTPClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = timeout
    
    def post(self, data: dict) -> dict:
        """发送POST请求"""
        response = self.session.post(
            f"{self.base_url}/api/medical-insurance",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        return response.json()

# crypto.py - 加密解密
class CryptoManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        # SM4加密实现
        pass
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        # SM4解密实现
        pass
    
    def sign(self, data: str) -> str:
        """数字签名"""
        # SM3签名实现
        pass

# protocol.py - 协议处理
class ProtocolHandler:
    def build_request(self, interface_code: str, data: dict) -> dict:
        """构建标准请求格式"""
        return {
            "infno": interface_code,
            "msgid": self._generate_msgid(),
            "mdtrtarea_admvs": self.org_code[:6],
            "insuplc_admdvs": self.org_code[:6],
            "recer_sys_code": "HIS",
            "signtype": "SM3",
            "infver": "V1.0",
            "inf_time": self._get_current_time(),
            "fixmedins_code": self.org_code,
            "input": data
        }
```

### 2. 数据库操作模块 (database/)
```python
# manager.py - 数据库管理器
class DatabaseManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.init_database()
    
    def init_database(self):
        """初始化数据库表和存储过程"""
        sql_script = self._load_migration_script()
        self._execute_script(sql_script)
    
    def save_request(self, interface_code: str, data: dict) -> int:
        """保存请求记录"""
        pass
    
    def save_response(self, request_id: int, response: dict):
        """保存响应记录"""
        pass
    
    def get_pending_requests(self) -> list:
        """获取待处理请求"""
        pass

# models.py - 数据模型
@dataclass
class MedicalInsuranceRequest:
    request_id: int
    interface_code: str
    input_data: dict
    status: str
    create_time: datetime
    
@dataclass
class MedicalInsuranceResponse:
    response_id: int
    request_id: int
    response_data: dict
    infcode: str
    err_msg: str
    create_time: datetime
```

### 3. 异步处理模块 (async_processor/)
```python
# worker.py - 后台工作进程
class AsyncWorker:
    def __init__(self, sdk_client):
        self.sdk_client = sdk_client
        self.running = False
        self.queue = Queue()
    
    def start(self):
        """启动后台工作进程"""
        self.running = True
        worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        worker_thread.start()
    
    def _run_loop(self):
        """主工作循环"""
        while self.running:
            try:
                request_id = self.queue.get(timeout=1)
                self._process_request(request_id)
            except queue.Empty:
                self._check_pending_requests()
                time.sleep(1)

# queue_manager.py - 队列管理
class QueueManager:
    def __init__(self):
        self.request_queue = Queue()
        self.priority_queue = PriorityQueue()
    
    def add_request(self, request_id: int, priority: int = 0):
        """添加请求到队列"""
        if priority > 0:
            self.priority_queue.put((priority, request_id))
        else:
            self.request_queue.put(request_id)

# scheduler.py - 任务调度
class TaskScheduler:
    def __init__(self):
        self.scheduled_tasks = {}
    
    def schedule_retry(self, request_id: int, delay: int):
        """调度重试任务"""
        retry_time = datetime.now() + timedelta(seconds=delay)
        self.scheduled_tasks[request_id] = retry_time
```

### 4. Python脚本模块 (scripts/)
```python
# service.py - 后台服务脚本
class MedicalInsuranceService:
    """可以作为Windows服务运行的后台服务"""
    
    def __init__(self):
        self.sdk = None
        self.running = False
    
    def start_service(self):
        """启动服务"""
        self.sdk = MedicalInsuranceSDK.from_config()
        self.running = True
        self._monitor_signals()
    
    def _monitor_signals(self):
        """监控信号文件，处理HIS请求"""
        signal_dir = "C:/MedicalInsurance/signals/"
        while self.running:
            for signal_file in os.listdir(signal_dir):
                if signal_file.endswith('.signal'):
                    request_id = self._parse_signal_file(signal_file)
                    self.sdk.async_processor.add_to_queue(request_id)
                    os.remove(os.path.join(signal_dir, signal_file))
            time.sleep(0.1)

# installer.py - 安装脚本
class SDKInstaller:
    """SDK安装和配置工具"""
    
    def install(self, config: dict):
        """安装SDK"""
        # 1. 创建目录结构
        self._create_directories()
        
        # 2. 初始化数据库
        self._init_database(config['db_connection'])
        
        # 3. 创建配置文件
        self._create_config_file(config)
        
        # 4. 安装Windows服务（可选）
        self._install_windows_service()
    
    def uninstall(self):
        """卸载SDK"""
        pass

# monitor.py - 监控脚本
class SDKMonitor:
    """SDK运行状态监控"""
    
    def get_status(self) -> dict:
        """获取SDK运行状态"""
        return {
            "service_running": self._check_service_status(),
            "database_connected": self._check_database_connection(),
            "pending_requests": self._get_pending_count(),
            "error_requests": self._get_error_count(),
            "last_success_time": self._get_last_success_time()
        }
    
    def generate_report(self) -> str:
        """生成监控报告"""
        pass
```

## 统一入口 - 主客户端

```python
# client.py - 主客户端（统一入口）
class MedicalInsuranceSDK:
    """医保SDK主客户端 - 统一入口"""
    
    def __init__(self, 
                 app_id: str,
                 app_secret: str, 
                 org_code: str,
                 base_url: str,
                 db_connection_string: str,
                 enable_async: bool = True):
        
        # 初始化各个模块
        self.communication = CommunicationModule(app_id, app_secret, org_code, base_url)
        self.database = DatabaseManager(db_connection_string)
        self.async_processor = AsyncProcessor(self) if enable_async else None
        self.config = ConfigManager()
        
        # 启动后台服务
        if enable_async:
            self.async_processor.start()
    
    @classmethod
    def setup(cls, **config) -> 'MedicalInsuranceSDK':
        """一键安装和初始化"""
        installer = SDKInstaller()
        installer.install(config)
        return cls(**config)
    
    @classmethod
    def from_config(cls, config_file: str = None) -> 'MedicalInsuranceSDK':
        """从配置文件创建实例"""
        config = ConfigManager.load_config(config_file)
        return cls(**config)
    
    # 核心API方法
    def call_sync(self, interface_code: str, data: dict) -> dict:
        """同步调用"""
        return self.communication.call(interface_code, data)
    
    def call_async(self, interface_code: str, data: dict) -> int:
        """异步调用"""
        request_id = self.database.save_request(interface_code, data)
        if self.async_processor:
            self.async_processor.add_to_queue(request_id)
        return request_id
    
    def get_result(self, request_id: int) -> dict:
        """获取结果"""
        return self.database.get_result(request_id)
    
    def get_status(self) -> dict:
        """获取SDK状态"""
        monitor = SDKMonitor()
        return monitor.get_status()
```

## 使用方式

### 1. 一键安装
```python
from medical_insurance_sdk import MedicalInsuranceSDK

# 一键安装和初始化
sdk = MedicalInsuranceSDK.setup(
    app_id="your_app_id",
    app_secret="your_secret",
    org_code="your_org_code",
    base_url="https://api.example.com",
    db_connection_string="your_connection_string"
)
```

### 2. HIS系统调用
```sql
-- HIS只需要调用存储过程
EXEC sp_medical_insurance_call '1101', '{"psn_no": "123456"}', 1, @request_id OUTPUT;
SELECT * FROM v_medical_insurance_result WHERE request_id = @request_id;
```

### 3. Python直接调用
```python
# 直接使用SDK
sdk = MedicalInsuranceSDK.from_config()
result = sdk.call_sync("1101", {"psn_no": "123456"})
```

## 部署方式

### 方式1：Python包安装
```bash
pip install medical-insurance-sdk
python -c "from medical_insurance_sdk import setup; setup()"
```

### 方式2：Windows服务
```bash
# 安装为Windows服务
medical-insurance-sdk install-service
net start MedicalInsuranceSDK
```

### 方式3：Docker容器
```dockerfile
FROM python:3.9
RUN pip install medical-insurance-sdk
CMD ["medical-insurance-sdk", "run-service"]
```

## 总结

这个All-in-One的SDK包含：

1. **通讯模块** - 处理HTTP通信、加密解密、协议格式化
2. **数据库操作模块** - 管理请求响应数据、自动创建表结构
3. **异步处理模块** - 后台队列处理、任务调度、重试机制
4. **Python脚本模块** - 后台服务、安装工具、监控工具

**核心优势：**
- 一个包解决所有问题
- 一行代码完成安装
- HIS系统集成超简单
- 维护升级统一管理

你觉得这个完整的架构设计如何？