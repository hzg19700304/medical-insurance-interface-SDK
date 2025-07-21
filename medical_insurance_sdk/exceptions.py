"""医保SDK异常定义"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class MedicalInsuranceException(Exception):
    """医保SDK基础异常类
    
    所有医保SDK异常的基类，提供标准化的异常信息结构
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        retry_after: Optional[int] = None,
        severity: str = "ERROR"
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.cause = cause
        self.retry_after = retry_after  # 重试间隔（秒）
        self.severity = severity  # ERROR, WARNING, CRITICAL
        self.timestamp = datetime.now()
        self.exception_id = self._generate_exception_id()

    def _generate_exception_id(self) -> str:
        """生成异常唯一标识"""
        import uuid
        return str(uuid.uuid4())[:8]

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录和序列化"""
        return {
            "exception_id": self.exception_id,
            "exception_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "retry_after": self.retry_after,
            "cause": str(self.cause) if self.cause else None
        }

    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def is_retryable(self) -> bool:
        """判断异常是否可重试"""
        return self.retry_after is not None

    def get_user_message(self) -> str:
        """获取用户友好的错误信息"""
        return self.message


# ============================================================================
# 业务异常类 - Business Exceptions
# ============================================================================

class BusinessException(MedicalInsuranceException):
    """业务异常基类"""
    
    def __init__(self, message: str, business_code: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.business_code = business_code

class ValidationException(BusinessException):
    """数据验证异常"""

    def __init__(self, message: str, field_errors: Optional[Dict[str, List[str]]] = None, **kwargs):
        super().__init__(
            message, 
            error_code="VALIDATION_ERROR", 
            details={"field_errors": field_errors or {}},
            **kwargs
        )
        self.field_errors = field_errors or {}

    def get_user_message(self) -> str:
        """获取用户友好的验证错误信息"""
        if self.field_errors:
            error_messages = []
            for field, errors in self.field_errors.items():
                error_messages.extend(errors)
            return f"数据验证失败: {'; '.join(error_messages)}"
        return self.message

class RequiredFieldException(ValidationException):
    """必填字段异常"""
    
    def __init__(self, field_name: str, **kwargs):
        message = f"必填字段 '{field_name}' 不能为空"
        super().__init__(message, field_errors={field_name: [message]}, **kwargs)
        self.field_name = field_name

class FieldFormatException(ValidationException):
    """字段格式异常"""
    
    def __init__(self, field_name: str, expected_format: str, actual_value: Any = None, **kwargs):
        message = f"字段 '{field_name}' 格式不正确，期望格式: {expected_format}"
        if actual_value is not None:
            message += f"，实际值: {actual_value}"
        super().__init__(message, field_errors={field_name: [message]}, **kwargs)
        self.field_name = field_name
        self.expected_format = expected_format
        self.actual_value = actual_value

class FieldLengthException(ValidationException):
    """字段长度异常"""
    
    def __init__(self, field_name: str, max_length: int, actual_length: int, **kwargs):
        message = f"字段 '{field_name}' 长度超限，最大长度: {max_length}，实际长度: {actual_length}"
        super().__init__(message, field_errors={field_name: [message]}, **kwargs)
        self.field_name = field_name
        self.max_length = max_length
        self.actual_length = actual_length

class EnumValueException(ValidationException):
    """枚举值异常"""
    
    def __init__(self, field_name: str, valid_values: List[str], actual_value: Any, **kwargs):
        message = f"字段 '{field_name}' 值无效，有效值: {', '.join(valid_values)}，实际值: {actual_value}"
        super().__init__(message, field_errors={field_name: [message]}, **kwargs)
        self.field_name = field_name
        self.valid_values = valid_values
        self.actual_value = actual_value

class ConditionalValidationException(ValidationException):
    """条件验证异常"""
    
    def __init__(self, condition: str, required_fields: List[str], **kwargs):
        message = f"在条件 '{condition}' 下，以下字段不能为空: {', '.join(required_fields)}"
        super().__init__(message, **kwargs)
        self.condition = condition
        self.required_fields = required_fields


# ============================================================================
# 配置异常类 - Configuration Exceptions
# ============================================================================

class ConfigurationException(MedicalInsuranceException):
    """配置异常基类"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="CONFIG_ERROR", 
            details={"config_key": config_key},
            **kwargs
        )
        self.config_key = config_key

class MissingConfigException(ConfigurationException):
    """缺少配置异常"""
    
    def __init__(self, config_key: str, **kwargs):
        message = f"缺少必需的配置项: {config_key}"
        super().__init__(message, config_key=config_key, **kwargs)

class InvalidConfigException(ConfigurationException):
    """无效配置异常"""
    
    def __init__(self, config_key: str, config_value: Any, reason: str, **kwargs):
        message = f"配置项 '{config_key}' 值无效: {config_value}，原因: {reason}"
        super().__init__(
            message, 
            config_key=config_key, 
            details={"config_value": config_value, "reason": reason},
            **kwargs
        )
        self.config_value = config_value
        self.reason = reason

class InterfaceConfigException(ConfigurationException):
    """接口配置异常"""
    
    def __init__(self, api_code: str, config_issue: str, **kwargs):
        message = f"接口 {api_code} 配置异常: {config_issue}"
        super().__init__(
            message, 
            details={"api_code": api_code, "config_issue": config_issue},
            **kwargs
        )
        self.api_code = api_code
        self.config_issue = config_issue

class OrganizationConfigException(ConfigurationException):
    """机构配置异常"""
    
    def __init__(self, org_code: str, config_issue: str, **kwargs):
        message = f"机构 {org_code} 配置异常: {config_issue}"
        super().__init__(
            message, 
            details={"org_code": org_code, "config_issue": config_issue},
            **kwargs
        )
        self.org_code = org_code
        self.config_issue = config_issue


# ============================================================================
# 网络异常类 - Network Exceptions
# ============================================================================

class NetworkException(MedicalInsuranceException):
    """网络异常基类"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        # 网络异常通常可以重试
        if 'retry_after' not in kwargs and status_code in [500, 502, 503, 504]:
            kwargs['retry_after'] = 5  # 5秒后重试
            
        super().__init__(
            message,
            error_code="NETWORK_ERROR",
            details={"status_code": status_code, "response_body": response_body},
            **kwargs
        )
        self.status_code = status_code
        self.response_body = response_body

class ConnectionException(NetworkException):
    """连接异常"""
    
    def __init__(self, url: str, cause: Optional[Exception] = None, **kwargs):
        message = f"无法连接到服务器: {url}"
        super().__init__(message, cause=cause, retry_after=10, **kwargs)
        self.url = url

class TimeoutException(NetworkException):
    """超时异常"""
    
    def __init__(self, timeout_seconds: int, operation: str = "请求", **kwargs):
        message = f"{operation}超时 ({timeout_seconds}秒)"
        super().__init__(message, retry_after=5, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.operation = operation

class HTTPException(NetworkException):
    """HTTP异常"""
    
    def __init__(self, status_code: int, reason: str, url: str, **kwargs):
        message = f"HTTP错误 {status_code}: {reason} (URL: {url})"
        super().__init__(message, status_code=status_code, **kwargs)
        self.reason = reason
        self.url = url

class TooManyRequestsException(HTTPException):
    """请求过多异常"""
    
    def __init__(self, retry_after: int = 60, **kwargs):
        super().__init__(
            status_code=429, 
            reason="Too Many Requests", 
            url=kwargs.get('url', ''),
            retry_after=retry_after,
            **kwargs
        )


# ============================================================================
# 认证和授权异常类 - Authentication & Authorization Exceptions
# ============================================================================

class AuthenticationException(MedicalInsuranceException):
    """认证异常基类"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)

class InvalidCredentialsException(AuthenticationException):
    """无效凭据异常"""
    
    def __init__(self, credential_type: str = "用户凭据", **kwargs):
        message = f"{credential_type}无效或已过期"
        super().__init__(message, **kwargs)
        self.credential_type = credential_type

class TokenExpiredException(AuthenticationException):
    """令牌过期异常"""
    
    def __init__(self, token_type: str = "访问令牌", **kwargs):
        message = f"{token_type}已过期，请重新获取"
        super().__init__(message, **kwargs)
        self.token_type = token_type

class InsufficientPermissionsException(AuthenticationException):
    """权限不足异常"""
    
    def __init__(self, required_permission: str, **kwargs):
        message = f"权限不足，需要权限: {required_permission}"
        super().__init__(message, **kwargs)
        self.required_permission = required_permission


# ============================================================================
# 网关异常类 - Gateway Exceptions
# ============================================================================

class GatewayException(MedicalInsuranceException):
    """网关异常基类"""

    def __init__(self, message: str, gateway_code: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="GATEWAY_ERROR", 
            details={"gateway_code": gateway_code},
            **kwargs
        )
        self.gateway_code = gateway_code

class MissingHeadersError(GatewayException):
    """缺少请求头异常"""

    def __init__(self, missing_headers: List[str], **kwargs):
        message = f"缺少必需的请求头: {', '.join(missing_headers)}"
        super().__init__(message, **kwargs)
        self.missing_headers = missing_headers

class TimestampExpiredError(GatewayException):
    """时间戳过期异常"""

    def __init__(self, timestamp: int, max_age_minutes: int = 30, **kwargs):
        message = f"签名时间戳已过期，最大允许时间差: {max_age_minutes}分钟"
        super().__init__(
            message, 
            details={"timestamp": timestamp, "max_age_minutes": max_age_minutes},
            **kwargs
        )
        self.timestamp = timestamp
        self.max_age_minutes = max_age_minutes

class InvalidUserError(GatewayException):
    """无效用户异常"""

    def __init__(self, access_key: str, **kwargs):
        message = f"无效的访问密钥: {access_key[:8]}..."
        super().__init__(message, details={"access_key": access_key}, **kwargs)
        self.access_key = access_key

class SignatureError(GatewayException):
    """签名错误异常"""

    def __init__(self, expected_signature: str, actual_signature: str, **kwargs):
        message = "签名验证失败"
        super().__init__(
            message, 
            details={
                "expected_signature": expected_signature[:16] + "...",
                "actual_signature": actual_signature[:16] + "..."
            },
            **kwargs
        )
        self.expected_signature = expected_signature
        self.actual_signature = actual_signature

class UnknownGatewayError(GatewayException):
    """未知网关错误异常"""

    def __init__(self, response_code: int, response_message: str, **kwargs):
        message = f"未知网关错误 [{response_code}]: {response_message}"
        super().__init__(
            message, 
            details={"response_code": response_code, "response_message": response_message},
            **kwargs
        )
        self.response_code = response_code
        self.response_message = response_message


# ============================================================================
# 数据库异常类 - Database Exceptions
# ============================================================================

class DatabaseException(MedicalInsuranceException):
    """数据库异常基类"""

    def __init__(self, message: str, sql: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="DATABASE_ERROR", 
            details={"sql": sql},
            **kwargs
        )
        self.sql = sql

class ConnectionPoolException(DatabaseException):
    """连接池异常"""
    
    def __init__(self, pool_name: str, reason: str, **kwargs):
        message = f"数据库连接池 '{pool_name}' 异常: {reason}"
        super().__init__(message, retry_after=5, **kwargs)
        self.pool_name = pool_name
        self.reason = reason

class QueryExecutionException(DatabaseException):
    """查询执行异常"""
    
    def __init__(self, sql: str, error_details: str, **kwargs):
        message = f"SQL查询执行失败: {error_details}"
        super().__init__(message, sql=sql, **kwargs)
        self.error_details = error_details

class TransactionException(DatabaseException):
    """事务异常"""
    
    def __init__(self, operation: str, reason: str, **kwargs):
        message = f"事务{operation}失败: {reason}"
        super().__init__(message, **kwargs)
        self.operation = operation
        self.reason = reason

class DataIntegrityException(DatabaseException):
    """数据完整性异常"""
    
    def __init__(self, constraint_name: str, table_name: str, **kwargs):
        message = f"数据完整性约束违反: {constraint_name} (表: {table_name})"
        super().__init__(
            message, 
            details={"constraint_name": constraint_name, "table_name": table_name},
            **kwargs
        )
        self.constraint_name = constraint_name
        self.table_name = table_name


# ============================================================================
# 数据处理异常类 - Data Processing Exceptions
# ============================================================================

class DataParsingException(MedicalInsuranceException):
    """数据解析异常基类"""

    def __init__(self, message: str, parsing_context: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message, 
            error_code="DATA_PARSING_ERROR", 
            details={"parsing_context": parsing_context or {}},
            **kwargs
        )
        self.parsing_context = parsing_context or {}

class JSONParsingException(DataParsingException):
    """JSON解析异常"""
    
    def __init__(self, json_data: str, error_details: str, **kwargs):
        message = f"JSON解析失败: {error_details}"
        super().__init__(
            message, 
            parsing_context={"json_data": json_data[:200] + "..." if len(json_data) > 200 else json_data},
            **kwargs
        )
        self.json_data = json_data
        self.error_details = error_details

class ResponseMappingException(DataParsingException):
    """响应映射异常"""
    
    def __init__(self, field_path: str, response_data: Dict[str, Any], **kwargs):
        message = f"响应数据映射失败，字段路径: {field_path}"
        super().__init__(
            message, 
            parsing_context={"field_path": field_path, "response_data": response_data},
            **kwargs
        )
        self.field_path = field_path
        self.response_data = response_data

class DataTransformException(DataParsingException):
    """数据转换异常"""
    
    def __init__(self, transform_type: str, input_value: Any, error_details: str, **kwargs):
        message = f"数据转换失败 ({transform_type}): {error_details}"
        super().__init__(
            message, 
            parsing_context={
                "transform_type": transform_type, 
                "input_value": input_value, 
                "error_details": error_details
            },
            **kwargs
        )
        self.transform_type = transform_type
        self.input_value = input_value
        self.error_details = error_details

# ============================================================================
# 接口处理异常类 - Interface Processing Exceptions
# ============================================================================

class InterfaceProcessingException(MedicalInsuranceException):
    """接口处理异常基类"""

    def __init__(self, message: str, api_code: Optional[str] = None, processing_stage: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="INTERFACE_PROCESSING_ERROR", 
            details={"api_code": api_code, "processing_stage": processing_stage},
            **kwargs
        )
        self.api_code = api_code
        self.processing_stage = processing_stage

class InterfaceNotSupportedException(InterfaceProcessingException):
    """接口不支持异常"""
    
    def __init__(self, api_code: str, **kwargs):
        message = f"不支持的接口: {api_code}"
        super().__init__(message, api_code=api_code, processing_stage="validation", **kwargs)

class InterfaceDisabledException(InterfaceProcessingException):
    """接口已禁用异常"""
    
    def __init__(self, api_code: str, reason: str = "接口已被管理员禁用", **kwargs):
        message = f"接口 {api_code} 已禁用: {reason}"
        super().__init__(message, api_code=api_code, processing_stage="validation", **kwargs)
        self.reason = reason

class RequestBuildException(InterfaceProcessingException):
    """请求构建异常"""
    
    def __init__(self, api_code: str, build_error: str, **kwargs):
        message = f"构建接口 {api_code} 请求失败: {build_error}"
        super().__init__(message, api_code=api_code, processing_stage="request_build", **kwargs)
        self.build_error = build_error

class ResponseParseException(InterfaceProcessingException):
    """响应解析异常"""
    
    def __init__(self, api_code: str, parse_error: str, response_data: Optional[Dict[str, Any]] = None, **kwargs):
        message = f"解析接口 {api_code} 响应失败: {parse_error}"
        super().__init__(
            message, 
            api_code=api_code, 
            processing_stage="response_parse",
            details={"parse_error": parse_error, "response_data": response_data},
            **kwargs
        )
        self.parse_error = parse_error
        self.response_data = response_data


# ============================================================================
# 协议异常类 - Protocol Exceptions
# ============================================================================

class ProtocolException(MedicalInsuranceException):
    """协议异常基类"""

    def __init__(self, message: str, protocol_stage: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="PROTOCOL_ERROR", 
            details={"protocol_stage": protocol_stage},
            **kwargs
        )
        self.protocol_stage = protocol_stage

class InvalidRequestException(ProtocolException):
    """无效请求异常"""

    def __init__(self, message: str, request_data: Optional[Dict[str, Any]] = None, **kwargs):
        # 避免details参数冲突
        details = kwargs.pop('details', {})
        details.update({"request_data": request_data})
        
        super().__init__(
            message, 
            protocol_stage="request_validation",
            **kwargs
        )
        # 手动设置details以避免冲突
        self.details.update(details)
        self.request_data = request_data

class InvalidResponseException(ProtocolException):
    """无效响应异常"""

    def __init__(self, message: str, response_data: Optional[Dict[str, Any]] = None, **kwargs):
        # 避免details参数冲突
        details = kwargs.pop('details', {})
        details.update({"response_data": response_data})
        
        super().__init__(
            message, 
            protocol_stage="response_validation",
            **kwargs
        )
        # 手动设置details以避免冲突
        self.details.update(details)
        self.response_data = response_data

class MessageIdGenerationException(ProtocolException):
    """报文ID生成异常"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, protocol_stage="message_id_generation", **kwargs)

class EncryptionException(ProtocolException):
    """加密异常"""
    
    def __init__(self, operation: str, algorithm: str, error_details: str, **kwargs):
        message = f"{operation}失败 (算法: {algorithm}): {error_details}"
        super().__init__(
            message, 
            protocol_stage="encryption",
            details={"operation": operation, "algorithm": algorithm, "error_details": error_details},
            **kwargs
        )
        self.operation = operation
        self.algorithm = algorithm
        self.error_details = error_details

class SignatureException(ProtocolException):
    """签名异常"""
    
    def __init__(self, operation: str, signature_type: str, error_details: str, **kwargs):
        message = f"签名{operation}失败 (类型: {signature_type}): {error_details}"
        super().__init__(
            message, 
            protocol_stage="signature",
            details={"operation": operation, "signature_type": signature_type, "error_details": error_details},
            **kwargs
        )
        self.operation = operation
        self.signature_type = signature_type
        self.error_details = error_details


# ============================================================================
# 缓存异常类 - Cache Exceptions
# ============================================================================

class CacheException(MedicalInsuranceException):
    """缓存异常基类"""

    def __init__(self, message: str, cache_operation: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="CACHE_ERROR", 
            details={"cache_operation": cache_operation},
            **kwargs
        )
        self.cache_operation = cache_operation

class CacheConnectionException(CacheException):
    """缓存连接异常"""
    
    def __init__(self, cache_type: str, connection_details: str, **kwargs):
        message = f"无法连接到{cache_type}缓存: {connection_details}"
        super().__init__(message, cache_operation="connection", retry_after=10, **kwargs)
        self.cache_type = cache_type
        self.connection_details = connection_details

class CacheKeyException(CacheException):
    """缓存键异常"""
    
    def __init__(self, cache_key: str, operation: str, reason: str, **kwargs):
        message = f"缓存键 '{cache_key}' {operation}失败: {reason}"
        super().__init__(message, cache_operation=operation, **kwargs)
        self.cache_key = cache_key
        self.operation = operation
        self.reason = reason

class CacheSerializationException(CacheException):
    """缓存序列化异常"""
    
    def __init__(self, operation: str, data_type: str, error_details: str, **kwargs):
        message = f"缓存数据{operation}失败 (类型: {data_type}): {error_details}"
        super().__init__(message, cache_operation=operation, **kwargs)
        self.operation = operation
        self.data_type = data_type
        self.error_details = error_details

# ============================================================================
# 集成异常类 - Integration Exceptions
# ============================================================================

class IntegrationException(MedicalInsuranceException):
    """集成异常基类"""
    
    def __init__(self, message: str, integration_type: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="INTEGRATION_ERROR",
            details={"integration_type": integration_type},
            **kwargs
        )
        self.integration_type = integration_type

class HISIntegrationException(IntegrationException):
    """HIS系统集成异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, integration_type="HIS", **kwargs)
        self.operation = operation

class DataSyncException(IntegrationException):
    """数据同步异常"""
    
    def __init__(self, message: str, sync_direction: Optional[str] = None, table_name: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            integration_type="DataSync",
            details={"sync_direction": sync_direction, "table_name": table_name},
            **kwargs
        )
        self.sync_direction = sync_direction
        self.table_name = table_name

class ConflictResolutionException(IntegrationException):
    """冲突解决异常"""
    
    def __init__(self, message: str, conflict_id: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            integration_type="ConflictResolution",
            details={"conflict_id": conflict_id},
            **kwargs
        )
        self.conflict_id = conflict_id

# ============================================================================
# 异步处理异常类 - Async Processing Exceptions
# ============================================================================

class AsyncProcessingException(MedicalInsuranceException):
    """异步处理异常基类"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, **kwargs):
        super().__init__(
            message, 
            error_code="ASYNC_PROCESSING_ERROR",
            details={"task_id": task_id},
            **kwargs
        )
        self.task_id = task_id

class TaskExecutionException(AsyncProcessingException):
    """任务执行异常"""
    
    def __init__(self, task_id: str, task_name: str, error_details: str, **kwargs):
        message = f"异步任务 '{task_name}' 执行失败: {error_details}"
        super().__init__(message, task_id=task_id, **kwargs)
        self.task_name = task_name
        self.error_details = error_details

class TaskTimeoutException(AsyncProcessingException):
    """任务超时异常"""
    
    def __init__(self, task_id: str, timeout_seconds: int, **kwargs):
        message = f"异步任务超时 (任务ID: {task_id}, 超时时间: {timeout_seconds}秒)"
        super().__init__(message, task_id=task_id, **kwargs)
        self.timeout_seconds = timeout_seconds

class TaskNotFoundException(AsyncProcessingException):
    """任务未找到异常"""
    
    def __init__(self, task_id: str, **kwargs):
        message = f"未找到异步任务: {task_id}"
        super().__init__(message, task_id=task_id, **kwargs)

# ============================================================================
# 系统异常类 - System Exceptions
# ============================================================================

class SystemException(MedicalInsuranceException):
    """系统异常基类"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="SYSTEM_ERROR", severity="CRITICAL", **kwargs)

class ResourceExhaustedException(SystemException):
    """资源耗尽异常"""
    
    def __init__(self, resource_type: str, current_usage: str, limit: str, **kwargs):
        message = f"{resource_type}资源耗尽 (当前: {current_usage}, 限制: {limit})"
        super().__init__(
            message, 
            details={"resource_type": resource_type, "current_usage": current_usage, "limit": limit},
            **kwargs
        )
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit

class ServiceUnavailableException(SystemException):
    """服务不可用异常"""
    
    def __init__(self, service_name: str, reason: str, **kwargs):
        message = f"服务 '{service_name}' 不可用: {reason}"
        super().__init__(message, retry_after=30, **kwargs)
        self.service_name = service_name
        self.reason = reason

class CircuitBreakerException(SystemException):
    """熔断器异常"""
    
    def __init__(self, service_name: str, failure_count: int, threshold: int, **kwargs):
        message = f"服务 '{service_name}' 熔断器开启 (失败次数: {failure_count}/{threshold})"
        super().__init__(
            message, 
            details={"service_name": service_name, "failure_count": failure_count, "threshold": threshold},
            retry_after=60,
            **kwargs
        )
        self.service_name = service_name
        self.failure_count = failure_count
        self.threshold = threshold

# ============================================================================
# 异常工厂类 - Exception Factory
# ============================================================================

class ExceptionFactory:
    """异常工厂类，用于根据错误代码创建相应的异常"""
    
    # 错误代码到异常类的映射
    ERROR_CODE_MAPPING = {
        # 验证异常
        "REQUIRED_FIELD": RequiredFieldException,
        "FIELD_FORMAT": FieldFormatException,
        "FIELD_LENGTH": FieldLengthException,
        "ENUM_VALUE": EnumValueException,
        
        # 配置异常
        "MISSING_CONFIG": MissingConfigException,
        "INVALID_CONFIG": InvalidConfigException,
        "INTERFACE_CONFIG": InterfaceConfigException,
        "ORGANIZATION_CONFIG": OrganizationConfigException,
        
        # 网络异常
        "CONNECTION_ERROR": ConnectionException,
        "TIMEOUT_ERROR": TimeoutException,
        "HTTP_ERROR": HTTPException,
        "TOO_MANY_REQUESTS": TooManyRequestsException,
        
        # 认证异常
        "INVALID_CREDENTIALS": InvalidCredentialsException,
        "TOKEN_EXPIRED": TokenExpiredException,
        "INSUFFICIENT_PERMISSIONS": InsufficientPermissionsException,
        
        # 网关异常
        "MISSING_HEADERS": MissingHeadersError,
        "TIMESTAMP_EXPIRED": TimestampExpiredError,
        "INVALID_USER": InvalidUserError,
        "SIGNATURE_ERROR": SignatureError,
        
        # 数据库异常
        "CONNECTION_POOL": ConnectionPoolException,
        "QUERY_EXECUTION": QueryExecutionException,
        "TRANSACTION_ERROR": TransactionException,
        
        # 集成异常
        "INTEGRATION_ERROR": IntegrationException,
        "HIS_INTEGRATION": HISIntegrationException,
        "DATA_SYNC": DataSyncException,
        "CONFLICT_RESOLUTION": ConflictResolutionException,
        "DATA_INTEGRITY": DataIntegrityException,
        
        # 数据处理异常
        "JSON_PARSING": JSONParsingException,
        "RESPONSE_MAPPING": ResponseMappingException,
        "DATA_TRANSFORM": DataTransformException,
        
        # 接口处理异常
        "INTERFACE_NOT_SUPPORTED": InterfaceNotSupportedException,
        "INTERFACE_DISABLED": InterfaceDisabledException,
        "REQUEST_BUILD": RequestBuildException,
        "RESPONSE_PARSE": ResponseParseException,
        
        # 协议异常
        "INVALID_REQUEST": InvalidRequestException,
        "INVALID_RESPONSE": InvalidResponseException,
        "MESSAGE_ID_GENERATION": MessageIdGenerationException,
        "ENCRYPTION_ERROR": EncryptionException,
        "SIGNATURE_ERROR": SignatureException,
        
        # 缓存异常
        "CACHE_CONNECTION": CacheConnectionException,
        "CACHE_KEY": CacheKeyException,
        "CACHE_SERIALIZATION": CacheSerializationException,
        
        # 异步处理异常
        "TASK_EXECUTION": TaskExecutionException,
        "TASK_TIMEOUT": TaskTimeoutException,
        "TASK_NOT_FOUND": TaskNotFoundException,
        
        # 系统异常
        "RESOURCE_EXHAUSTED": ResourceExhaustedException,
        "SERVICE_UNAVAILABLE": ServiceUnavailableException,
        "CIRCUIT_BREAKER": CircuitBreakerException
    }
    
    @classmethod
    def create_exception(
        cls, 
        error_code: str, 
        message: str, 
        **kwargs
    ) -> MedicalInsuranceException:
        """根据错误代码创建异常"""
        exception_class = cls.ERROR_CODE_MAPPING.get(error_code, MedicalInsuranceException)
        
        try:
            return exception_class(message, **kwargs)
        except TypeError:
            # 如果参数不匹配，使用基础异常类
            return MedicalInsuranceException(
                message, 
                error_code=error_code, 
                details=kwargs
            )
    
    @classmethod
    def from_medical_response(cls, response_data: Dict[str, Any]) -> MedicalInsuranceException:
        """从医保接口响应创建异常"""
        infcode = response_data.get('infcode', -1)
        err_msg = response_data.get('err_msg', '未知错误')
        
        if infcode == -1:
            return InvalidResponseException(
                f"医保接口返回错误: {err_msg}",
                response_data=response_data
            )
        else:
            return MedicalInsuranceException(
                f"医保接口业务错误 [{infcode}]: {err_msg}",
                error_code=f"MEDICAL_INTERFACE_{infcode}",
                details={"infcode": infcode, "response_data": response_data}
            )
    
    @classmethod
    def from_http_error(cls, status_code: int, reason: str, url: str) -> NetworkException:
        """从HTTP错误创建异常"""
        if status_code == 429:
            return TooManyRequestsException(url=url)
        elif status_code in [500, 502, 503, 504]:
            return HTTPException(status_code, reason, url, retry_after=5)
        else:
            return HTTPException(status_code, reason, url)
    
    @classmethod
    def from_validation_errors(cls, field_errors: Dict[str, List[str]]) -> ValidationException:
        """从字段验证错误创建异常"""
        error_messages = []
        for field, errors in field_errors.items():
            error_messages.extend(errors)
        
        message = f"数据验证失败: {'; '.join(error_messages)}"
        return ValidationException(message, field_errors=field_errors)
    
    @classmethod
    def from_database_error(cls, error: Exception, sql: Optional[str] = None) -> DatabaseException:
        """从数据库错误创建异常"""
        error_message = str(error)
        
        if "connection" in error_message.lower():
            return ConnectionPoolException("default", error_message)
        elif "timeout" in error_message.lower():
            return QueryExecutionException(sql or "", f"查询超时: {error_message}")
        elif "constraint" in error_message.lower():
            return DataIntegrityException("unknown_constraint", "unknown_table")
        else:
            return QueryExecutionException(sql or "", error_message)
    
    @classmethod
    def wrap_exception(cls, exception: Exception, context: Optional[Dict[str, Any]] = None) -> MedicalInsuranceException:
        """包装普通异常为医保SDK异常"""
        if isinstance(exception, MedicalInsuranceException):
            return exception
        
        context = context or {}
        
        # 根据异常类型进行转换
        if isinstance(exception, ConnectionError):
            return ConnectionException(str(exception), cause=exception)
        elif isinstance(exception, TimeoutError):
            return TimeoutException(30, cause=exception)
        elif isinstance(exception, ValueError):
            return ValidationException(str(exception), cause=exception)
        elif isinstance(exception, KeyError):
            return ConfigurationException(f"缺少必需的配置项: {exception}", cause=exception)
        else:
            return MedicalInsuranceException(
                str(exception),
                error_code="WRAPPED_EXCEPTION",
                details=context,
                cause=exception
            )


# ============================================================================
# 异常处理辅助函数
# ============================================================================

def handle_medical_interface_exception(func):
    """医保接口异常处理装饰器"""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MedicalInsuranceException:
            # 已经是医保SDK异常，直接抛出
            raise
        except Exception as e:
            # 包装为医保SDK异常
            wrapped_exception = ExceptionFactory.wrap_exception(e, {
                "function": func.__name__,
                "args": str(args)[:200],
                "kwargs": {k: str(v)[:100] for k, v in kwargs.items()}
            })
            raise wrapped_exception
    
    return wrapper


def create_validation_exception_from_errors(errors: Dict[str, Any]) -> ValidationException:
    """从验证错误字典创建验证异常"""
    field_errors = {}
    
    for field, error_info in errors.items():
        if isinstance(error_info, list):
            field_errors[field] = error_info
        elif isinstance(error_info, str):
            field_errors[field] = [error_info]
        else:
            field_errors[field] = [str(error_info)]
    
    return ExceptionFactory.from_validation_errors(field_errors)


def is_retryable_exception(exception: Exception) -> bool:
    """判断异常是否可重试"""
    if isinstance(exception, MedicalInsuranceException):
        return exception.is_retryable()
    
    # 网络相关异常通常可重试
    retryable_types = [
        ConnectionError,
        TimeoutError,
        OSError  # 包括网络相关的OSError
    ]
    
    return any(isinstance(exception, exc_type) for exc_type in retryable_types)


def get_exception_severity(exception: Exception) -> str:
    """获取异常严重程度"""
    if isinstance(exception, MedicalInsuranceException):
        return exception.severity
    
    # 系统级异常通常是严重的
    critical_types = [
        SystemError,
        MemoryError,
        KeyboardInterrupt,
        SystemExit
    ]
    
    if any(isinstance(exception, exc_type) for exc_type in critical_types):
        return "CRITICAL"
    
    return "ERROR"


# ============================================================================
# 导出的异常类列表
# ============================================================================

__all__ = [
    # 基础异常
    'MedicalInsuranceException',
    
    # 业务异常
    'BusinessException',
    'ValidationException',
    'RequiredFieldException',
    'FieldFormatException',
    'FieldLengthException',
    'EnumValueException',
    'ConditionalValidationException',
    
    # 配置异常
    'ConfigurationException',
    'MissingConfigException',
    'InvalidConfigException',
    'InterfaceConfigException',
    'OrganizationConfigException',
    
    # 网络异常
    'NetworkException',
    'ConnectionException',
    'TimeoutException',
    'HTTPException',
    'TooManyRequestsException',
    
    # 认证异常
    'AuthenticationException',
    'InvalidCredentialsException',
    'TokenExpiredException',
    'InsufficientPermissionsException',
    
    # 网关异常
    'GatewayException',
    'MissingHeadersError',
    'TimestampExpiredError',
    'InvalidUserError',
    'SignatureError',
    'UnknownGatewayError',
    
    # 数据库异常
    'DatabaseException',
    'ConnectionPoolException',
    'QueryExecutionException',
    'TransactionException',
    'DataIntegrityException',
    
    # 数据处理异常
    'DataParsingException',
    'JSONParsingException',
    'ResponseMappingException',
    'DataTransformException',
    
    # 接口处理异常
    'InterfaceProcessingException',
    'InterfaceNotSupportedException',
    'InterfaceDisabledException',
    'RequestBuildException',
    'ResponseParseException',
    
    # 协议异常
    'ProtocolException',
    'InvalidRequestException',
    'InvalidResponseException',
    'MessageIdGenerationException',
    'EncryptionException',
    'SignatureException',
    
    # 缓存异常
    'CacheException',
    'CacheConnectionException',
    'CacheKeyException',
    'CacheSerializationException',
    
    # 异步处理异常
    'AsyncProcessingException',
    'TaskExecutionException',
    'TaskTimeoutException',
    'TaskNotFoundException',
    
    # 系统异常
    'SystemException',
    'ResourceExhaustedException',
    'ServiceUnavailableException',
    'CircuitBreakerException',
    
    # 工厂类和辅助函数
    'ExceptionFactory',
    'handle_medical_interface_exception',
    'create_validation_exception_from_errors',
    'is_retryable_exception',
    'get_exception_severity'
]
