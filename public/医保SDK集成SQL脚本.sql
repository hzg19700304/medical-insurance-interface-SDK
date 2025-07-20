-- 医保SDK集成SQL脚本
-- 这个脚本会被SDK自动执行，创建必要的表和存储过程

-- 1. 创建请求表
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='medical_insurance_requests' AND xtype='U')
BEGIN
    CREATE TABLE medical_insurance_requests (
        request_id INT IDENTITY(1,1) PRIMARY KEY,
        interface_code VARCHAR(10) NOT NULL,
        input_data NVARCHAR(MAX) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
        create_time DATETIME NOT NULL DEFAULT GETDATE(),
        update_time DATETIME,
        retry_count INT DEFAULT 0,
        INDEX idx_status_time (status, create_time)
    );
    PRINT '创建表: medical_insurance_requests';
END

-- 2. 创建响应表
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='medical_insurance_responses' AND xtype='U')
BEGIN
    CREATE TABLE medical_insurance_responses (
        response_id INT IDENTITY(1,1) PRIMARY KEY,
        request_id INT NOT NULL,
        response_data NVARCHAR(MAX) NOT NULL,
        infcode VARCHAR(10),
        err_msg NVARCHAR(500),
        create_time DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (request_id) REFERENCES medical_insurance_requests(request_id)
    );
    PRINT '创建表: medical_insurance_responses';
END

-- 3. 创建结果视图
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='v_medical_insurance_result' AND xtype='V')
BEGIN
    EXEC('
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
        resp.create_time as response_time,
        CASE 
            WHEN r.status = ''COMPLETED'' AND resp.infcode = ''0'' THEN ''SUCCESS''
            WHEN r.status = ''COMPLETED'' AND resp.infcode != ''0'' THEN ''BUSINESS_ERROR''
            WHEN r.status = ''ERROR'' THEN ''SYSTEM_ERROR''
            WHEN r.status = ''PROCESSING'' THEN ''PROCESSING''
            ELSE ''PENDING''
        END as result_status
    FROM medical_insurance_requests r
    LEFT JOIN medical_insurance_responses resp ON r.request_id = resp.request_id
    ');
    PRINT '创建视图: v_medical_insurance_result';
END

-- 4. 创建HIS调用的存储过程
IF EXISTS (SELECT * FROM sysobjects WHERE name='sp_medical_insurance_call' AND xtype='P')
    DROP PROCEDURE sp_medical_insurance_call;
GO

CREATE PROCEDURE sp_medical_insurance_call
    @interface_code VARCHAR(10),
    @input_data NVARCHAR(MAX),
    @async BIT = 1,  -- 1=异步, 0=同步
    @timeout INT = 30,  -- 同步调用超时时间(秒)
    @request_id INT OUTPUT,
    @result NVARCHAR(MAX) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- 插入请求记录
    INSERT INTO medical_insurance_requests (interface_code, input_data, status)
    VALUES (@interface_code, @input_data, 'PENDING');
    
    SET @request_id = SCOPE_IDENTITY();
    
    -- 触发SDK处理（通过写入信号表或文件）
    DECLARE @signal_file VARCHAR(200) = 'C:\MedicalInsurance\signals\request_' + CAST(@request_id AS VARCHAR(10)) + '.signal';
    DECLARE @cmd NVARCHAR(500) = 'echo ' + CAST(@request_id AS VARCHAR(10)) + ' > "' + @signal_file + '"';
    EXEC xp_cmdshell @cmd, no_output;
    
    IF @async = 0
    BEGIN
        -- 同步调用：等待结果
        DECLARE @wait_count INT = 0;
        DECLARE @max_wait INT = @timeout * 2; -- 每0.5秒检查一次
        
        WHILE @wait_count < @max_wait
        BEGIN
            SELECT @result = response_data
            FROM v_medical_insurance_result
            WHERE request_id = @request_id AND result_status IN ('SUCCESS', 'BUSINESS_ERROR', 'SYSTEM_ERROR');
            
            IF @result IS NOT NULL
                BREAK;
                
            WAITFOR DELAY '00:00:00.500'; -- 等待0.5秒
            SET @wait_count = @wait_count + 1;
        END
        
        IF @result IS NULL
            SET @result = '{"infcode": "-1", "err_msg": "调用超时"}';
    END
    ELSE
    BEGIN
        -- 异步调用：立即返回请求ID
        SET @result = '{"request_id": ' + CAST(@request_id AS VARCHAR(10)) + ', "status": "PENDING"}';
    END
END
GO

-- 5. 创建查询结果的存储过程
IF EXISTS (SELECT * FROM sysobjects WHERE name='sp_get_medical_insurance_result' AND xtype='P')
    DROP PROCEDURE sp_get_medical_insurance_result;
GO

CREATE PROCEDURE sp_get_medical_insurance_result
    @request_id INT,
    @result NVARCHAR(MAX) OUTPUT,
    @status VARCHAR(20) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        @result = response_data,
        @status = result_status
    FROM v_medical_insurance_result
    WHERE request_id = @request_id;
    
    IF @result IS NULL
    BEGIN
        SET @result = '{"infcode": "-1", "err_msg": "未找到请求记录"}';
        SET @status = 'NOT_FOUND';
    END
END
GO

-- 6. 创建批量查询的存储过程
IF EXISTS (SELECT * FROM sysobjects WHERE name='sp_get_medical_insurance_batch_result' AND xtype='P')
    DROP PROCEDURE sp_get_medical_insurance_batch_result;
GO

CREATE PROCEDURE sp_get_medical_insurance_batch_result
    @request_ids VARCHAR(1000)  -- 逗号分隔的请求ID列表
AS
BEGIN
    SET NOCOUNT ON;
    
    -- 创建临时表存储ID
    CREATE TABLE #temp_ids (request_id INT);
    
    -- 解析ID列表
    DECLARE @sql NVARCHAR(MAX) = 'INSERT INTO #temp_ids (request_id) VALUES (' + REPLACE(@request_ids, ',', '),(') + ')';
    EXEC sp_executesql @sql;
    
    -- 返回结果
    SELECT 
        r.request_id,
        r.interface_code,
        r.result_status,
        r.response_data,
        r.err_msg,
        r.request_time,
        r.response_time
    FROM v_medical_insurance_result r
    INNER JOIN #temp_ids t ON r.request_id = t.request_id
    ORDER BY r.request_id;
    
    DROP TABLE #temp_ids;
END
GO

-- 7. 创建监控统计视图
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='v_medical_insurance_stats' AND xtype='V')
BEGIN
    EXEC('
    CREATE VIEW v_medical_insurance_stats AS
    SELECT 
        interface_code,
        COUNT(*) as total_requests,
        SUM(CASE WHEN result_status = ''SUCCESS'' THEN 1 ELSE 0 END) as success_count,
        SUM(CASE WHEN result_status = ''BUSINESS_ERROR'' THEN 1 ELSE 0 END) as business_error_count,
        SUM(CASE WHEN result_status = ''SYSTEM_ERROR'' THEN 1 ELSE 0 END) as system_error_count,
        SUM(CASE WHEN result_status = ''PENDING'' THEN 1 ELSE 0 END) as pending_count,
        SUM(CASE WHEN result_status = ''PROCESSING'' THEN 1 ELSE 0 END) as processing_count,
        AVG(CASE 
            WHEN response_time IS NOT NULL AND request_time IS NOT NULL 
            THEN DATEDIFF(SECOND, request_time, response_time) 
            ELSE NULL 
        END) as avg_response_time_seconds,
        MIN(request_time) as first_request_time,
        MAX(request_time) as last_request_time
    FROM v_medical_insurance_result
    WHERE request_time >= DATEADD(DAY, -7, GETDATE())  -- 最近7天
    GROUP BY interface_code
    ');
    PRINT '创建视图: v_medical_insurance_stats';
END

-- 8. 创建清理历史数据的存储过程
IF EXISTS (SELECT * FROM sysobjects WHERE name='sp_cleanup_medical_insurance_history' AND xtype='P')
    DROP PROCEDURE sp_cleanup_medical_insurance_history;
GO

CREATE PROCEDURE sp_cleanup_medical_insurance_history
    @days_to_keep INT = 30  -- 保留天数
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @cutoff_date DATETIME = DATEADD(DAY, -@days_to_keep, GETDATE());
    DECLARE @deleted_count INT;
    
    -- 删除响应记录
    DELETE FROM medical_insurance_responses
    WHERE request_id IN (
        SELECT request_id 
        FROM medical_insurance_requests 
        WHERE create_time < @cutoff_date
    );
    
    -- 删除请求记录
    DELETE FROM medical_insurance_requests
    WHERE create_time < @cutoff_date;
    
    SET @deleted_count = @@ROWCOUNT;
    
    PRINT '清理完成，删除了 ' + CAST(@deleted_count AS VARCHAR(10)) + ' 条历史记录';
END
GO

PRINT '医保SDK数据库初始化完成！';
PRINT '可用的存储过程：';
PRINT '  - sp_medical_insurance_call: 调用医保接口';
PRINT '  - sp_get_medical_insurance_result: 获取单个结果';
PRINT '  - sp_get_medical_insurance_batch_result: 批量获取结果';
PRINT '  - sp_cleanup_medical_insurance_history: 清理历史数据';
PRINT '可用的视图：';
PRINT '  - v_medical_insurance_result: 查询结果';
PRINT '  - v_medical_insurance_stats: 统计信息';