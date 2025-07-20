"""
Celery异步任务定义
"""

import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_task
from celery.exceptions import Retry

from .celery_app import celery_app
from ..sdk import MedicalInsuranceSDK
from ..config.manager import ConfigManager
from ..core.database import DatabaseManager
from ..exceptions import MedicalInsuranceException, NetworkException


@celery_app.task(bind=True, name='async_call_interface')
def async_call_interface(self, api_code: str, input_data: dict, org_code: str, 
                        task_options: Optional[dict] = None) -> dict:
    """
    异步调用医保接口任务
    
    Args:
        api_code: 接口编码
        input_data: 输入数据
        org_code: 机构编码
        task_options: 任务选项
    
    Returns:
        dict: 调用结果
    """
    task_id = self.request.id
    task_options = task_options or {}
    
    try:
        # 更新任务状态为处理中
        _update_task_status(task_id, 'PROCESSING', {
            'api_code': api_code,
            'org_code': org_code,
            'start_time': datetime.now().isoformat()
        })
        
        # 创建SDK实例
        from ..core.database import DatabaseConfig
        from ..config.models import SDKConfig
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        sdk_config = SDKConfig(database_config=db_config)
        sdk = MedicalInsuranceSDK(sdk_config)
        
        # 调用接口
        response = sdk.call(api_code, {'data': input_data}, org_code=org_code)
        
        # 构建成功结果
        result = {
            'success': True,
            'task_id': task_id,
            'api_code': api_code,
            'org_code': org_code,
            'response': response.to_dict() if hasattr(response, 'to_dict') else response,
            'completed_at': datetime.now().isoformat()
        }
        
        # 更新任务状态为成功
        _update_task_status(task_id, 'SUCCESS', result)
        
        return result
        
    except NetworkException as e:
        # 网络异常，可以重试
        retry_count = self.request.retries
        max_retries = task_options.get('max_retries', 3)
        
        if retry_count < max_retries:
            # 计算重试延迟（指数退避）
            countdown = min(60 * (2 ** retry_count), 300)  # 最大5分钟
            
            error_info = {
                'error_type': 'NetworkException',
                'error_message': str(e),
                'retry_count': retry_count + 1,
                'next_retry_at': (datetime.now() + timedelta(seconds=countdown)).isoformat()
            }
            
            _update_task_status(task_id, 'RETRY', error_info)
            
            raise self.retry(countdown=countdown, exc=e)
        else:
            # 超过最大重试次数
            error_result = {
                'success': False,
                'task_id': task_id,
                'api_code': api_code,
                'org_code': org_code,
                'error_type': 'NetworkException',
                'error_message': str(e),
                'retry_count': retry_count,
                'failed_at': datetime.now().isoformat()
            }
            
            _update_task_status(task_id, 'FAILURE', error_result)
            return error_result
            
    except Exception as e:
        # 其他异常，不重试
        error_result = {
            'success': False,
            'task_id': task_id,
            'api_code': api_code,
            'org_code': org_code,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'failed_at': datetime.now().isoformat()
        }
        
        _update_task_status(task_id, 'FAILURE', error_result)
        return error_result


@celery_app.task(bind=True, name='async_batch_call_interface')
def async_batch_call_interface(self, batch_requests: List[dict], 
                              task_options: Optional[dict] = None) -> dict:
    """
    批量异步调用医保接口任务
    
    Args:
        batch_requests: 批量请求列表，每个元素包含api_code, input_data, org_code
        task_options: 任务选项
    
    Returns:
        dict: 批量调用结果
    """
    task_id = self.request.id
    task_options = task_options or {}
    
    try:
        # 更新任务状态
        _update_task_status(task_id, 'PROCESSING', {
            'batch_size': len(batch_requests),
            'start_time': datetime.now().isoformat()
        })
        
        # 创建SDK实例
        from ..core.database import DatabaseConfig
        from ..config.models import SDKConfig
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        sdk_config = SDKConfig(database_config=db_config)
        sdk = MedicalInsuranceSDK(sdk_config)
        
        results = []
        success_count = 0
        failure_count = 0
        
        # 逐个处理请求
        for i, request_data in enumerate(batch_requests):
            try:
                api_code = request_data['api_code']
                input_data = request_data['input_data']
                org_code = request_data['org_code']
                
                # 更新进度
                progress = {
                    'current': i + 1,
                    'total': len(batch_requests),
                    'percentage': round((i + 1) / len(batch_requests) * 100, 2)
                }
                
                current_task.update_state(
                    state='PROGRESS',
                    meta=progress
                )
                
                # 调用接口
                response = sdk.call(api_code, {'data': input_data}, org_code=org_code)
                
                result_item = {
                    'index': i,
                    'success': True,
                    'api_code': api_code,
                    'org_code': org_code,
                    'response': response.to_dict() if hasattr(response, 'to_dict') else response
                }
                
                results.append(result_item)
                success_count += 1
                
            except Exception as e:
                result_item = {
                    'index': i,
                    'success': False,
                    'api_code': request_data.get('api_code', ''),
                    'org_code': request_data.get('org_code', ''),
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
                
                results.append(result_item)
                failure_count += 1
        
        # 构建最终结果
        final_result = {
            'success': True,
            'task_id': task_id,
            'batch_size': len(batch_requests),
            'success_count': success_count,
            'failure_count': failure_count,
            'results': results,
            'completed_at': datetime.now().isoformat()
        }
        
        _update_task_status(task_id, 'SUCCESS', final_result)
        return final_result
        
    except Exception as e:
        error_result = {
            'success': False,
            'task_id': task_id,
            'batch_size': len(batch_requests),
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'failed_at': datetime.now().isoformat()
        }
        
        _update_task_status(task_id, 'FAILURE', error_result)
        return error_result


@celery_app.task(name='cleanup_expired_tasks')
def cleanup_expired_tasks():
    """
    清理过期的任务记录
    """
    try:
        from ..core.database import DatabaseConfig
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        db_manager = DatabaseManager(db_config)
        
        # 删除24小时前的任务记录
        expire_time = datetime.now() - timedelta(hours=24)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 清理任务状态表
            cursor.execute("""
                DELETE FROM async_task_status 
                WHERE created_at < %s
            """, (expire_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cleanup_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error_message': str(e),
            'cleanup_time': datetime.now().isoformat()
        }


def _update_task_status(task_id: str, status: str, data: dict):
    """
    更新任务状态到数据库
    
    Args:
        task_id: 任务ID
        status: 任务状态
        data: 任务数据
    """
    try:
        from ..core.database import DatabaseConfig
        db_config = DatabaseConfig.from_env()
        config_manager = ConfigManager(db_config)
        db_manager = DatabaseManager(db_config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入或更新任务状态
            cursor.execute("""
                INSERT INTO async_task_status 
                (task_id, status, data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                data = VALUES(data),
                updated_at = VALUES(updated_at)
            """, (
                task_id,
                status,
                json.dumps(data, ensure_ascii=False),
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            
    except Exception as e:
        # 记录错误但不影响主任务
        print(f"Failed to update task status: {e}")