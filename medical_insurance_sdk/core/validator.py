"""
配置驱动的数据验证器
支持必填字段、格式规则、条件依赖验证
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .config_manager import ConfigManager
from .rule_engine import ValidationRuleEngine, FieldRuleValidator, DataTransformer, ConditionalRuleEngine
from ..models.config import InterfaceConfig
from ..models.validation import ValidationResult, FieldValidationRule
from ..exceptions import ValidationException


class DataValidator:
    """配置驱动的数据验证器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.rule_engine = ValidationRuleEngine()
    
    def validate_input_data(self, api_code: str, input_data: dict, org_code: str = None) -> ValidationResult:
        """根据接口配置验证输入数据"""
        try:
            # 获取接口配置
            interface_config = self.config_manager.get_interface_config(api_code, org_code)
            
            # 构建验证规则
            validation_rules = {
                'field_rules': {},
                'conditional_rules': interface_config.validation_rules.get('conditional_rules', []),
                'data_transforms': interface_config.validation_rules.get('data_transforms', {})
            }
            
            # 合并必填字段规则
            for field_name, field_config in interface_config.required_params.items():
                validation_rules['field_rules'][field_name] = {
                    'required': True,
                    'display_name': field_config.get('display_name', field_name),
                    'description': field_config.get('description', '')
                }
            
            # 合并字段验证规则
            for field_name, field_rules in interface_config.validation_rules.items():
                if field_name not in ['conditional_rules', 'data_transforms']:
                    if field_name in validation_rules['field_rules']:
                        validation_rules['field_rules'][field_name].update(field_rules)
                    else:
                        validation_rules['field_rules'][field_name] = field_rules
            
            # 执行数据验证
            validation_result = ValidationResult()
            
            # 验证必填字段
            self._validate_required_fields(input_data, interface_config.required_params, validation_result)
            
            # 验证字段规则
            self._validate_field_rules(input_data, validation_rules['field_rules'], validation_result)
            
            # 验证条件依赖规则
            self._validate_conditional_rules(input_data, validation_rules, validation_result)
            
            self.logger.debug(f"接口 {api_code} 数据验证完成，结果: {validation_result.is_valid}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"数据验证过程中发生错误: {e}")
            result = ValidationResult()
            result.add_error("system", f"验证过程异常: {str(e)}")
            return result
    
    def _validate_required_fields(self, data: dict, required_params: Dict[str, Any], result: ValidationResult):
        """验证必填字段"""
        for field_name, field_config in required_params.items():
            if field_name not in data or self._is_empty_value(data[field_name]):
                display_name = field_config.get('display_name', field_name)
                description = field_config.get('description', '')
                error_msg = f"{display_name}不能为空"
                if description:
                    error_msg += f" ({description})"
                result.add_error(field_name, error_msg)
    
    def _validate_field_rules(self, data: dict, validation_rules: Dict[str, Any], result: ValidationResult):
        """验证字段规则"""
        for field_name, field_value in data.items():
            if field_name in validation_rules:
                rules = validation_rules[field_name]
                self._apply_field_rules(field_name, field_value, rules, result)
    
    def _validate_conditional_rules(self, data: dict, validation_rules: Dict[str, Any], result: ValidationResult):
        """验证条件依赖规则"""
        conditional_rules = validation_rules.get('conditional_rules', [])
        for rule in conditional_rules:
            condition = rule.get('condition')
            if self._evaluate_condition(condition, data):
                # 条件满足，检查必填字段
                required_fields = rule.get('required_fields', [])
                for field in required_fields:
                    if field not in data or self._is_empty_value(data[field]):
                        error_message = rule.get('error_message', f"{field}在当前条件下不能为空")
                        result.add_error(field, error_message)
    
    def _apply_field_rules(self, field_name: str, field_value: Any, rules: dict, result: ValidationResult):
        """应用字段验证规则"""
        # 如果值为空，跳过格式验证（必填验证已在前面处理）
        if self._is_empty_value(field_value):
            return
        
        field_value_str = str(field_value)
        
        # 长度验证
        if 'max_length' in rules:
            max_length = rules['max_length']
            if len(field_value_str) > max_length:
                result.add_error(field_name, f"{field_name}长度不能超过{max_length}位")
        
        if 'min_length' in rules:
            min_length = rules['min_length']
            if len(field_value_str) < min_length:
                result.add_error(field_name, f"{field_name}长度不能少于{min_length}位")
        
        # 正则验证
        if 'pattern' in rules:
            pattern = rules['pattern']
            if not re.match(pattern, field_value_str):
                error_msg = rules.get('pattern_error', f"{field_name}格式不正确")
                result.add_error(field_name, error_msg)
        
        # 枚举值验证
        if 'enum_values' in rules:
            enum_values = rules['enum_values']
            if field_value not in enum_values:
                result.add_error(field_name, f"{field_name}必须是以下值之一: {', '.join(map(str, enum_values))}")
        
        # 数值范围验证
        if 'min_value' in rules or 'max_value' in rules:
            try:
                numeric_value = float(field_value)
                if 'min_value' in rules and numeric_value < rules['min_value']:
                    result.add_error(field_name, f"{field_name}不能小于{rules['min_value']}")
                if 'max_value' in rules and numeric_value > rules['max_value']:
                    result.add_error(field_name, f"{field_name}不能大于{rules['max_value']}")
            except (ValueError, TypeError):
                if 'min_value' in rules or 'max_value' in rules:
                    result.add_error(field_name, f"{field_name}必须是有效的数值")
        
        # 日期格式验证
        if 'date_format' in rules:
            date_format = rules['date_format']
            try:
                datetime.strptime(field_value_str, date_format)
            except ValueError:
                result.add_error(field_name, f"{field_name}日期格式不正确，应为{date_format}")
        
        # 自定义验证函数
        if 'custom_validator' in rules:
            custom_validator = rules['custom_validator']
            if callable(custom_validator):
                try:
                    is_valid = custom_validator(field_value)
                    if not is_valid:
                        error_msg = rules.get('custom_error', f"{field_name}验证失败")
                        result.add_error(field_name, error_msg)
                except Exception as e:
                    result.add_error(field_name, f"{field_name}自定义验证异常: {str(e)}")
    
    def _evaluate_condition(self, condition: dict, data: dict) -> bool:
        """评估条件表达式"""
        if not condition:
            return False
        
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if field not in data:
            return False
        
        field_value = data[field]
        
        if operator == 'eq':
            return field_value == value
        elif operator == 'ne':
            return field_value != value
        elif operator == 'in':
            return field_value in value if isinstance(value, (list, tuple)) else False
        elif operator == 'not_in':
            return field_value not in value if isinstance(value, (list, tuple)) else True
        elif operator == 'not_empty':
            return not self._is_empty_value(field_value)
        elif operator == 'empty':
            return self._is_empty_value(field_value)
        elif operator == 'gt':
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'gte':
            try:
                return float(field_value) >= float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'lt':
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'lte':
            try:
                return float(field_value) <= float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'contains':
            return str(value) in str(field_value)
        elif operator == 'starts_with':
            return str(field_value).startswith(str(value))
        elif operator == 'ends_with':
            return str(field_value).endswith(str(value))
        elif operator == 'regex':
            try:
                return bool(re.match(str(value), str(field_value)))
            except re.error:
                return False
        
        return False
    
    def _apply_data_transforms(self, data: dict, validation_rules: Dict[str, Any]) -> dict:
        """应用数据转换规则"""
        transformed_data = data.copy()
        
        # 获取数据转换规则
        data_transforms = validation_rules.get('data_transforms', {})
        
        for field_name, transform_config in data_transforms.items():
            if field_name in transformed_data:
                field_value = transformed_data[field_name]
                
                if isinstance(transform_config, dict):
                    transform_type = transform_config.get('type')
                elif isinstance(transform_config, str):
                    transform_type = transform_config
                else:
                    continue
                
                try:
                    transformed_value = self._apply_single_transform(field_value, transform_type, transform_config)
                    transformed_data[field_name] = transformed_value
                except Exception as e:
                    self.logger.warning(f"字段 {field_name} 数据转换失败: {e}")
        
        return transformed_data
    
    def _apply_single_transform(self, value: Any, transform_type: str, config: Union[str, dict]) -> Any:
        """应用单个数据转换"""
        if self._is_empty_value(value):
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
        elif transform_type == 'replace':
            if isinstance(config, dict):
                old_value = config.get('old', '')
                new_value = config.get('new', '')
                return value_str.replace(old_value, new_value)
        elif transform_type == 'regex_replace':
            if isinstance(config, dict):
                pattern = config.get('pattern', '')
                replacement = config.get('replacement', '')
                return re.sub(pattern, replacement, value_str)
        elif transform_type == 'pad_left':
            if isinstance(config, dict):
                length = config.get('length', 0)
                char = config.get('char', '0')
                return value_str.rjust(length, char)
        elif transform_type == 'pad_right':
            if isinstance(config, dict):
                length = config.get('length', 0)
                char = config.get('char', '0')
                return value_str.ljust(length, char)
        elif transform_type == 'format_date':
            if isinstance(config, dict):
                from_format = config.get('from_format', '%Y-%m-%d')
                to_format = config.get('to_format', '%Y%m%d')
                try:
                    date_obj = datetime.strptime(value_str, from_format)
                    return date_obj.strftime(to_format)
                except ValueError:
                    return value
        
        return value
    
    def _is_empty_value(self, value: Any) -> bool:
        """判断值是否为空"""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
    
    def validate_batch_data(self, api_code: str, batch_data: List[dict], org_code: str = None) -> List[ValidationResult]:
        """批量验证数据"""
        results = []
        for i, data in enumerate(batch_data):
            try:
                result = self.validate_input_data(api_code, data, org_code)
                # 为批量数据添加索引信息
                if not result.is_valid:
                    for field, errors in result.errors.items():
                        result.errors[field] = [f"第{i+1}条数据: {error}" for error in errors]
                results.append(result)
            except Exception as e:
                error_result = ValidationResult()
                error_result.add_error("system", f"第{i+1}条数据验证异常: {str(e)}")
                results.append(error_result)
        
        return results
    
    def create_field_validator(self, field_config: Dict[str, Any]) -> FieldValidationRule:
        """根据配置创建字段验证规则"""
        return FieldValidationRule(
            field_name=field_config.get('field_name', ''),
            required=field_config.get('required', False),
            data_type=field_config.get('data_type'),
            min_length=field_config.get('min_length'),
            max_length=field_config.get('max_length'),
            pattern=field_config.get('pattern'),
            enum_values=field_config.get('enum_values'),
            custom_validator=field_config.get('custom_validator'),
            error_message=field_config.get('error_message')
        )
    
    def get_validation_summary(self, api_code: str, org_code: str = None) -> Dict[str, Any]:
        """获取接口验证规则摘要"""
        try:
            interface_config = self.config_manager.get_interface_config(api_code, org_code)
            
            summary = {
                'api_code': api_code,
                'api_name': interface_config.api_name,
                'required_fields': list(interface_config.required_params.keys()),
                'optional_fields': list(interface_config.optional_params.keys()),
                'validation_rules_count': len(interface_config.validation_rules),
                'has_conditional_rules': 'conditional_rules' in interface_config.validation_rules,
                'has_data_transforms': 'data_transforms' in interface_config.validation_rules,
                'default_values': interface_config.default_values
            }
            
            # 统计验证规则类型
            rule_types = set()
            for field_rules in interface_config.validation_rules.values():
                if isinstance(field_rules, dict):
                    rule_types.update(field_rules.keys())
            
            summary['validation_rule_types'] = list(rule_types)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取验证规则摘要失败: {e}")
            return {'error': str(e)}
    
    def register_custom_validator(self, name: str, validator_func: callable):
        """注册自定义验证器"""
        self.rule_engine.register_custom_validator(name, validator_func)
    
    def register_custom_transform(self, name: str, transform_func: callable):
        """注册自定义数据转换器"""
        self.rule_engine.register_custom_transform(name, transform_func)
    
    def get_supported_rule_types(self) -> Dict[str, List[str]]:
        """获取支持的规则类型"""
        return self.rule_engine.get_supported_rule_types()


class ValidationRuleEngine:
    """验证规则引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._custom_validators = {}
        self._custom_transforms = {}
    
    def register_custom_validator(self, name: str, validator_func: callable):
        """注册自定义验证器"""
        self._custom_validators[name] = validator_func
        self.logger.info(f"注册自定义验证器: {name}")
    
    def register_custom_transform(self, name: str, transform_func: callable):
        """注册自定义数据转换器"""
        self._custom_transforms[name] = transform_func
        self.logger.info(f"注册自定义数据转换器: {name}")
    
    def get_custom_validator(self, name: str) -> Optional[callable]:
        """获取自定义验证器"""
        return self._custom_validators.get(name)
    
    def get_custom_transform(self, name: str) -> Optional[callable]:
        """获取自定义数据转换器"""
        return self._custom_transforms.get(name)
    
    def evaluate_expression(self, expression: str, context: Dict[str, Any]) -> Any:
        """评估表达式"""
        try:
            # 简单的表达式评估，支持基本的数学和逻辑运算
            # 注意：这里使用受限的eval，实际生产环境中应该使用更安全的表达式引擎
            
            # 替换上下文变量
            for key, value in context.items():
                expression = expression.replace(f"${{{key}}}", str(value))
            
            # 安全的表达式评估（仅支持基本运算）
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "max": max,
                "min": min,
                "sum": sum,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "round": round,
            }
            
            # 添加上下文变量
            allowed_names.update(context)
            
            result = eval(expression, allowed_names)
            return result
            
        except Exception as e:
            self.logger.error(f"表达式评估失败: {expression}, 错误: {e}")
            return None
    
    def build_validation_chain(self, rules: List[Dict[str, Any]]) -> List[callable]:
        """构建验证链"""
        validators = []
        
        for rule in rules:
            rule_type = rule.get('type')
            
            if rule_type == 'required':
                validators.append(self._create_required_validator(rule))
            elif rule_type == 'length':
                validators.append(self._create_length_validator(rule))
            elif rule_type == 'pattern':
                validators.append(self._create_pattern_validator(rule))
            elif rule_type == 'enum':
                validators.append(self._create_enum_validator(rule))
            elif rule_type == 'range':
                validators.append(self._create_range_validator(rule))
            elif rule_type == 'custom':
                validators.append(self._create_custom_validator(rule))
        
        return validators
    
    def _create_required_validator(self, rule: Dict[str, Any]) -> callable:
        """创建必填验证器"""
        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()
            if value is None or (isinstance(value, str) and value.strip() == ''):
                result.add_error('field', rule.get('message', '字段不能为空'))
            return result
        return validator
    
    def _create_length_validator(self, rule: Dict[str, Any]) -> callable:
        """创建长度验证器"""
        min_length = rule.get('min')
        max_length = rule.get('max')
        
        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()
            if value is not None:
                length = len(str(value))
                if min_length is not None and length < min_length:
                    result.add_error('field', f'长度不能少于{min_length}位')
                if max_length is not None and length > max_length:
                    result.add_error('field', f'长度不能超过{max_length}位')
            return result
        return validator
    
    def _create_pattern_validator(self, rule: Dict[str, Any]) -> callable:
        """创建正则验证器"""
        pattern = rule.get('pattern')
        message = rule.get('message', '格式不正确')
        
        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()
            if value is not None and pattern:
                if not re.match(pattern, str(value)):
                    result.add_error('field', message)
            return result
        return validator
    
    def _create_enum_validator(self, rule: Dict[str, Any]) -> callable:
        """创建枚举验证器"""
        enum_values = rule.get('values', [])
        
        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()
            if value is not None and value not in enum_values:
                result.add_error('field', f'必须是以下值之一: {", ".join(map(str, enum_values))}')
            return result
        return validator
    
    def _create_range_validator(self, rule: Dict[str, Any]) -> callable:
        """创建范围验证器"""
        min_value = rule.get('min')
        max_value = rule.get('max')
        
        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()
            if value is not None:
                try:
                    numeric_value = float(value)
                    if min_value is not None and numeric_value < min_value:
                        result.add_error('field', f'不能小于{min_value}')
                    if max_value is not None and numeric_value > max_value:
                        result.add_error('field', f'不能大于{max_value}')
                except (ValueError, TypeError):
                    result.add_error('field', '必须是有效的数值')
            return result
        return validator
    
    def _create_custom_validator(self, rule: Dict[str, Any]) -> callable:
        """创建自定义验证器"""
        validator_name = rule.get('validator')
        custom_validator = self.get_custom_validator(validator_name)
        
        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()
            if custom_validator:
                try:
                    is_valid = custom_validator(value, rule)
                    if not is_valid:
                        result.add_error('field', rule.get('message', '验证失败'))
                except Exception as e:
                    result.add_error('field', f'自定义验证异常: {str(e)}')
            return result
        return validator