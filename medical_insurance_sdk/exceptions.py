"""医保SDK异常定义"""

from typing import Optional, Dict, Any


class MedicalInsuranceException(Exception):
    """医保SDK基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ValidationException(MedicalInsuranceException):
    """数据验证异常"""

    def __init__(self, message: str, field_errors: Optional[Dict[str, list]] = None):
        super().__init__(
            message, "VALIDATION_ERROR", {"field_errors": field_errors or {}}
        )
        self.field_errors = field_errors or {}


class ConfigurationException(MedicalInsuranceException):
    """配置异常"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})
        self.config_key = config_key


class NetworkException(MedicalInsuranceException):
    """网络异常"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(
            message,
            "NETWORK_ERROR",
            {"status_code": status_code, "response_body": response_body},
        )
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationException(MedicalInsuranceException):
    """认证异常"""

    def __init__(self, message: str):
        super().__init__(message, "AUTH_ERROR")


class GatewayException(MedicalInsuranceException):
    """网关异常"""

    def __init__(self, message: str, gateway_code: Optional[str] = None):
        super().__init__(message, "GATEWAY_ERROR", {"gateway_code": gateway_code})
        self.gateway_code = gateway_code


class MissingHeadersError(GatewayException):
    """缺少请求头异常"""

    pass


class TimestampExpiredError(GatewayException):
    """时间戳过期异常"""

    pass


class InvalidUserError(GatewayException):
    """无效用户异常"""

    pass


class SignatureError(GatewayException):
    """签名错误异常"""

    pass


class UnknownGatewayError(GatewayException):
    """未知网关错误异常"""

    pass


class DatabaseException(MedicalInsuranceException):
    """数据库异常"""

    def __init__(self, message: str, sql: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR", {"sql": sql})
        self.sql = sql


class DataParsingException(MedicalInsuranceException):
    """数据解析异常"""

    def __init__(self, message: str, parsing_context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATA_PARSING_ERROR", {"parsing_context": parsing_context or {}})
        self.parsing_context = parsing_context or {}


class InterfaceProcessingException(MedicalInsuranceException):
    """接口处理异常"""

    def __init__(self, message: str, api_code: Optional[str] = None, processing_stage: Optional[str] = None):
        super().__init__(
            message, 
            "INTERFACE_PROCESSING_ERROR", 
            {"api_code": api_code, "processing_stage": processing_stage}
        )
        self.api_code = api_code
        self.processing_stage = processing_stage


class ProtocolException(MedicalInsuranceException):
    """协议异常"""

    def __init__(self, message: str, protocol_stage: Optional[str] = None):
        super().__init__(message, "PROTOCOL_ERROR", {"protocol_stage": protocol_stage})
        self.protocol_stage = protocol_stage


class InvalidRequestException(ProtocolException):
    """无效请求异常"""

    def __init__(self, message: str, request_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, "request_validation")
        self.request_data = request_data


class InvalidResponseException(ProtocolException):
    """无效响应异常"""

    def __init__(self, message: str, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, "response_validation")
        self.response_data = response_data


class MessageIdGenerationException(ProtocolException):
    """报文ID生成异常"""

    def __init__(self, message: str):
        super().__init__(message, "message_id_generation")


class CacheException(MedicalInsuranceException):
    """缓存异常"""

    def __init__(self, message: str, cache_operation: Optional[str] = None):
        super().__init__(message, "CACHE_ERROR", {"cache_operation": cache_operation})
        self.cache_operation = cache_operation
