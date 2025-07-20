# 医保接口通用SDK系统需求文档

## 系统架构概述

通过**硬件设备输入触发**的方式实现医保接口调用，做到最小化代码入侵。

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 刷卡/扫码   │───▶│  外挂小程序  │───▶│ 数据库触发器 │───▶│  医保接口   │
│ 硬件设备    │    │ (监听输入)  │    │ (自动调用)  │    │   调用      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 实体卡/二维码│    │ 本地数据库   │    │ 存储过程     │    │ 响应数据    │
│ 识别        │    │ 插入记录    │    │ 医保SDK     │    │ 存储        │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 1. 硬件设备层

### 1.1 实体卡读取
```
设备：USB读卡器（仿真键盘模式）
输出：直接输出卡号字符串到当前焦点窗口
格式：18位身份证号或医保卡号
示例：430123199001011234
```

### 1.2 电子凭证扫码
```
设备：扫码枪或摄像头
输出：28位二维码字符串
格式：医保电子凭证二维码内容
示例：1234567890123456789012345678
```

## 2. 外挂小程序设计

### 2.1 程序功能
```python
# medical_insurance_listener.py
import time
import threading
import pyodbc
import keyboard
import cv2
import pyzbar
from datetime import datetime
import json
import logging

class MedicalInsuranceListener:
    """医保输入监听程序"""
    
    def __init__(self):
        # 数据库连接
        self.db_connection = "DRIVER={SQL Server};SERVER=localhost;DATABASE=HIS;Trusted_Connection=yes;"
        
        # 输入缓存
        self.input_buffer = ""
        self.last_input_time = 0
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('medical_listener.log'),
                logging.StreamHandler()
            ]
        )
        
        logging.info("医保监听程序启动")
    
    def start_listening(self):
        """启动监听"""
        # 启动键盘监听线程
        keyboard_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        keyboard_thread.start()
        
        # 启动摄像头监听线程（如果需要）
        camera_thread = threading.Thread(target=self._camera_listener, daemon=True)
        camera_thread.start()
        
        logging.info("开始监听键盘和摄像头输入...")
        
        # 主循环
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("程序停止")
    
    def _keyboard_listener(self):
        """键盘输入监听"""
        def on_key_event(event):
            if event.event_type == keyboard.KEY_DOWN:
                current_time = time.time()
                
                # 如果距离上次输入超过2秒，清空缓存
                if current_time - self.last_input_time > 2:
                    self.input_buffer = ""
                
                self.last_input_time = current_time
                
                if event.name == 'enter':
                    # 回车键表示输入完成
                    if self.input_buffer:
                        self._process_input(self.input_buffer.strip())
                        self.input_buffer = ""
                elif len(event.name) == 1:
                    # 普通字符
                    self.input_buffer += event.name
                elif event.name.isdigit():
                    # 数字键
                    self.input_buffer += event.name
        
        keyboard.hook(on_key_event)
        keyboard.wait()
    
    def _camera_listener(self):
        """摄像头二维码监听"""
        cap = cv2.VideoCapture(0)  # 使用默认摄像头
        
        while True:
            try:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # 解码二维码
                barcodes = pyzbar.decode(frame)
                
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    
                    # 检查是否是医保电子凭证（28位）
                    if len(barcode_data) == 28 and barcode_data.isdigit():
                        self._process_input(barcode_data, input_type='qrcode')
                
                time.sleep(0.1)  # 避免过度占用CPU
                
            except Exception as e:
                logging.error(f"摄像头监听异常: {e}")
                time.sleep(1)
    
    def _process_input(self, input_data, input_type='card'):
        """处理输入数据"""
        try:
            logging.info(f"接收到输入: {input_data} (类型: {input_type})")
            
            # 验证输入格式
            if not self._validate_input(input_data, input_type):
                logging.warning(f"输入格式无效: {input_data}")
                return
            
            # 插入触发记录
            self._insert_trigger_record(input_data, input_type)
            
        except Exception as e:
            logging.error(f"处理输入异常: {e}")
    
    def _validate_input(self, input_data, input_type):
        """验证输入格式"""
        if input_type == 'card':
            # 身份证号：18位
            return len(input_data) == 18 and input_data.isdigit()
        elif input_type == 'qrcode':
            # 医保电子凭证：28位
            return len(input_data) == 28 and input_data.isdigit()
        
        return False
    
    def _insert_trigger_record(self, input_data, input_type):
        """插入触发记录到数据库"""
        try:
            with pyodbc.connect(self.db_connection) as conn:
                cursor = conn.cursor()
                
                # 插入触发记录
                cursor.execute("""
                    INSERT INTO medical_trigger (
                        input_data, 
                        input_type, 
                        trigger_time, 
                        status,
                        workstation_id
                    ) VALUES (?, ?, GETDATE(), 'PENDING', ?)
                """, (
                    input_data, 
                    input_type, 
                    self._get_workstation_id()
                ))
                
                conn.commit()
                logging.info(f"触发记录已插入: {input_data}")
                
        except Exception as e:
            logging.error(f"插入触发记录失败: {e}")
    
    def _get_workstation_id(self):
        """获取工作站ID"""
        import socket
        return socket.gethostname()

if __name__ == "__main__":
    listener = MedicalInsuranceListener()
    listener.start_listening()
```

### 2.2 程序部署
```python
# install_listener.py - 安装脚本
import os
import shutil
import winreg
import sys

def install_listener():
    """安装监听程序"""
    
    # 1. 复制程序文件到系统目录
    program_dir = r"C:\MedicalInsurance"
    if not os.path.exists(program_dir):
        os.makedirs(program_dir)
    
    # 复制主程序
    shutil.copy("medical_insurance_listener.py", program_dir)
    shutil.copy("config.json", program_dir)
    
    # 2. 创建启动脚本
    startup_script = f"""
@echo off
cd /d {program_dir}
python medical_insurance_listener.py
"""
    
    with open(os.path.join(program_dir, "start_listener.bat"), "w") as f:
        f.write(startup_script)
    
    # 3. 添加到开机启动
    startup_folder = os.path.join(
        os.environ['APPDATA'], 
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    
    shutil.copy(
        os.path.join(program_dir, "start_listener.bat"),
        os.path.join(startup_folder, "medical_insurance_listener.bat")
    )
    
    print("医保监听程序安装完成")
    print(f"程序目录: {program_dir}")
    print("已添加到开机启动")

if __name__ == "__main__":
    install_listener()
```

## 3. 数据库触发器设计

### 3.1 触发表结构
```sql
-- 创建医保触发表
CREATE TABLE medical_trigger (
    id INT IDENTITY(1,1) PRIMARY KEY,
    input_data VARCHAR(50) NOT NULL,           -- 输入数据（卡号或二维码）
    input_type VARCHAR(20) NOT NULL,           -- 输入类型（card/qrcode）
    trigger_time DATETIME NOT NULL,            -- 触发时间
    status VARCHAR(20) DEFAULT 'PENDING',      -- 处理状态
    workstation_id VARCHAR(50),                -- 工作站ID
    result_data NVARCHAR(MAX),                 -- 处理结果
    error_message NVARCHAR(500),               -- 错误信息
    process_time DATETIME,                     -- 处理时间
    INDEX idx_status_time (status, trigger_time)
);
```

### 3.2 触发器实现
```sql
-- 创建触发器
CREATE TRIGGER tr_medical_trigger
ON medical_trigger
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @id INT;
    DECLARE @input_data VARCHAR(50);
    DECLARE @input_type VARCHAR(20);
    
    -- 获取插入的记录
    SELECT @id = id, @input_data = input_data, @input_type = input_type
    FROM inserted;
    
    -- 更新状态为处理中
    UPDATE medical_trigger 
    SET status = 'PROCESSING', process_time = GETDATE()
    WHERE id = @id;
    
    -- 异步调用处理存储过程
    DECLARE @sql NVARCHAR(1000);
    SET @sql = 'EXEC sp_process_medical_trigger ' + CAST(@id AS VARCHAR(10));
    
    -- 使用作业异步执行（避免阻塞触发器）
    EXEC msdb.dbo.sp_add_job
        @job_name = 'MedicalTrigger_' + CAST(@id AS VARCHAR(10)),
        @enabled = 1,
        @delete_level = 3;  -- 完成后删除作业
    
    EXEC msdb.dbo.sp_add_jobstep
        @job_name = 'MedicalTrigger_' + CAST(@id AS VARCHAR(10)),
        @step_name = 'ProcessTrigger',
        @command = @sql;
    
    EXEC msdb.dbo.sp_add_jobserver
        @job_name = 'MedicalTrigger_' + CAST(@id AS VARCHAR(10));
    
    EXEC msdb.dbo.sp_start_job
        @job_name = 'MedicalTrigger_' + CAST(@id AS VARCHAR(10));
END
GO
```

### 3.3 处理存储过程
```sql
-- 创建医保处理存储过程
CREATE PROCEDURE sp_process_medical_trigger
    @trigger_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @input_data VARCHAR(50);
    DECLARE @input_type VARCHAR(20);
    DECLARE @workstation_id VARCHAR(50);
    DECLARE @result NVARCHAR(MAX);
    DECLARE @error_msg NVARCHAR(500);
    
    BEGIN TRY
        -- 获取触发记录
        SELECT @input_data = input_data, @input_type = input_type, @workstation_id = workstation_id
        FROM medical_trigger
        WHERE id = @trigger_id;
        
        -- 根据输入类型调用不同的医保接口
        IF @input_type = 'card'
        BEGIN
            -- 身份证号 → 调用人员信息查询
            EXEC sp_call_medical_insurance 
                @interface_code = '1101',
                @input_data = '{"psn_no": "' + @input_data + '"}',
                @result = @result OUTPUT;
        END
        ELSE IF @input_type = 'qrcode'
        BEGIN
            -- 二维码 → 调用电子凭证解析
            EXEC sp_call_medical_insurance 
                @interface_code = '6101',
                @input_data = '{"qr_code": "' + @input_data + '"}',
                @result = @result OUTPUT;
        END
        
        -- 更新处理结果
        UPDATE medical_trigger 
        SET status = 'COMPLETED',
            result_data = @result,
            process_time = GETDATE()
        WHERE id = @trigger_id;
        
    END TRY
    BEGIN CATCH
        -- 处理异常
        SET @error_msg = ERROR_MESSAGE();
        
        UPDATE medical_trigger 
        SET status = 'ERROR',
            error_message = @error_msg,
            process_time = GETDATE()
        WHERE id = @trigger_id;
    END CATCH
END
GO
```

## 4. 医保SDK集成

### 4.1 SDK调用存储过程
```sql
-- 医保SDK调用存储过程
CREATE PROCEDURE sp_call_medical_insurance
    @interface_code VARCHAR(10),
    @input_data NVARCHAR(MAX),
    @result NVARCHAR(MAX) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @cmd NVARCHAR(4000);
    DECLARE @temp_file VARCHAR(100) = 'temp_' + CAST(NEWID() AS VARCHAR(36)) + '.json';
    DECLARE @temp_path VARCHAR(200) = 'C:\MedicalInsurance\temp\' + @temp_file;
    
    -- 构建Python调用命令
    SET @cmd = 'python C:\MedicalInsurance\sdk_caller.py "' + 
               @interface_code + '" "' + 
               REPLACE(@input_data, '"', '""') + '" "' + 
               @temp_path + '"';
    
    -- 执行Python脚本
    EXEC xp_cmdshell @cmd, no_output;
    
    -- 读取结果文件
    DECLARE @powershell_cmd NVARCHAR(1000);
    SET @powershell_cmd = 'powershell -Command "Get-Content ''' + @temp_path + ''' -Raw"';
    
    -- 创建临时表存储结果
    CREATE TABLE #temp_result (result_line NVARCHAR(MAX));
    INSERT INTO #temp_result EXEC xp_cmdshell @powershell_cmd;
    
    -- 获取结果
    SELECT @result = STRING_AGG(result_line, '') 
    FROM #temp_result 
    WHERE result_line IS NOT NULL;
    
    -- 清理临时文件
    SET @cmd = 'del "' + @temp_path + '"';
    EXEC xp_cmdshell @cmd, no_output;
    
    DROP TABLE #temp_result;
END
GO
```

### 4.2 Python SDK调用脚本
```python
# sdk_caller.py
import sys
import json
from medical_insurance_sdk import MedicalInsuranceClient

def main():
    if len(sys.argv) != 4:
        print("用法: python sdk_caller.py <interface_code> <input_data> <output_file>")
        return
    
    interface_code = sys.argv[1]
    input_data = json.loads(sys.argv[2])
    output_file = sys.argv[3]
    
    try:
        # 初始化SDK客户端
        client = MedicalInsuranceClient.from_config("C:/MedicalInsurance/config.json")
        
        # 调用医保接口
        result = client.call(interface_code, input_data)
        
        # 保存结果到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("调用成功")
        
    except Exception as e:
        error_result = {
            "infcode": "-1",
            "err_msg": f"SDK调用异常: {str(e)}"
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, ensure_ascii=False, indent=2)
        
        print(f"调用失败: {str(e)}")

if __name__ == "__main__":
    main()
```

## 5. 系统部署流程

### 5.1 医院端部署（一次性）
```bash
# 1. 安装Python环境和依赖
pip install medical-insurance-sdk pyodbc keyboard opencv-python pyzbar

# 2. 部署监听程序
python install_listener.py

# 3. 配置数据库连接
# 编辑 C:\MedicalInsurance\config.json

# 4. 创建数据库表和触发器
sqlcmd -S server -d database -i create_medical_trigger.sql
```

### 5.2 DBA操作（一次性）
```sql
-- 1. 创建触发表
CREATE TABLE medical_trigger (...);

-- 2. 创建触发器
CREATE TRIGGER tr_medical_trigger ON medical_trigger AFTER INSERT AS ...;

-- 3. 创建处理存储过程
CREATE PROCEDURE sp_process_medical_trigger ...;
CREATE PROCEDURE sp_call_medical_insurance ...;

-- 4. 启用xp_cmdshell（如果需要）
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;
```

## 6. 使用流程

### 6.1 日常使用
```
1. 患者来到收费窗口
2. 收费员刷患者医保卡 → USB读卡器输出卡号
3. 外挂程序监听到输入 → 插入触发记录
4. 数据库触发器自动执行 → 调用医保接口
5. 几秒后，收费员在HIS中看到患者医保信息
```

### 6.2 系统监控
```sql
-- 查看触发记录
SELECT * FROM medical_trigger ORDER BY trigger_time DESC;

-- 查看处理状态统计
SELECT status, COUNT(*) as count
FROM medical_trigger
WHERE trigger_time >= DATEADD(DAY, -1, GETDATE())
GROUP BY status;

-- 查看错误记录
SELECT * FROM medical_trigger 
WHERE status = 'ERROR' 
ORDER BY trigger_time DESC;
```

## 7. 方案优势

### 7.1 零代码入侵
- ✅ HIS系统完全不需要修改
- ✅ 只需要DBA创建表和触发器
- ✅ 外挂程序独立运行

### 7.2 实时响应
- ✅ 刷卡即触发，响应速度快
- ✅ 异步处理，不阻塞操作
- ✅ 自动化程度高

### 7.3 部署简单
- ✅ 一次部署，长期使用
- ✅ 配置简单，维护方便
- ✅ 兼容性好，适用各种HIS

### 7.4 扩展性强
- ✅ 支持多种输入设备
- ✅ 支持多种医保接口
- ✅ 可以添加更多触发条件

这个方案真的很巧妙！通过硬件输入触发的方式，既解决了零代码入侵的问题，又实现了实时处理。你觉得还有哪些细节需要完善？