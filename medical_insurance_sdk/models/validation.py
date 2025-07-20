"""验证结果模型"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ValidationResult:
    """验证结果类"""
    
    is_valid: bool = True
    errors: Dict[str, List[str]] = field(default_factory=dict)
    warnings: Dict[str, List[str]] = field(default_factory=dict)
    validated_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, field: str, message: str):
        """添加错误信息"""
        self.is_valid = False
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)
    
    def add_warning(self, field: str, message: str):
        """添加警告信息"""
        if field not in self.warnings:
            self.warnings[field] = []
        self.warnings[field].append(message)
    
    def get_error_messages(self) -> List[str]:
        """获取所有错误信息"""
        messages = []
        for field, field_errors in self.errors.items():
            for error in field_errors:
                messages.append(f"{field}: {error}")
        return messages
    
    def get_warning_messages(self) -> List[str]:
        """获取所有警告信息"""
        messages = []
        for field, field_warnings in self.warnings.items():
            for warning in field_warnings:
                messages.append(f"{field}: {warning}")
        return messages
    
    def get_field_errors(self, field: str) -> List[str]:
        """获取指定字段的错误信息"""
        return self.errors.get(field, [])
    
    def get_field_warnings(self, field: str) -> List[str]:
        """获取指定字段的警告信息"""
        return self.warnings.get(field, [])
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return not self.is_valid
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return bool(self.warnings)
    
    def clear_errors(self):
        """清除所有错误"""
        self.errors.clear()
        self.is_valid = True
    
    def clear_warnings(self):
        """清除所有警告"""
        self.warnings.clear()
    
    def clear_field_errors(self, field: str):
        """清除指定字段的错误"""
        if field in self.errors:
            del self.errors[field]
        # 重新检查是否还有其他错误
        self.is_valid = len(self.errors) == 0
    
    def merge(self, other: 'ValidationResult'):
        """合并另一个验证结果"""
        if not other.is_valid:
            self.is_valid = False
        
        # 合并错误
        for field, field_errors in other.errors.items():
            if field not in self.errors:
                self.errors[field] = []
            self.errors[field].extend(field_errors)
        
        # 合并警告
        for field, field_warnings in other.warnings.items():
            if field not in self.warnings:
                self.warnings[field] = []
            self.warnings[field].extend(field_warnings)
        
        # 合并验证后的数据
        self.validated_data.update(other.validated_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'validated_data': self.validated_data,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """从字典创建验证结果对象"""
        result = cls()
        result.is_valid = data.get('is_valid', True)
        result.errors = data.get('errors', {})
        result.warnings = data.get('warnings', {})
        result.validated_data = data.get('validated_data', {})
        return result
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_valid:
            status = "Valid"
        else:
            status = f"Invalid ({len(self.errors)} errors)"
        
        if self.warnings:
            status += f" ({len(self.warnings)} warnings)"
        
        return f"ValidationResult: {status}"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"ValidationResult(is_valid={self.is_valid}, "
                f"errors={len(self.errors)}, warnings={len(self.warnings)})")


@dataclass
class FieldValidationRule:
    """字段验证规则"""
    
    field_name: str
    required: bool = False
    data_type: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None
    
    def validate(self, value: Any) -> ValidationResult:
        """验证字段值"""
        result = ValidationResult()
        
        # 检查必填
        if self.required and (value is None or value == ""):
            result.add_error(self.field_name, 
                           self.error_message or f"{self.field_name}不能为空")
            return result
        
        # 如果值为空且非必填，跳过其他验证
        if value is None or value == "":
            return result
        
        # 数据类型验证
        if self.data_type:
            if not self._validate_type(value):
                result.add_error(self.field_name, 
                               f"{self.field_name}数据类型不正确，期望{self.data_type}")
        
        # 长度验证
        if self.min_length is not None and len(str(value)) < self.min_length:
            result.add_error(self.field_name, 
                           f"{self.field_name}长度不能少于{self.min_length}位")
        
        if self.max_length is not None and len(str(value)) > self.max_length:
            result.add_error(self.field_name, 
                           f"{self.field_name}长度不能超过{self.max_length}位")
        
        # 正则验证
        if self.pattern:
            import re
            if not re.match(self.pattern, str(value)):
                result.add_error(self.field_name, 
                               self.error_message or f"{self.field_name}格式不正确")
        
        # 枚举值验证
        if self.enum_values and value not in self.enum_values:
            result.add_error(self.field_name, 
                           f"{self.field_name}必须是以下值之一: {', '.join(map(str, self.enum_values))}")
        
        # 自定义验证器
        if self.custom_validator:
            try:
                custom_result = self.custom_validator(value)
                if isinstance(custom_result, ValidationResult):
                    result.merge(custom_result)
                elif isinstance(custom_result, bool) and not custom_result:
                    result.add_error(self.field_name, 
                                   self.error_message or f"{self.field_name}验证失败")
            except Exception as e:
                result.add_error(self.field_name, f"{self.field_name}验证异常: {str(e)}")
        
        return result
    
    def _validate_type(self, value: Any) -> bool:
        """验证数据类型"""
        type_mapping = {
            'str': str,
            'string': str,
            'int': int,
            'integer': int,
            'float': float,
            'bool': bool,
            'boolean': bool,
            'list': list,
            'dict': dict
        }
        
        expected_type = type_mapping.get(self.data_type.lower())
        if expected_type:
            return isinstance(value, expected_type)
        
        return True  # 未知类型不验证