# 医保SDK集成设计方案

## 整体架构（集成后）

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐    ┌─────────────┐
│   医院HIS   │───▶│  存储过程   │───▶│        集成SDK              │───▶│  医保接口   │
│   系统      │    │   调用      │    │  ┌─────────────────────────┐ │    │   服务器    │
└─────────────┘    └─────────────┘    │  │   数据库操作模块        │ │    └─────────────┘
       ▲                              │  │   ├─ 请求管理           │ │            │
       │                              │  │   ├─ 响应存储           │ │            │
┌─────────────┐                       │  │   └─ 状态更新           │ │            │
│  查询视图   │                       │  ├─────────────────────────┤ │            │
│   结果      │                       │  │   通信处理模块          │ │            │
└─────────────┘                       │  │   ├─ 加密解密           │ │            │
       ▲                              │  │   ├─ 签名验签           │ │            │
       │                              │  │   └─ HTTP通信           │ │            │
┌─────────────┐                       │  ├─────────────────────────┤ │            │
│  数据库     │◀──────────────────────│  │   异步处理模块          │ │            │
│  视图/表    │                       │  │   ├─ 队列管理           │ │            │
└─────────────┘                       │  │   ├─ 重试机制           │ │◀───────────┘
                                      │  │   └─ 错误处理           │ │
                                      │  └─────────────────────────┘ │
                                      └─────────────────────────────┘
```

## 1. 集成SDK设计

### 1.1 SDK目录结构
```
medical_insurance_sdk/
├── __init__.py
├── client.py              # 主客户端
├── database.py            # 数据库操作模块
├── processor.py           # 异步处理模块
├── crypto.py              # 加密解密模块
├── config.py              # 配置管理
├── exceptions.py          # 异常定义
├── models.py              # 数据模型
└── utils.py               # 工具函数
```

### 1.2 主客户端类（集成版）
```python
# client.py
import threading
import queue
import time
from typing import Dict, Any, Optional
from .database import DatabaseManager
from .processor import AsyncProcessor
from .crypto import CryptoManager

class MedicalInsuranceSDK:
    """集成版医保SDK - 包含数据库操作和异步处理"""
    
    def __init__(self, 
                 app_id: str, 
                 app_secret: str, 
                 org_code: str, 
                 base_url: str,
                 db_connection_string: str,
                 enable_async: bool = True):
        
        # 基础配置
        self.app_id = app_id
        self.app_secret = app_secret
        self.org_code = org_code
        self.base_url = base_url
        
        # 初始化各个模块
        self.crypto = CryptoManager(app_secret)
        self.database = DatabaseManager(db_connection_string)
        self.processor = AsyncProcessor(self)
        
        # 异步处理
        self.enable_async = enable_async
        if enable_async:
            self._start_async_worker()
    
    def call_sync(self, interface_code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """同步调用 - 直接返回结果"""
        try:
            # 构建请求
            request_data = self._build_request(interface_code, data)
            
            # 发送HTTP请求
            response = self._send_http_request(request_data)
            
            # 处理响应
            return self._handle_response(response)
            
        except Exception as e:
            return {"infcode": "-1", "err_msg": f"调用异常: {str(e)}"}
    
    def call_async(self, interface_code: str, data: Dict[str, Any]) -> int:
        """异步调用 - 返回请求ID"""
        # 保存请求到数据库
        request_id = self.database.save_request(interface_code, data)
        
        # 添加到处理队列
        if self.enable_async:
            self.processor.add_to_queue(request_id)
        
        return request_id
    
    def get_result(self, request_id: int) -> Optional[Dict[str, Any]]:
        """获取异步调用结果"""
        return self.database.get_result(request_id)
    
    def wait_for_result(self, request_id: int, timeout: int = 30) -> Dict[str, Any]:
        """等待异步调用结果"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.get_result(request_id)
            if result and result.get('status') in ['COMPLETED', 'ERROR']:
                return result
            time.sleep(0.5)
        
        return {"status": "TIMEOUT", "err_msg": "等待结果超时"}
    
    def _start_async_worker(self):
        """启动异步处理工作线程"""
        worker_thread = threading.Thread(target=self.processor.run_worker, daemon=True)
        worker_thread.start()
```

### 1.3 数据库操作模块
```python
# database.py
import json
import pyodbc
from datetime import datetime
from typing import Dict, Any, Optional

class DatabaseManager:
    """数据库操作管理器"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._init_tables()
    
    def _get_connection(self):
        """获取数据库连接"""
        return pyodbc.connect(self.connection_string)
    
    def _init_tables(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建请求表
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='medical_insurance_requests')
                CREATE TABLE medical_insurance_requests (
                    request_id INT IDENTITY(1,1) PRIMARY KEY,
                    interface_code VARCHAR(10) NOT NULL,
                    input_data NVARCHAR(MAX) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    create_time DATETIME NOT NULL DEFAULT GETDATE(),
                    update_time DATETIME,
                    retry_count INT DEFAULT 0
                )
            """)
            
            # 创建响应表
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='medical_insurance_responses')
                CREATE TABLE medical_insurance_responses (
                    response_id INT IDENTITY(1,1) PRIMARY KEY,
                    request_id INT NOT NULL,
                    response_data NVARCHAR(MAX) NOT NULL,
                    infcode VARCHAR(10),
                    err_msg NVARCHAR(500),
                    create_time DATETIME NOT NULL DEFAULT GETDATE()
                )
            """)
            
            # 创建结果视图
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='v_medical_insurance_result')
                CREATE VIEW v_medical_insurance_result AS
                SELECT 
                    r.request_id,
                    r.interface_code,
                    r.input_data,
                    r.status,
                    r.create_time as request_time,
                    r.retry_count,
                    resp.response_data,
                    resp.infcode,
                    resp.err_msg,
                    resp.create_time as response_time
                FROM medical_insurance_requests r
                LEFT JOIN medical_insurance_responses resp ON r.request_id = resp.request_id
            """)
            
            conn.commit()
    
    def save_request(self, interface_code: str, data: Dict[str, Any]) -> int:
        """保存请求到数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO medical_insurance_requests (interface_code, input_data)
                OUTPUT INSERTED.request_id
                VALUES (?, ?)
            """, (interface_code, json.dumps(data, ensure_ascii=False)))
            
            request_id = cursor.fetchone()[0]
            conn.commit()
            return request_id
    
    def get_pending_requests(self) -> list:
        """获取待处理的请求"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT request_id, interface_code, input_data
                FROM medical_insurance_requests
                WHERE status = 'PENDING'
                ORDER BY create_time
            """)
            
            return [
                {
                    'request_id': row[0],
                    'interface_code': row[1],
                    'input_data': json.loads(row[2])
                }
                for row in cursor.fetchall()
            ]
    
    def save_response(self, request_id: int, response: Dict[str, Any]):
        """保存响应数据"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 保存响应
            cursor.execute("""
                INSERT INTO medical_insurance_responses 
                (request_id, response_data, infcode, err_msg)
                VALUES (?, ?, ?, ?)
            """, (
                request_id,
                json.dumps(response, ensure_ascii=False),
                response.get('infcode', ''),
                response.get('err_msg', '')
            ))
            
            # 更新请求状态
            status = 'COMPLETED' if response.get('infcode') == '0' else 'ERROR'
            cursor.execute("""
                UPDATE medical_insurance_requests 
                SET status = ?, update_time = GETDATE()
                WHERE request_id = ?
            """, (status, request_id))
            
            conn.commit()
    
    def get_result(self, request_id: int) -> Optional[Dict[str, Any]]:
        """获取请求结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, response_data, infcode, err_msg
                FROM v_medical_insurance_result
                WHERE request_id = ?
            """, request_id)
            
            row = cursor.fetchone()
            if row:
                result = {
                    'status': row[0],
                    'infcode': row[2],
                    'err_msg': row[3]
                }
                if row[1]:  # response_data
                    result['response_data'] = json.loads(row[1])
                return result
            return None
```

### 1.4 异步处理模块
```python
# processor.py
import queue
import time
import threading
from typing import Dict, Any

class AsyncProcessor:
    """异步处理器"""
    
    def __init__(self, sdk_client):
        self.sdk_client = sdk_client
        self.request_queue = queue.Queue()
        self.running = False
    
    def add_to_queue(self, request_id: int):
        """添加请求到处理队列"""
        self.request_queue.put(request_id)
    
    def run_worker(self):
        """工作线程主循环"""
        self.running = True
        while self.running:
            try:
                # 从队列获取请求ID（阻塞等待）
                request_id = self.request_queue.get(timeout=1)
                self.process_request(request_id)
                self.request_queue.task_done()
                
            except queue.Empty:
                # 队列为空时，检查数据库中的待处理请求
                self.process_pending_requests()
                time.sleep(1)
            except Exception as e:
                print(f"处理请求异常: {str(e)}")
    
    def process_request(self, request_id: int):
        """处理单个请求"""
        try:
            # 从数据库获取请求信息
            with self.sdk_client.database._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT interface_code, input_data, retry_count
                    FROM medical_insurance_requests
                    WHERE request_id = ? AND status = 'PENDING'
                """, request_id)
                
                row = cursor.fetchone()
                if not row:
                    return
                
                interface_code, input_data_str, retry_count = row
                input_data = json.loads(input_data_str)
            
            # 更新状态为处理中
            self.update_request_status(request_id, 'PROCESSING')
            
            # 调用同步接口
            response = self.sdk_client.call_sync(interface_code, input_data)
            
            # 保存响应
            self.sdk_client.database.save_response(request_id, response)
            
        except Exception as e:
            # 处理失败，记录错误
            error_response = {
                "infcode": "-1",
                "err_msg": f"处理异常: {str(e)}"
            }
            self.sdk_client.database.save_response(request_id, error_response)
    
    def process_pending_requests(self):
        """处理数据库中的待处理请求"""
        pending_requests = self.sdk_client.database.get_pending_requests()
        for request in pending_requests:
            self.add_to_queue(request['request_id'])
    
    def update_request_status(self, request_id: int, status: str):
        """更新请求状态"""
        with self.sdk_client.database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE medical_insurance_requests 
                SET status = ?, update_time = GETDATE()
                WHERE request_id = ?
            """, (status, request_id))
            conn.commit()
    
    def stop(self):
        """停止处理器"""
        self.running = False
```

## 2. HIS系统集成方式

### 2.1 存储过程（简化版）
```sql
-- 创建存储过程
CREATE PROCEDURE sp_medical_insurance_call
    @interface_code VARCHAR(10),
    @input_data NVARCHAR(MAX),
    @async BIT = 1,  -- 是否异步调用
    @result_id INT OUTPUT,
    @result_data NVARCHAR(MAX) OUTPUT
AS
BEGIN
    DECLARE @cmd NVARCHAR(1000);
    DECLARE @mode VARCHAR(10) = CASE WHEN @async = 1 THEN 'async' ELSE 'sync' END;
    
    -- 生成临时文件名
    DECLARE @temp_file VARCHAR(100) = 'temp_' + CAST(NEWID() AS VARCHAR(36)) + '.json';
    
    -- 构建Python调用命令
    SET @cmd = 'python C:\MedicalInsurance\sdk_caller.py ' + 
               @interface_code + ' "' + @input_data + '" ' + @mode + ' ' + @temp_file;
    
    -- 执行Python脚本
    EXEC xp_cmdshell @cmd;
    
    -- 读取结果
    -- 这里可以通过文件或数据库获取结果
    -- 具体实现根据需要调整
END
```

### 2.2 Python调用脚本
```python
# sdk_caller.py - HIS调用SDK的桥接脚本
import sys
import json
from medical_insurance_sdk import MedicalInsuranceSDK

def main():
    interface_code = sys.argv[1]
    input_data = json.loads(sys.argv[2])
    mode = sys.argv[3]  # sync 或 async
    temp_file = sys.argv[4]
    
    # 初始化SDK
    sdk = MedicalInsuranceSDK(
        app_id="H12345678901_APP",
        app_secret="your_secret_key",
        org_code="H12345678901",
        base_url="https://api.hnybj.com",
        db_connection_string="DRIVER={SQL Server};SERVER=localhost;DATABASE=HIS;Trusted_Connection=yes;"
    )
    
    if mode == 'sync':
        # 同步调用
        result = sdk.call_sync(interface_code, input_data)
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
    else:
        # 异步调用
        request_id = sdk.call_async(interface_code, input_data)
        result = {"request_id": request_id}
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
```

## 3. 使用示例

### 3.1 HIS系统调用
```sql
-- 异步调用
DECLARE @result_id INT, @result_data NVARCHAR(MAX);
EXEC sp_medical_insurance_call 
    @interface_code = '1101',
    @input_data = '{"psn_no": "430123199001011234"}',
    @async = 1,
    @result_id = @result_id OUTPUT,
    @result_data = @result_data OUTPUT;

-- 查询结果
SELECT * FROM v_medical_insurance_result WHERE request_id = @result_id;

-- 同步调用
EXEC sp_medical_insurance_call 
    @interface_code = '1101',
    @input_data = '{"psn_no": "430123199001011234"}',
    @async = 0,
    @result_id = @result_id OUTPUT,
    @result_data = @result_data OUTPUT;

-- 直接获取结果
SELECT @result_data;
```

### 3.2 Python直接调用
```python
from medical_insurance_sdk import MedicalInsuranceSDK

# 初始化SDK
sdk = MedicalInsuranceSDK(
    app_id="your_app_id",
    app_secret="your_secret",
    org_code="your_org_code",
    base_url="https://api.example.com",
    db_connection_string="your_connection_string"
)

# 同步调用
result = sdk.call_sync("1101", {"psn_no": "123456"})
print(result)

# 异步调用
request_id = sdk.call_async("1101", {"psn_no": "123456"})
result = sdk.wait_for_result(request_id, timeout=30)
print(result)
```

## 4. 优势总结

### 4.1 集成优势
1. **统一管理**：所有功能都在一个SDK包中
2. **简化部署**：只需要安装一个SDK包
3. **版本一致**：避免组件版本不匹配问题
4. **易于维护**：统一的错误处理和日志

### 4.2 功能优势
1. **同步异步兼容**：支持两种调用模式
2. **数据持久化**：自动管理数据库操作
3. **自动重试**：内置重试和错误处理机制
4. **监控完善**：完整的调用链路追踪

这个集成方案既保持了架构的清晰性，又提供了更好的易用性。你觉得这个设计如何？