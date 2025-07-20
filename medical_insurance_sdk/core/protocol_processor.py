"""
医保接口协议处理器

实现医保接口协议的请求构建、响应解析、报文ID生成等核心功能
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from ..models.request import MedicalInsuranceRequest
from ..models.response import MedicalInsuranceResponse
from ..models.config import OrganizationConfig, InterfaceConfig
from .gateway_auth import GatewayHeaders

if TYPE_CHECKING:
    from .config_manager import ConfigManager


class ProtocolProcessor:
    """医保接口协议处理器"""
    
    def __init__(self, config_manager: 'ConfigManager'):
        """
        初始化协议处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
    
    def build_request(self, api_code: str, input_data: Dict[str, Any], org_code: str, **kwargs) -> MedicalInsuranceRequest:
        """
        构建医保接口请求
        
        Args:
            api_code: 接口编码
            input_data: 输入数据
            org_code: 机构编码
            **kwargs: 其他参数
            
        Returns:
            构建好的医保接口请求对象
        """
        # 获取机构配置
        org_config = self.config_manager.get_organization_config(org_code)
        
        # 获取接口配置
        interface_config = self.config_manager.get_interface_config(api_code, org_code)
        
        # 生成报文ID
        msgid = self._generate_message_id()
        
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建请求对象
        request = MedicalInsuranceRequest(
            infno=api_code,
            msgid=msgid,
            mdtrtarea_admvs=kwargs.get('mdtrtarea_admvs', org_config.region_code),
            insuplc_admdvs=kwargs.get('insuplc_admdvs', org_config.region_code),
            recer_sys_code=kwargs.get('recer_sys_code', '99'),
            dev_no=kwargs.get('dev_no', 'null'),
            dev_safe_info=kwargs.get('dev_safe_info', 'null'),
            cainfo=kwargs.get('cainfo', 'null'),
            signtype=kwargs.get('signtype', org_config.sign_type),
            infver=kwargs.get('infver', '1.0.0'),
            opter_type=kwargs.get('opter_type', '1'),
            opter=kwargs.get('opter', org_config.org_code),
            opter_name=kwargs.get('opter_name', org_config.org_name),
            inf_time=current_time,
            fixmedins_code=org_config.org_code,
            fixmedins_name=org_config.org_name,
            sign_no=kwargs.get('sign_no', 'null'),
            input=input_data
        )
        
        return request
    
    def parse_response(self, response_data: Dict[str, Any]) -> MedicalInsuranceResponse:
        """
        解析医保接口响应
        
        Args:
            response_data: 响应数据字典
            
        Returns:
            解析后的医保接口响应对象
        """
        return MedicalInsuranceResponse.from_dict(response_data)
    
    def build_gateway_headers(self, api_code: str, org_code: str, **kwargs) -> Dict[str, str]:
        """
        构建网关请求头
        
        Args:
            api_code: 接口编码
            org_code: 机构编码
            **kwargs: 其他参数
            
        Returns:
            网关请求头字典
        """
        # 获取机构配置
        org_config = self.config_manager.get_organization_config(org_code)
        
        # 构建网关请求头
        gateway_headers = GatewayHeaders(
            api_name=kwargs.get('api_name', f'api_{api_code}'),
            api_version=kwargs.get('api_version', '1.0'),
            access_key=org_config.app_id,
            secret_key=org_config.app_secret
        )
        
        return gateway_headers.generate_headers()
    
    def _generate_message_id(self) -> str:
        """
        生成报文ID
        
        报文ID生成规则：
        1. 使用UUID4生成唯一标识
        2. 去除连字符
        3. 转换为大写
        4. 截取前30位
        
        Returns:
            30位报文ID
        """
        # 方案1：基于UUID生成
        uuid_str = str(uuid.uuid4()).replace('-', '').upper()
        return uuid_str[:30]
    
    def _generate_message_id_with_timestamp(self) -> str:
        """
        基于时间戳生成报文ID（备选方案）
        
        格式：YYYYMMDDHHMMSS + 16位随机数
        
        Returns:
            30位报文ID
        """
        # 获取当前时间戳
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # 14位
        
        # 生成16位随机数
        import random
        import string
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        
        return timestamp + random_str
    
    def validate_request(self, request: MedicalInsuranceRequest) -> tuple[bool, Optional[str]]:
        """
        验证请求数据的完整性
        
        Args:
            request: 医保接口请求对象
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查必填字段
        required_fields = {
            'infno': '交易编号',
            'msgid': '报文ID',
            'inf_time': '交易时间',
            'fixmedins_code': '定点医药机构编号',
            'fixmedins_name': '定点医药机构名称',
            'opter': '经办人',
            'opter_name': '经办人姓名'
        }
        
        for field, field_name in required_fields.items():
            value = getattr(request, field, None)
            if not value or value == "":
                return False, f"{field_name}不能为空"
        
        # 检查字段长度
        length_limits = {
            'infno': 4,
            'msgid': 30,
            'mdtrtarea_admvs': 6,
            'insuplc_admdvs': 6,
            'recer_sys_code': 10,
            'dev_no': 100,
            'signtype': 10,
            'infver': 6,
            'opter_type': 3,
            'opter': 30,
            'opter_name': 50,
            'fixmedins_code': 12,
            'fixmedins_name': 200,
            'sign_no': 30
        }
        
        for field, max_length in length_limits.items():
            value = getattr(request, field, "")
            if len(str(value)) > max_length:
                return False, f"{field}长度不能超过{max_length}位"
        
        return True, None
    
    def validate_response(self, response: MedicalInsuranceResponse) -> tuple[bool, Optional[str]]:
        """
        验证响应数据的有效性
        
        Args:
            response: 医保接口响应对象
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查响应状态码
        if response.infcode != 0:
            return False, f"接口调用失败: {response.err_msg}"
        
        # 检查输出数据
        if not response.output:
            return False, "响应数据为空"
        
        return True, None
    
    def extract_error_info(self, response: MedicalInsuranceResponse) -> Dict[str, Any]:
        """
        提取错误信息
        
        Args:
            response: 医保接口响应对象
            
        Returns:
            错误信息字典
        """
        return {
            'error_code': response.infcode,
            'error_message': response.err_msg,
            'warning_message': response.warn_msg,
            'response_time': response.respond_time,
            'ref_message_id': response.inf_refmsgid
        }
    
    def build_request_with_template(self, api_code: str, input_data: Dict[str, Any], 
                                  org_code: str, **kwargs) -> MedicalInsuranceRequest:
        """
        使用模板构建请求（支持自定义请求格式）
        
        Args:
            api_code: 接口编码
            input_data: 输入数据
            org_code: 机构编码
            **kwargs: 其他参数
            
        Returns:
            构建好的医保接口请求对象
        """
        # 获取接口配置
        interface_config = self.config_manager.get_interface_config(api_code, org_code)
        
        # 如果有自定义请求模板，使用模板构建
        if interface_config.request_template:
            processed_input = self._apply_request_template(
                input_data, 
                interface_config.request_template
            )
        else:
            processed_input = input_data
        
        # 构建标准请求
        return self.build_request(api_code, processed_input, org_code, **kwargs)
    
    def _apply_request_template(self, input_data: Dict[str, Any], 
                              template: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用请求模板
        
        Args:
            input_data: 原始输入数据
            template: 请求模板
            
        Returns:
            处理后的输入数据
        """
        import re
        
        def replace_variables(obj: Any, data: Dict[str, Any]) -> Any:
            """递归替换模板变量"""
            if isinstance(obj, str):
                # 替换 ${variable} 格式的变量
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, obj)
                result = obj
                for match in matches:
                    if match in data:
                        result = result.replace(f'${{{match}}}', str(data[match]))
                return result
            elif isinstance(obj, dict):
                return {k: replace_variables(v, data) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_variables(item, data) for item in obj]
            else:
                return obj
        
        return replace_variables(template, input_data)
    
    def get_operation_type(self, api_code: str) -> str:
        """
        根据接口编码获取操作类型（用于超时配置）
        
        Args:
            api_code: 接口编码
            
        Returns:
            操作类型
        """
        # 根据接口编码前缀判断操作类型
        if api_code.startswith('11'):  # 1101-1199 查询类
            return 'query'
        elif api_code.startswith('22'):  # 2201-2299 结算类
            return 'settlement'
        elif api_code.startswith('47'):  # 4701等 上传类
            return 'upload'
        else:
            return 'default'


class MessageIdGenerator:
    """报文ID生成器"""
    
    @staticmethod
    def generate_uuid_based() -> str:
        """基于UUID生成报文ID"""
        uuid_str = str(uuid.uuid4()).replace('-', '').upper()
        return uuid_str[:30]
    
    @staticmethod
    def generate_timestamp_based() -> str:
        """基于时间戳生成报文ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # 14位
        
        # 生成16位随机数
        import random
        import string
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        
        return timestamp + random_str
    
    @staticmethod
    def generate_sequential(prefix: str = "MSG") -> str:
        """生成序列号形式的报文ID"""
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        return f"{prefix}{timestamp}"[:30]


class ProtocolValidator:
    """协议验证器"""
    
    @staticmethod
    def validate_api_code(api_code: str) -> bool:
        """验证接口编码格式"""
        if not api_code or len(api_code) != 4:
            return False
        return api_code.isdigit()
    
    @staticmethod
    def validate_message_id(msgid: str) -> bool:
        """验证报文ID格式"""
        if not msgid or len(msgid) > 30:
            return False
        return True
    
    @staticmethod
    def validate_region_code(region_code: str) -> bool:
        """验证区划代码格式"""
        if not region_code or len(region_code) != 6:
            return False
        return region_code.isdigit()
    
    @staticmethod
    def validate_org_code(org_code: str) -> bool:
        """验证机构编码格式"""
        if not org_code or len(org_code) > 12:
            return False
        return True
    
    @staticmethod
    def validate_timestamp_format(timestamp: str) -> bool:
        """验证时间戳格式"""
        try:
            datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False


# 协议相关异常类
class ProtocolException(Exception):
    """协议异常基类"""
    pass


class InvalidRequestException(ProtocolException):
    """无效请求异常"""
    pass


class InvalidResponseException(ProtocolException):
    """无效响应异常"""
    pass


class MessageIdGenerationException(ProtocolException):
    """报文ID生成异常"""
    pass