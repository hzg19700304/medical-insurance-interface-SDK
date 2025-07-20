"""
数据解析器模块
支持直接映射、数组映射、条件映射、计算字段和表达式评估
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

from .config_manager import ConfigManager
from ..models.config import InterfaceConfig
from ..exceptions import DataParsingException


class DataParser:
    """数据解析器 - 支持多种映射方式和计算字段"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._expression_evaluator = ExpressionEvaluator()
        self._custom_parsers = {}
    
    def parse_response_data(self, api_code: str, response_data: dict, org_code: str = None) -> dict:
        """根据接口配置解析响应数据"""
        try:
            # 获取接口配置
            interface_config = self.config_manager.get_interface_config(api_code, org_code)
            
            # 获取响应映射规则
            response_mapping = interface_config.response_mapping
            if not response_mapping:
                self.logger.warning(f"接口 {api_code} 未配置响应映射规则，返回原始数据")
                return response_data
            
            # 解析响应数据
            parsed_data = self._parse_data_with_mapping(response_data, response_mapping)
            
            self.logger.debug(f"接口 {api_code} 响应数据解析完成")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析响应数据失败: {api_code}, 错误: {e}")
            raise DataParsingException(f"解析响应数据失败: {e}")
    
    def _parse_data_with_mapping(self, source_data: dict, mapping_rules: Dict[str, Any]) -> dict:
        """根据映射规则解析数据"""
        parsed_data = {}
        
        for target_field, mapping_config in mapping_rules.items():
            try:
                parsed_value = self._apply_mapping_rule(source_data, mapping_config)
                if parsed_value is not None:
                    parsed_data[target_field] = parsed_value
            except Exception as e:
                self.logger.warning(f"字段 {target_field} 映射失败: {e}")
                # 继续处理其他字段，不中断整个解析过程
        
        return parsed_data
    
    def _apply_mapping_rule(self, source_data: dict, mapping_config: Union[str, Dict[str, Any]]) -> Any:
        """应用单个映射规则"""
        if isinstance(mapping_config, str):
            # 简单路径映射
            return self._extract_value_by_path(source_data, mapping_config)
        
        if not isinstance(mapping_config, dict):
            return mapping_config
        
        mapping_type = mapping_config.get('type', 'direct')
        
        if mapping_type == 'direct':
            return self._apply_direct_mapping(source_data, mapping_config)
        elif mapping_type == 'array_mapping':
            return self._apply_array_mapping(source_data, mapping_config)
        elif mapping_type == 'conditional':
            return self._apply_conditional_mapping(source_data, mapping_config)
        elif mapping_type == 'computed':
            return self._apply_computed_mapping(source_data, mapping_config)
        elif mapping_type == 'nested':
            return self._apply_nested_mapping(source_data, mapping_config)
        elif mapping_type == 'custom':
            return self._apply_custom_mapping(source_data, mapping_config)
        else:
            self.logger.warning(f"未知的映射类型: {mapping_type}")
            return None
    
    def _apply_direct_mapping(self, source_data: dict, mapping_config: Dict[str, Any]) -> Any:
        """应用直接映射"""
        source_path = mapping_config.get('source_path', '')
        default_value = mapping_config.get('default_value')
        transform = mapping_config.get('transform')
        
        # 提取源数据
        value = self._extract_value_by_path(source_data, source_path)
        
        # 如果值为空且有默认值，使用默认值
        if value is None and default_value is not None:
            value = default_value
        
        # 应用数据转换
        if value is not None and transform:
            value = self._apply_data_transform(value, transform)
        
        return value
    
    def _apply_array_mapping(self, source_data: dict, mapping_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用数组映射"""
        source_path = mapping_config.get('source_path', '')
        item_mapping = mapping_config.get('item_mapping', {})
        filter_condition = mapping_config.get('filter')
        sort_config = mapping_config.get('sort')
        limit = mapping_config.get('limit')
        
        # 提取源数组数据
        source_array = self._extract_value_by_path(source_data, source_path)
        if not isinstance(source_array, list):
            return []
        
        # 映射每个数组项
        mapped_array = []
        for item in source_array:
            if isinstance(item, dict):
                # 应用过滤条件
                if filter_condition and not self._evaluate_filter_condition(item, filter_condition):
                    continue
                
                # 映射数组项
                mapped_item = self._parse_data_with_mapping(item, item_mapping)
                mapped_array.append(mapped_item)
        
        # 应用排序
        if sort_config:
            mapped_array = self._apply_array_sort(mapped_array, sort_config)
        
        # 应用限制
        if limit and isinstance(limit, int) and limit > 0:
            mapped_array = mapped_array[:limit]
        
        return mapped_array
    
    def _apply_conditional_mapping(self, source_data: dict, mapping_config: Dict[str, Any]) -> Any:
        """应用条件映射"""
        condition = mapping_config.get('condition', {})
        true_rule = mapping_config.get('true_rule')
        false_rule = mapping_config.get('false_rule')
        
        # 评估条件
        condition_result = self._evaluate_condition(condition, source_data)
        
        # 根据条件结果选择映射规则
        if condition_result and true_rule:
            return self._apply_mapping_rule(source_data, true_rule)
        elif not condition_result and false_rule:
            return self._apply_mapping_rule(source_data, false_rule)
        
        return None
    
    def _apply_computed_mapping(self, source_data: dict, mapping_config: Dict[str, Any]) -> Any:
        """应用计算字段映射"""
        expression = mapping_config.get('expression', '')
        context = mapping_config.get('context', {})
        
        # 构建计算上下文
        compute_context = {**source_data, **context}
        
        # 评估表达式
        try:
            result = self._expression_evaluator.evaluate(expression, compute_context)
            return result
        except Exception as e:
            self.logger.error(f"计算字段表达式评估失败: {expression}, 错误: {e}")
            return None
    
    def _apply_nested_mapping(self, source_data: dict, mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """应用嵌套映射"""
        source_path = mapping_config.get('source_path', '')
        nested_mapping = mapping_config.get('mapping', {})
        
        # 提取嵌套源数据
        nested_source = self._extract_value_by_path(source_data, source_path)
        if not isinstance(nested_source, dict):
            return {}
        
        # 递归应用映射规则
        return self._parse_data_with_mapping(nested_source, nested_mapping)
    
    def _apply_custom_mapping(self, source_data: dict, mapping_config: Dict[str, Any]) -> Any:
        """应用自定义映射"""
        parser_name = mapping_config.get('parser')
        parser_config = mapping_config.get('config', {})
        
        custom_parser = self._custom_parsers.get(parser_name)
        if custom_parser and callable(custom_parser):
            try:
                return custom_parser(source_data, parser_config)
            except Exception as e:
                self.logger.error(f"自定义解析器 {parser_name} 执行失败: {e}")
        
        return None
    
    def _extract_value_by_path(self, data: dict, path: str) -> Any:
        """根据路径提取数据值"""
        if not path or not isinstance(data, dict):
            return None
        
        # 支持点号分隔的路径，如 "output.baseinfo.psn_name"
        path_parts = path.split('.')
        current_data = data
        
        for part in path_parts:
            if isinstance(current_data, dict) and part in current_data:
                current_data = current_data[part]
            elif isinstance(current_data, list) and part.isdigit():
                # 支持数组索引访问
                index = int(part)
                if 0 <= index < len(current_data):
                    current_data = current_data[index]
                else:
                    return None
            else:
                return None
        
        return current_data
    
    def _evaluate_condition(self, condition: Dict[str, Any], data: dict) -> bool:
        """评估条件表达式"""
        if not condition:
            return True
        
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if not field or not operator:
            return True
        
        field_value = self._extract_value_by_path(data, field)
        
        if operator == 'eq':
            return field_value == value
        elif operator == 'ne':
            return field_value != value
        elif operator == 'in':
            return field_value in value if isinstance(value, (list, tuple)) else False
        elif operator == 'not_in':
            return field_value not in value if isinstance(value, (list, tuple)) else True
        elif operator == 'not_empty':
            return field_value is not None and field_value != '' and field_value != []
        elif operator == 'empty':
            return field_value is None or field_value == '' or field_value == []
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
            return str(value) in str(field_value) if field_value is not None else False
        elif operator == 'starts_with':
            return str(field_value).startswith(str(value)) if field_value is not None else False
        elif operator == 'ends_with':
            return str(field_value).endswith(str(value)) if field_value is not None else False
        elif operator == 'regex':
            try:
                return bool(re.match(str(value), str(field_value))) if field_value is not None else False
            except re.error:
                return False
        
        return False
    
    def _evaluate_filter_condition(self, item: dict, filter_condition: Dict[str, Any]) -> bool:
        """评估数组项过滤条件"""
        return self._evaluate_condition(filter_condition, item)
    
    def _apply_array_sort(self, array: List[Dict[str, Any]], sort_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用数组排序"""
        sort_field = sort_config.get('field')
        sort_order = sort_config.get('order', 'asc')  # asc 或 desc
        
        if not sort_field:
            return array
        
        try:
            reverse = sort_order.lower() == 'desc'
            return sorted(array, key=lambda x: x.get(sort_field, ''), reverse=reverse)
        except Exception as e:
            self.logger.warning(f"数组排序失败: {e}")
            return array
    
    def _apply_data_transform(self, value: Any, transform_config: Union[str, Dict[str, Any]]) -> Any:
        """应用数据转换"""
        if isinstance(transform_config, str):
            transform_type = transform_config
            transform_params = {}
        elif isinstance(transform_config, dict):
            transform_type = transform_config.get('type')
            transform_params = transform_config.get('params', {})
        else:
            return value
        
        if value is None:
            return value
        
        try:
            if transform_type == 'string':
                return str(value)
            elif transform_type == 'int':
                return int(float(value))
            elif transform_type == 'float':
                return float(value)
            elif transform_type == 'bool':
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif transform_type == 'upper':
                return str(value).upper()
            elif transform_type == 'lower':
                return str(value).lower()
            elif transform_type == 'trim':
                return str(value).strip()
            elif transform_type == 'format_date':
                from_format = transform_params.get('from_format', '%Y-%m-%d')
                to_format = transform_params.get('to_format', '%Y%m%d')
                if isinstance(value, str):
                    date_obj = datetime.strptime(value, from_format)
                    return date_obj.strftime(to_format)
            elif transform_type == 'replace':
                old_value = transform_params.get('old', '')
                new_value = transform_params.get('new', '')
                return str(value).replace(old_value, new_value)
            elif transform_type == 'regex_replace':
                pattern = transform_params.get('pattern', '')
                replacement = transform_params.get('replacement', '')
                return re.sub(pattern, replacement, str(value))
            elif transform_type == 'round':
                decimals = transform_params.get('decimals', 2)
                return round(float(value), decimals)
            elif transform_type == 'abs':
                return abs(float(value))
            elif transform_type == 'custom':
                transform_name = transform_params.get('name')
                custom_transform = self._custom_parsers.get(f"transform_{transform_name}")
                if custom_transform and callable(custom_transform):
                    return custom_transform(value, transform_params)
        
        except Exception as e:
            self.logger.warning(f"数据转换失败: {transform_type}, 值: {value}, 错误: {e}")
        
        return value
    
    def register_custom_parser(self, name: str, parser_func: Callable):
        """注册自定义解析器"""
        self._custom_parsers[name] = parser_func
        self.logger.info(f"注册自定义解析器: {name}")
    
    def register_custom_transform(self, name: str, transform_func: Callable):
        """注册自定义数据转换器"""
        self._custom_parsers[f"transform_{name}"] = transform_func
        self.logger.info(f"注册自定义数据转换器: {name}")
    
    def parse_structured_data(self, api_code: str, response_data: dict, output_format: str = 'structured', org_code: str = None) -> dict:
        """解析结构化数据"""
        try:
            # 获取接口配置
            interface_config = self.config_manager.get_interface_config(api_code, org_code)
            
            # 获取数据解析规则
            parsing_rules = interface_config.data_parsing_rules if hasattr(interface_config, 'data_parsing_rules') else {}
            
            if not parsing_rules:
                # 如果没有专门的解析规则，使用响应映射规则
                return self.parse_response_data(api_code, response_data, org_code)
            
            parsed_data = {}
            
            # 应用字段映射
            field_mappings = parsing_rules.get('field_mappings', {})
            for target_field, source_path in field_mappings.items():
                value = self._extract_value_by_path(response_data, source_path)
                if value is not None:
                    parsed_data[target_field] = value
            
            # 应用数组字段映射
            array_fields = parsing_rules.get('array_fields', {})
            for target_field, array_config in array_fields.items():
                source_path = array_config.get('source')
                field_mappings = array_config.get('fields', {})
                
                source_array = self._extract_value_by_path(response_data, source_path)
                if isinstance(source_array, list):
                    mapped_array = []
                    for item in source_array:
                        if isinstance(item, dict):
                            mapped_item = {}
                            for target_key, source_key in field_mappings.items():
                                if source_key in item:
                                    mapped_item[target_key] = item[source_key]
                            mapped_array.append(mapped_item)
                    parsed_data[target_field] = mapped_array
            
            # 应用计算字段
            computed_fields = parsing_rules.get('computed_fields', {})
            for target_field, compute_config in computed_fields.items():
                expression = compute_config.get('expression', '')
                if expression:
                    try:
                        # 构建计算上下文
                        context = {**response_data, **parsed_data}
                        result = self._expression_evaluator.evaluate(expression, context)
                        parsed_data[target_field] = result
                    except Exception as e:
                        self.logger.warning(f"计算字段 {target_field} 计算失败: {e}")
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析结构化数据失败: {api_code}, 错误: {e}")
            raise DataParsingException(f"解析结构化数据失败: {e}")
    
    def get_parsing_summary(self, api_code: str, org_code: str = None) -> Dict[str, Any]:
        """获取解析规则摘要"""
        try:
            interface_config = self.config_manager.get_interface_config(api_code, org_code)
            
            summary = {
                'api_code': api_code,
                'api_name': interface_config.api_name,
                'has_response_mapping': bool(interface_config.response_mapping),
                'response_mapping_count': len(interface_config.response_mapping) if interface_config.response_mapping else 0,
                'has_data_parsing_rules': hasattr(interface_config, 'data_parsing_rules') and bool(interface_config.data_parsing_rules),
                'supported_mapping_types': [
                    'direct', 'array_mapping', 'conditional', 
                    'computed', 'nested', 'custom'
                ]
            }
            
            # 分析映射规则类型
            if interface_config.response_mapping:
                mapping_types = set()
                for mapping_config in interface_config.response_mapping.values():
                    if isinstance(mapping_config, dict):
                        mapping_type = mapping_config.get('type', 'direct')
                        mapping_types.add(mapping_type)
                    else:
                        mapping_types.add('simple_path')
                
                summary['used_mapping_types'] = list(mapping_types)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取解析规则摘要失败: {e}")
            return {'error': str(e)}


class ExpressionEvaluator:
    """表达式评估器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._custom_functions = {}
    
    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """评估表达式"""
        try:
            # 预处理表达式，替换上下文变量
            processed_expression = self._preprocess_expression(expression, context)
            
            # 构建安全的执行环境
            safe_globals = self._build_safe_globals()
            safe_locals = {**context, **self._custom_functions}
            
            # 执行表达式
            result = eval(processed_expression, safe_globals, safe_locals)
            return result
            
        except Exception as e:
            self.logger.error(f"表达式评估失败: {expression}, 错误: {e}")
            raise
    
    def _preprocess_expression(self, expression: str, context: Dict[str, Any]) -> str:
        """预处理表达式"""
        # 替换 ${variable} 格式的变量引用
        def replace_variable(match):
            var_name = match.group(1)
            if var_name in context:
                value = context[var_name]
                if isinstance(value, str):
                    return f"'{value}'"
                else:
                    return str(value)
            return match.group(0)
        
        # 使用正则表达式替换变量引用
        processed = re.sub(r'\$\{([^}]+)\}', replace_variable, expression)
        return processed
    
    def _build_safe_globals(self) -> Dict[str, Any]:
        """构建安全的全局执行环境"""
        return {
            "__builtins__": {},
            # 数学函数
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "len": len,
            "round": round,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            # 常用函数
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "reversed": reversed,
            # 类型检查
            "isinstance": isinstance,
            "type": type,
            # 自定义函数
            **self._custom_functions
        }
    
    def register_function(self, name: str, func: Callable):
        """注册自定义函数"""
        self._custom_functions[name] = func
        self.logger.info(f"注册自定义函数: {name}")
    
    def get_registered_functions(self) -> List[str]:
        """获取已注册的自定义函数列表"""
        return list(self._custom_functions.keys())