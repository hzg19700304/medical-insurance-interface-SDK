# 启动Celery Worker指南

## 1. 打开新的终端窗口

## 2. 激活虚拟环境
```bash
venv\Scripts\Activate.ps1
```

## 3. 启动Celery Worker
```bash
python scripts/start_celery_worker.py worker
```

## 4. 预期输出
你应该看到类似这样的输出：
```
Starting Celery Worker...
Command: celery -A medical_insurance_sdk.async_processing.celery_app worker --loglevel=info --concurrency=4 --queues=default,medical_interface,medical_batch,maintenance
Working directory: E:\medical-insurance-interface-SDK
--------------------------------------------------

 -------------- celery@COMPUTER-NAME v5.5.3 (immunity)
--- ***** ----- 
-- ******* ---- Windows-10-10.0.19041-SP0 2025-07-21 09:10:00
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         medical_insurance_sdk:0x...
- ** ---------- .> transport:   redis://:**@localhost:6379/0
- ** ---------- .> results:     redis://:**@localhost:6379/0
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: ON
--- ***** ----- 
 -------------- [queues]
                .> default          exchange=default(direct) key=default
                .> medical_interface exchange=medical_interface(direct) key=medical_interface
                .> medical_batch     exchange=medical_batch(direct) key=medical_batch
                .> maintenance       exchange=maintenance(direct) key=maintenance

[tasks]
  . async_batch_call_interface
  . async_call_interface
  . cleanup_expired_tasks

[2025-07-21 09:10:00,000: INFO/MainProcess] Connected to redis://:**@localhost:6379/0
[2025-07-21 09:10:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-07-21 09:10:00,000: INFO/MainProcess] mingle: all alone
[2025-07-21 09:10:00,000: INFO/MainProcess] celery@COMPUTER-NAME ready.
```

## 5. 验证Worker启动成功
- 回到Flower界面 (http://localhost:5555)
- 刷新页面
- 在"Workers"标签页应该能看到活跃的Worker

## 6. 测试异步任务
在第三个终端窗口中运行：
```bash
python test_async_tasks.py
```

## 注意事项
- 保持Flower和Worker都在运行状态
- 如果遇到问题，检查Redis容器是否正在运行
- 使用 Ctrl+C 可以停止Worker或Flower