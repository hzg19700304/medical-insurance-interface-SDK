-- 异步任务状态表
CREATE TABLE IF NOT EXISTS async_task_status (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL UNIQUE COMMENT '任务ID',
    status VARCHAR(50) NOT NULL COMMENT '任务状态：PENDING/PROCESSING/SUCCESS/FAILURE/RETRY/REVOKED',
    data JSON COMMENT '任务数据和结果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_task_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异步任务状态表';