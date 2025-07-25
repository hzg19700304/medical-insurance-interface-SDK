#!/usr/bin/env python3
"""
测试日志和监控系统 - 连接真实数据库
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.log_manager import LogManager, LogContext
from medical_insurance_sdk.core.data_manager import DataManager, LogQuery, StatQuery
from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.models.log import OperationLog


def test_database_connection():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    
    try:
        # 从环境变量创建数据库配置
        db_config = DatabaseConfig.from_env()
        print(f"数据库配置: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(db_config)
        
        # 测试连接
        health = db_manager.check_connection_health()
        if health:
            print("✅ 数据库连接健康")
        else:
            print("❌ 数据库连接异常")
            return None
        
        # 测试查询
        tables = db_manager.execute_query("SHOW TABLES")
        print(f"✅ 数据库包含 {len(tables)} 个表:")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"   - {table_name}")
        
        return db_manager
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


def test_data_manager_with_real_db(db_manager):
    """测试数据管理器 - 真实数据库"""
    print("\n=== 测试数据管理器（真实数据库） ===")
    
    try:
        # 创建数据管理器
        data_manager = DataManager(db_manager)
        print("✅ 数据管理器创建成功")
        
        # 创建测试用的操作日志
        operation_log = OperationLog(
            operation_id=f'test-op-{uuid.uuid4().hex[:8]}',
            api_code='1101',
            api_name='人员信息获取',
            business_category='基础信息业务',
            business_type='query',
            institution_code='TEST_ORG_001',
            psn_no='430123199001011234',
            request_data={
                'infno': '1101',
                'input': {
                    'psn_no': '430123199001011234'
                }
            },
            response_data={
                'infcode': 0,
                'output': {
                    'baseinfo': {
                        'psn_name': '张三',
                        'gend': '1',
                        'brdy': '1990-01-01'
                    }
                }
            },
            status='success',
            trace_id=f'test-trace-{uuid.uuid4().hex[:8]}',
            client_ip='127.0.0.1',
            operation_time=datetime.now(),
            complete_time=datetime.now()
        )
        
        # 测试保存操作日志
        print("测试保存操作日志...")
        success = data_manager.save_operation_log(operation_log)
        if success:
            print("✅ 操作日志保存成功")
        else:
            print("❌ 操作日志保存失败")
            return False
        
        # 测试查询操作日志
        print("测试查询操作日志...")
        query = LogQuery(
            api_code='1101',
            institution_code='TEST_ORG_001',
            status='success',
            limit=10
        )
        
        logs = data_manager.get_operation_logs(query)
        print(f"✅ 查询到 {len(logs)} 条操作日志")
        
        if logs:
            latest_log = logs[0]
            print(f"   最新日志: {latest_log.operation_id} - {latest_log.api_name}")
            print(f"   操作时间: {latest_log.operation_time}")
            print(f"   状态: {latest_log.status}")
        
        # 测试根据ID查询
        print("测试根据ID查询...")
        log_by_id = data_manager.get_operation_log_by_id(operation_log.operation_id)
        if log_by_id:
            print(f"✅ 根据ID查询成功: {log_by_id.operation_id}")
        else:
            print("❌ 根据ID查询失败")
        
        # 测试统计功能
        print("测试统计功能...")
        stat_query = StatQuery(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            api_code='1101',
            group_by='api_code'
        )
        
        stat_result = data_manager.get_statistics(stat_query)
        print(f"✅ 统计查询成功:")
        print(f"   总调用数: {stat_result.total_count}")
        print(f"   成功数: {stat_result.success_count}")
        print(f"   失败数: {stat_result.failed_count}")
        print(f"   成功率: {stat_result.success_rate:.2f}%")
        print(f"   平均响应时间: {stat_result.avg_response_time:.2f}秒")
        
        # 测试接口统计
        print("测试接口统计...")
        interface_stats = data_manager.get_interface_statistics('1101', days=1)
        print(f"✅ 接口统计:")
        print(f"   接口编码: {interface_stats.api_code}")
        print(f"   总调用数: {interface_stats.total_calls}")
        print(f"   成功率: {interface_stats.success_rate:.2f}%")
        
        # 测试系统统计
        print("测试系统统计...")
        system_stats = data_manager.get_system_statistics(days=1)
        print(f"✅ 系统统计:")
        print(f"   总调用数: {system_stats.total_calls}")
        print(f"   活跃接口数: {system_stats.total_apis}")
        print(f"   活跃机构数: {len(system_stats.active_institutions)}")
        
        # 测试错误摘要
        print("测试错误摘要...")
        error_summary = data_manager.get_error_summary(hours=24)
        print(f"✅ 错误摘要: {len(error_summary)} 种错误类型")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_operations(db_manager):
    """测试批量操作"""
    print("\n=== 测试批量操作 ===")
    
    try:
        data_manager = DataManager(db_manager)
        
        # 创建多个测试日志
        operation_logs = []
        for i in range(5):
            log = OperationLog(
                operation_id=f'batch-test-{uuid.uuid4().hex[:8]}',
                api_code=f'110{i+1}',
                api_name=f'测试接口{i+1}',
                business_category='基础信息业务',
                business_type='query',
                institution_code=f'TEST_ORG_{i+1:03d}',
                psn_no=f'43012319900101123{i}',
                request_data={'test': f'data_{i}'},
                response_data={'result': f'success_{i}'},
                status='success' if i % 2 == 0 else 'failed',
                trace_id=f'batch-trace-{uuid.uuid4().hex[:8]}',
                client_ip='192.168.1.100',
                operation_time=datetime.now() - timedelta(minutes=i),
                complete_time=datetime.now() - timedelta(minutes=i) + timedelta(seconds=1)
            )
            operation_logs.append(log)
        
        # 批量保存
        print("测试批量保存...")
        saved_count = data_manager.batch_save_operation_logs(operation_logs)
        print(f"✅ 批量保存成功: {saved_count} 条记录")
        
        # 验证保存结果
        print("验证批量保存结果...")
        query = LogQuery(
            start_time=datetime.now() - timedelta(hours=1),
            limit=20
        )
        all_logs = data_manager.get_operation_logs(query)
        print(f"✅ 当前总共有 {len(all_logs)} 条日志记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_real_db(db_manager):
    """测试完整集成 - 真实数据库"""
    print("\n=== 测试完整集成（真实数据库） ===")
    
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
        data_manager = DataManager(db_manager)
        
        # 模拟完整的API调用流程
        trace_id = f'integration-test-{uuid.uuid4().hex[:8]}'
        operation_id = f'op-{uuid.uuid4().hex[:8]}'
        
        context = {
            'trace_id': trace_id,
            'operation_id': operation_id,
            'operation': 'api_call_1101',
            'api_code': '1101',
            'org_code': 'INTEGRATION_TEST_ORG',
            'client_ip': '192.168.1.200'
        }
        
        print(f"开始集成测试，追踪ID: {trace_id}")
        
        with LogContext(log_manager, **context) as log_ctx:
            log_ctx.log_info("开始处理API调用")
            
            # 模拟API调用
            request_data = {
                'infno': '1101',
                'input': {
                    'psn_no': '430123199001011234',
                    'certno': '430123199001011234'
                }
            }
            
            # 模拟处理时间
            import time
            time.sleep(0.1)
            
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
            
            # 记录API调用日志
            log_manager.log_api_call('1101', request_data, response_data, context)
            
            # 创建操作日志并保存到数据库
            operation_log = OperationLog(
                operation_id=operation_id,
                api_code='1101',
                api_name='人员信息获取',
                business_category='基础信息业务',
                business_type='query',
                institution_code='INTEGRATION_TEST_ORG',
                psn_no='430123199001011234',
                request_data=request_data,
                response_data=response_data,
                status='success',
                trace_id=trace_id,
                client_ip='192.168.1.200',
                operation_time=datetime.now() - timedelta(seconds=1),
                complete_time=datetime.now()
            )
            
            # 保存到数据库
            success = data_manager.save_operation_log(operation_log)
            if success:
                log_ctx.log_info("操作日志保存到数据库成功")
            else:
                log_ctx.log_info("操作日志保存到数据库失败")
            
            log_ctx.log_info("API调用处理完成")
        
        # 验证数据库中的记录
        print("验证数据库记录...")
        saved_log = data_manager.get_operation_log_by_id(operation_id)
        if saved_log:
            print(f"✅ 数据库验证成功:")
            print(f"   操作ID: {saved_log.operation_id}")
            print(f"   追踪ID: {saved_log.trace_id}")
            print(f"   API编码: {saved_log.api_code}")
            print(f"   状态: {saved_log.status}")
            print(f"   机构编码: {saved_log.institution_code}")
        else:
            print("❌ 数据库验证失败，未找到记录")
            return False
        
        # 检查日志文件
        log_files = list(Path(temp_dir).glob('*.log'))
        if log_files:
            print(f"✅ 生成了 {len(log_files)} 个日志文件")
            
            # 检查日志内容
            with open(log_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                if trace_id in content:
                    print("✅ 日志文件包含追踪ID")
                else:
                    print("⚠ 日志文件不包含追踪ID")
        
        print("✅ 完整集成测试通过")
        
        log_manager.close()
        return True
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """主测试函数"""
    print("开始测试日志和监控系统（连接真实数据库）...")
    
    try:
        # 测试数据库连接
        db_manager = test_database_connection()
        if not db_manager:
            print("❌ 数据库连接失败，无法继续测试")
            return 1
        
        # 测试数据管理器
        if not test_data_manager_with_real_db(db_manager):
            print("❌ 数据管理器测试失败")
            return 1
        
        # 测试批量操作
        if not test_batch_operations(db_manager):
            print("❌ 批量操作测试失败")
            return 1
        
        # 测试完整集成
        if not test_integration_with_real_db(db_manager):
            print("❌ 完整集成测试失败")
            return 1
        
        # 关闭数据库连接
        db_manager.close()
        
        print("\n🎉 所有测试通过！日志和监控系统与真实数据库集成成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())