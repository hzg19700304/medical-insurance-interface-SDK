#!/usr/bin/env python3
"""医保SDK错误处理系统演示

展示错误处理和异常管理的主要功能
"""

import time
import logging
from medical_insurance_sdk.exceptions import (
    MedicalInsuranceException,
    ValidationException,
    NetworkException,
    ExceptionFactory
)
from medical_insurance_sdk.core.error_handler import (
    ErrorHandler,
    RetryConfig,
    medical_interface_error_handler,
    handle_medical_interface_error,
    handle_database_error,
    handle_cache_error
)
from medical_insurance_sdk.utils.error_utils import (
    ErrorContext,
    format_error_for_user,
    create_error_response
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_exception_hierarchy():
    """演示异常体系结构"""
    print("=" * 60)
    print("1. 异常体系结构演示")
    print("=" * 60)
    
    # 创建不同类型的异常
    exceptions = [
        ValidationException("字段验证失败", field_errors={"name": ["不能为空"]}),
        NetworkException("网络连接超时", status_code=504, retry_after=10),
        ExceptionFactory.create_exception("REQUIRED_FIELD", "用户名不能为空", field_name="username"),
        ExceptionFactory.from_medical_response({"infcode": -1, "err_msg": "参数错误"})
    ]
    
    for i, exc in enumerate(exceptions, 1):
        print(f"\n异常 {i}: {exc}")
        print(f"  错误代码: {exc.error_code}")
        print(f"  可重试: {exc.is_retryable()}")
        print(f"  严重程度: {exc.severity}")
        print(f"  用户消息: {exc.get_user_message()}")


def demo_retry_mechanism():
    """演示重试机制"""
    print("\n" + "=" * 60)
    print("2. 重试机制演示")
    print("=" * 60)
    
    # 创建自定义重试配置
    retry_config = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0
    )
    
    error_handler = ErrorHandler(retry_config=retry_config)
    
    # 模拟不稳定的服务
    call_count = 0
    
    @error_handler.with_retry("demo_service")
    def unstable_service():
        nonlocal call_count
        call_count += 1
        print(f"  尝试调用服务 (第{call_count}次)")
        
        if call_count < 3:
            raise NetworkException("网络不稳定", retry_after=1)
        return {"status": "success", "data": "服务调用成功"}
    
    try:
        result = unstable_service()
        print(f"✓ 重试成功: {result}")
    except Exception as e:
        print(f"✗ 重试失败: {e}")


def demo_circuit_breaker():
    """演示熔断器机制"""
    print("\n" + "=" * 60)
    print("3. 熔断器机制演示")
    print("=" * 60)
    
    error_handler = ErrorHandler()
    
    # 模拟经常失败的服务
    @error_handler.with_circuit_breaker("unreliable_service")
    def unreliable_service():
        import random
        if random.random() < 0.7:  # 70%失败率
            raise NetworkException("服务异常")
        return "服务正常"
    
    # 测试熔断器行为
    for i in range(8):
        try:
            result = unreliable_service()
            print(f"  调用 {i+1}: ✓ {result}")
        except Exception as e:
            print(f"  调用 {i+1}: ✗ {e}")
        
        # 显示熔断器状态
        cb = error_handler.get_circuit_breaker("unreliable_service")
        print(f"    熔断器状态: {cb.state}, 失败次数: {cb.failure_count}")
        
        time.sleep(0.1)


def demo_medical_interface_error_handling():
    """演示医保接口专用错误处理"""
    print("\n" + "=" * 60)
    print("4. 医保接口错误处理演示")
    print("=" * 60)
    
    # 配置特定接口的重试策略
    medical_interface_error_handler.configure_interface_retry(
        "1101",
        RetryConfig(max_attempts=2, base_delay=1.0)
    )
    
    # 注册降级策略
    def fallback_for_1101(exception, *args, **kwargs):
        return {
            "success": False,
            "error": "人员信息查询服务暂时不可用，请稍后重试",
            "fallback": True,
            "api_code": "1101"
        }
    
    medical_interface_error_handler.register_interface_fallback("1101", fallback_for_1101)
    
    # 使用装饰器处理医保接口调用
    @medical_interface_error_handler.handle_interface_call("1101")
    def query_person_info(psn_no: str):
        print(f"  查询人员信息: {psn_no}")
        
        # 模拟不同的错误情况
        import random
        error_type = random.choice(["network", "validation", "success"])
        
        if error_type == "network":
            raise NetworkException("医保服务器连接超时")
        elif error_type == "validation":
            raise ValidationException("人员编号格式错误")
        else:
            return {"infcode": 0, "output": {"psn_name": "张三", "psn_no": psn_no}}
    
    # 测试接口调用
    for i in range(3):
        try:
            result = query_person_info("430123199001011234")
            print(f"  调用 {i+1}: ✓ {result}")
        except Exception as e:
            print(f"  调用 {i+1}: ✗ {e}")
    
    # 显示接口健康状态
    health_status = medical_interface_error_handler.get_interface_health_status("1101")
    print(f"\n接口1101健康状态: {health_status}")


def demo_error_context_and_formatting():
    """演示错误上下文和格式化"""
    print("\n" + "=" * 60)
    print("5. 错误上下文和格式化演示")
    print("=" * 60)
    
    # 使用错误上下文
    ctx = None
    try:
        with ErrorContext("user_registration", user_id="12345", action="validate") as ctx:
            time.sleep(0.1)  # 模拟操作
            raise ValidationException("用户名已存在", field_errors={"username": ["该用户名已被使用"]})
    except Exception as e:
        if ctx:
            print("错误上下文信息:")
            context_info = ctx.to_dict()
            for key, value in context_info.items():
                print(f"  {key}: {value}")
        
        # 格式化用户友好的错误信息
        user_error = format_error_for_user(e)
        print(f"\n用户友好格式: {user_error}")
        
        # 创建API错误响应
        api_response = create_error_response(e, "user_registration", "req_12345", include_details=True)
        print(f"\nAPI错误响应: {api_response}")


def demo_specialized_decorators():
    """演示专用装饰器"""
    print("\n" + "=" * 60)
    print("6. 专用装饰器演示")
    print("=" * 60)
    
    # 医保接口装饰器
    @handle_medical_interface_error
    def call_medical_api():
        print("  调用医保接口...")
        raise NetworkException("医保服务器响应超时", retry_after=5)
    
    # 数据库操作装饰器
    @handle_database_error
    def query_database():
        print("  查询数据库...")
        raise ConnectionError("数据库连接失败")
    
    # 缓存操作装饰器
    @handle_cache_error
    def get_from_cache():
        print("  从缓存获取数据...")
        raise ConnectionError("Redis连接失败")
        return "cached_data"
    
    # 测试各种装饰器
    operations = [
        ("医保接口", call_medical_api),
        ("数据库操作", query_database),
        ("缓存操作", get_from_cache)
    ]
    
    for name, operation in operations:
        try:
            result = operation()
            print(f"  {name}: ✓ {result}")
        except Exception as e:
            print(f"  {name}: ✗ {e}")


def main():
    """主演示函数"""
    print("医保SDK错误处理系统功能演示")
    print("=" * 60)
    
    demo_exception_hierarchy()
    demo_retry_mechanism()
    demo_circuit_breaker()
    demo_medical_interface_error_handling()
    demo_error_context_and_formatting()
    demo_specialized_decorators()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()