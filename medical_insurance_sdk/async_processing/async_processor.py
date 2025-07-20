"""
异步处理器
提供异步任务的状态管理、超时和错误处理机制
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from celery.result import AsyncResult

from .celery_app import celery_app
from .tasks import async_call_interface, async_batch_call_interface
from .task_manager import TaskManager
from ..config.manager import ConfigManager
from ..exceptions import MedicalInsuranceException


class AsyncProcessor:
    """异步处理器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        if config_manager is None:
            from ..core.database import DatabaseConfig
            db_config = DatabaseConfig.from_env()
            config_manager = ConfigManager(db_config)
        self.config_manager = config_manager
        self.task_manager = TaskManager(self.config_manager)
    
    def submit_interface_call(self, api_code: str, input_data: dict, org_code: str,
                            task_options: Optional[dict] = None) -> str:
        """
        提交异步接口调用任务
        
        Args:
            api_code: 接口编码
            input_data: 输入数据
            org_code: 机构编码
            task_options: 任务选项
                - max_retries: 最大重试次数
                - countdown: 延迟执行时间（秒）
                - expires: 任务过期时间
                - priority: 任务优先级
        
        Returns:
            str: 任务ID
        """
        task_options = task_options or {}
        
        # 设置任务参数
        task_kwargs = {
            'api_code': api_code,
            'input_data': input_data,
            'org_code': org_code,
            'task_options': task_options
        }
        
        # 设置Celery任务选项
        celery_options = {}
        
        if 'countdown' in task_options:
            celery_options['countdown'] = task_options['countdown']
        
        if 'expires' in task_options:
            if isinstance(task_options['expires'], int):
                # 如果是整数，表示秒数
                celery_options['expires'] = datetime.now() + timedelta(seconds=task_options['expires'])
            else:
                celery_options['expires'] = task_options['expires']
        
        if 'priority' in task_options:
            celery_options['priority'] = task_options['priority']
        
        # 提交任务
        async_result = async_call_interface.apply_async(
            kwargs=task_kwargs,
            **celery_options
        )
        
        return async_result.id
    
    def submit_batch_interface_call(self, batch_requests: List[dict],
                                  task_options: Optional[dict] = None) -> str:
        """
        提交批量异步接口调用任务
        
        Args:
            batch_requests: 批量请求列表
                每个元素包含: api_code, input_data, org_code
            task_options: 任务选项
        
        Returns:
            str: 任务ID
        """
        task_options = task_options or {}
        
        # 验证批量请求格式
        for i, request in enumerate(batch_requests):
            if not all(key in request for key in ['api_code', 'input_data', 'org_code']):
                raise MedicalInsuranceException(
                    f"批量请求第{i+1}项缺少必要字段: api_code, input_data, org_code"
                )
        
        # 设置任务参数
        task_kwargs = {
            'batch_requests': batch_requests,
            'task_options': task_options
        }
        
        # 设置Celery任务选项
        celery_options = {}
        
        if 'countdown' in task_options:
            celery_options['countdown'] = task_options['countdown']
        
        if 'expires' in task_options:
            if isinstance(task_options['expires'], int):
                celery_options['expires'] = datetime.now() + timedelta(seconds=task_options['expires'])
            else:
                celery_options['expires'] = task_options['expires']
        
        # 提交任务
        async_result = async_batch_call_interface.apply_async(
            kwargs=task_kwargs,
            **celery_options
        )
        
        return async_result.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 任务状态信息
        """
        return self.task_manager.get_task_status(task_id)
    
    def wait_for_result(self, task_id: str, timeout: Optional[float] = None,
                       check_interval: float = 1.0) -> Dict[str, Any]:
        """
        等待任务完成并返回结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
        
        Returns:
            dict: 任务结果
        """
        try:
            async_result = AsyncResult(task_id, app=celery_app)
            
            # 等待结果
            result = async_result.get(timeout=timeout)
            
            return {
                'success': True,
                'task_id': task_id,
                'result': result,
                'completed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'task_id': task_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'failed_at': datetime.now().isoformat()
            }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 取消结果
        """
        return self.task_manager.cancel_task(task_id)
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务进度（主要用于批量任务）
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 进度信息
        """
        try:
            async_result = AsyncResult(task_id, app=celery_app)
            
            if async_result.state == 'PROGRESS':
                progress_info = async_result.info
                return {
                    'task_id': task_id,
                    'status': 'PROGRESS',
                    'progress': progress_info,
                    'checked_at': datetime.now().isoformat()
                }
            else:
                return {
                    'task_id': task_id,
                    'status': async_result.state,
                    'info': async_result.info,
                    'checked_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error_message': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    def list_tasks(self, status: Optional[str] = None, 
                   limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 过滤状态
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            list: 任务列表
        """
        return self.task_manager.list_tasks(status, limit, offset)
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Args:
            hours: 统计时间范围（小时）
        
        Returns:
            dict: 统计信息
        """
        return self.task_manager.get_task_statistics(hours)
    
    def cleanup_expired_tasks(self, hours: int = 24) -> Dict[str, Any]:
        """
        清理过期任务
        
        Args:
            hours: 清理多少小时前的任务
        
        Returns:
            dict: 清理结果
        """
        try:
            from .tasks import cleanup_expired_tasks
            
            # 提交清理任务
            async_result = cleanup_expired_tasks.apply_async()
            
            # 等待清理完成
            result = async_result.get(timeout=60)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'cleanup_time': datetime.now().isoformat()
            }
    
    def handle_task_timeout(self, task_id: str) -> Dict[str, Any]:
        """
        处理任务超时
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 处理结果
        """
        try:
            # 取消超时任务
            cancel_result = self.cancel_task(task_id)
            
            if cancel_result['success']:
                # 记录超时信息
                timeout_info = {
                    'task_id': task_id,
                    'timeout_handled_at': datetime.now().isoformat(),
                    'reason': 'Task timeout',
                    'action': 'cancelled'
                }
                
                # 更新任务状态
                self.task_manager._update_task_status_in_db(
                    task_id, 'TIMEOUT', timeout_info
                )
                
                return {
                    'success': True,
                    'task_id': task_id,
                    'message': 'Task timeout handled successfully',
                    'details': timeout_info
                }
            else:
                return cancel_result
                
        except Exception as e:
            return {
                'success': False,
                'task_id': task_id,
                'error_message': str(e),
                'error_type': type(e).__name__
            }
    
    def handle_task_error(self, task_id: str, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务错误
        
        Args:
            task_id: 任务ID
            error_info: 错误信息
        
        Returns:
            dict: 处理结果
        """
        try:
            # 获取任务状态
            task_status = self.get_task_status(task_id)
            
            # 构建错误处理信息
            error_handling_info = {
                'task_id': task_id,
                'original_error': error_info,
                'task_status': task_status,
                'error_handled_at': datetime.now().isoformat()
            }
            
            # 根据错误类型决定处理策略
            error_type = error_info.get('error_type', '')
            
            if error_type in ['NetworkException', 'TimeoutError']:
                # 网络相关错误，可能需要重试
                error_handling_info['suggested_action'] = 'retry'
                error_handling_info['retry_recommended'] = True
            elif error_type in ['ValidationException', 'ConfigurationException']:
                # 配置或验证错误，需要人工干预
                error_handling_info['suggested_action'] = 'manual_intervention'
                error_handling_info['retry_recommended'] = False
            else:
                # 其他错误
                error_handling_info['suggested_action'] = 'investigate'
                error_handling_info['retry_recommended'] = False
            
            # 更新任务状态
            self.task_manager._update_task_status_in_db(
                task_id, 'ERROR_HANDLED', error_handling_info
            )
            
            return {
                'success': True,
                'task_id': task_id,
                'error_handling_info': error_handling_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'task_id': task_id,
                'error_message': str(e),
                'error_type': type(e).__name__
            }