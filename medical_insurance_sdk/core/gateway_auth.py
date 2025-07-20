"""
医保接口网关认证处理模块

实现网关请求头生成、HmacSHA1签名算法、签名验证和时间戳检查功能
"""

import time
import hmac
import hashlib
import base64
from typing import Dict, Optional
from dataclasses import dataclass


class GatewayHeaders:
    """网关请求头管理类"""
    
    def __init__(self, api_name: str, api_version: str, access_key: str, secret_key: str):
        """
        初始化网关请求头管理器
        
        Args:
            api_name: API名称
            api_version: API版本
            access_key: 访问密钥
            secret_key: 签名密钥
        """
        self.api_name = api_name
        self.api_version = api_version
        self.access_key = access_key
        self.secret_key = secret_key
        self.timestamp = int(time.time() * 1000)  # 13位毫秒时间戳
    
    def generate_headers(self) -> Dict[str, str]:
        """
        生成完整的网关请求头
        
        Returns:
            包含所有必需头部信息的字典
        """
        signature = self._generate_signature()
        
        return {
            'Content-Type': 'text/plain; charset=utf-8',
            '_api_name': self.api_name,
            '_api_version': self.api_version,
            '_api_timestamp': str(self.timestamp),
            '_api_access_key': self.access_key,
            '_api_signature': signature
        }
    
    def _generate_signature(self) -> str:
        """
        生成HmacSHA1签名
        
        签名步骤：
        1. 构建参数字典并按key排序
        2. 按key自然排序并拼接为字符串
        3. 使用HmacSHA1算法签名
        4. Base64编码
        
        Returns:
            Base64编码的签名字符串
        """
        # 1. 构建参数字典并按key排序
        params = {
            '_api_access_key': self.access_key,
            '_api_name': self.api_name,
            '_api_timestamp': str(self.timestamp),
            '_api_version': self.api_version
        }
        
        # 2. 按key自然排序并拼接
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        # 3. HmacSHA1签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # 4. Base64编码
        return base64.b64encode(signature).decode('utf-8')
    
    def set_custom_timestamp(self, timestamp: int):
        """
        设置自定义时间戳（主要用于测试）
        
        Args:
            timestamp: 13位毫秒时间戳
        """
        self.timestamp = timestamp


class GatewayAuthenticator:
    """网关认证器"""
    
    @staticmethod
    def verify_signature(api_name: str, api_version: str, timestamp: int, 
                        access_key: str, secret_key: str, provided_signature: str) -> bool:
        """
        验证签名是否正确
        
        Args:
            api_name: API名称
            api_version: API版本
            timestamp: 时间戳
            access_key: 访问密钥
            secret_key: 签名密钥
            provided_signature: 提供的签名
            
        Returns:
            签名是否正确
        """
        gateway_headers = GatewayHeaders(api_name, api_version, access_key, secret_key)
        gateway_headers.set_custom_timestamp(timestamp)
        expected_signature = gateway_headers._generate_signature()
        return expected_signature == provided_signature
    
    @staticmethod
    def check_timestamp_validity(timestamp: int, max_age_minutes: int = 30) -> bool:
        """
        检查时间戳是否在有效期内
        
        Args:
            timestamp: 13位毫秒时间戳
            max_age_minutes: 最大有效期（分钟）
            
        Returns:
            时间戳是否有效
        """
        current_timestamp = int(time.time() * 1000)
        time_diff_minutes = (current_timestamp - timestamp) / (1000 * 60)
        return abs(time_diff_minutes) <= max_age_minutes
    
    @staticmethod
    def validate_headers(headers: Dict[str, str], secret_key: str) -> tuple[bool, Optional[str]]:
        """
        验证完整的请求头
        
        Args:
            headers: 请求头字典
            secret_key: 签名密钥
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查必需的头部字段
        required_headers = ['_api_name', '_api_version', '_api_timestamp', '_api_access_key', '_api_signature']
        for header in required_headers:
            if header not in headers:
                return False, f"缺少必需的请求头: {header}"
        
        try:
            timestamp = int(headers['_api_timestamp'])
        except ValueError:
            return False, "时间戳格式错误"
        
        # 检查时间戳有效性
        if not GatewayAuthenticator.check_timestamp_validity(timestamp):
            return False, "签名时间戳超时"
        
        # 验证签名
        is_valid = GatewayAuthenticator.verify_signature(
            headers['_api_name'],
            headers['_api_version'],
            timestamp,
            headers['_api_access_key'],
            secret_key,
            headers['_api_signature']
        )
        
        if not is_valid:
            return False, "签名验证失败"
        
        return True, None


@dataclass
class GatewayError:
    """网关错误信息"""
    code: int
    message: str
    details: Optional[str] = None


class GatewayErrorHandler:
    """网关错误处理器"""
    
    # 常见错误码定义
    ERROR_CODES = {
        'MISSING_HEADERS': 400,
        'INVALID_TIMESTAMP': 401,
        'TIMESTAMP_EXPIRED': 401,
        'INVALID_USER': 401,
        'SIGNATURE_MISMATCH': 401,
        'UNKNOWN_ERROR': 500
    }
    
    @staticmethod
    def handle_gateway_error(response_code: int, message: str) -> GatewayError:
        """
        处理网关错误并返回标准化错误信息
        
        Args:
            response_code: HTTP响应码
            message: 错误消息
            
        Returns:
            标准化的网关错误对象
        """
        if response_code == 401:
            if "缺少服务网关的请求头" in message:
                return GatewayError(
                    code=GatewayErrorHandler.ERROR_CODES['MISSING_HEADERS'],
                    message="请求头不完整",
                    details="请检查_api_*字段是否完整"
                )
            elif "签名时间戳超时" in message:
                return GatewayError(
                    code=GatewayErrorHandler.ERROR_CODES['TIMESTAMP_EXPIRED'],
                    message="签名时间戳超时",
                    details="请重新生成时间戳和签名"
                )
            elif "非法用户" in message:
                return GatewayError(
                    code=GatewayErrorHandler.ERROR_CODES['INVALID_USER'],
                    message="AK密钥无效",
                    details="请检查access_key配置"
                )
            elif "签名不一致" in message:
                return GatewayError(
                    code=GatewayErrorHandler.ERROR_CODES['SIGNATURE_MISMATCH'],
                    message="签名验证失败",
                    details="请检查secret_key和签名算法"
                )
        
        return GatewayError(
            code=GatewayErrorHandler.ERROR_CODES['UNKNOWN_ERROR'],
            message=f"网关错误: {message}",
            details=f"HTTP状态码: {response_code}"
        )
    
    @staticmethod
    def is_gateway_error(response_code: int) -> bool:
        """
        判断是否为网关错误
        
        Args:
            response_code: HTTP响应码
            
        Returns:
            是否为网关错误
        """
        return response_code in [400, 401, 403, 500, 502, 503, 504]


# 自定义异常类
class GatewayException(Exception):
    """网关异常基类"""
    
    def __init__(self, error: GatewayError):
        self.error = error
        super().__init__(error.message)


class MissingHeadersError(GatewayException):
    """缺少请求头错误"""
    pass


class TimestampExpiredError(GatewayException):
    """时间戳过期错误"""
    pass


class InvalidUserError(GatewayException):
    """无效用户错误"""
    pass


class SignatureError(GatewayException):
    """签名错误"""
    pass


class UnknownGatewayError(GatewayException):
    """未知网关错误"""
    pass