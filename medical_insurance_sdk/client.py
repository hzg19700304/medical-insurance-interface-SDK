"""医保SDK客户端"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from concurrent.futures import ThreadPoolExecutor, Future

from .sdk import MedicalInsuranceSDK
from .core.universal_processor import UniversalInterfaceProcessor
from .core.database import DatabaseConfig
from .config.models import SDKConfig
from .async_processing import AsyncProcessor
from .exceptions import (
    MedicalInsuranceException,
    ValidationException,
    ConfigurationException
)


class MedicalInsuranceClient:
    """医保接口客户端 - 主要对外接口
    
    提供同步和异步调用方法，集成通用接口处理器，
    为用户提供简单易用的医保接口调用能力。
    """

    def __init__(self, config: Optional[SDKConfig] = None):
        """初始化客户端

        Args:
            config: SDK配置，如果为None则使用默认配置
        """
        if config is None:
            # 使用默认配置
            db_config = DatabaseConfig.from_env()
            config = SDKConfig(database_config=db_config)

        self.sdk = MedicalInsuranceSDK(config)
        self.universal_processor = UniversalInterfaceProcessor(self.sdk)
        # 复用SDK的ConfigManager，避免创建新的连接池
        self.async_processor = AsyncProcessor(self.sdk.config_manager)
        self.logger = logging.getLogger(__name__)
        
        # 异步执行器（用于简单异步任务）
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="medical-sdk-async")
        self._async_tasks = {}  # 存储异步任务
        
        self.logger.info("医保接口客户端初始化完成")

    def call(self, api_code: str, data: dict, org_code: str, **kwargs) -> dict:
        """同步调用医保接口

        Args:
            api_code: 接口编码，如'1101'
            data: 接口输入数据
            org_code: 机构编码
            **kwargs: 其他参数

        Returns:
            dict: 接口响应数据

        Raises:
            MedicalInsuranceException: 调用失败时抛出异常
        """
        try:
            self.logger.info(f"同步调用医保接口: {api_code}, 机构: {org_code}")
            
            # 直接调用SDK核心，构造SDK期望的数据格式
            sdk_data = {"data": data}
            result = self.sdk.call(
                api_code=api_code,
                data=sdk_data,
                org_code=org_code,
                **kwargs
            )
            
            # 将SDK响应转换为字典格式
            if hasattr(result, 'to_dict'):
                result = result.to_dict()
            
            self.logger.info(f"同步调用完成: {api_code}")
            return result
            
        except Exception as e:
            self.logger.error(f"同步调用失败: {api_code}, 错误: {e}")
            raise

    def call_async(self, api_code: str, data: dict, org_code: str, 
                   use_celery: bool = True, **kwargs) -> str:
        """异步调用医保接口

        Args:
            api_code: 接口编码
            data: 接口输入数据
            org_code: 机构编码
            use_celery: 是否使用Celery（默认True），False则使用线程池
            **kwargs: 其他参数

        Returns:
            str: 任务ID，可用于查询任务状态
        """
        if use_celery:
            # 使用Celery异步处理
            try:
                self.logger.info(f"提交Celery异步任务: {api_code}, 机构: {org_code}")
                
                task_id = self.async_processor.submit_interface_call(
                    api_code=api_code,
                    input_data=data,
                    org_code=org_code,
                    task_options=kwargs.get('task_options', {})
                )
                
                self.logger.info(f"Celery任务提交成功，任务ID: {task_id}")
                return task_id
                
            except Exception as e:
                self.logger.error(f"提交Celery任务失败: {api_code}, 错误: {e}")
                raise MedicalInsuranceException(f"提交Celery任务失败: {e}")
        else:
            # 使用线程池异步处理（原有逻辑）
            import uuid
            task_id = str(uuid.uuid4())
            
            try:
                self.logger.info(f"提交线程池异步任务: {api_code}, 机构: {org_code}, 任务ID: {task_id}")
                
                # 提交异步任务
                future = self._executor.submit(
                    self._async_call_wrapper,
                    api_code, data, org_code, task_id, **kwargs
                )
                
                # 存储任务信息
                self._async_tasks[task_id] = {
                    'future': future,
                    'api_code': api_code,
                    'org_code': org_code,
                    'status': 'running',
                    'result': None,
                    'error': None,
                    'created_at': self._get_current_time()
                }
                
                return task_id
                
            except Exception as e:
                self.logger.error(f"提交线程池任务失败: {api_code}, 错误: {e}")
                raise MedicalInsuranceException(f"提交线程池任务失败: {e}")

    def get_task_result(self, task_id: str, use_celery: bool = None) -> dict:
        """获取异步任务结果

        Args:
            task_id: 任务ID
            use_celery: 是否使用Celery查询，None则自动判断

        Returns:
            dict: 任务结果，包含状态和数据
        """
        # 自动判断任务类型
        if use_celery is None:
            use_celery = task_id not in self._async_tasks
        
        if use_celery:
            # 从Celery获取任务状态
            try:
                return self.async_processor.get_task_status(task_id)
            except Exception as e:
                self.logger.error(f"获取Celery任务状态失败: {task_id}, 错误: {e}")
                return {
                    'task_id': task_id,
                    'status': 'ERROR',
                    'error': str(e)
                }
        else:
            # 从线程池任务获取状态
            if task_id not in self._async_tasks:
                raise MedicalInsuranceException(f"任务不存在: {task_id}")
            
            task_info = self._async_tasks[task_id]
            future = task_info['future']
            
            # 检查任务状态
            if future.done():
                if task_info['status'] == 'running':
                    try:
                        result = future.result()
                        task_info['status'] = 'completed'
                        task_info['result'] = result
                    except Exception as e:
                        task_info['status'] = 'failed'
                        task_info['error'] = str(e)
            
            return {
                'task_id': task_id,
                'status': task_info['status'],
                'api_code': task_info['api_code'],
                'org_code': task_info['org_code'],
                'result': task_info.get('result'),
                'error': task_info.get('error'),
                'created_at': task_info['created_at']
            }

    def call_batch(self, requests: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """批量调用医保接口

        Args:
            requests: 批量请求列表，每个请求包含api_code、data、org_code
            **kwargs: 其他参数

        Returns:
            List[Dict]: 批量调用结果列表
        """
        try:
            self.logger.info(f"批量调用医保接口，请求数量: {len(requests)}")
            
            # 使用通用接口处理器的批量调用功能
            results = self.universal_processor.call_batch_interfaces(requests, **kwargs)
            
            self.logger.info(f"批量调用完成，成功: {sum(1 for r in results if r.get('success'))}, "
                           f"失败: {sum(1 for r in results if not r.get('success'))}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量调用失败: {e}")
            raise MedicalInsuranceException(f"批量调用失败: {e}")

    def call_batch_async(self, requests: List[Dict[str, Any]], 
                        task_options: Optional[dict] = None) -> str:
        """异步批量调用医保接口

        Args:
            requests: 批量请求列表，每个请求包含api_code、input_data、org_code
            task_options: 任务选项

        Returns:
            str: 任务ID
        """
        try:
            self.logger.info(f"提交异步批量调用任务，请求数量: {len(requests)}")
            
            # 转换请求格式以适配Celery任务
            batch_requests = []
            for req in requests:
                batch_requests.append({
                    'api_code': req['api_code'],
                    'input_data': req['data'],
                    'org_code': req['org_code']
                })
            
            task_id = self.async_processor.submit_batch_interface_call(
                batch_requests=batch_requests,
                task_options=task_options or {}
            )
            
            self.logger.info(f"异步批量任务提交成功，任务ID: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"提交异步批量任务失败: {e}")
            raise MedicalInsuranceException(f"提交异步批量任务失败: {e}")

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """等待异步任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            dict: 任务结果
        """
        try:
            self.logger.info(f"等待任务完成: {task_id}")
            
            result = self.async_processor.wait_for_result(task_id, timeout)
            
            self.logger.info(f"任务完成: {task_id}, 成功: {result.get('success', False)}")
            return result
            
        except Exception as e:
            self.logger.error(f"等待任务失败: {task_id}, 错误: {e}")
            raise MedicalInsuranceException(f"等待任务失败: {e}")

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消异步任务

        Args:
            task_id: 任务ID

        Returns:
            dict: 取消结果
        """
        try:
            self.logger.info(f"取消任务: {task_id}")
            
            result = self.async_processor.cancel_task(task_id)
            
            self.logger.info(f"任务取消结果: {task_id}, 成功: {result.get('success', False)}")
            return result
            
        except Exception as e:
            self.logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return {
                'success': False,
                'task_id': task_id,
                'error_message': str(e)
            }

    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """获取任务进度（主要用于批量任务）

        Args:
            task_id: 任务ID

        Returns:
            dict: 进度信息
        """
        try:
            return self.async_processor.get_task_progress(task_id)
        except Exception as e:
            self.logger.error(f"获取任务进度失败: {task_id}, 错误: {e}")
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error_message': str(e)
            }

    def list_async_tasks(self, status: Optional[str] = None, 
                        limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出异步任务

        Args:
            status: 过滤状态
            limit: 限制数量
            offset: 偏移量

        Returns:
            list: 任务列表
        """
        try:
            return self.async_processor.list_tasks(status, limit, offset)
        except Exception as e:
            self.logger.error(f"列出任务失败: {e}")
            return []

    def get_async_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取异步任务统计信息

        Args:
            hours: 统计时间范围（小时）

        Returns:
            dict: 统计信息
        """
        try:
            return self.async_processor.get_statistics(hours)
        except Exception as e:
            self.logger.error(f"获取异步统计失败: {e}")
            return {
                'error': str(e),
                'hours': hours
            }

    def validate_data(self, api_code: str, data: dict, org_code: str) -> dict:
        """验证接口数据（不执行调用）

        Args:
            api_code: 接口编码
            data: 待验证数据
            org_code: 机构编码

        Returns:
            dict: 验证结果
        """
        try:
            self.logger.debug(f"验证接口数据: {api_code}, 机构: {org_code}")
            
            result = self.universal_processor.validate_interface_data(api_code, data, org_code)
            
            self.logger.debug(f"数据验证完成: {api_code}, 有效: {result['is_valid']}")
            return result
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {api_code}, 错误: {e}")
            raise ValidationException(f"数据验证失败: {e}")

    def get_interface_info(self, api_code: str, org_code: str = None) -> dict:
        """获取接口信息

        Args:
            api_code: 接口编码
            org_code: 机构编码（可选）

        Returns:
            dict: 接口信息
        """
        try:
            return self.universal_processor.get_interface_info(api_code, org_code)
        except Exception as e:
            self.logger.error(f"获取接口信息失败: {api_code}, 错误: {e}")
            raise ConfigurationException(f"获取接口信息失败: {e}")

    def get_supported_interfaces(self, org_code: str = None) -> List[dict]:
        """获取支持的接口列表

        Args:
            org_code: 机构编码（可选）

        Returns:
            List[dict]: 接口列表
        """
        try:
            return self.universal_processor.get_supported_interfaces(org_code)
        except Exception as e:
            self.logger.error(f"获取接口列表失败: {e}")
            return []

    def test_connection(self, org_code: str) -> dict:
        """测试与指定机构的连接

        Args:
            org_code: 机构编码

        Returns:
            dict: 连接测试结果
        """
        try:
            self.logger.info(f"测试机构连接: {org_code}")
            
            # 获取机构配置
            org_config = self.sdk.get_organization_config(org_code)
            
            # 尝试调用一个简单的查询接口进行连接测试
            # 这里使用一个不会产生实际业务影响的测试调用
            test_result = {
                'org_code': org_code,
                'org_name': org_config.get('org_name', ''),
                'base_url': org_config.get('base_url', ''),
                'connected': False,
                'error': None,
                'response_time': 0
            }
            
            import time
            start_time = time.time()
            
            try:
                # 使用人员信息查询接口测试连接（使用无效参数，只测试连通性）
                self.call("1101", {"psn_no": "connection_test"}, org_code)
                test_result['connected'] = True
            except Exception as e:
                # 即使调用失败，如果是业务错误（非网络错误），也认为连接正常
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ['网络', 'timeout', 'connection', '连接']):
                    test_result['connected'] = False
                    test_result['error'] = str(e)
                else:
                    # 业务错误，说明连接正常
                    test_result['connected'] = True
            
            test_result['response_time'] = round((time.time() - start_time) * 1000, 2)
            
            self.logger.info(f"连接测试完成: {org_code}, 连接状态: {test_result['connected']}")
            return test_result
            
        except Exception as e:
            self.logger.error(f"连接测试失败: {org_code}, 错误: {e}")
            return {
                'org_code': org_code,
                'connected': False,
                'error': str(e),
                'response_time': 0
            }

    def get_processing_stats(self) -> dict:
        """获取处理统计信息

        Returns:
            dict: 统计信息
        """
        return self.universal_processor.get_processing_stats()

    def reset_stats(self):
        """重置统计信息"""
        self.universal_processor.reset_processing_stats()
        self.logger.info("统计信息已重置")

    def cleanup_async_tasks(self, max_age_hours: int = 24):
        """清理过期的异步任务

        Args:
            max_age_hours: 任务最大保留时间（小时）
        """
        import time
        current_time = time.time()
        expired_tasks = []
        
        for task_id, task_info in self._async_tasks.items():
            task_age = current_time - task_info['created_at']
            if task_age > max_age_hours * 3600:  # 转换为秒
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del self._async_tasks[task_id]
        
        if expired_tasks:
            self.logger.info(f"清理过期异步任务: {len(expired_tasks)}个")

    def close(self):
        """关闭客户端，释放资源"""
        try:
            # 关闭异步执行器
            if hasattr(self, '_executor') and self._executor:
                self._executor.shutdown(wait=True)
            
            # 关闭SDK
            if hasattr(self, 'sdk') and self.sdk:
                self.sdk.close()
            
            self.logger.info("医保接口客户端已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭客户端时发生错误: {e}")

    def _async_call_wrapper(self, api_code: str, data: dict, org_code: str, task_id: str, **kwargs) -> dict:
        """异步调用包装器"""
        try:
            self.logger.info(f"执行异步调用: {api_code}, 任务ID: {task_id}")
            
            result = self.universal_processor.call_interface(
                api_code=api_code,
                input_data=data,
                org_code=org_code,
                operation_id=task_id,
                **kwargs
            )
            
            self.logger.info(f"异步调用完成: {api_code}, 任务ID: {task_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"异步调用失败: {api_code}, 任务ID: {task_id}, 错误: {e}")
            raise

    def _get_current_time(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
