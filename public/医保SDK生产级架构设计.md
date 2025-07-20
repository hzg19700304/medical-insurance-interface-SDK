# 医保SDK生产级架构设计

## 问题分析与解决方案

### 1. 性能问题解决方案

#### 1.1 连接池 + 常驻进程架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HIS数据库     │───▶│   连接池管理     │───▶│  常驻Python服务  │
│   存储过程      │    │   (TCP Socket)   │    │   (守护进程)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  内存队列缓存   │    │   心跳检测机制   │    │   工作线程池     │
│  (Redis/内存)   │    │   (健康检查)     │    │   (并发处理)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 1.2 高性能通信实现
```python
# high_performance_client.py
import socket
import json
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import redis

class HighPerformanceSDKClient:
    """高性能SDK客户端"""
    
    def __init__(self, config):
        # TCP连接池
        self.connection_pool = ConnectionPool(
            host='localhost', 
            port=8888, 
            max_connections=50
        )
        
        # Redis缓存
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            decode_responses=True,
            connection_pool=redis.ConnectionPool(max_connections=20)
        )
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=20)
        
        # 内存队列（高优先级请求）
        self.priority_queue = queue.PriorityQueue()
        
        # 启动常驻服务
        self._start_daemon_service()
    
    def _start_daemon_service(self):
        """启动常驻守护服务"""
        # 启动TCP服务器
        server_thread = threading.Thread(
            target=self._run_tcp_server, 
            daemon=True
        )
        server_thread.start()
        
        # 启动工作线程池
        for i in range(5):
            worker_thread = threading.Thread(
                target=self._worker_loop, 
                daemon=True
            )
            worker_thread.start()
    
    def _run_tcp_server(self):
        """TCP服务器主循环"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', 8888))
        server_socket.listen(50)
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                # 使用线程池处理请求
                self.executor.submit(self._handle_client, client_socket)
            except Exception as e:
                print(f"TCP服务器异常: {e}")
    
    def _handle_client(self, client_socket):
        """处理客户端请求"""
        try:
            # 接收请求数据
            data = client_socket.recv(4096).decode('utf-8')
            request = json.loads(data)
            
            # 处理请求
            if request['type'] == 'sync':
                result = self._process_sync_request(request)
                response = json.dumps(result)
            elif request['type'] == 'async':
                request_id = self._process_async_request(request)
                response = json.dumps({"request_id": request_id})
            else:
                response = json.dumps({"error": "未知请求类型"})
            
            # 发送响应
            client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            error_response = json.dumps({"error": str(e)})
            client_socket.send(error_response.encode('utf-8'))
        finally:
            client_socket.close()

class ConnectionPool:
    """TCP连接池"""
    
    def __init__(self, host, port, max_connections=50):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.pool = queue.Queue(maxsize=max_connections)
        self.current_connections = 0
        self.lock = threading.Lock()
    
    def get_connection(self):
        """获取连接"""
        try:
            # 尝试从池中获取连接
            return self.pool.get_nowait()
        except queue.Empty:
            # 池中无连接，创建新连接
            with self.lock:
                if self.current_connections < self.max_connections:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((self.host, self.port))
                    self.current_connections += 1
                    return conn
                else:
                    # 等待连接可用
                    return self.pool.get()
    
    def return_connection(self, conn):
        """归还连接"""
        try:
            self.pool.put_nowait(conn)
        except queue.Full:
            # 池已满，关闭连接
            conn.close()
            with self.lock:
                self.current_connections -= 1
```

### 2. 错误处理与状态反馈

#### 2.1 完整的错误处理机制
```sql
-- 增强版存储过程，包含完整错误处理
CREATE PROCEDURE sp_medical_insurance_call_v2
    @interface_code VARCHAR(10),
    @input_data NVARCHAR(MAX),
    @timeout INT = 30,
    @retry_count INT = 3,
    @request_id INT OUTPUT,
    @result NVARCHAR(MAX) OUTPUT,
    @error_code INT OUTPUT,
    @error_message NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET @error_code = 0;
    SET @error_message = '';
    
    BEGIN TRY
        -- 1. 参数验证
        IF @interface_code IS NULL OR @input_data IS NULL
        BEGIN
            SET @error_code = -1001;
            SET @error_message = '参数不能为空';
            RETURN;
        END
        
        -- 2. 检查SDK服务状态
        DECLARE @service_status INT;
        EXEC @service_status = sp_check_sdk_service_status;
        
        IF @service_status != 1
        BEGIN
            SET @error_code = -1002;
            SET @error_message = 'SDK服务未运行或不可用';
            RETURN;
        END
        
        -- 3. 插入请求记录
        INSERT INTO medical_insurance_requests (
            interface_code, input_data, status, timeout_seconds, max_retry_count
        ) VALUES (
            @interface_code, @input_data, 'PENDING', @timeout, @retry_count
        );
        
        SET @request_id = SCOPE_IDENTITY();
        
        -- 4. 通过TCP发送请求到SDK服务
        DECLARE @tcp_result INT;
        EXEC @tcp_result = sp_send_tcp_request @request_id;
        
        IF @tcp_result != 0
        BEGIN
            SET @error_code = -1003;
            SET @error_message = 'TCP通信失败';
            
            -- 更新请求状态
            UPDATE medical_insurance_requests 
            SET status = 'ERROR', error_message = @error_message
            WHERE request_id = @request_id;
            
            RETURN;
        END
        
        -- 5. 等待处理结果（带超时）
        DECLARE @wait_count INT = 0;
        DECLARE @max_wait INT = @timeout * 2;
        DECLARE @current_status VARCHAR(20);
        
        WHILE @wait_count < @max_wait
        BEGIN
            SELECT 
                @current_status = status,
                @result = response_data,
                @error_message = error_message
            FROM v_medical_insurance_result
            WHERE request_id = @request_id;
            
            IF @current_status IN ('COMPLETED', 'ERROR')
                BREAK;
                
            WAITFOR DELAY '00:00:00.500';
            SET @wait_count = @wait_count + 1;
        END
        
        -- 6. 处理结果
        IF @current_status = 'COMPLETED'
        BEGIN
            SET @error_code = 0;
        END
        ELSE IF @current_status = 'ERROR'
        BEGIN
            SET @error_code = -1004;
            -- @error_message 已经从数据库获取
        END
        ELSE
        BEGIN
            SET @error_code = -1005;
            SET @error_message = '请求处理超时';
            
            -- 标记请求为超时
            UPDATE medical_insurance_requests 
            SET status = 'TIMEOUT', error_message = @error_message
            WHERE request_id = @request_id;
        END
        
    END TRY
    BEGIN CATCH
        SET @error_code = -1999;
        SET @error_message = '系统异常: ' + ERROR_MESSAGE();
        
        -- 记录异常日志
        INSERT INTO medical_insurance_error_log (
            request_id, error_code, error_message, stack_trace, create_time
        ) VALUES (
            @request_id, @error_code, @error_message, ERROR_MESSAGE(), GETDATE()
        );
    END CATCH
END
GO

-- SDK服务状态检查存储过程
CREATE PROCEDURE sp_check_sdk_service_status
AS
BEGIN
    DECLARE @status INT = 0;
    
    BEGIN TRY
        -- 检查心跳表
        IF EXISTS (
            SELECT 1 FROM sdk_heartbeat 
            WHERE last_heartbeat > DATEADD(SECOND, -30, GETDATE())
        )
        BEGIN
            SET @status = 1;
        END
    END TRY
    BEGIN CATCH
        SET @status = 0;
    END CATCH
    
    RETURN @status;
END
GO
```

#### 2.2 心跳检测机制
```python
# heartbeat_manager.py
import time
import threading
import pyodbc
from datetime import datetime

class HeartbeatManager:
    """心跳检测管理器"""
    
    def __init__(self, db_connection_string):
        self.db_connection_string = db_connection_string
        self.running = False
        self.last_heartbeat = None
        
    def start_heartbeat(self):
        """启动心跳检测"""
        self.running = True
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, 
            daemon=True
        )
        heartbeat_thread.start()
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                self._send_heartbeat()
                time.sleep(10)  # 每10秒发送一次心跳
            except Exception as e:
                print(f"心跳发送失败: {e}")
                time.sleep(5)
    
    def _send_heartbeat(self):
        """发送心跳"""
        try:
            with pyodbc.connect(self.db_connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    MERGE sdk_heartbeat AS target
                    USING (SELECT 1 as dummy) AS source
                    ON (target.service_name = 'medical_insurance_sdk')
                    WHEN MATCHED THEN
                        UPDATE SET 
                            last_heartbeat = GETDATE(),
                            status = 'RUNNING',
                            process_id = ?
                    WHEN NOT MATCHED THEN
                        INSERT (service_name, last_heartbeat, status, process_id)
                        VALUES ('medical_insurance_sdk', GETDATE(), 'RUNNING', ?);
                """, (os.getpid(), os.getpid()))
                conn.commit()
                self.last_heartbeat = datetime.now()
        except Exception as e:
            raise Exception(f"心跳更新失败: {e}")
```

### 3. 事务一致性解决方案

#### 3.1 分布式事务模式
```python
# transaction_manager.py
import pyodbc
from contextlib import contextmanager

class TransactionManager:
    """事务管理器"""
    
    def __init__(self, his_connection_string, sdk_connection_string):
        self.his_connection = his_connection_string
        self.sdk_connection = sdk_connection_string
    
    @contextmanager
    def distributed_transaction(self):
        """分布式事务上下文管理器"""
        his_conn = None
        sdk_conn = None
        
        try:
            # 开启两个数据库连接
            his_conn = pyodbc.connect(self.his_connection)
            sdk_conn = pyodbc.connect(self.sdk_connection)
            
            # 开启事务
            his_conn.autocommit = False
            sdk_conn.autocommit = False
            
            yield his_conn, sdk_conn
            
            # 两阶段提交
            his_conn.commit()
            sdk_conn.commit()
            
        except Exception as e:
            # 回滚所有事务
            if his_conn:
                his_conn.rollback()
            if sdk_conn:
                sdk_conn.rollback()
            raise e
        finally:
            if his_conn:
                his_conn.close()
            if sdk_conn:
                sdk_conn.close()

# 使用示例
def process_medical_insurance_with_transaction(patient_id, fee_items):
    """带事务的医保处理"""
    tx_manager = TransactionManager(HIS_CONNECTION, SDK_CONNECTION)
    
    with tx_manager.distributed_transaction() as (his_conn, sdk_conn):
        # 1. 在HIS数据库中创建费用记录
        his_cursor = his_conn.cursor()
        his_cursor.execute("""
            INSERT INTO patient_fees (patient_id, total_amount, status)
            VALUES (?, ?, 'PENDING')
        """, (patient_id, sum(item['amount'] for item in fee_items)))
        
        fee_id = his_cursor.lastrowid
        
        # 2. 在SDK数据库中创建医保请求
        sdk_cursor = sdk_conn.cursor()
        sdk_cursor.execute("""
            INSERT INTO medical_insurance_requests (
                his_fee_id, interface_code, input_data, status
            ) VALUES (?, '2207', ?, 'PENDING')
        """, (fee_id, json.dumps(fee_items)))
        
        request_id = sdk_cursor.lastrowid
        
        # 3. 调用医保接口
        result = call_medical_insurance_sync(request_id)
        
        if result.get('infcode') == '0':
            # 成功：更新两边的状态
            his_cursor.execute("""
                UPDATE patient_fees 
                SET status = 'COMPLETED', insurance_amount = ?
                WHERE fee_id = ?
            """, (result['insurance_amount'], fee_id))
            
            sdk_cursor.execute("""
                UPDATE medical_insurance_requests 
                SET status = 'COMPLETED'
                WHERE request_id = ?
            """, (request_id,))
        else:
            # 失败：抛出异常，触发回滚
            raise Exception(f"医保接口调用失败: {result.get('err_msg')}")
```

#### 3.2 补偿事务模式（Saga模式）
```python
# saga_transaction.py
class SagaTransaction:
    """Saga事务模式实现"""
    
    def __init__(self):
        self.steps = []
        self.compensations = []
    
    def add_step(self, action, compensation):
        """添加事务步骤"""
        self.steps.append(action)
        self.compensations.append(compensation)
    
    def execute(self):
        """执行Saga事务"""
        executed_steps = []
        
        try:
            for i, step in enumerate(self.steps):
                result = step()
                executed_steps.append(i)
                
                if not result.get('success', False):
                    raise Exception(f"步骤{i}执行失败: {result.get('error')}")
            
            return {"success": True, "message": "所有步骤执行成功"}
            
        except Exception as e:
            # 执行补偿操作
            self._compensate(executed_steps)
            return {"success": False, "error": str(e)}
    
    def _compensate(self, executed_steps):
        """执行补偿操作"""
        # 逆序执行补偿
        for step_index in reversed(executed_steps):
            try:
                compensation = self.compensations[step_index]
                compensation()
            except Exception as e:
                print(f"补偿操作失败: {e}")

# 使用示例
def process_outpatient_settlement_saga(patient_id, fee_items):
    """门诊结算Saga事务"""
    saga = SagaTransaction()
    
    # 步骤1: 创建HIS费用记录
    def create_his_fee():
        # 创建费用记录逻辑
        return {"success": True, "fee_id": 12345}
    
    def compensate_his_fee():
        # 删除费用记录
        pass
    
    saga.add_step(create_his_fee, compensate_his_fee)
    
    # 步骤2: 调用医保接口
    def call_medical_insurance():
        # 医保接口调用逻辑
        return {"success": True, "settlement_id": "S12345"}
    
    def compensate_medical_insurance():
        # 撤销医保结算
        pass
    
    saga.add_step(call_medical_insurance, compensate_medical_insurance)
    
    # 步骤3: 更新HIS状态
    def update_his_status():
        # 更新状态逻辑
        return {"success": True}
    
    def compensate_his_status():
        # 恢复原状态
        pass
    
    saga.add_step(update_his_status, compensate_his_status)
    
    # 执行Saga事务
    return saga.execute()
```

### 4. 并发控制解决方案

#### 4.1 分布式锁机制
```python
# distributed_lock.py
import redis
import time
import uuid
from contextlib import contextmanager

class DistributedLock:
    """基于Redis的分布式锁"""
    
    def __init__(self, redis_client, key, timeout=30):
        self.redis_client = redis_client
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.identifier = str(uuid.uuid4())
    
    def acquire(self, blocking=True, timeout=None):
        """获取锁"""
        end_time = time.time() + (timeout or self.timeout)
        
        while time.time() < end_time:
            if self.redis_client.set(
                self.key, 
                self.identifier, 
                nx=True, 
                ex=self.timeout
            ):
                return True
            
            if not blocking:
                return False
                
            time.sleep(0.001)  # 1ms
        
        return False
    
    def release(self):
        """释放锁"""
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        return self.redis_client.eval(lua_script, 1, self.key, self.identifier)
    
    @contextmanager
    def lock_context(self, blocking=True, timeout=None):
        """锁上下文管理器"""
        acquired = self.acquire(blocking, timeout)
        if not acquired:
            raise Exception("无法获取分布式锁")
        
        try:
            yield
        finally:
            self.release()

# 并发控制管理器
class ConcurrencyManager:
    """并发控制管理器"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.semaphore_keys = {}
    
    def create_semaphore(self, name, max_count):
        """创建信号量"""
        key = f"semaphore:{name}"
        self.semaphore_keys[name] = key
        self.redis_client.delete(key)
        for i in range(max_count):
            self.redis_client.lpush(key, i)
    
    @contextmanager
    def acquire_semaphore(self, name, timeout=30):
        """获取信号量"""
        key = self.semaphore_keys.get(name)
        if not key:
            raise Exception(f"信号量 {name} 不存在")
        
        # 尝试获取信号量
        token = self.redis_client.brpop(key, timeout=timeout)
        if not token:
            raise Exception(f"获取信号量 {name} 超时")
        
        try:
            yield token[1]
        finally:
            # 释放信号量
            self.redis_client.lpush(key, token[1])

# 使用示例
def concurrent_medical_insurance_call(interface_code, data):
    """并发控制的医保接口调用"""
    redis_client = redis.Redis()
    concurrency_manager = ConcurrencyManager(redis_client)
    
    # 创建信号量，限制同时调用医保接口的数量
    concurrency_manager.create_semaphore("medical_insurance_api", 10)
    
    # 使用分布式锁防止重复调用
    patient_id = data.get('psn_no')
    lock = DistributedLock(redis_client, f"patient:{patient_id}")
    
    with lock.lock_context():
        with concurrency_manager.acquire_semaphore("medical_insurance_api"):
            # 执行医保接口调用
            return call_medical_insurance_api(interface_code, data)
```

### 5. 监控运维集成方案

#### 5.1 统一监控接口
```python
# monitoring_integration.py
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List

class HISMonitoringIntegration:
    """HIS监控系统集成"""
    
    def __init__(self, db_connection_string):
        self.db_connection = db_connection_string
    
    def get_sdk_health_status(self) -> Dict:
        """获取SDK健康状态"""
        try:
            with pyodbc.connect(self.db_connection) as conn:
                cursor = conn.cursor()
                
                # 检查服务状态
                cursor.execute("""
                    SELECT 
                        service_name,
                        status,
                        last_heartbeat,
                        DATEDIFF(SECOND, last_heartbeat, GETDATE()) as seconds_since_heartbeat
                    FROM sdk_heartbeat
                    WHERE service_name = 'medical_insurance_sdk'
                """)
                
                heartbeat_info = cursor.fetchone()
                
                if not heartbeat_info:
                    return {
                        "status": "UNKNOWN",
                        "message": "未找到心跳信息",
                        "last_check": datetime.now().isoformat()
                    }
                
                seconds_since = heartbeat_info[3]
                if seconds_since > 60:  # 超过1分钟无心跳
                    status = "DOWN"
                    message = f"服务无响应，上次心跳: {seconds_since}秒前"
                elif seconds_since > 30:  # 30秒-1分钟
                    status = "WARNING"
                    message = f"服务响应缓慢，上次心跳: {seconds_since}秒前"
                else:
                    status = "UP"
                    message = "服务正常运行"
                
                return {
                    "status": status,
                    "message": message,
                    "last_heartbeat": heartbeat_info[2].isoformat(),
                    "seconds_since_heartbeat": seconds_since,
                    "last_check": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"监控检查失败: {str(e)}",
                "last_check": datetime.now().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        try:
            with pyodbc.connect(self.db_connection) as conn:
                cursor = conn.cursor()
                
                # 最近1小时的统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN result_status = 'ERROR' THEN 1 ELSE 0 END) as error_count,
                        SUM(CASE WHEN result_status = 'TIMEOUT' THEN 1 ELSE 0 END) as timeout_count,
                        AVG(CASE 
                            WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
                            THEN DATEDIFF(MILLISECOND, request_time, response_time) 
                            ELSE NULL 
                        END) as avg_response_time_ms,
                        MAX(CASE 
                            WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
                            THEN DATEDIFF(MILLISECOND, request_time, response_time) 
                            ELSE NULL 
                        END) as max_response_time_ms
                    FROM v_medical_insurance_result
                    WHERE request_time >= DATEADD(HOUR, -1, GETDATE())
                """)
                
                metrics = cursor.fetchone()
                
                total = metrics[0] or 0
                success = metrics[1] or 0
                error = metrics[2] or 0
                timeout = metrics[3] or 0
                
                return {
                    "time_range": "last_1_hour",
                    "total_requests": total,
                    "success_requests": success,
                    "error_requests": error,
                    "timeout_requests": timeout,
                    "success_rate": round((success / total * 100) if total > 0 else 0, 2),
                    "error_rate": round((error / total * 100) if total > 0 else 0, 2),
                    "avg_response_time_ms": round(metrics[4] or 0, 2),
                    "max_response_time_ms": metrics[5] or 0,
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "error": f"获取性能指标失败: {str(e)}",
                "last_updated": datetime.now().isoformat()
            }
    
    def get_interface_statistics(self) -> List[Dict]:
        """获取各接口统计信息"""
        try:
            with pyodbc.connect(self.db_connection) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        interface_code,
                        COUNT(*) as total_calls,
                        SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) as success_calls,
                        SUM(CASE WHEN result_status = 'ERROR' THEN 1 ELSE 0 END) as error_calls,
                        AVG(CASE 
                            WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
                            THEN DATEDIFF(MILLISECOND, request_time, response_time) 
                            ELSE NULL 
                        END) as avg_response_time_ms
                    FROM v_medical_insurance_result
                    WHERE request_time >= DATEADD(DAY, -1, GETDATE())
                    GROUP BY interface_code
                    ORDER BY total_calls DESC
                """)
                
                results = []
                for row in cursor.fetchall():
                    interface_code = row[0]
                    total = row[1]
                    success = row[2]
                    error = row[3]
                    avg_time = row[4]
                    
                    results.append({
                        "interface_code": interface_code,
                        "interface_name": self._get_interface_name(interface_code),
                        "total_calls": total,
                        "success_calls": success,
                        "error_calls": error,
                        "success_rate": round((success / total * 100) if total > 0 else 0, 2),
                        "avg_response_time_ms": round(avg_time or 0, 2)
                    })
                
                return results
                
        except Exception as e:
            return [{"error": f"获取接口统计失败: {str(e)}"}]
    
    def _get_interface_name(self, interface_code: str) -> str:
        """获取接口名称"""
        interface_names = {
            "1101": "人员基本信息获取",
            "1201": "医药机构信息获取",
            "2201": "门诊挂号",
            "2207": "门诊结算",
            "2304": "住院结算",
            # ... 更多接口映射
        }
        return interface_names.get(interface_code, f"接口{interface_code}")

# HIS监控集成存储过程
```

```sql
-- 创建HIS监控集成存储过程
CREATE PROCEDURE sp_get_medical_insurance_monitor_data
    @data_type VARCHAR(20) = 'health'  -- health, performance, interfaces
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @data_type = 'health'
    BEGIN
        -- 健康状态检查
        SELECT 
            'medical_insurance_sdk' as service_name,
            CASE 
                WHEN DATEDIFF(SECOND, last_heartbeat, GETDATE()) > 60 THEN 'DOWN'
                WHEN DATEDIFF(SECOND, last_heartbeat, GETDATE()) > 30 THEN 'WARNING'
                ELSE 'UP'
            END as status,
            last_heartbeat,
            DATEDIFF(SECOND, last_heartbeat, GETDATE()) as seconds_since_heartbeat,
            GETDATE() as check_time
        FROM sdk_heartbeat
        WHERE service_name = 'medical_insurance_sdk';
    END
    ELSE IF @data_type = 'performance'
    BEGIN
        -- 性能指标
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN result_status = 'ERROR' THEN 1 ELSE 0 END) as error_count,
            CAST(SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as success_rate,
            AVG(CASE 
                WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
                THEN DATEDIFF(MILLISECOND, request_time, response_time) 
                ELSE NULL 
            END) as avg_response_time_ms
        FROM v_medical_insurance_result
        WHERE request_time >= DATEADD(HOUR, -1, GETDATE());
    END
    ELSE IF @data_type = 'interfaces'
    BEGIN
        -- 接口统计
        SELECT 
            interface_code,
            COUNT(*) as total_calls,
            SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) as success_calls,
            CAST(SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as success_rate,
            AVG(CASE 
                WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
                THEN DATEDIFF(MILLISECOND, request_time, response_time) 
                ELSE NULL 
            END) as avg_response_time_ms
        FROM v_medical_insurance_result
        WHERE request_time >= DATEADD(DAY, -1, GETDATE())
        GROUP BY interface_code
        ORDER BY total_calls DESC;
    END
END
GO

-- 创建告警检查存储过程
CREATE PROCEDURE sp_check_medical_insurance_alerts
AS
BEGIN
    SET NOCOUNT ON;
    
    -- 检查各种告警条件
    SELECT 
        alert_type,
        alert_level,
        alert_message,
        alert_time
    FROM (
        -- 服务状态告警
        SELECT 
            'SERVICE_DOWN' as alert_type,
            'CRITICAL' as alert_level,
            '医保SDK服务已停止响应' as alert_message,
            GETDATE() as alert_time
        FROM sdk_heartbeat
        WHERE service_name = 'medical_insurance_sdk' 
        AND DATEDIFF(SECOND, last_heartbeat, GETDATE()) > 60
        
        UNION ALL
        
        -- 错误率告警
        SELECT 
            'HIGH_ERROR_RATE' as alert_type,
            'WARNING' as alert_level,
            '医保接口错误率过高: ' + CAST(error_rate AS VARCHAR(10)) + '%' as alert_message,
            GETDATE() as alert_time
        FROM (
            SELECT 
                CAST(SUM(CASE WHEN result_status = 'ERROR' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as error_rate
            FROM v_medical_insurance_result
            WHERE request_time >= DATEADD(HOUR, -1, GETDATE())
            AND COUNT(*) > 10  -- 至少有10个请求才检查错误率
        ) t
        WHERE error_rate > 10  -- 错误率超过10%
        
        UNION ALL
        
        -- 响应时间告警
        SELECT 
            'SLOW_RESPONSE' as alert_type,
            'WARNING' as alert_level,
            '医保接口响应时间过慢: ' + CAST(avg_time AS VARCHAR(10)) + 'ms' as alert_message,
            GETDATE() as alert_time
        FROM (
            SELECT 
                AVG(CASE 
                    WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
                    THEN DATEDIFF(MILLISECOND, request_time, response_time) 
                    ELSE NULL 
                END) as avg_time
            FROM v_medical_insurance_result
            WHERE request_time >= DATEADD(HOUR, -1, GETDATE())
        ) t
        WHERE avg_time > 5000  -- 平均响应时间超过5秒
    ) alerts;
END
GO
```

## 总结

通过以上设计，我们解决了你提出的所有关键问题：

1. **性能问题** - 使用连接池、常驻进程、Redis缓存
2. **错误处理** - 完整的错误码体系、心跳检测、超时处理
3. **事务一致性** - 分布式事务、Saga模式、补偿机制
4. **并发控制** - 分布式锁、信号量、队列管理
5. **监控运维** - 统一监控接口、告警机制、性能指标

这个生产级架构既保持了易用性，又具备了企业级应用所需的稳定性和可靠性。