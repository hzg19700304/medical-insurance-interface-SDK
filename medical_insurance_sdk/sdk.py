"""医保SDK核心类"""

import time
import logging
from typing import Dict, Any, Optional
from .config.models import SDKConfig
from .core import (
    ConfigManager, 
    DataValidator, 
    ProtocolProcessor, 
    MedicalInsuranceHTTPClient,
    GatewayHeaders
)
from .models.response import MedicalInsuranceResponse
from .models.request import MedicalInsuranceRequest
from .models.log import OperationLog
from .exceptions import (
    MedicalInsuranceException, 
    ValidationException, 
    NetworkException,
    ConfigurationException
)


logger = logging.getLogger(__name__)


class MedicalInsuranceSDK:
    """医保SDK核心类
    
    提供医保接口的统一调用能力，集成所有核心组件。
    """

    def __init__(self, config: SDKConfig):
        """初始化SDK

        Args:
            config: SDK配置
        """
        self.config = config
        
        # 初始化核心组件
        try:
            self.config_manager = ConfigManager(config.database_config)
            self.data_validator = DataValidator(self.config_manager)
            self.protocol_processor = ProtocolProcessor(self.config_manager)
            self.http_client = MedicalInsuranceHTTPClient(config.http_config)
            
            logger.info("医保SDK初始化完成")
            
        except Exception as e:
            error_msg = f"SDK初始化失败: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationException(error_msg) from e

    def call(self, api_code: str, data: dict, **kwargs) -> MedicalInsuranceResponse:
        """统一接口调用方法

        Args:
            api_code: 接口编码
            data: 接口数据
            **kwargs: 其他参数，包括org_code等

        Returns:
            MedicalInsuranceResponse: 响应对象

        Raises:
            MedicalInsuranceException: 调用失败时抛出异常
        """
        org_code = kwargs.get("org_code")
        if not org_code:
            raise MedicalInsuranceException("机构编码不能为空")

        operation_id = self._generate_operation_id()
        start_time = time.time()
        
        try:
            logger.info(f"开始调用医保接口: {api_code}, 机构: {org_code}, 操作ID: {operation_id}")
            
            # 1. 数据验证（基于配置）
            validation_result = self.data_validator.validate_input_data(
                api_code, data.get('data', {}), org_code
            )
            
            if not validation_result.is_valid:
                raise ValidationException(
                    "输入数据验证失败", 
                    field_errors=validation_result.errors
                )
            
            # 2. 构建请求
            request = self.protocol_processor.build_request(api_code, data, org_code)
            headers = self.protocol_processor.build_gateway_headers(api_code, org_code)
            
            # 3. 发送请求
            org_config = self.config_manager.get_organization_config(org_code)
            response_data = self.http_client.call_medical_api(
                url=org_config.base_url,
                request_data=request.to_dict(),
                headers=headers,
                timeout=org_config.get_timeout('default')
            )
            
            # 4. 解析响应
            response = self.protocol_processor.parse_response(response_data)
            
            # 5. 记录日志
            self._log_api_call(
                operation_id=operation_id,
                api_code=api_code,
                org_code=org_code,
                request_data=request.to_dict(),
                response_data=response_data,
                status='success',
                duration=time.time() - start_time,
                **kwargs
            )
            
            logger.info(f"医保接口调用成功: {api_code}, 耗时: {time.time() - start_time:.3f}秒")
            return response

        except ValidationException as e:
            logger.error(f"数据验证失败: {api_code}, 错误: {str(e)}")
            self._log_api_call(
                operation_id=operation_id,
                api_code=api_code,
                org_code=org_code,
                request_data=data,
                response_data=None,
                status='validation_failed',
                error_message=str(e),
                duration=time.time() - start_time,
                **kwargs
            )
            raise
            
        except NetworkException as e:
            logger.error(f"网络请求失败: {api_code}, 错误: {str(e)}")
            self._log_api_call(
                operation_id=operation_id,
                api_code=api_code,
                org_code=org_code,
                request_data=data,
                response_data=None,
                status='network_failed',
                error_message=str(e),
                duration=time.time() - start_time,
                **kwargs
            )
            raise
            
        except Exception as e:
            error_msg = f"接口调用失败: {str(e)}"
            logger.error(f"医保接口调用异常: {api_code}, 错误: {error_msg}")
            self._log_api_call(
                operation_id=operation_id,
                api_code=api_code,
                org_code=org_code,
                request_data=data,
                response_data=None,
                status='failed',
                error_message=error_msg,
                duration=time.time() - start_time,
                **kwargs
            )
            raise MedicalInsuranceException(error_msg) from e

    def call_async(self, api_code: str, data: dict, **kwargs) -> str:
        """异步接口调用方法

        Args:
            api_code: 接口编码
            data: 接口数据
            **kwargs: 其他参数

        Returns:
            str: 任务ID
        """
        # TODO: 实现异步调用功能
        raise NotImplementedError("异步调用功能将在后续任务中实现")
    
    def get_interface_config(self, api_code: str, org_code: str = None) -> Dict[str, Any]:
        """获取接口配置信息
        
        Args:
            api_code: 接口编码
            org_code: 机构编码（可选）
            
        Returns:
            接口配置信息
        """
        try:
            interface_config = self.config_manager.get_interface_config(api_code, org_code)
            return interface_config.to_dict()
        except Exception as e:
            logger.error(f"获取接口配置失败: {api_code}, 错误: {str(e)}")
            raise ConfigurationException(f"获取接口配置失败: {str(e)}") from e
    
    def get_organization_config(self, org_code: str) -> Dict[str, Any]:
        """获取机构配置信息
        
        Args:
            org_code: 机构编码
            
        Returns:
            机构配置信息
        """
        try:
            org_config = self.config_manager.get_organization_config(org_code)
            # 隐藏敏感信息
            config_dict = org_config.to_dict()
            config_dict['app_secret'] = '***'
            return config_dict
        except Exception as e:
            logger.error(f"获取机构配置失败: {org_code}, 错误: {str(e)}")
            raise ConfigurationException(f"获取机构配置失败: {str(e)}") from e
    
    def validate_data(self, api_code: str, data: dict, org_code: str = None) -> Dict[str, Any]:
        """验证接口数据
        
        Args:
            api_code: 接口编码
            data: 待验证数据
            org_code: 机构编码（可选）
            
        Returns:
            验证结果
        """
        try:
            validation_result = self.data_validator.validate_input_data(api_code, data, org_code)
            return {
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
                'error_messages': validation_result.get_error_messages()
            }
        except Exception as e:
            logger.error(f"数据验证失败: {api_code}, 错误: {str(e)}")
            raise ValidationException(f"数据验证失败: {str(e)}") from e
    
    def reload_config(self, config_type: str = None):
        """重新加载配置
        
        Args:
            config_type: 配置类型，可选值: 'interface', 'organization', None(全部)
        """
        try:
            self.config_manager.reload_config(config_type)
            logger.info(f"配置重新加载完成: {config_type or '全部'}")
        except Exception as e:
            logger.error(f"配置重新加载失败: {str(e)}")
            raise ConfigurationException(f"配置重新加载失败: {str(e)}") from e
    
    def close(self):
        """关闭SDK，释放资源"""
        try:
            if hasattr(self, 'http_client') and self.http_client:
                self.http_client.close()
            
            if hasattr(self, 'config_manager') and self.config_manager:
                self.config_manager.close()
            
            logger.info("医保SDK已关闭")
            
        except Exception as e:
            logger.error(f"SDK关闭时发生错误: {str(e)}")
    
    def _generate_operation_id(self) -> str:
        """生成操作ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _log_api_call(self, operation_id: str, api_code: str, org_code: str,
                     request_data: Dict[str, Any], response_data: Optional[Dict[str, Any]],
                     status: str, duration: float, error_message: str = None, **kwargs):
        """记录API调用日志"""
        try:
            # 获取接口配置以获取业务分类信息
            try:
                interface_config = self.config_manager.get_interface_config(api_code, org_code)
                business_category = interface_config.business_category
                business_type = interface_config.business_type
                api_name = interface_config.api_name
            except:
                business_category = "未知"
                business_type = "未知"
                api_name = f"接口{api_code}"
            
            # 创建操作日志对象
            from datetime import datetime
            log_entry = OperationLog(
                operation_id=operation_id,
                api_code=api_code,
                api_name=api_name,
                business_category=business_category,
                business_type=business_type,
                institution_code=org_code,
                psn_no=kwargs.get('psn_no'),
                mdtrt_id=kwargs.get('mdtrt_id'),
                request_data=request_data,
                response_data=response_data,
                status=status,
                error_message=error_message,
                operation_time=datetime.now(),
                complete_time=datetime.now(),
                operator_id=kwargs.get('operator_id'),
                trace_id=kwargs.get('trace_id', operation_id),
                client_ip=kwargs.get('client_ip', '127.0.0.1')
            )
            
            # 这里应该调用数据管理器保存日志，但由于数据管理器还未实现，先记录到系统日志
            logger.info(f"API调用日志: {operation_id}, {api_code}, {status}, 耗时: {duration:.3f}秒")
            
        except Exception as e:
            logger.error(f"记录API调用日志失败: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
