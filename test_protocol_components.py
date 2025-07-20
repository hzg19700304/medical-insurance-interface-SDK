"""
测试医保协议处理组件
"""

import time
from medical_insurance_sdk.core.gateway_auth import GatewayHeaders, GatewayAuthenticator
from medical_insurance_sdk.core.protocol_processor import MessageIdGenerator, ProtocolValidator


def test_gateway_headers():
    """测试网关请求头生成"""
    print("=== 测试网关请求头生成 ===")
    
    # 创建网关请求头
    gateway = GatewayHeaders(
        api_name="test_api",
        api_version="1.0",
        access_key="test_ak",
        secret_key="test_sk"
    )
    
    # 生成请求头
    headers = gateway.generate_headers()
    
    print("生成的请求头:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    # 验证签名
    is_valid = GatewayAuthenticator.verify_signature(
        api_name="test_api",
        api_version="1.0",
        timestamp=gateway.timestamp,
        access_key="test_ak",
        secret_key="test_sk",
        provided_signature=headers['_api_signature']
    )
    
    print(f"签名验证结果: {'通过' if is_valid else '失败'}")
    
    # 测试时间戳验证
    is_timestamp_valid = GatewayAuthenticator.check_timestamp_validity(gateway.timestamp)
    print(f"时间戳验证结果: {'有效' if is_timestamp_valid else '无效'}")
    
    return is_valid and is_timestamp_valid


def test_message_id_generation():
    """测试报文ID生成"""
    print("\n=== 测试报文ID生成 ===")
    
    # 测试UUID方式
    uuid_id = MessageIdGenerator.generate_uuid_based()
    print(f"UUID方式生成的报文ID: {uuid_id} (长度: {len(uuid_id)})")
    
    # 测试时间戳方式
    timestamp_id = MessageIdGenerator.generate_timestamp_based()
    print(f"时间戳方式生成的报文ID: {timestamp_id} (长度: {len(timestamp_id)})")
    
    # 测试序列号方式
    sequential_id = MessageIdGenerator.generate_sequential()
    print(f"序列号方式生成的报文ID: {sequential_id} (长度: {len(sequential_id)})")
    
    # 验证ID唯一性
    ids = set()
    for _ in range(100):
        ids.add(MessageIdGenerator.generate_uuid_based())
    
    print(f"生成100个UUID报文ID，唯一性检查: {'通过' if len(ids) == 100 else '失败'}")
    
    return len(uuid_id) <= 30 and len(timestamp_id) <= 30 and len(sequential_id) <= 30


def test_protocol_validator():
    """测试协议验证器"""
    print("\n=== 测试协议验证器 ===")
    
    # 测试接口编码验证
    valid_api_codes = ["1101", "2201", "4701"]
    invalid_api_codes = ["110", "11011", "abcd", ""]
    
    print("接口编码验证:")
    for code in valid_api_codes:
        result = ProtocolValidator.validate_api_code(code)
        print(f"  {code}: {'有效' if result else '无效'}")
    
    for code in invalid_api_codes:
        result = ProtocolValidator.validate_api_code(code)
        print(f"  {code}: {'有效' if result else '无效'}")
    
    # 测试区划代码验证
    valid_region_codes = ["430100", "440100"]
    invalid_region_codes = ["43010", "4301001", "abcdef"]
    
    print("\n区划代码验证:")
    for code in valid_region_codes:
        result = ProtocolValidator.validate_region_code(code)
        print(f"  {code}: {'有效' if result else '无效'}")
    
    for code in invalid_region_codes:
        result = ProtocolValidator.validate_region_code(code)
        print(f"  {code}: {'有效' if result else '无效'}")
    
    # 测试时间戳格式验证
    valid_timestamps = ["2024-01-15 10:30:00", "2023-12-31 23:59:59"]
    invalid_timestamps = ["2024-01-15", "10:30:00", "2024/01/15 10:30:00"]
    
    print("\n时间戳格式验证:")
    for ts in valid_timestamps:
        result = ProtocolValidator.validate_timestamp_format(ts)
        print(f"  {ts}: {'有效' if result else '无效'}")
    
    for ts in invalid_timestamps:
        result = ProtocolValidator.validate_timestamp_format(ts)
        print(f"  {ts}: {'有效' if result else '无效'}")
    
    return True


def test_gateway_error_handling():
    """测试网关错误处理"""
    print("\n=== 测试网关错误处理 ===")
    
    from medical_insurance_sdk.core.gateway_auth import GatewayErrorHandler
    
    # 测试不同类型的错误
    test_cases = [
        (401, "缺少服务网关的请求头"),
        (401, "签名时间戳超时"),
        (401, "非法用户"),
        (401, "签名不一致"),
        (500, "服务器内部错误")
    ]
    
    for code, message in test_cases:
        error = GatewayErrorHandler.handle_gateway_error(code, message)
        print(f"错误码 {code}, 消息 '{message}':")
        print(f"  处理结果: {error.message}")
        print(f"  详细信息: {error.details}")
    
    return True


if __name__ == "__main__":
    print("开始测试医保协议处理组件...")
    
    try:
        # 运行所有测试
        test1_result = test_gateway_headers()
        test2_result = test_message_id_generation()
        test3_result = test_protocol_validator()
        test4_result = test_gateway_error_handling()
        
        print(f"\n=== 测试结果汇总 ===")
        print(f"网关请求头测试: {'通过' if test1_result else '失败'}")
        print(f"报文ID生成测试: {'通过' if test2_result else '失败'}")
        print(f"协议验证器测试: {'通过' if test3_result else '失败'}")
        print(f"错误处理测试: {'通过' if test4_result else '失败'}")
        
        all_passed = all([test1_result, test2_result, test3_result, test4_result])
        print(f"\n总体测试结果: {'全部通过' if all_passed else '存在失败'}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()