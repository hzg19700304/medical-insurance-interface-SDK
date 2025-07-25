#!/usr/bin/env python3
"""
测试数据验证组件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.validator import DataValidator
from medical_insurance_sdk.core.rule_engine import ValidationRuleEngine, FieldRuleValidator, DataTransformer
from medical_insurance_sdk.models.validation import ValidationResult


def test_field_rule_validator():
    """测试字段规则验证器"""
    print("=== 测试字段规则验证器 ===")
    
    validator = FieldRuleValidator()
    
    # 测试必填验证
    rules = {'required': True, 'required_message': '姓名不能为空'}
    result = validator.validate_field('name', '', rules)
    print(f"必填验证 - 空值: {result.is_valid}, 错误: {result.errors}")
    
    result = validator.validate_field('name', '张三', rules)
    print(f"必填验证 - 有值: {result.is_valid}")
    
    # 测试长度验证
    rules = {'min_length': 2, 'max_length': 10}
    result = validator.validate_field('name', '张', rules)
    print(f"长度验证 - 太短: {result.is_valid}, 错误: {result.errors}")
    
    result = validator.validate_field('name', '张三', rules)
    print(f"长度验证 - 正常: {result.is_valid}")
    
    # 测试正则验证
    rules = {'pattern': r'^\d{11}$', 'pattern_error': '手机号格式不正确'}
    result = validator.validate_field('phone', '1234567890', rules)
    print(f"正则验证 - 错误格式: {result.is_valid}, 错误: {result.errors}")
    
    result = validator.validate_field('phone', '13812345678', rules)
    print(f"正则验证 - 正确格式: {result.is_valid}")
    
    print()


def test_data_transformer():
    """测试数据转换器"""
    print("=== 测试数据转换器 ===")
    
    transformer = DataTransformer()
    
    # 测试基本转换
    data = {
        'name': '  张三  ',
        'phone': '138-1234-5678',
        'id_card': '123456789012345678'
    }
    
    transform_rules = {
        'name': 'trim',
        'phone': {'type': 'remove_chars', 'chars': '-'},
        'id_card': {'type': 'pad_left', 'length': 20, 'char': '0'}
    }
    
    result = transformer.transform_data(data, transform_rules)
    print(f"原始数据: {data}")
    print(f"转换后数据: {result}")
    print()


def test_validation_rule_engine():
    """测试验证规则引擎"""
    print("=== 测试验证规则引擎 ===")
    
    engine = ValidationRuleEngine()
    
    # 测试数据
    data = {
        'name': '张三',
        'age': '25',
        'phone': '13812345678',
        'email': 'zhangsan@example.com',
        'type': 'individual'
    }
    
    # 验证规则
    rules = {
        'field_rules': {
            'name': {
                'required': True,
                'min_length': 2,
                'max_length': 10
            },
            'age': {
                'required': True,
                'type': 'int',
                'min_value': 0,
                'max_value': 120
            },
            'phone': {
                'required': True,
                'pattern': r'^\d{11}$'
            },
            'email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            }
        },
        'conditional_rules': [
            {
                'condition': 'type == "individual"',
                'type': 'required',
                'required_fields': ['name', 'phone'],
                'error_message': '个人用户必须填写姓名和手机号'
            }
        ],
        'data_transforms': {
            'name': 'trim',
            'phone': {'type': 'remove_chars', 'chars': '-'},
            'age': 'to_int'
        }
    }
    
    result = engine.validate_and_transform(data, rules)
    print(f"验证结果: {result.is_valid}")
    if not result.is_valid:
        print(f"错误信息: {result.errors}")
    else:
        print(f"转换后数据: {result.validated_data}")
    
    print()


def test_expression_evaluator():
    """测试表达式评估器"""
    print("=== 测试表达式评估器 ===")
    
    from medical_insurance_sdk.core.rule_engine import ExpressionEvaluator
    
    evaluator = ExpressionEvaluator()
    
    context = {
        'age': 25,
        'type': 'individual',
        'amount': 1000.5,
        'items': [1, 2, 3, 4, 5]
    }
    
    # 测试各种表达式
    expressions = [
        'age > 18',
        'type == "individual"',
        'amount >= 1000',
        'len(items) > 3',
        'age >= 18 and type == "individual"',
        'sum(items) == 15',
        'max(items) == 5'
    ]
    
    for expr in expressions:
        try:
            result = evaluator.evaluate(expr, context)
            print(f"表达式: {expr} => {result}")
        except Exception as e:
            print(f"表达式: {expr} => 错误: {e}")
    
    print()


if __name__ == '__main__':
    print("开始测试数据验证组件...")
    print()
    
    test_field_rule_validator()
    test_data_transformer()
    test_validation_rule_engine()
    test_expression_evaluator()
    
    print("测试完成！")