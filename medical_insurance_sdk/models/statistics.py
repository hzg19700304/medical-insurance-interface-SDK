"""统计数据模型"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Any, Optional


@dataclass
class InterfaceStatistics:
    """接口调用统计模型"""
    
    stat_date: date
    institution_code: str
    api_code: str
    api_name: str = ""
    business_category: str = ""
    business_type: str = ""
    total_calls: int = 0
    success_calls: int = 0
    failed_calls: int = 0
    pending_calls: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = 0.0
    error_rate: float = 0.0
    success_rate: float = 0.0
    error_types: Dict[str, int] = field(default_factory=dict)
    hourly_distribution: Dict[int, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        self.calculate_rates()
        if not self.hourly_distribution:
            self.hourly_distribution = {hour: 0 for hour in range(24)}

    def calculate_rates(self):
        """计算成功率和错误率"""
        if self.total_calls > 0:
            self.success_rate = round(self.success_calls / self.total_calls * 100, 2)
            self.error_rate = round(self.failed_calls / self.total_calls * 100, 2)
        else:
            self.success_rate = 0.0
            self.error_rate = 0.0

    def add_call_record(self, status: str, response_time: float, error_code: Optional[str] = None, call_hour: int = None):
        """添加调用记录"""
        self.total_calls += 1
        
        if status == "success":
            self.success_calls += 1
        elif status == "failed":
            self.failed_calls += 1
            if error_code:
                self.error_types[error_code] = self.error_types.get(error_code, 0) + 1
        elif status == "pending":
            self.pending_calls += 1
        
        # 更新响应时间统计
        if response_time > 0:
            if self.max_response_time == 0 or response_time > self.max_response_time:
                self.max_response_time = response_time
            if self.min_response_time == 0 or response_time < self.min_response_time:
                self.min_response_time = response_time
            
            # 重新计算平均响应时间
            total_response_time = self.avg_response_time * (self.total_calls - 1) + response_time
            self.avg_response_time = round(total_response_time / self.total_calls, 3)
        
        # 更新小时分布
        if call_hour is not None and 0 <= call_hour <= 23:
            self.hourly_distribution[call_hour] = self.hourly_distribution.get(call_hour, 0) + 1
        
        # 重新计算比率
        self.calculate_rates()
        self.updated_at = datetime.now()

    def get_peak_hours(self, top_n: int = 3) -> List[tuple]:
        """获取调用高峰时段"""
        sorted_hours = sorted(self.hourly_distribution.items(), key=lambda x: x[1], reverse=True)
        return sorted_hours[:top_n]

    def get_top_errors(self, top_n: int = 5) -> List[tuple]:
        """获取最常见的错误类型"""
        sorted_errors = sorted(self.error_types.items(), key=lambda x: x[1], reverse=True)
        return sorted_errors[:top_n]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "stat_date": self.stat_date.isoformat(),
            "institution_code": self.institution_code,
            "api_code": self.api_code,
            "api_name": self.api_name,
            "business_category": self.business_category,
            "business_type": self.business_type,
            "total_calls": self.total_calls,
            "success_calls": self.success_calls,
            "failed_calls": self.failed_calls,
            "pending_calls": self.pending_calls,
            "avg_response_time": self.avg_response_time,
            "max_response_time": self.max_response_time,
            "min_response_time": self.min_response_time,
            "error_rate": self.error_rate,
            "success_rate": self.success_rate,
            "error_types": self.error_types,
            "hourly_distribution": self.hourly_distribution,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterfaceStatistics":
        """从字典创建统计对象"""
        def parse_date(date_str: str) -> date:
            """解析日期字符串"""
            try:
                return datetime.fromisoformat(date_str).date()
            except (ValueError, AttributeError):
                return date.today()

        def parse_datetime(dt_str: str) -> datetime:
            """解析日期时间字符串"""
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return datetime.now()

        return cls(
            stat_date=parse_date(data.get("stat_date", "")),
            institution_code=data.get("institution_code", ""),
            api_code=data.get("api_code", ""),
            api_name=data.get("api_name", ""),
            business_category=data.get("business_category", ""),
            business_type=data.get("business_type", ""),
            total_calls=data.get("total_calls", 0),
            success_calls=data.get("success_calls", 0),
            failed_calls=data.get("failed_calls", 0),
            pending_calls=data.get("pending_calls", 0),
            avg_response_time=data.get("avg_response_time", 0.0),
            max_response_time=data.get("max_response_time", 0.0),
            min_response_time=data.get("min_response_time", 0.0),
            error_rate=data.get("error_rate", 0.0),
            success_rate=data.get("success_rate", 0.0),
            error_types=data.get("error_types", {}),
            hourly_distribution=data.get("hourly_distribution", {}),
            created_at=parse_datetime(data.get("created_at", "")),
            updated_at=parse_datetime(data.get("updated_at", ""))
        )


@dataclass
class SystemStatistics:
    """系统整体统计模型"""
    
    stat_date: date
    total_institutions: int = 0
    total_apis: int = 0
    total_calls: int = 0
    total_success: int = 0
    total_failed: int = 0
    overall_success_rate: float = 0.0
    overall_error_rate: float = 0.0
    avg_response_time: float = 0.0
    active_institutions: List[str] = field(default_factory=list)
    top_apis: List[Dict[str, Any]] = field(default_factory=list)
    top_errors: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        self.calculate_overall_rates()

    def calculate_overall_rates(self):
        """计算整体成功率和错误率"""
        if self.total_calls > 0:
            self.overall_success_rate = round(self.total_success / self.total_calls * 100, 2)
            self.overall_error_rate = round(self.total_failed / self.total_calls * 100, 2)
        else:
            self.overall_success_rate = 0.0
            self.overall_error_rate = 0.0

    def add_interface_stats(self, interface_stats: InterfaceStatistics):
        """添加接口统计数据"""
        self.total_calls += interface_stats.total_calls
        self.total_success += interface_stats.success_calls
        self.total_failed += interface_stats.failed_calls
        
        # 更新平均响应时间
        if interface_stats.avg_response_time > 0:
            total_response_time = self.avg_response_time * (self.total_calls - interface_stats.total_calls)
            total_response_time += interface_stats.avg_response_time * interface_stats.total_calls
            self.avg_response_time = round(total_response_time / self.total_calls, 3)
        
        # 添加活跃机构
        if interface_stats.institution_code not in self.active_institutions:
            self.active_institutions.append(interface_stats.institution_code)
        
        self.calculate_overall_rates()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "stat_date": self.stat_date.isoformat(),
            "total_institutions": self.total_institutions,
            "total_apis": self.total_apis,
            "total_calls": self.total_calls,
            "total_success": self.total_success,
            "total_failed": self.total_failed,
            "overall_success_rate": self.overall_success_rate,
            "overall_error_rate": self.overall_error_rate,
            "avg_response_time": self.avg_response_time,
            "active_institutions": self.active_institutions,
            "top_apis": self.top_apis,
            "top_errors": self.top_errors,
            "performance_metrics": self.performance_metrics,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemStatistics":
        """从字典创建系统统计对象"""
        def parse_date(date_str: str) -> date:
            """解析日期字符串"""
            try:
                return datetime.fromisoformat(date_str).date()
            except (ValueError, AttributeError):
                return date.today()

        def parse_datetime(dt_str: str) -> datetime:
            """解析日期时间字符串"""
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return datetime.now()

        return cls(
            stat_date=parse_date(data.get("stat_date", "")),
            total_institutions=data.get("total_institutions", 0),
            total_apis=data.get("total_apis", 0),
            total_calls=data.get("total_calls", 0),
            total_success=data.get("total_success", 0),
            total_failed=data.get("total_failed", 0),
            overall_success_rate=data.get("overall_success_rate", 0.0),
            overall_error_rate=data.get("overall_error_rate", 0.0),
            avg_response_time=data.get("avg_response_time", 0.0),
            active_institutions=data.get("active_institutions", []),
            top_apis=data.get("top_apis", []),
            top_errors=data.get("top_errors", []),
            performance_metrics=data.get("performance_metrics", {}),
            created_at=parse_datetime(data.get("created_at", ""))
        )