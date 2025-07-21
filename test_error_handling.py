#!/usr/bin/env python3
"""测试错误处理和异常管理功能"""

import time
import logging
from medical_insurance_sdk.exceptions import (
    MedicalInsuranceException,
    ValidationException,
    NetworkException,
    ConfigurationException,
    ExceptionFactory
)
from medical_insurance_sdk.core.error_handler import (
    ErrorHandler,
    RetryConfig,
    CircuitBreaker,
    default_error_handler
)
from medical_insurance_sdk.utils.error_utils import (
    ErrorContext,
    ErrorAggregator,
    format_error_for_user,
    create_error_response
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_exception_hierarchy():
    """测试异常体系"""
    print("=== 测试异常体系 ===")
    
    # 测试基础异常
    try:
        raise MedicalInsuranceException("测试基础异常", error_code="TEST_ERROR")
    except MedicalInsuranceException as e:
        print(f"基础异常: {e}")
        print(f"异常字典: {e.to_dict()}")
        print(f"是否可重试: {e.is_retryable()}")
        print()
    
    # 测试验证异常
    try:
        raise ValidationException("字段验证失败", field_errors={"name": ["不能为空"]})
    except ValidationException as e:
        print(f"验证异常: {e}")
        print(f"用户消息: {e.get_user_message()}")
        print(f"字段错误: {e.field_errors}")
        print()
    
    # 测试网络异常（可重试）
    try:
        raise NetworkException("网络连接失败", status_code=500, retry_after=5)
    except NetworkException as e:
        print(f"网络异常: {e}")
        print(f"是否可重试: {e.is_retryable()}")
        print(f"重试间隔: {e.retry_after}秒")
        print()


def test_exception_factory():
    """测试异常工厂"""
    print("=== 测试异常工厂 ===")
    
    # 通过错误代码创建异常
    exc1 = ExceptionFactory.create_exception("REQUIRED_FIELD", "姓名不能为空", field_name="name")
    print(f"工厂创建异常1: {exc1}")
    
    # 从医保响应创建异常
    response_data = {"infcode": -1, "err_msg": "参数错误"}
    exc2 = ExceptionFactory.from_medical_response(response_data)
    print(f"工厂创建异常2: {exc2}")
    print()


def test_retry_mechanism():
    """测试重试机制"""
    print("=== 测试重试机制 ===")
    
    # 创建错误处理器
    retry_config = RetryConfig(max_attempts=3, base_delay=0.1)
    error_handler = ErrorHandler(retry_config=retry_config)
    
    # 模拟会失败的函数
    call_count = 0
    
    @error_handler.with_retry("test_operation")
    def failing_function():
        nonlocal call_count
        call_count += 1
        print(f"第{call_count}次调用")
        
        if call_count < 3:
            raise NetworkException("网络异常", retry_after=1)
        return "成功"
    
    try:
        result = failing_function()
        print(f"重试成功，结果: {result}")
    except Exception as e:
        print(f"重试失败: {e}")
    
    print()


def test_circuit_breaker():
    """测试熔断器"""
    print("=== 测试熔断器 ===")
    
    circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    
    def unstable_service():
        import random
        if random.random() < 0.8:  # 80%失败率
            raise NetworkException("服务不稳定")
        return "成功"
    
    # 测试熔断器
    for i in range(5):
        try:
            result = circuit_breaker.call(unstable_service)
            print(f"调用{i+1}成功: {result}")
        except Exception as e:
            print(f"调用{i+1}失败: {e}")
        
        print(f"熔断器状态: {circuit_breaker.state}, 失败次数: {circuit_breaker.failure_count}")
        time.sleep(0.1)
    
    print()


def test_error_context():
    """测试错误上下文"""
    print("=== 测试错误上下文 ===")
    
    try:
        with ErrorContext("test_operation", user_id="123", api_code="1101") as ctx:
            time.sleep(0.1)  # 模拟操作
            raise ValidationException("测试异常")
    except Exception as e:
        print(f"异常: {e}")
        print(f"上下文: {ctx.to_dict()}")
    
    print()


def test_error_aggregator():
    """测试错误聚合器"""
    print("=== 测试错误聚合器 ===")
    
    aggregator = ErrorAggregator()
    
    # 添加多个错误
    aggregator.add_error(ValidationException("字段1错误"), {"field": "name"})
    aggregator.add_error(ValidationException("字段2错误"), {"field": "age"})
    aggregator.add_error(NetworkException("网络错误"), {"url": "http://example.com"})
    
    # 获取摘要
    summary = aggregator.get_summary()
    print(f"错误摘要: {summary}")
    
    # 获取详细报告
    report = aggregator.get_detailed_report()
    print(f"详细报告: {report}")
    
    print()


def test_error_formatting():
    """测试错误格式化"""
    print("=== 测试错误格式化 ===")
    
    # 测试用户友好格式
    exc = ValidationException("数据验证失败", field_errors={"name": ["不能为空", "长度不能超过50"]})
    user_format = format_error_for_user(exc)
    print(f"用户格式: {user_format}")
    
    # 测试错误响应格式
    error_response = create_error_response(exc, "user_registration", "req_123", include_details=True)
    print(f"错误响应: {error_response}")
    
    print()


def test_comprehensive_error_handling():
    """测试综合错误处理"""
    print("=== 测试综合错误处理 ===")
    
    # 模拟医保接口调用
    @default_error_handler.with_error_handling(
        operation_name="medical_interface_call",
        retry_config=RetryConfig(max_attempts=2, base_delay=0.1),
        enable_circuit_breaker=True
    )
    def call_medical_interface(api_code: str, data: dict):
        print(f"调用医保接口: {api_code}")
        
        # 模拟不同类型的错误
        import random
        error_type = random.choice(["network", "validation", "success"])
        
        if error_type == "network":
            raise NetworkException("网络连接失败", retry_after=1)
        elif error_type == "validation":
            raise ValidationException("参数验证失败", field_errors={"psn_no": ["格式错误"]})
        else:
            return {"infcode": 0, "output": {"result": "成功"}}
    
    # 测试多次调用
    for i in range(3):
        try:
            result = call_medical_interface("1101", {"psn_no": "123456"})
            print(f"调用{i+1}成功: {result}")
        except Exception as e:
            error_response = default_error_handler.handle_exception(e, "medical_interface_call")
            print(f"调用{i+1}失败: {error_response}")
        
        time.sleep(0.1)
    
    # 获取错误统计
    stats = default_error_handler.get_error_statistics()
    print(f"错误统计: {stats}")
    
    print()


def main():
    """主测试函数"""
    print("开始测试医保SDK错误处理和异常管理功能\n")
    
    test_exception_hierarchy()
    test_exception_factory()
    test_retry_mechanism()
    test_circuit_breaker()
    test_error_context()
    test_error_aggregator()
    test_error_formatting()
    test_comprehensive_error_handling()
    
    print("所有测试完成！")


if __name__ == "__main__":
    main()