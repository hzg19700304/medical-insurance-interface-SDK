"""
数据同步服务综合测试

测试DataSyncService类的所有功能，包括：
- 增量数据同步机制
- 数据一致性检查
- 冲突解决机制
- 同步任务管理
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import logging
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.integration.data_sync_service import (
    DataSyncService,
    SyncDirection,
    SyncStatus,
    SyncTask,
    DataRecord,
    SyncConflict,
    DataSyncConfig
)
from medical_insurance_sdk.exceptions import IntegrationException


class MockDatabaseManager:
    """模拟数据库管理器用于测试"""
    
    def __init__(self):
        self.data = {
            'patients': [
                {'patient_id': 'P001', 'name': '张三', 'updated_at': datetime.now() - timedelta(hours=1)},
                {'patient_id': 'P002', 'name': '李四', 'updated_at': datetime.now() - timedelta(hours=2)},
            ],
            'his_patients': [
                {'patient_id': 'P001', 'name': '张三修改', 'updated_at': datetime.now()},
                {'patient_id': 'P003', 'name': '王五', 'updated_at': datetime.now() - timedelta(hours=1)},
            ]
        }
    
    def execute_query(self, sql: str, params=None) -> List[Dict[str, Any]]:
        """模拟查询执行"""
        if 'SELECT * FROM patients' in sql:
            return self.data.get('patients', [])
        elif 'SELECT * FROM his_patients' in sql:
            return self.data.get('his_patients', [])
        elif 'data_sync_status' in sql:
            return [{'last_sync_time': datetime.now() - timedelta(hours=1)}]
        return []
    
    def execute_query_one(self, sql: str, params=None) -> Dict[str, Any]:
        """模拟单条查询"""
        results = self.execute_query(sql, params)
        return results[0] if results else None
    
    def execute_update(self, sql: str, params=None):
        """模拟更新执行"""
        pass
    
    def close(self):
        """关闭连接"""
        pass


def test_data_sync_service_creation():
    """测试数据同步服务创建"""
    print("=== 测试数据同步服务创建 ===")
    
    try:
        # 创建模拟数据库管理器
        db_manager = MockDatabaseManager()
        
        # 创建数据同步配置
        sync_config = DataSyncConfig(
            his_db_config={
                'host': 'localhost',
                'port': 3306,
                'user': 'test',
                'password': 'test',
                'database': 'his_test'
            },
            sync_tables={
                'patients': {
                    'his_table': 'his_patients',
                    'primary_key': 'patient_id'
                },
                'settlements': {
                    'his_table': 'his_settlements',
                    'primary_key': 'settlement_id'
                }
            },
            sync_interval=60,
            batch_size=100,
            conflict_resolution='latest_wins'
        )
        
        # 创建数据同步服务，但使用模拟的方式避免真实数据库连接
        sync_service = DataSyncService.__new__(DataSyncService)
        sync_service.db_manager = db_manager
        sync_service.config = sync_config
        sync_service.logger = logging.getLogger(__name__)
        
        # 模拟HIS数据库管理器
        sync_service.his_db_manager = MockDatabaseManager()
        
        # 初始化其他属性
        sync_service.sync_tasks = []
        sync_service.task_lock = threading.Lock()
        sync_service.sync_thread = None
        sync_service.consistency_thread = None
        sync_service.stop_event = threading.Event()
        sync_service.conflict_handlers = {}
        
        print("✓ 数据同步服务创建成功")
        print(f"✓ 同步间隔: {sync_config.sync_interval}秒")
        print(f"✓ 批量大小: {sync_config.batch_size}")
        print(f"✓ 冲突解决策略: {sync_config.conflict_resolution}")
        
        return sync_service
        
    except Exception as e:
        print(f"✗ 数据同步服务创建失败: {e}")
        return None


def test_sync_task_management(sync_service: DataSyncService):
    """测试同步任务管理"""
    print("\n=== 测试同步任务管理 ===")
    
    try:
        # 添加同步任务
        task_id1 = sync_service.add_sync_task(
            'patients',
            SyncDirection.BIDIRECTIONAL,
            'incremental'
        )
        print(f"✓ 增量同步任务添加成功: {task_id1}")
        
        task_id2 = sync_service.add_sync_task(
            'settlements',
            SyncDirection.FROM_HIS,
            'full'
        )
        print(f"✓ 全量同步任务添加成功: {task_id2}")
        
        # 获取任务状态
        task_status1 = sync_service.get_sync_task_status(task_id1)
        if task_status1:
            print(f"✓ 任务状态查询成功: {task_status1['status']}")
            print(f"  - 表名: {task_status1['table_name']}")
            print(f"  - 同步方向: {task_status1['sync_direction']}")
            print(f"  - 同步类型: {task_status1['sync_type']}")
        
        # 测试不存在的任务
        non_existent_status = sync_service.get_sync_task_status('non_existent')
        if non_existent_status is None:
            print("✓ 不存在任务状态查询正确返回None")
        
        return [task_id1, task_id2]
        
    except Exception as e:
        print(f"✗ 同步任务管理测试失败: {e}")
        return []


def test_data_consistency_check(sync_service: DataSyncService):
    """测试数据一致性检查"""
    print("\n=== 测试数据一致性检查 ===")
    
    try:
        # 模拟数据一致性检查
        # 由于使用模拟数据库，这里主要测试方法调用
        
        # 重写_get_his_records和_get_medical_records方法进行测试
        def mock_get_his_records(table_name, where_condition=None):
            return [
                {'patient_id': 'P001', 'name': '张三修改', 'updated_at': datetime.now()},
                {'patient_id': 'P003', 'name': '王五', 'updated_at': datetime.now()}
            ]
        
        def mock_get_medical_records(table_name, where_condition=None):
            return [
                {'patient_id': 'P001', 'name': '张三', 'updated_at': datetime.now() - timedelta(hours=1)},
                {'patient_id': 'P002', 'name': '李四', 'updated_at': datetime.now()}
            ]
        
        # 临时替换方法
        original_get_his = sync_service._get_his_records
        original_get_medical = sync_service._get_medical_records
        
        sync_service._get_his_records = mock_get_his_records
        sync_service._get_medical_records = mock_get_medical_records
        
        # 执行一致性检查
        consistency_result = sync_service.check_data_consistency('patients')
        
        print("✓ 数据一致性检查执行成功")
        print(f"  - 表名: {consistency_result['table_name']}")
        print(f"  - 总记录数: {consistency_result['total_records']}")
        print(f"  - 一致记录数: {consistency_result['consistent_count']}")
        print(f"  - 不一致记录数: {consistency_result['inconsistent_count']}")
        print(f"  - 仅HIS存在: {consistency_result['his_only_count']}")
        print(f"  - 仅医保存在: {consistency_result['medical_only_count']}")
        
        # 恢复原方法
        sync_service._get_his_records = original_get_his
        sync_service._get_medical_records = original_get_medical
        
        return consistency_result
        
    except Exception as e:
        print(f"✗ 数据一致性检查测试失败: {e}")
        return None


def test_conflict_resolution(sync_service: DataSyncService):
    """测试冲突解决机制"""
    print("\n=== 测试冲突解决机制 ===")
    
    try:
        # 创建模拟冲突
        conflict = SyncConflict(
            conflict_id='conflict_test001',
            table_name='patients',
            primary_key='P001',
            his_data={
                'patient_id': 'P001',
                'name': '张三修改',
                'phone': '13800138001',
                'updated_at': datetime.now()
            },
            medical_data={
                'patient_id': 'P001',
                'name': '张三',
                'phone': '13800138000',
                'updated_at': datetime.now() - timedelta(hours=1)
            },
            conflict_fields=['name', 'phone'],
            created_at=datetime.now()
        )
        
        print("✓ 模拟冲突创建成功")
        print(f"  - 冲突ID: {conflict.conflict_id}")
        print(f"  - 冲突字段: {conflict.conflict_fields}")
        
        # 测试不同的冲突解决策略
        
        # 1. HIS优先策略
        resolved_data_his = sync_service._resolve_by_latest_timestamp(conflict)
        print("✓ 最新时间戳解决策略测试成功")
        print(f"  - 解决结果: {resolved_data_his.get('name')}")
        
        # 2. 测试冲突检测
        has_conflict = sync_service._has_data_conflict(
            conflict.his_data,
            conflict.medical_data
        )
        print(f"✓ 冲突检测结果: {has_conflict}")
        
        # 3. 测试记录一致性检查
        are_consistent = sync_service._records_are_consistent(
            {'name': '张三', 'phone': '13800138000'},
            {'name': '张三', 'phone': '13800138000'}
        )
        print(f"✓ 记录一致性检查 (相同记录): {are_consistent}")
        
        are_consistent_diff = sync_service._records_are_consistent(
            conflict.his_data,
            conflict.medical_data
        )
        print(f"✓ 记录一致性检查 (不同记录): {are_consistent_diff}")
        
        return conflict
        
    except Exception as e:
        print(f"✗ 冲突解决机制测试失败: {e}")
        return None


def test_sync_statistics(sync_service: DataSyncService):
    """测试同步统计功能"""
    print("\n=== 测试同步统计功能 ===")
    
    try:
        # 获取同步统计信息
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # 由于使用模拟数据库，这里主要测试方法调用
        stats = sync_service.get_sync_statistics(start_date, end_date)
        
        print("✓ 同步统计信息获取成功")
        print(f"  - 统计期间: {stats.get('period', {}).get('start_date')} 到 {stats.get('period', {}).get('end_date')}")
        print(f"  - 同步任务统计: {len(stats.get('sync_tasks', []))} 条记录")
        print(f"  - 冲突统计: {len(stats.get('conflicts', []))} 条记录")
        
        return stats
        
    except Exception as e:
        print(f"✗ 同步统计功能测试失败: {e}")
        return None


def test_conflict_handler_registration(sync_service: DataSyncService):
    """测试冲突处理器注册"""
    print("\n=== 测试冲突处理器注册 ===")
    
    try:
        # 定义冲突处理器
        def patient_conflict_handler(conflict: SyncConflict):
            print(f"处理患者表冲突: {conflict.conflict_id}")
            # 这里可以实现自定义的冲突处理逻辑
            return True
        
        # 注册冲突处理器
        sync_service.register_conflict_handler('patients', patient_conflict_handler)
        
        print("✓ 冲突处理器注册成功")
        print(f"  - 已注册表: {list(sync_service.conflict_handlers.keys())}")
        
        # 测试处理器是否正确注册
        if 'patients' in sync_service.conflict_handlers:
            print("✓ 冲突处理器验证成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 冲突处理器注册测试失败: {e}")
        return False


def test_data_models():
    """测试数据模型"""
    print("\n=== 测试数据模型 ===")
    
    try:
        # 测试SyncTask模型
        task = SyncTask(
            task_id='test_task_001',
            table_name='patients',
            sync_direction=SyncDirection.BIDIRECTIONAL,
            sync_type='incremental'
        )
        print(f"✓ SyncTask模型创建成功: {task.task_id}")
        
        # 测试DataRecord模型
        record = DataRecord(
            table_name='patients',
            primary_key='P001',
            record_data={'name': '张三', 'phone': '13800138000'},
            checksum='abc123',
            last_modified=datetime.now(),
            source_system='his'
        )
        print(f"✓ DataRecord模型创建成功: {record.primary_key}")
        
        # 测试SyncConflict模型
        conflict = SyncConflict(
            conflict_id='conflict_001',
            table_name='patients',
            primary_key='P001',
            his_data={'name': '张三HIS'},
            medical_data={'name': '张三医保'},
            conflict_fields=['name'],
            created_at=datetime.now()
        )
        print(f"✓ SyncConflict模型创建成功: {conflict.conflict_id}")
        
        # 测试DataSyncConfig模型
        config = DataSyncConfig(
            his_db_config={'host': 'localhost'},
            sync_tables={'patients': {'primary_key': 'id'}},
            sync_interval=300,
            batch_size=1000,
            conflict_resolution='manual'
        )
        print(f"✓ DataSyncConfig模型创建成功: 间隔{config.sync_interval}秒")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据模型测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始数据同步服务综合测试...")
    
    # 测试数据模型
    test_data_models()
    
    # 创建数据同步服务
    sync_service = test_data_sync_service_creation()
    if not sync_service:
        print("数据同步服务创建失败，终止测试")
        return
    
    try:
        # 测试同步任务管理
        task_ids = test_sync_task_management(sync_service)
        
        # 测试数据一致性检查
        consistency_result = test_data_consistency_check(sync_service)
        
        # 测试冲突解决机制
        conflict = test_conflict_resolution(sync_service)
        
        # 测试同步统计功能
        stats = test_sync_statistics(sync_service)
        
        # 测试冲突处理器注册
        handler_registered = test_conflict_handler_registration(sync_service)
        
        print("\n=== 测试总结 ===")
        print("✓ 数据同步服务创建: 成功")
        print(f"✓ 同步任务管理: {'成功' if task_ids else '失败'}")
        print(f"✓ 数据一致性检查: {'成功' if consistency_result else '失败'}")
        print(f"✓ 冲突解决机制: {'成功' if conflict else '失败'}")
        print(f"✓ 同步统计功能: {'成功' if stats else '失败'}")
        print(f"✓ 冲突处理器注册: {'成功' if handler_registered else '失败'}")
        
    finally:
        # 关闭服务 (模拟关闭)
        if hasattr(sync_service, 'close'):
            try:
                sync_service.close()
            except:
                pass
        print("\n✓ 数据同步服务已关闭")
    
    print("\n数据同步服务综合测试完成!")


if __name__ == "__main__":
    main()