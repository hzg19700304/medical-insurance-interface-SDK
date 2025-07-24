"""
通用接口处理器模块
提供统一的医保接口调用处理，支持配置驱动的数据验证、请求构建和响应解析
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config_manager import ConfigManager
from .validator import DataValidator
from .data_parser import DataParser
from .protocol_processor import ProtocolProcessor
from ..models.config import InterfaceConfig, OrganizationConfig
from ..models.validation import ValidationResult
from ..exceptions import (
    ValidationException, 
    ConfigurationException, 
    DataParsingException,
    InterfaceProcessingException
)


class UniversalInterfaceProcessor:
    """通用接口处理器 - 核心组件"""
    
    def __init__(self, sdk: 'MedicalInsuranceSDK'):
        self.sdk = sdk
        self.config_manager = sdk.config_manager
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.data_validator = DataValidator(self.config_manager)
        self.data_parser = DataParser(self.config_manager)
        self.protocol_processor = ProtocolProcessor(self.config_manager)
        
        # 处理统计
        self._processing_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'validation_errors': 0,
            'parsing_errors': 0
        }
    
    def call_interface(self, api_code: str, input_data: dict, org_code: str, **kwargs) -> dict:
        """通用接口调用方法 - 唯一的接口调用入口"""
        operation_id = kwargs.get('operation_id', str(uuid.uuid4()))
        start_time = datetime.now()
        
        try:
            self._processing_stats['total_calls'] += 1
            
            self.logger.info(f"开始处理接口调用: {api_code}, 机构: {org_code}, 操作ID: {operation_id}")
            
            # 1. 获取接口配置
            interface_config = self._get_interface_config(api_code, org_code)
            
            # 2. 数据预处理（应用默认值、数据转换等）
            processed_data = self._preprocess_input_data(input_data, interface_config)
            
            # 3. 构建请求数据
            request_data = self._build_request_data(processed_data, interface_config, org_code)
            
            # 4. 数据验证由SDK核心统一处理，这里不再重复验证
            
            # 5. 调用SDK核心
            response = self._call_sdk_core(api_code, request_data, org_code, **kwargs)
            
            # 6. 解析响应数据
            parsed_output = self._parse_response_data(api_code, response, org_code)
            
            # 7. 记录成功统计
            self._processing_stats['successful_calls'] += 1
            
            # 8. 记录处理日志
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"接口调用处理完成: {api_code}, 耗时: {processing_time:.3f}秒")
            
            return parsed_output
            
        except ValidationException:
            self._processing_stats['failed_calls'] += 1
            raise
        except DataParsingException:
            self._processing_stats['parsing_errors'] += 1
            self._processing_stats['failed_calls'] += 1
            raise
        except Exception as e:
            self._processing_stats['failed_calls'] += 1
            self.logger.error(f"接口调用处理失败: {api_code}, 错误: {e}")
            raise InterfaceProcessingException(f"接口调用处理失败: {e}")
    
    def _get_interface_config(self, api_code: str, org_code: str) -> InterfaceConfig:
        """获取接口配置"""
        try:
            # 获取机构配置以确定地区信息
            org_config = self.config_manager.get_organization_config(org_code)
            region = org_config.province_code if org_config else None
            
            # 获取接口配置
            interface_config = self.config_manager.get_interface_config(api_code, region)
            
            self.logger.debug(f"获取接口配置成功: {api_code}, 地区: {region}")
            return interface_config
            
        except Exception as e:
            self.logger.error(f"获取接口配置失败: {api_code}, 机构: {org_code}, 错误: {e}")
            raise ConfigurationException(f"获取接口配置失败: {e}")
    
    def _preprocess_input_data(self, input_data: dict, interface_config: InterfaceConfig) -> dict:
        """数据预处理（应用默认值、数据转换等）"""
        processed_data = input_data.copy()
        
        try:
            # 1. 应用默认值
            for field, default_value in interface_config.default_values.items():
                if field not in processed_data or processed_data[field] is None:
                    processed_data[field] = default_value
                    self.logger.debug(f"应用默认值: {field} = {default_value}")
            
            # 2. 应用数据转换规则
            data_transforms = interface_config.validation_rules.get('data_transforms', {})
            if data_transforms:
                processed_data = self._apply_data_transforms(processed_data, data_transforms)
            
            # 3. 数据类型转换
            processed_data = self._apply_type_conversions(processed_data, interface_config)
            
            self.logger.debug(f"数据预处理完成，字段数量: {len(processed_data)}")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"数据预处理失败: {e}")
            raise InterfaceProcessingException(f"数据预处理失败: {e}")
    
    def _validate_input_data(self, api_code: str, input_data: dict, org_code: str) -> ValidationResult:
        """数据验证"""
        try:
            validation_result = self.data_validator.validate_input_data(api_code, input_data, org_code)
            
            if validation_result.is_valid:
                self.logger.debug(f"数据验证通过: {api_code}")
            else:
                self.logger.warning(f"数据验证失败: {api_code}, 错误: {validation_result.get_error_messages()}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"数据验证过程异常: {api_code}, 错误: {e}")
            result = ValidationResult()
            result.add_error("system", f"验证过程异常: {str(e)}")
            return result
    
    def _build_request_data(self, input_data: dict, interface_config: InterfaceConfig, org_code: str) -> dict:
        """构建请求数据"""
        try:
            # 使用请求模板构建数据
            if interface_config.request_template:
                request_data = self._apply_request_template(input_data, interface_config.request_template)
            else:
                # 使用默认格式
                request_data = {
                    "data": input_data
                }
            
            # 应用参数映射
            if interface_config.param_mapping:
                request_data = self._apply_parameter_mapping(request_data, interface_config.param_mapping)
            
            self.logger.debug(f"请求数据构建完成")
            return request_data
            
        except Exception as e:
            self.logger.error(f"构建请求数据失败: {e}")
            raise InterfaceProcessingException(f"构建请求数据失败: {e}")
    
    def _call_sdk_core(self, api_code: str, request_data: dict, org_code: str, **kwargs) -> dict:
        """调用SDK核心"""
        try:
            # 调用SDK的call方法
            response = self.sdk.call(api_code, request_data, org_code=org_code, **kwargs)
            
            self.logger.debug(f"SDK核心调用完成: {api_code}")
            return response.to_dict() if hasattr(response, 'to_dict') else response
            
        except Exception as e:
            self.logger.error(f"SDK核心调用失败: {api_code}, 错误: {e}")
            raise
    
    def _parse_response_data(self, api_code: str, response_data: dict, org_code: str) -> dict:
        """解析响应数据"""
        try:
            # 使用数据解析器解析响应
            parsed_data = self.data_parser.parse_response_data(api_code, response_data, org_code)
            
            self.logger.debug(f"响应数据解析完成: {api_code}")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析响应数据失败: {api_code}, 错误: {e}")
            # 解析失败时返回原始数据，不中断流程
            self.logger.warning(f"返回原始响应数据: {api_code}")
            return response_data
    
    def _apply_data_transforms(self, data: dict, transforms: Dict[str, Any]) -> dict:
        """应用数据转换规则"""
        transformed_data = data.copy()
        
        for field_name, transform_config in transforms.items():
            if field_name in transformed_data:
                try:
                    original_value = transformed_data[field_name]
                    transformed_value = self._apply_single_transform(original_value, transform_config)
                    transformed_data[field_name] = transformed_value
                    
                    if original_value != transformed_value:
                        self.logger.debug(f"数据转换: {field_name} = {original_value} -> {transformed_value}")
                        
                except Exception as e:
                    self.logger.warning(f"字段 {field_name} 数据转换失败: {e}")
        
        return transformed_data
    
    def _apply_single_transform(self, value: Any, transform_config: Any) -> Any:
        """应用单个数据转换"""
        if value is None:
            return value
        
        if isinstance(transform_config, str):
            transform_type = transform_config
        elif isinstance(transform_config, dict):
            transform_type = transform_config.get('type')
        else:
            return value
        
        value_str = str(value)
        
        if transform_type == 'remove_spaces':
            return value_str.replace(' ', '')
        elif transform_type == 'trim':
            return value_str.strip()
        elif transform_type == 'upper':
            return value_str.upper()
        elif transform_type == 'lower':
            return value_str.lower()
        elif transform_type == 'string_upper':
            return value_str.upper()
        elif transform_type == 'title':
            return value_str.title()
        
        return value
    
    def _apply_type_conversions(self, data: dict, interface_config: InterfaceConfig) -> dict:
        """应用数据类型转换"""
        converted_data = data.copy()
        
        # 根据必填参数和可选参数的类型配置进行转换
        all_params = {**interface_config.required_params, **interface_config.optional_params}
        
        for field_name, field_config in all_params.items():
            if field_name in converted_data and isinstance(field_config, dict):
                field_type = field_config.get('type')
                if field_type:
                    try:
                        original_value = converted_data[field_name]
                        converted_value = self._convert_field_type(original_value, field_type)
                        converted_data[field_name] = converted_value
                    except Exception as e:
                        self.logger.warning(f"字段 {field_name} 类型转换失败: {e}")
        
        return converted_data
    
    def _convert_field_type(self, value: Any, target_type: str) -> Any:
        """转换字段类型"""
        if value is None:
            return value
        
        if target_type == 'string' or target_type == 'str':
            return str(value)
        elif target_type == 'integer' or target_type == 'int':
            return int(float(value))
        elif target_type == 'float' or target_type == 'number':
            return float(value)
        elif target_type == 'boolean' or target_type == 'bool':
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        
        return value
    
    def _apply_request_template(self, input_data: dict, template: Dict[str, Any]) -> dict:
        """应用请求模板"""
        def replace_placeholders(obj):
            if isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
                # 替换占位符 ${field_name}
                field_name = obj[2:-1]
                return input_data.get(field_name, obj)
            else:
                return obj
        
        return replace_placeholders(template)
    
    def _apply_parameter_mapping(self, request_data: dict, param_mapping: Dict[str, Any]) -> dict:
        """应用参数映射"""
        # 这里可以实现更复杂的参数映射逻辑
        # 目前简单返回原始数据
        return request_data
    
    def call_batch_interfaces(self, batch_requests: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """批量接口调用"""
        results = []
        
        for i, request in enumerate(batch_requests):
            try:
                api_code = request.get('api_code')
                input_data = request.get('input_data', {})
                org_code = request.get('org_code')
                
                if not api_code or not org_code:
                    results.append({
                        'success': False,
                        'error': '缺少必要参数: api_code 或 org_code',
                        'index': i
                    })
                    continue
                
                # 调用单个接口
                result = self.call_interface(api_code, input_data, org_code, **kwargs)
                results.append({
                    'success': True,
                    'data': result,
                    'index': i
                })
                
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'index': i
                })
        
        return results
    
    def get_interface_info(self, api_code: str, org_code: str = None) -> Dict[str, Any]:
        """获取接口信息"""
        try:
            interface_config = self._get_interface_config(api_code, org_code or 'default')
            
            return {
                'api_code': interface_config.api_code,
                'api_name': interface_config.api_name,
                'business_category': interface_config.business_category,
                'business_type': interface_config.business_type,
                'required_params': list(interface_config.required_params.keys()),
                'optional_params': list(interface_config.optional_params.keys()),
                'default_values': interface_config.default_values,
                'timeout_seconds': interface_config.timeout_seconds,
                'max_retry_times': interface_config.max_retry_times,
                'is_active': interface_config.is_active
            }
            
        except Exception as e:
            self.logger.error(f"获取接口信息失败: {api_code}, 错误: {e}")
            return {'error': str(e)}
    
    def validate_interface_data(self, api_code: str, input_data: dict, org_code: str) -> Dict[str, Any]:
        """验证接口数据（不执行调用）"""
        try:
            # 获取接口配置
            interface_config = self._get_interface_config(api_code, org_code)
            
            # 数据预处理
            processed_data = self._preprocess_input_data(input_data, interface_config)
            
            # 数据验证
            validation_result = self._validate_input_data(api_code, processed_data, org_code)
            
            return {
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
                'processed_data': processed_data if validation_result.is_valid else None,
                'error_messages': validation_result.get_error_messages()
            }
            
        except Exception as e:
            self.logger.error(f"验证接口数据失败: {api_code}, 错误: {e}")
            return {
                'is_valid': False,
                'errors': {'system': [str(e)]},
                'error_messages': [str(e)]
            }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self._processing_stats.copy()
        
        # 计算成功率
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
            stats['failure_rate'] = stats['failed_calls'] / stats['total_calls']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        return stats
    
    def reset_processing_stats(self):
        """重置处理统计"""
        self._processing_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'validation_errors': 0,
            'parsing_errors': 0
        }
        self.logger.info("处理统计已重置")
    
    def register_custom_parser(self, name: str, parser_func):
        """注册自定义解析器"""
        self.data_parser.register_custom_parser(name, parser_func)
    
    def register_custom_validator(self, name: str, validator_func):
        """注册自定义验证器"""
        self.data_validator.register_custom_validator(name, validator_func)
    
    def get_supported_interfaces(self, org_code: str = None) -> List[Dict[str, Any]]:
        """获取支持的接口列表"""
        try:
            # 获取所有接口配置
            all_configs = self.config_manager.get_all_interface_configs()
            
            interfaces = []
            for config in all_configs:
                interfaces.append({
                    'api_code': config.api_code,
                    'api_name': config.api_name,
                    'business_category': config.business_category,
                    'business_type': config.business_type,
                    'is_active': config.is_active
                })
            
            return interfaces
            
        except Exception as e:
            self.logger.error(f"获取支持的接口列表失败: {e}")
            return []


class DataHelper:
    """数据处理辅助工具类 - 提供常用的数据处理方法"""
    
    @staticmethod
    def extract_person_basic_info(response_data: dict) -> dict:
        """提取人员基本信息的便捷方法"""
        return {
            'name': response_data.get('person_name', ''),
            'id': response_data.get('person_id', ''),
            'id_card': response_data.get('id_card', ''),
            'gender': response_data.get('gender', ''),
            'birth_date': response_data.get('birth_date', ''),
            'age': response_data.get('age', 0)
        }
    
    @staticmethod
    def extract_insurance_info(response_data: dict) -> List[dict]:
        """提取参保信息的便捷方法"""
        return response_data.get('insurance_list', [])
    
    @staticmethod
    def calculate_total_balance(insurance_list: List[dict]) -> float:
        """计算总余额的便捷方法"""
        return sum(item.get('balance', 0) for item in insurance_list)
    
    @staticmethod
    def format_settlement_summary(response_data: dict) -> dict:
        """格式化结算摘要的便捷方法"""
        return {
            'settlement_id': response_data.get('settlement_id', ''),
            'total': float(response_data.get('total_amount', 0)),
            'insurance_pay': float(response_data.get('insurance_amount', 0)),
            'personal_pay': float(response_data.get('personal_amount', 0)),
            'settlement_time': response_data.get('settlement_time', '')
        }
    
    @staticmethod
    def extract_error_info(response_data: dict) -> dict:
        """提取错误信息的便捷方法"""
        return {
            'error_code': response_data.get('infcode', ''),
            'error_message': response_data.get('err_msg', ''),
            'warning_message': response_data.get('warn_msg', ''),
            'is_success': response_data.get('infcode') == 0
        }
    
    @staticmethod
    def format_medical_record(response_data: dict) -> dict:
        """格式化医疗记录的便捷方法"""
        return {
            'record_id': response_data.get('mdtrt_id', ''),
            'person_no': response_data.get('psn_no', ''),
            'visit_date': response_data.get('begntime', ''),
            'end_date': response_data.get('endtime', ''),
            'diagnosis': response_data.get('dise_codg', ''),
            'hospital_code': response_data.get('fixmedins_code', ''),
            'hospital_name': response_data.get('fixmedins_name', '')
        }
    
    @staticmethod
    def validate_id_card(id_card: str) -> bool:
        """验证身份证号码格式"""
        import re
        if not id_card or len(id_card) not in [15, 18]:
            return False
        
        if len(id_card) == 18:
            pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]$'
            return bool(re.match(pattern, id_card))
        else:
            pattern = r'^[1-9]\d{5}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}$'
            return bool(re.match(pattern, id_card))
    
    @staticmethod
    def format_amount(amount: Any, decimals: int = 2) -> str:
        """格式化金额"""
        try:
            return f"{float(amount):.{decimals}f}"
        except (ValueError, TypeError):
            return "0.00"
    
    @staticmethod
    def parse_date_string(date_str: str, input_format: str = '%Y-%m-%d', output_format: str = '%Y%m%d') -> str:
        """解析日期字符串"""
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, input_format)
            return date_obj.strftime(output_format)
        except (ValueError, TypeError):
            return date_str