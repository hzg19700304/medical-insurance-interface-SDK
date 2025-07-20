"""
异步任务管理器
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery.result import AsyncResult

from .celery_app import celery_app
from ..config.manager import ConfigManager
from ..core.database import DatabaseManager


class TaskManager:
    """异步任务管理器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        if config_manager is None:
            from ..core.database import DatabaseConfig
            db_config = DatabaseConfig.from_env()
            config_manager = ConfigManager(db_config)
        self.config_manager = config_manager
        self.db_manager = DatabaseManager(self.config_manager.db_manager.config)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务状态信息
        """
        try:
            # 从Celery获取任务状态
            async_result = AsyncResult(task_id, app=celery_app)
            
            # 从数据库获取详细信息
            db_status = self._get_task_status_from_db(task_id)
            
            # 合并状态信息
            status_info = {
                'task_id': task_id,
                'status': async_result.status,
                'result': async_result.result,
                'traceback': async_result.traceback,
                'date_done': async_result.date_done.isoformat() if async_result.date_done else None,
                'successful': async_result.successful(),
                'failed': async_result.failed(),
                'ready': async_result.ready(),
            }
            
            # 添加数据库中的详细信息
            if db_status:
                status_info.update({
                    'created_at': db_status['created_at'].isoformat() if db_status['created_at'] else None,
                    'updated_at': db_status['updated_at'].isoformat() if db_status['updated_at'] else None,
                    'detailed_data': db_status['data']
                })
            
            return status_info
            
        except Exception as e:
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error_message': str(e),
                'error_type': type(e).__name__
            }
    
    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        获取任务结果（阻塞等待）
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            
        Returns:
            任务结果
        """
        async_result = AsyncResult(task_id, app=celery_app)
        return async_result.get(timeout=timeout)
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 取消结果
        """
        try:
            async_result = AsyncResult(task_id, app=celery_app)
            async_result.revoke(terminate=True)
            
            # 更新数据库状态
            self._update_task_status_in_db(task_id, 'REVOKED', {
                'cancelled_at': datetime.now().isoformat(),
                'reason': 'User cancelled'
            })
            
            return {
                'success': True,
                'task_id': task_id,
                'message': 'Task cancelled successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'task_id': task_id,
                'error_message': str(e)
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
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                where_clause = ""
                params = []
                
                if status:
                    where_clause = "WHERE status = %s"
                    params.append(status)
                
                # 查询任务
                cursor.execute(f"""
                    SELECT task_id, status, data, created_at, updated_at
                    FROM async_task_status
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, params + [limit, offset])
                
                tasks = cursor.fetchall()
                
                # 处理结果
                result = []
                for task in tasks:
                    task_info = {
                        'task_id': task['task_id'],
                        'status': task['status'],
                        'created_at': task['created_at'].isoformat() if task['created_at'] else None,
                        'updated_at': task['updated_at'].isoformat() if task['updated_at'] else None,
                    }
                    
                    # 解析数据
                    if task['data']:
                        try:
                            task_info['data'] = json.loads(task['data'])
                        except json.JSONDecodeError:
                            task_info['data'] = task['data']
                    
                    result.append(task_info)
                
                return result
                
        except Exception as e:
            return []
    
    def get_task_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Args:
            hours: 统计时间范围（小时）
            
        Returns:
            dict: 统计信息
        """
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 统计各状态任务数量
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM async_task_status
                    WHERE created_at >= %s
                    GROUP BY status
                """, (start_time,))
                
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # 统计总数
                cursor.execute("""
                    SELECT COUNT(*) as total_count
                    FROM async_task_status
                    WHERE created_at >= %s
                """, (start_time,))
                
                total_count = cursor.fetchone()['total_count']
                
                # 统计成功率
                success_count = status_counts.get('SUCCESS', 0)
                failure_count = status_counts.get('FAILURE', 0)
                success_rate = (success_count / (success_count + failure_count) * 100) if (success_count + failure_count) > 0 else 0
                
                return {
                    'time_range_hours': hours,
                    'total_tasks': total_count,
                    'status_counts': status_counts,
                    'success_rate': round(success_rate, 2),
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_task_status_from_db(self, task_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取任务状态"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT task_id, status, data, created_at, updated_at
                    FROM async_task_status
                    WHERE task_id = %s
                """, (task_id,))
                
                row = cursor.fetchone()
                
                result = cursor.fetchone()
                
                if result and result['data']:
                    try:
                        result['data'] = json.loads(result['data'])
                    except json.JSONDecodeError:
                        pass
                
                return result
                
        except Exception:
            return None
    
    def _update_task_status_in_db(self, task_id: str, status: str, data: Dict[str, Any]):
        """更新数据库中的任务状态"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
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
                
        except Exception:
            pass  # 静默失败，不影响主流程