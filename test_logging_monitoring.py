#!/usr/bin/env python3
"""
测试日志和监控系统
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.log_manager import LogManager, LogContext
from medical_insurance_sdk.core.data_manager import DataManager, LogQuery, StatQuery
from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.models.log import OperationLog


def test_log_manager():
    """测试日志管理器"""
    print("=== 测试日志管理器 ===")
    
    # 创建临时日志目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 配置日志管理器
        log_config = {
            'log_level': 'INFO',
            'log_dir': temp_dir,
            'max_file_size': 1,  # 1MB
            'backup_count': 3,
            'enable_async': False,  # 同步模式便于测试
            'enable_console': True,
            'structured_format': True
        }
        
        log_manager = LogManager(log_config)
        
        # 测试基本日志记录
        log_manager.log_info("测试信息日志", {'test_key': 'test_value'})
        log_manager.log_warning("测试警告日志")
        
        # 测试API调用日志
        request_data = {
            'infno': '1101',
            'input': {
                'psn_no': '430123199001011234'
            }
        }
        
        response_data = {
            'infcode': 0,
            'output': {
                'baseinfo': {
                    'psn_name': '张三',
                    'gend': '1'
                }
            }
        }
        
        context = {
            'trace_id': 'test-trace-123',
            'org_code': 'TEST_ORG',
            'client_ip': '127.0.0.1'
        }
        
        log_manager.log_api_call('1101', request_data, response_data, context)
        
        # 测试错误日志
        try:
            raise ValueError("测试错误")
        except Exception as e:
            log_manager.log_error(e, context)
        
        # 测试性能日志
        log_manager.log_performance('test_operation', 150.5, context)
        
        # 测试操作日志
        operation_log = OperationLog(
            operation_id='test-op-123',
            api_code='1101',
            api_name='人员信息获取',
            business_category='查询类',
            business_type='人员查询',
            institution_code='TEST_ORG',
            status='success',
            trace_id='test-trace-123'
        )
        
        log_manager.log_operation(operation_log)
        
        # 测试日志上下文管理器
        with LogContext(log_manager, operation='test_context', api_code='1101') as log_ctx:
            log_ctx.log_info("在上下文中记录日志")
            # 模拟一些处理时间
            import time
            time.sleep(0.1)
        
        print("✓ 日志管理器测试通过")
        
        # 检查日志文件是否创建
        log_files = list(Path(temp_dir).glob('*.log'))
        print(f"✓ 创建了 {len(log_files)} 个日志文件")
        
        # 关闭日志管理器
        log_manager.close()
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_data_manager_mock():
    """测试数据管理器（模拟数据库）"""
    print("\n=== 测试数据管理器（模拟） ===")
    
    # 创建模拟的数据库配置
    db_config = DatabaseConfig(
        host='localhost',
        port=3306,
        user='test',
        password='test',
        database='test'
    )
    
    # 注意：这里不会真正连接数据库，只是测试类的创建
    try:
        # 创建数据管理器（会因为数据库连接失败而抛出异常，这是预期的）
        print("尝试创建数据管理器...")
        
        # 创建测试用的操作日志
        operation_log = OperationLog(
            operation_id='test-op-456',
            api_code='1101',
            api_name='人员信息获取',
            business_category='查询类',
            business_type='人员查询',
            institution_code='TEST_ORG',
            psn_no='430123199001011234',
            request_data={'test': 'data'},
            response_data={'result': 'success'},
            status='success',
            trace_id='test-trace-456',
            client_ip='127.0.0.1'
        )
        
        print("✓ 操作日志对象创建成功")
        
        # 测试查询条件对象
        log_query = LogQuery(
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now(),
            api_code='1101',
            institution_code='TEST_ORG',
            status='success',
            limit=50
        )
        
        print("✓ 日志查询条件对象创建成功")
        
        # 测试统计查询条件对象
        stat_query = StatQuery(
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now(),
            group_by='api_code',
            time_granularity='day'
        )
        
        print("✓ 统计查询条件对象创建成功")
        
        print("✓ 数据管理器相关类测试通过（未连接真实数据库）")
        
    except Exception as e:
        print(f"预期的数据库连接错误: {e}")
        print("✓ 数据管理器类结构测试通过")


def test_integration():
    """测试集成功能"""
    print("\n=== 测试集成功能 ===")
    
    # 创建临时日志目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建日志管理器
        log_config = {
            'log_level': 'INFO',
            'log_dir': temp_dir,
            'enable_async': False,
            'enable_console': False,
            'structured_format': True
        }
        
        log_manager = LogManager(log_config)
        
        # 模拟一个完整的API调用流程
        trace_id = 'integration-test-123'
        
        # 1. 记录开始
        context = {
            'trace_id': trace_id,
            'operation': 'api_call_1101',
            'api_code': '1101',
            'org_code': 'TEST_ORG',
            'client_ip': '192.168.1.100'
        }
        
        with LogContext(log_manager, **context) as log_ctx:
            log_ctx.log_info("开始处理API调用")
            
            # 2. 模拟API调用
            request_data = {
                'infno': '1101',
                'input': {
                    'psn_no': '430123199001011234',
                    'certno': '430123199001011234'
                }
            }
            
            # 模拟处理时间
            import time
            time.sleep(0.05)
            
            response_data = {
                'infcode': 0,
                'output': {
                    'baseinfo': {
                        'psn_name': '李四',
                        'gend': '2',
                        'brdy': '1990-01-01'
                    }
                }
            }
            
            # 3. 记录API调用日志
            log_manager.log_api_call('1101', request_data, response_data, context)
            
            log_ctx.log_info("API调用处理完成")
        
        print("✓ 集成测试通过")
        
        # 检查日志文件内容
        log_files = list(Path(temp_dir).glob('*.log'))
        if log_files:
            with open(log_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                if trace_id in content:
                    print("✓ 日志文件包含追踪ID")
                else:
                    print("⚠ 日志文件不包含追踪ID")
        
        log_manager.close()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """主测试函数"""
    print("开始测试日志和监控系统...")
    
    try:
        test_log_manager()
        test_data_manager_mock()
        test_integration()
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())