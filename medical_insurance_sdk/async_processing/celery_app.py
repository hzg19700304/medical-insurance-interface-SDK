"""
Celery应用配置
"""

import os
from celery import Celery
from kombu import Queue
from datetime import timedelta

# 创建Celery应用实例
celery_app = Celery('medical_insurance_sdk')

# 配置Celery
def configure_celery():
    """配置Celery应用"""
    
    # Redis配置
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    redis_db = os.getenv('REDIS_DB', '0')
    redis_password = os.getenv('REDIS_PASSWORD', '')
    
    # 构建Redis URL
    if redis_password:
        redis_url = f'redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}'
    else:
        redis_url = f'redis://{redis_host}:{redis_port}/{redis_db}'
    
    # Celery配置
    celery_app.conf.update(
        # Broker配置
        broker_url=redis_url,
        result_backend=redis_url,
        
        # 任务序列化
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,
        
        # 任务路由
        task_routes={
            'medical_insurance_sdk.async_processing.tasks.async_call_interface': {
                'queue': 'medical_interface'
            },
            'medical_insurance_sdk.async_processing.tasks.async_batch_call_interface': {
                'queue': 'medical_batch'
            },
            'medical_insurance_sdk.async_processing.tasks.cleanup_expired_tasks': {
                'queue': 'maintenance'
            }
        },
        
        # 队列配置
        task_default_queue='default',
        task_queues=(
            Queue('default'),
            Queue('medical_interface', routing_key='medical_interface'),
            Queue('medical_batch', routing_key='medical_batch'),
            Queue('maintenance', routing_key='maintenance'),
        ),
        
        # 任务执行配置
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_reject_on_worker_lost=True,
        
        # 结果过期时间
        result_expires=timedelta(hours=24),
        
        # 任务超时配置
        task_soft_time_limit=300,  # 5分钟软超时
        task_time_limit=600,       # 10分钟硬超时
        
        # 重试配置
        task_default_retry_delay=60,
        task_max_retries=3,
        
        # 监控配置
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # 定时任务配置
        beat_schedule={
            'cleanup-expired-tasks': {
                'task': 'medical_insurance_sdk.async_processing.tasks.cleanup_expired_tasks',
                'schedule': timedelta(hours=1),  # 每小时执行一次清理
            },
        },
    )

# 初始化配置
configure_celery()

# 自动发现任务
celery_app.autodiscover_tasks(['medical_insurance_sdk.async_processing'])