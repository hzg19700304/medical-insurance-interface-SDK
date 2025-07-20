"""操作日志模型"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class OperationLog:
    """操作日志模型"""

    operation_id: str
    api_code: str
    api_name: str
    business_category: str
    business_type: str
    institution_code: str
    psn_no: Optional[str] = None
    mdtrt_id: Optional[str] = None
    request_data: Dict[str, Any] = None
    response_data: Optional[Dict[str, Any]] = None
    status: str = "pending"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    operation_time: datetime = None
    complete_time: Optional[datetime] = None
    operator_id: Optional[str] = None
    trace_id: str = ""
    client_ip: str = ""

    def __post_init__(self):
        """初始化后处理"""
        if self.request_data is None:
            self.request_data = {}
        if self.operation_time is None:
            self.operation_time = datetime.now()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationLog":
        """从字典创建操作日志对象"""
        from datetime import datetime
        
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            """解析日期时间字符串"""
            if not dt_str:
                return None
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        
        return cls(
            operation_id=data.get("operation_id", ""),
            api_code=data.get("api_code", ""),
            api_name=data.get("api_name", ""),
            business_category=data.get("business_category", ""),
            business_type=data.get("business_type", ""),
            institution_code=data.get("institution_code", ""),
            psn_no=data.get("psn_no"),
            mdtrt_id=data.get("mdtrt_id"),
            request_data=data.get("request_data", {}),
            response_data=data.get("response_data"),
            status=data.get("status", "pending"),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            operation_time=parse_datetime(data.get("operation_time")),
            complete_time=parse_datetime(data.get("complete_time")),
            operator_id=data.get("operator_id"),
            trace_id=data.get("trace_id", ""),
            client_ip=data.get("client_ip", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "operation_id": self.operation_id,
            "api_code": self.api_code,
            "api_name": self.api_name,
            "business_category": self.business_category,
            "business_type": self.business_type,
            "institution_code": self.institution_code,
            "psn_no": self.psn_no,
            "mdtrt_id": self.mdtrt_id,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "status": self.status,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "operation_time": (
                self.operation_time.isoformat() if self.operation_time else None
            ),
            "complete_time": (
                self.complete_time.isoformat() if self.complete_time else None
            ),
            "operator_id": self.operator_id,
            "trace_id": self.trace_id,
            "client_ip": self.client_ip,
        }

    def is_success(self) -> bool:
        """判断操作是否成功"""
        return self.status == "success"

    def is_failed(self) -> bool:
        """判断操作是否失败"""
        return self.status == "failed"

    def is_pending(self) -> bool:
        """判断操作是否待处理"""
        return self.status == "pending"

    def is_processing(self) -> bool:
        """判断操作是否处理中"""
        return self.status == "processing"

    def mark_success(self, response_data: Optional[Dict[str, Any]] = None):
        """标记操作成功"""
        self.status = "success"
        self.complete_time = datetime.now()
        if response_data:
            self.response_data = response_data
        self.error_code = None
        self.error_message = None

    def mark_failed(self, error_code: str, error_message: str):
        """标记操作失败"""
        self.status = "failed"
        self.complete_time = datetime.now()
        self.error_code = error_code
        self.error_message = error_message

    def mark_processing(self):
        """标记操作处理中"""
        self.status = "processing"

    def get_duration_seconds(self) -> Optional[float]:
        """获取操作持续时间（秒）"""
        if not self.operation_time:
            return None
        
        end_time = self.complete_time or datetime.now()
        duration = end_time - self.operation_time
        return duration.total_seconds()

    def get_summary(self) -> Dict[str, Any]:
        """获取操作摘要信息"""
        return {
            "operation_id": self.operation_id,
            "api_code": self.api_code,
            "api_name": self.api_name,
            "status": self.status,
            "institution_code": self.institution_code,
            "operation_time": self.operation_time.isoformat() if self.operation_time else None,
            "duration_seconds": self.get_duration_seconds(),
            "has_error": bool(self.error_code),
            "trace_id": self.trace_id
        }
