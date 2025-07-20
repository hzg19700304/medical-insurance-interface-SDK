"""
验证规则引擎
实现字段规则验证逻辑、条件表达式评估和数据转换功能
"""

import re
import ast
import operator
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal

from ..models.validation import ValidationResult
from ..exceptions import ValidationException


class ExpressionEvaluator:
    """表达式评估器"""
    
    # 支持的操作符
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
        ast.Not: operator.not_,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }
    
    # 支持的内置函数
    FUNCTIONS = {
        'abs': abs,
        'max': max,
        'min': min,
        'sum': sum,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'round': round,
        'isinstance': isinstance,
        'type': type,
        'hasattr': hasattr,
        'getattr': getattr,
        'all': all,
        'any': any,
        'sorted': sorted,
        'reversed': reversed,
        'enumerate': enumerate,
        'zip': zip,
        'range': range,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """安全地评估表达式"""
        try:
            # 解析表达式为AST
            tree = ast.parse(expression, mode='eval')
            
            # 评估AST
            result = self._eval_node(tree.body, context)
            return result
            
        except Exception as e:
            self.logger.error(f"表达式评估失败: {expression}, 错误: {e}")
            raise ValidationException(f"表达式评估失败: {str(e)}")
    
    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """递归评估AST节点"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 兼容性
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8 兼容性
            return node.s
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            elif node.id in self.FUNCTIONS:
                return self.FUNCTIONS[node.id]
            else:
                raise NameError(f"未定义的变量: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op = self.OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                raise ValueError(f"不支持的二元操作符: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op = self.OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError(f"不支持的一元操作符: {type(node.op)}")
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_func = self.OPERATORS.get(type(op))
                if op_func:
                    result = result and op_func(left, right)
                    left = right  # 链式比较
                else:
                    raise ValueError(f"不支持的比较操作符: {type(op)}")
            return result
        elif isinstance(node, ast.BoolOp):
            op = self.OPERATORS.get(type(node.op))
            if op:
                values = [self._eval_node(value, context) for value in node.values]
                result = values[0]
                for value in values[1:]:
                    result = op(result, value)
                return result
            else:
                raise ValueError(f"不支持的布尔操作符: {type(node.op)}")
        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func, context)
            args = [self._eval_node(arg, context) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value, context) for kw in node.keywords}
            return func(*args, **kwargs)
        elif isinstance(node, ast.List):
            return [self._eval_node(item, context) for item in node.elts]
        elif isinstance(node, ast.Dict):
            keys = [self._eval_node(k, context) for k in node.keys]
            values = [self._eval_node(v, context) for v in node.values]
            return dict(zip(keys, values))
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(item, context) for item in node.elts)
        elif isinstance(node, ast.Set):
            return {self._eval_node(item, context) for item in node.elts}
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            slice_value = self._eval_node(node.slice, context)
            return value[slice_value]
        elif isinstance(node, ast.Attribute):
            value = self._eval_node(node.value, context)
            return getattr(value, node.attr)
        elif isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, context)
            if test:
                return self._eval_node(node.body, context)
            else:
                return self._eval_node(node.orelse, context)
        else:
            raise ValueError(f"不支持的AST节点类型: {type(node)}")


class FieldRuleValidator:
    """字段规则验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.expression_evaluator = ExpressionEvaluator()
    
    def validate_field(self, field_name: str, field_value: Any, rules: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """验证单个字段"""
        result = ValidationResult()
        context = context or {}
        context[field_name] = field_value
        
        # 必填验证
        if rules.get('required', False):
            if self._is_empty_value(field_value):
                result.add_error(field_name, rules.get('required_message', f'{field_name}不能为空'))
                return result  # 必填验证失败，跳过其他验证
        
        # 如果值为空且非必填，跳过其他验证
        if self._is_empty_value(field_value):
            return result
        
        # 数据类型验证
        if 'type' in rules:
            if not self._validate_type(field_value, rules['type']):
                result.add_error(field_name, f'{field_name}数据类型不正确，期望{rules["type"]}')
        
        # 长度验证
        self._validate_length(field_name, field_value, rules, result)
        
        # 数值范围验证
        self._validate_range(field_name, field_value, rules, result)
        
        # 正则表达式验证
        self._validate_pattern(field_name, field_value, rules, result)
        
        # 枚举值验证
        self._validate_enum(field_name, field_value, rules, result)
        
        # 日期验证
        self._validate_date(field_name, field_value, rules, result)
        
        # 自定义表达式验证
        self._validate_expression(field_name, field_value, rules, context, result)
        
        # 依赖字段验证
        self._validate_dependencies(field_name, field_value, rules, context, result)
        
        return result
    
    def _validate_length(self, field_name: str, field_value: Any, rules: Dict[str, Any], result: ValidationResult):
        """长度验证"""
        if 'min_length' in rules or 'max_length' in rules or 'exact_length' in rules:
            length = len(str(field_value))
            
            if 'min_length' in rules and length < rules['min_length']:
                result.add_error(field_name, f'{field_name}长度不能少于{rules["min_length"]}位')
            
            if 'max_length' in rules and length > rules['max_length']:
                result.add_error(field_name, f'{field_name}长度不能超过{rules["max_length"]}位')
            
            if 'exact_length' in rules and length != rules['exact_length']:
                result.add_error(field_name, f'{field_name}长度必须为{rules["exact_length"]}位')
    
    def _validate_range(self, field_name: str, field_value: Any, rules: Dict[str, Any], result: ValidationResult):
        """数值范围验证"""
        if 'min_value' in rules or 'max_value' in rules:
            try:
                numeric_value = self._to_number(field_value)
                
                if 'min_value' in rules and numeric_value < rules['min_value']:
                    result.add_error(field_name, f'{field_name}不能小于{rules["min_value"]}')
                
                if 'max_value' in rules and numeric_value > rules['max_value']:
                    result.add_error(field_name, f'{field_name}不能大于{rules["max_value"]}')
                    
            except (ValueError, TypeError):
                result.add_error(field_name, f'{field_name}必须是有效的数值')
    
    def _validate_pattern(self, field_name: str, field_value: Any, rules: Dict[str, Any], result: ValidationResult):
        """正则表达式验证"""
        if 'pattern' in rules:
            pattern = rules['pattern']
            if not re.match(pattern, str(field_value)):
                error_msg = rules.get('pattern_error', f'{field_name}格式不正确')
                result.add_error(field_name, error_msg)
    
    def _validate_enum(self, field_name: str, field_value: Any, rules: Dict[str, Any], result: ValidationResult):
        """枚举值验证"""
        if 'enum_values' in rules:
            enum_values = rules['enum_values']
            if field_value not in enum_values:
                result.add_error(field_name, f'{field_name}必须是以下值之一: {", ".join(map(str, enum_values))}')
    
    def _validate_date(self, field_name: str, field_value: Any, rules: Dict[str, Any], result: ValidationResult):
        """日期验证"""
        if 'date_format' in rules:
            date_format = rules['date_format']
            try:
                datetime.strptime(str(field_value), date_format)
            except ValueError:
                result.add_error(field_name, f'{field_name}日期格式不正确，应为{date_format}')
        
        if 'date_range' in rules:
            date_range = rules['date_range']
            try:
                date_value = datetime.strptime(str(field_value), rules.get('date_format', '%Y-%m-%d'))
                
                if 'min_date' in date_range:
                    min_date = datetime.strptime(date_range['min_date'], rules.get('date_format', '%Y-%m-%d'))
                    if date_value < min_date:
                        result.add_error(field_name, f'{field_name}不能早于{date_range["min_date"]}')
                
                if 'max_date' in date_range:
                    max_date = datetime.strptime(date_range['max_date'], rules.get('date_format', '%Y-%m-%d'))
                    if date_value > max_date:
                        result.add_error(field_name, f'{field_name}不能晚于{date_range["max_date"]}')
                        
            except ValueError:
                pass  # 日期格式验证已在上面处理
    
    def _validate_expression(self, field_name: str, field_value: Any, rules: Dict[str, Any], context: Dict[str, Any], result: ValidationResult):
        """自定义表达式验证"""
        if 'expression' in rules:
            expression = rules['expression']
            try:
                is_valid = self.expression_evaluator.evaluate(expression, context)
                if not is_valid:
                    error_msg = rules.get('expression_error', f'{field_name}验证失败')
                    result.add_error(field_name, error_msg)
            except Exception as e:
                result.add_error(field_name, f'{field_name}表达式验证异常: {str(e)}')
    
    def _validate_dependencies(self, field_name: str, field_value: Any, rules: Dict[str, Any], context: Dict[str, Any], result: ValidationResult):
        """依赖字段验证"""
        if 'dependencies' in rules:
            dependencies = rules['dependencies']
            for dep in dependencies:
                condition = dep.get('condition')
                required_fields = dep.get('required_fields', [])
                
                try:
                    if self.expression_evaluator.evaluate(condition, context):
                        for req_field in required_fields:
                            if req_field not in context or self._is_empty_value(context[req_field]):
                                error_msg = dep.get('error_message', f'当{field_name}为{field_value}时，{req_field}不能为空')
                                result.add_error(req_field, error_msg)
                except Exception as e:
                    result.add_error(field_name, f'依赖验证异常: {str(e)}')
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """验证数据类型"""
        type_mapping = {
            'str': str,
            'string': str,
            'int': (int, str),  # 允许字符串形式的数字
            'integer': (int, str),
            'float': (int, float, str),  # 允许字符串形式的数字
            'number': (int, float, str),
            'bool': bool,
            'boolean': bool,
            'list': list,
            'array': list,
            'dict': dict,
            'object': dict,
            'date': (str, datetime, date),
            'datetime': (str, datetime),
        }
        
        expected_types = type_mapping.get(expected_type.lower())
        if expected_types:
            if isinstance(expected_types, tuple):
                # 对于数值类型，额外检查字符串是否可以转换为数值
                if expected_type.lower() in ['int', 'integer'] and isinstance(value, str):
                    try:
                        int(value)
                        return True
                    except ValueError:
                        return False
                elif expected_type.lower() in ['float', 'number'] and isinstance(value, str):
                    try:
                        float(value)
                        return True
                    except ValueError:
                        return False
                return isinstance(value, expected_types)
            else:
                return isinstance(value, expected_types)
        
        return True  # 未知类型不验证
    
    def _to_number(self, value: Any) -> Union[int, float, Decimal]:
        """转换为数值"""
        if isinstance(value, (int, float, Decimal)):
            return value
        
        try:
            # 尝试转换为整数
            if '.' not in str(value):
                return int(value)
            else:
                return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"无法转换为数值: {value}")
    
    def _is_empty_value(self, value: Any) -> bool:
        """判断值是否为空"""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
            return True
        return False


class DataTransformer:
    """数据转换器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.expression_evaluator = ExpressionEvaluator()
        self._custom_transforms = {}
    
    def register_transform(self, name: str, transform_func: Callable):
        """注册自定义转换函数"""
        self._custom_transforms[name] = transform_func
        self.logger.info(f"注册自定义转换函数: {name}")
    
    def transform_data(self, data: Dict[str, Any], transform_rules: Dict[str, Any]) -> Dict[str, Any]:
        """根据规则转换数据"""
        transformed_data = data.copy()
        
        for field_name, transform_config in transform_rules.items():
            if field_name in transformed_data:
                try:
                    original_value = transformed_data[field_name]
                    transformed_value = self._apply_transforms(original_value, transform_config, transformed_data)
                    transformed_data[field_name] = transformed_value
                except Exception as e:
                    self.logger.warning(f"字段 {field_name} 数据转换失败: {e}")
        
        return transformed_data
    
    def _apply_transforms(self, value: Any, transform_config: Union[str, Dict, List], context: Dict[str, Any]) -> Any:
        """应用转换规则"""
        if isinstance(transform_config, str):
            # 简单转换类型
            return self._apply_single_transform(value, transform_config, {}, context)
        elif isinstance(transform_config, dict):
            # 单个转换配置
            transform_type = transform_config.get('type')
            return self._apply_single_transform(value, transform_type, transform_config, context)
        elif isinstance(transform_config, list):
            # 转换链
            result = value
            for transform in transform_config:
                result = self._apply_transforms(result, transform, context)
            return result
        else:
            return value
    
    def _apply_single_transform(self, value: Any, transform_type: str, config: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """应用单个转换"""
        if value is None:
            return value
        
        try:
            if transform_type == 'trim':
                return str(value).strip()
            elif transform_type == 'upper':
                return str(value).upper()
            elif transform_type == 'lower':
                return str(value).lower()
            elif transform_type == 'title':
                return str(value).title()
            elif transform_type == 'remove_spaces':
                return str(value).replace(' ', '')
            elif transform_type == 'remove_chars':
                chars = config.get('chars', '')
                result = str(value)
                for char in chars:
                    result = result.replace(char, '')
                return result
            elif transform_type == 'replace':
                old_value = config.get('old', '')
                new_value = config.get('new', '')
                return str(value).replace(old_value, new_value)
            elif transform_type == 'regex_replace':
                pattern = config.get('pattern', '')
                replacement = config.get('replacement', '')
                return re.sub(pattern, replacement, str(value))
            elif transform_type == 'pad_left':
                length = config.get('length', 0)
                char = config.get('char', '0')
                return str(value).rjust(length, char)
            elif transform_type == 'pad_right':
                length = config.get('length', 0)
                char = config.get('char', '0')
                return str(value).ljust(length, char)
            elif transform_type == 'substring':
                start = config.get('start', 0)
                end = config.get('end')
                if end is not None:
                    return str(value)[start:end]
                else:
                    return str(value)[start:]
            elif transform_type == 'format_date':
                from_format = config.get('from_format', '%Y-%m-%d')
                to_format = config.get('to_format', '%Y%m%d')
                date_obj = datetime.strptime(str(value), from_format)
                return date_obj.strftime(to_format)
            elif transform_type == 'to_int':
                return int(float(str(value)))
            elif transform_type == 'to_float':
                return float(str(value))
            elif transform_type == 'to_decimal':
                return Decimal(str(value))
            elif transform_type == 'round':
                digits = config.get('digits', 0)
                return round(float(value), digits)
            elif transform_type == 'expression':
                expression = config.get('expression', '')
                eval_context = context.copy()
                eval_context['value'] = value
                return self.expression_evaluator.evaluate(expression, eval_context)
            elif transform_type == 'custom':
                func_name = config.get('function')
                if func_name in self._custom_transforms:
                    return self._custom_transforms[func_name](value, config, context)
                else:
                    self.logger.warning(f"未找到自定义转换函数: {func_name}")
                    return value
            elif transform_type == 'conditional':
                condition = config.get('condition', '')
                true_transform = config.get('true_transform')
                false_transform = config.get('false_transform')
                
                eval_context = context.copy()
                eval_context['value'] = value
                
                if self.expression_evaluator.evaluate(condition, eval_context):
                    if true_transform:
                        return self._apply_transforms(value, true_transform, context)
                else:
                    if false_transform:
                        return self._apply_transforms(value, false_transform, context)
                return value
            else:
                self.logger.warning(f"未知的转换类型: {transform_type}")
                return value
                
        except Exception as e:
            self.logger.error(f"转换失败: {transform_type}, 值: {value}, 错误: {e}")
            return value


class ConditionalRuleEngine:
    """条件规则引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.expression_evaluator = ExpressionEvaluator()
        self.field_validator = FieldRuleValidator()
    
    def evaluate_conditional_rules(self, data: Dict[str, Any], conditional_rules: List[Dict[str, Any]]) -> ValidationResult:
        """评估条件规则"""
        result = ValidationResult()
        
        for rule in conditional_rules:
            try:
                condition = rule.get('condition', '')
                if self.expression_evaluator.evaluate(condition, data):
                    # 条件满足，应用规则
                    self._apply_conditional_rule(data, rule, result)
            except Exception as e:
                self.logger.error(f"条件规则评估失败: {rule}, 错误: {e}")
                result.add_error('system', f'条件规则评估异常: {str(e)}')
        
        return result
    
    def _apply_conditional_rule(self, data: Dict[str, Any], rule: Dict[str, Any], result: ValidationResult):
        """应用条件规则"""
        rule_type = rule.get('type', 'required')
        
        if rule_type == 'required':
            # 条件必填
            required_fields = rule.get('required_fields', [])
            for field in required_fields:
                if field not in data or self._is_empty_value(data[field]):
                    error_msg = rule.get('error_message', f'{field}在当前条件下不能为空')
                    result.add_error(field, error_msg)
        
        elif rule_type == 'validation':
            # 条件验证
            field_rules = rule.get('field_rules', {})
            for field_name, field_rule in field_rules.items():
                if field_name in data:
                    field_result = self.field_validator.validate_field(field_name, data[field_name], field_rule, data)
                    result.merge(field_result)
        
        elif rule_type == 'mutual_exclusive':
            # 互斥字段
            fields = rule.get('fields', [])
            non_empty_fields = [f for f in fields if f in data and not self._is_empty_value(data[f])]
            if len(non_empty_fields) > 1:
                error_msg = rule.get('error_message', f'字段 {", ".join(fields)} 不能同时有值')
                for field in non_empty_fields:
                    result.add_error(field, error_msg)
        
        elif rule_type == 'at_least_one':
            # 至少一个字段有值
            fields = rule.get('fields', [])
            non_empty_fields = [f for f in fields if f in data and not self._is_empty_value(data[f])]
            if len(non_empty_fields) == 0:
                error_msg = rule.get('error_message', f'字段 {", ".join(fields)} 至少需要填写一个')
                for field in fields:
                    result.add_error(field, error_msg)
    
    def _is_empty_value(self, value: Any) -> bool:
        """判断值是否为空"""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
            return True
        return False


class ValidationRuleEngine:
    """完整的验证规则引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.field_validator = FieldRuleValidator()
        self.data_transformer = DataTransformer()
        self.conditional_engine = ConditionalRuleEngine()
        self._custom_validators = {}
    
    def register_custom_validator(self, name: str, validator_func: Callable):
        """注册自定义验证器"""
        self._custom_validators[name] = validator_func
        self.logger.info(f"注册自定义验证器: {name}")
    
    def register_custom_transform(self, name: str, transform_func: Callable):
        """注册自定义转换器"""
        self.data_transformer.register_transform(name, transform_func)
    
    def validate_and_transform(self, data: Dict[str, Any], rules: Dict[str, Any]) -> ValidationResult:
        """验证并转换数据"""
        result = ValidationResult()
        
        # 1. 字段级验证
        field_rules = rules.get('field_rules', {})
        for field_name, field_rule in field_rules.items():
            if field_name in data:
                field_result = self.field_validator.validate_field(field_name, data[field_name], field_rule, data)
                result.merge(field_result)
        
        # 2. 条件规则验证
        conditional_rules = rules.get('conditional_rules', [])
        if conditional_rules:
            conditional_result = self.conditional_engine.evaluate_conditional_rules(data, conditional_rules)
            result.merge(conditional_result)
        
        # 3. 如果验证通过，进行数据转换
        if result.is_valid:
            transform_rules = rules.get('data_transforms', {})
            if transform_rules:
                try:
                    transformed_data = self.data_transformer.transform_data(data, transform_rules)
                    result.validated_data = transformed_data
                except Exception as e:
                    result.add_error('system', f'数据转换失败: {str(e)}')
        
        return result
    
    def get_supported_rule_types(self) -> Dict[str, List[str]]:
        """获取支持的规则类型"""
        return {
            'field_rules': [
                'required', 'type', 'min_length', 'max_length', 'exact_length',
                'min_value', 'max_value', 'pattern', 'enum_values', 'date_format',
                'date_range', 'expression', 'dependencies'
            ],
            'conditional_rules': [
                'required', 'validation', 'mutual_exclusive', 'at_least_one'
            ],
            'data_transforms': [
                'trim', 'upper', 'lower', 'title', 'remove_spaces', 'remove_chars',
                'replace', 'regex_replace', 'pad_left', 'pad_right', 'substring',
                'format_date', 'to_int', 'to_float', 'to_decimal', 'round',
                'expression', 'custom', 'conditional'
            ]
        }