"""
数据同步服务

提供增量数据同步机制和数据一致性检查功能，包括：
- 增量数据同步
- 数据一致性检查
- 同步任务调度
- 冲突解决机制
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

from ..core.database import DatabaseManager, DatabaseConfig
from ..exceptions import (
    MedicalInsuranceException,
    ValidationException,
    DatabaseException,
    IntegrationException
)


class SyncDirection(Enum):
    """同步方向"""
    BIDIRECTIONAL = "bidirectional"  # 双向同步
    TO_HIS = "to_his"  # 同步到HIS
    FROM_HIS = "from_his"  # 从HIS同步


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"  # 待同步
    RUNNING = "running"  # 同步中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CONFLICT = "conflict"  # 冲突


@dataclass
class SyncTask:
    """同步任务"""
    task_id: str
    table_name: str
    sync_direction: SyncDirection
    sync_type: str  # full, incremental
    status: SyncStatus = SyncStatus.PENDING
    
    # 同步条件
    where_condition: Optional[str] = None
    sync_fields: Optional[List[str]] = None
    
    # 时间戳
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 结果统计
    total_records: int = 0
    synced_records: int = 0
    failed_records: int = 0
    conflict_records: int = 0
    
    # 错误信息
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class DataRecord:
    """数据记录"""
    table_name: str
    primary_key: str
    record_data: Dict[str, Any]
    checksum: str
    last_modified: datetime
    source_system: str  # his, medical_insurance


@dataclass
class SyncConflict:
    """同步冲突"""
    conflict_id: str
    table_name: str
    primary_key: str
    his_data: Dict[str, Any]
    medical_data: Dict[str, Any]
    conflict_fields: List[str]
    created_at: datetime
    resolved: bool = False
    resolution_strategy: Optional[str] = None


@dataclass
class DataSyncConfig:
    """数据同步配置"""
    # HIS数据库配置
    his_db_config: Dict[str, Any]
    
    # 同步表配置
    sync_tables: Dict[str, Dict[str, Any]]
    
    # 同步策略
    sync_interval: int = 300  # 同步间隔（秒）
    batch_size: int = 1000  # 批量处理大小
    max_retry_times: int = 3  # 最大重试次数
    
    # 冲突解决策略
    conflict_resolution: str = "manual"  # manual, his_wins, medical_wins, latest_wins
    
    # 数据一致性检查
    consistency_check_enabled: bool = True
    consistency_check_interval: int = 3600  # 一致性检查间隔（秒）


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self, db_manager: DatabaseManager, config: DataSyncConfig):
        self.db_manager = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # HIS数据库连接
        his_db_config = DatabaseConfig(**config.his_db_config)
        self.his_db_manager = DatabaseManager(his_db_config, pool_name="his_sync_db")
        
        # 同步任务队列
        self.sync_tasks: List[SyncTask] = []
        self.task_lock = threading.Lock()
        
        # 同步线程
        self.sync_thread: Optional[threading.Thread] = None
        self.consistency_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 冲突处理回调
        self.conflict_handlers: Dict[str, Callable] = {}
        
        self.logger.info("数据同步服务初始化完成")
    
    def start_sync_service(self):
        """启动同步服务"""
        if self.sync_thread and self.sync_thread.is_alive():
            self.logger.warning("同步服务已在运行")
            return
        
        self.stop_event.clear()
        
        # 启动同步线程
        self.sync_thread = threading.Thread(
            target=self._sync_worker,
            daemon=True,
            name="DataSyncWorker"
        )
        self.sync_thread.start()
        
        # 启动一致性检查线程
        if self.config.consistency_check_enabled:
            self.consistency_thread = threading.Thread(
                target=self._consistency_check_worker,
                daemon=True,
                name="ConsistencyCheckWorker"
            )
            self.consistency_thread.start()
        
        self.logger.info("数据同步服务已启动")
    
    def stop_sync_service(self):
        """停止同步服务"""
        self.stop_event.set()
        
        if self.sync_thread:
            self.sync_thread.join(timeout=10)
        
        if self.consistency_thread:
            self.consistency_thread.join(timeout=10)
        
        self.logger.info("数据同步服务已停止")
    
    def add_sync_task(self, table_name: str, sync_direction: SyncDirection, 
                      sync_type: str = "incremental", **kwargs) -> str:
        """添加同步任务"""
        task_id = self._generate_task_id()
        
        task = SyncTask(
            task_id=task_id,
            table_name=table_name,
            sync_direction=sync_direction,
            sync_type=sync_type,
            where_condition=kwargs.get('where_condition'),
            sync_fields=kwargs.get('sync_fields')
        )
        
        with self.task_lock:
            self.sync_tasks.append(task)
        
        self.logger.info(f"添加同步任务: {task_id} - {table_name}")
        return task_id
    
    def get_sync_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取同步任务状态"""
        with self.task_lock:
            for task in self.sync_tasks:
                if task.task_id == task_id:
                    return asdict(task)
        return None
    
    def perform_incremental_sync(self, table_name: str, sync_direction: SyncDirection,
                                last_sync_time: datetime = None) -> Dict[str, Any]:
        """执行增量同步"""
        if not last_sync_time:
            last_sync_time = self._get_last_sync_time(table_name)
        
        try:
            if sync_direction == SyncDirection.FROM_HIS:
                return self._sync_from_his(table_name, last_sync_time)
            elif sync_direction == SyncDirection.TO_HIS:
                return self._sync_to_his(table_name, last_sync_time)
            elif sync_direction == SyncDirection.BIDIRECTIONAL:
                result_from = self._sync_from_his(table_name, last_sync_time)
                result_to = self._sync_to_his(table_name, last_sync_time)
                return {
                    'from_his': result_from,
                    'to_his': result_to
                }
        except Exception as e:
            self.logger.error(f"增量同步失败 {table_name}: {e}")
            raise IntegrationException(f"增量同步失败: {e}")
    
    def perform_full_sync(self, table_name: str, sync_direction: SyncDirection) -> Dict[str, Any]:
        """执行全量同步"""
        try:
            if sync_direction == SyncDirection.FROM_HIS:
                return self._full_sync_from_his(table_name)
            elif sync_direction == SyncDirection.TO_HIS:
                return self._full_sync_to_his(table_name)
            elif sync_direction == SyncDirection.BIDIRECTIONAL:
                result_from = self._full_sync_from_his(table_name)
                result_to = self._full_sync_to_his(table_name)
                return {
                    'from_his': result_from,
                    'to_his': result_to
                }
        except Exception as e:
            self.logger.error(f"全量同步失败 {table_name}: {e}")
            raise IntegrationException(f"全量同步失败: {e}")
    
    def check_data_consistency(self, table_name: str) -> Dict[str, Any]:
        """检查数据一致性"""
        try:
            # 获取两边的数据记录
            his_records = self._get_his_records(table_name)
            medical_records = self._get_medical_records(table_name)
            
            # 比较数据一致性
            consistency_result = self._compare_data_consistency(
                table_name, his_records, medical_records
            )
            
            # 记录一致性检查结果
            self._save_consistency_check_result(table_name, consistency_result)
            
            return consistency_result
            
        except Exception as e:
            self.logger.error(f"数据一致性检查失败 {table_name}: {e}")
            raise IntegrationException(f"数据一致性检查失败: {e}")
    
    def resolve_conflict(self, conflict_id: str, resolution_strategy: str, 
                        custom_data: Dict[str, Any] = None) -> bool:
        """解决数据冲突"""
        try:
            # 获取冲突信息
            conflict = self._get_conflict_by_id(conflict_id)
            if not conflict:
                raise ValidationException(f"冲突记录不存在: {conflict_id}")
            
            # 根据策略解决冲突
            if resolution_strategy == "his_wins":
                resolved_data = conflict.his_data
            elif resolution_strategy == "medical_wins":
                resolved_data = conflict.medical_data
            elif resolution_strategy == "custom":
                resolved_data = custom_data or {}
            elif resolution_strategy == "latest_wins":
                resolved_data = self._resolve_by_latest_timestamp(conflict)
            else:
                raise ValidationException(f"不支持的解决策略: {resolution_strategy}")
            
            # 应用解决方案
            self._apply_conflict_resolution(conflict, resolved_data)
            
            # 更新冲突状态
            self._update_conflict_status(conflict_id, True, resolution_strategy)
            
            self.logger.info(f"冲突解决成功: {conflict_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"冲突解决失败 {conflict_id}: {e}")
            return False
    
    def get_sync_statistics(self, start_date: datetime = None, 
                           end_date: datetime = None) -> Dict[str, Any]:
        """获取同步统计信息"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        try:
            # 同步任务统计
            task_sql = """
                SELECT 
                    table_name,
                    sync_direction,
                    status,
                    COUNT(*) as count,
                    SUM(synced_records) as total_synced,
                    SUM(failed_records) as total_failed,
                    SUM(conflict_records) as total_conflicts
                FROM data_sync_tasks 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY table_name, sync_direction, status
            """
            task_stats = self.db_manager.execute_query(task_sql, (start_date, end_date))
            
            # 冲突统计
            conflict_sql = """
                SELECT 
                    table_name,
                    resolved,
                    COUNT(*) as count
                FROM data_sync_conflicts 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY table_name, resolved
            """
            conflict_stats = self.db_manager.execute_query(conflict_sql, (start_date, end_date))
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'sync_tasks': task_stats,
                'conflicts': conflict_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取同步统计失败: {e}")
            return {}
    
    def register_conflict_handler(self, table_name: str, handler: Callable):
        """注册冲突处理回调"""
        self.conflict_handlers[table_name] = handler
        self.logger.info(f"注册冲突处理器: {table_name}")
    
    def _sync_worker(self):
        """同步工作线程"""
        while not self.stop_event.wait(self.config.sync_interval):
            try:
                self._process_sync_tasks()
            except Exception as e:
                self.logger.error(f"同步工作线程异常: {e}")
    
    def _consistency_check_worker(self):
        """一致性检查工作线程"""
        while not self.stop_event.wait(self.config.consistency_check_interval):
            try:
                self._perform_consistency_checks()
            except Exception as e:
                self.logger.error(f"一致性检查线程异常: {e}")
    
    def _process_sync_tasks(self):
        """处理同步任务"""
        with self.task_lock:
            pending_tasks = [task for task in self.sync_tasks if task.status == SyncStatus.PENDING]
        
        for task in pending_tasks:
            try:
                self._execute_sync_task(task)
            except Exception as e:
                self.logger.error(f"执行同步任务失败 {task.task_id}: {e}")
                task.status = SyncStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()
    
    def _execute_sync_task(self, task: SyncTask):
        """执行同步任务"""
        task.status = SyncStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            if task.sync_type == "incremental":
                result = self.perform_incremental_sync(task.table_name, task.sync_direction)
            else:
                result = self.perform_full_sync(task.table_name, task.sync_direction)
            
            # 更新任务结果
            task.synced_records = result.get('synced_count', 0)
            task.failed_records = result.get('failed_count', 0)
            task.conflict_records = result.get('conflict_count', 0)
            task.status = SyncStatus.SUCCESS
            
        except Exception as e:
            task.status = SyncStatus.FAILED
            task.error_message = str(e)
            raise
        finally:
            task.completed_at = datetime.now()
            self._save_sync_task_result(task)
    
    def _sync_from_his(self, table_name: str, last_sync_time: datetime) -> Dict[str, Any]:
        """从HIS同步数据"""
        table_config = self.config.sync_tables.get(table_name, {})
        his_table = table_config.get('his_table', table_name)
        primary_key = table_config.get('primary_key', 'id')
        
        # 获取HIS中的增量数据
        where_condition = f"updated_at > '{last_sync_time.isoformat()}'"
        his_records = self._get_his_records(his_table, where_condition)
        
        synced_count = 0
        failed_count = 0
        conflict_count = 0
        
        for record in his_records:
            try:
                # 检查是否存在冲突
                existing_record = self._get_medical_record(table_name, record[primary_key])
                
                if existing_record and self._has_data_conflict(record, existing_record):
                    # 处理冲突
                    conflict_count += 1
                    self._handle_data_conflict(table_name, record, existing_record)
                else:
                    # 同步数据
                    self._upsert_medical_record(table_name, record)
                    synced_count += 1
                    
            except Exception as e:
                self.logger.error(f"同步记录失败 {record.get(primary_key)}: {e}")
                failed_count += 1
        
        # 更新最后同步时间
        self._update_last_sync_time(table_name, datetime.now())
        
        return {
            'synced_count': synced_count,
            'failed_count': failed_count,
            'conflict_count': conflict_count
        }
    
    def _sync_to_his(self, table_name: str, last_sync_time: datetime) -> Dict[str, Any]:
        """同步数据到HIS"""
        table_config = self.config.sync_tables.get(table_name, {})
        his_table = table_config.get('his_table', table_name)
        primary_key = table_config.get('primary_key', 'id')
        
        # 获取医保系统中的增量数据
        where_condition = f"updated_at > '{last_sync_time.isoformat()}'"
        medical_records = self._get_medical_records(table_name, where_condition)
        
        synced_count = 0
        failed_count = 0
        conflict_count = 0
        
        for record in medical_records:
            try:
                # 检查是否存在冲突
                existing_record = self._get_his_record(his_table, record[primary_key])
                
                if existing_record and self._has_data_conflict(record, existing_record):
                    # 处理冲突
                    conflict_count += 1
                    self._handle_data_conflict(table_name, record, existing_record)
                else:
                    # 同步数据
                    self._upsert_his_record(his_table, record)
                    synced_count += 1
                    
            except Exception as e:
                self.logger.error(f"同步记录失败 {record.get(primary_key)}: {e}")
                failed_count += 1
        
        return {
            'synced_count': synced_count,
            'failed_count': failed_count,
            'conflict_count': conflict_count
        }
    
    def _full_sync_from_his(self, table_name: str) -> Dict[str, Any]:
        """从HIS全量同步"""
        # 实现全量同步逻辑
        return self._sync_from_his(table_name, datetime.min)
    
    def _full_sync_to_his(self, table_name: str) -> Dict[str, Any]:
        """全量同步到HIS"""
        # 实现全量同步逻辑
        return self._sync_to_his(table_name, datetime.min)
    
    def _get_his_records(self, table_name: str, where_condition: str = None) -> List[Dict[str, Any]]:
        """获取HIS记录"""
        sql = f"SELECT * FROM {table_name}"
        if where_condition:
            sql += f" WHERE {where_condition}"
        
        return self.his_db_manager.execute_query(sql)
    
    def _get_medical_records(self, table_name: str, where_condition: str = None) -> List[Dict[str, Any]]:
        """获取医保系统记录"""
        sql = f"SELECT * FROM {table_name}"
        if where_condition:
            sql += f" WHERE {where_condition}"
        
        return self.db_manager.execute_query(sql)
    
    def _get_his_record(self, table_name: str, primary_key_value: Any) -> Optional[Dict[str, Any]]:
        """获取单个HIS记录"""
        table_config = self.config.sync_tables.get(table_name, {})
        primary_key = table_config.get('primary_key', 'id')
        
        sql = f"SELECT * FROM {table_name} WHERE {primary_key} = %s"
        return self.his_db_manager.execute_query_one(sql, (primary_key_value,))
    
    def _get_medical_record(self, table_name: str, primary_key_value: Any) -> Optional[Dict[str, Any]]:
        """获取单个医保系统记录"""
        table_config = self.config.sync_tables.get(table_name, {})
        primary_key = table_config.get('primary_key', 'id')
        
        sql = f"SELECT * FROM {table_name} WHERE {primary_key} = %s"
        return self.db_manager.execute_query_one(sql, (primary_key_value,))
    
    def _has_data_conflict(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> bool:
        """检查数据是否冲突"""
        # 比较关键字段是否不同
        for key, value1 in record1.items():
            if key in ['updated_at', 'created_at']:
                continue
            
            value2 = record2.get(key)
            if value1 != value2:
                return True
        
        return False
    
    def _handle_data_conflict(self, table_name: str, record1: Dict[str, Any], record2: Dict[str, Any]):
        """处理数据冲突"""
        conflict_id = self._generate_conflict_id()
        
        # 找出冲突字段
        conflict_fields = []
        for key, value1 in record1.items():
            if key in ['updated_at', 'created_at']:
                continue
            value2 = record2.get(key)
            if value1 != value2:
                conflict_fields.append(key)
        
        # 创建冲突记录
        conflict = SyncConflict(
            conflict_id=conflict_id,
            table_name=table_name,
            primary_key=str(record1.get('id', '')),
            his_data=record1,
            medical_data=record2,
            conflict_fields=conflict_fields,
            created_at=datetime.now()
        )
        
        # 保存冲突记录
        self._save_conflict_record(conflict)
        
        # 调用冲突处理器
        if table_name in self.conflict_handlers:
            try:
                self.conflict_handlers[table_name](conflict)
            except Exception as e:
                self.logger.error(f"冲突处理器执行失败: {e}")
        
        # 根据配置的策略自动解决冲突
        if self.config.conflict_resolution != "manual":
            self.resolve_conflict(conflict_id, self.config.conflict_resolution)
    
    def _compare_data_consistency(self, table_name: str, his_records: List[Dict[str, Any]], 
                                 medical_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """比较数据一致性"""
        table_config = self.config.sync_tables.get(table_name, {})
        primary_key = table_config.get('primary_key', 'id')
        
        # 创建索引
        his_index = {record[primary_key]: record for record in his_records}
        medical_index = {record[primary_key]: record for record in medical_records}
        
        # 统计结果
        consistent_count = 0
        inconsistent_count = 0
        his_only_count = 0
        medical_only_count = 0
        inconsistent_records = []
        
        # 检查一致性
        all_keys = set(his_index.keys()) | set(medical_index.keys())
        
        for key in all_keys:
            his_record = his_index.get(key)
            medical_record = medical_index.get(key)
            
            if his_record and medical_record:
                if self._records_are_consistent(his_record, medical_record):
                    consistent_count += 1
                else:
                    inconsistent_count += 1
                    inconsistent_records.append({
                        'primary_key': key,
                        'his_data': his_record,
                        'medical_data': medical_record
                    })
            elif his_record:
                his_only_count += 1
            else:
                medical_only_count += 1
        
        return {
            'table_name': table_name,
            'total_records': len(all_keys),
            'consistent_count': consistent_count,
            'inconsistent_count': inconsistent_count,
            'his_only_count': his_only_count,
            'medical_only_count': medical_only_count,
            'inconsistent_records': inconsistent_records[:10],  # 只返回前10条不一致记录
            'check_time': datetime.now().isoformat()
        }
    
    def _records_are_consistent(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> bool:
        """检查两条记录是否一致"""
        # 排除时间戳字段
        exclude_fields = {'updated_at', 'created_at', 'sync_time'}
        
        for key, value1 in record1.items():
            if key in exclude_fields:
                continue
            
            value2 = record2.get(key)
            if value1 != value2:
                return False
        
        return True
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"sync_{uuid.uuid4().hex[:8]}"
    
    def _generate_conflict_id(self) -> str:
        """生成冲突ID"""
        import uuid
        return f"conflict_{uuid.uuid4().hex[:8]}"
    
    def _get_last_sync_time(self, table_name: str) -> datetime:
        """获取最后同步时间"""
        sql = """
            SELECT last_sync_time 
            FROM data_sync_status 
            WHERE table_name = %s
        """
        result = self.db_manager.execute_query_one(sql, (table_name,))
        
        if result:
            return result['last_sync_time']
        else:
            # 如果没有记录，返回一个较早的时间
            return datetime.now() - timedelta(days=30)
    
    def _update_last_sync_time(self, table_name: str, sync_time: datetime):
        """更新最后同步时间"""
        sql = """
            INSERT INTO data_sync_status (table_name, last_sync_time, updated_at)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            last_sync_time = VALUES(last_sync_time),
            updated_at = VALUES(updated_at)
        """
        self.db_manager.execute_update(sql, (table_name, sync_time, datetime.now()))
    
    def _upsert_medical_record(self, table_name: str, record: Dict[str, Any]):
        """插入或更新医保系统记录"""
        # 这里需要根据具体表结构实现
        # 示例实现
        fields = list(record.keys())
        values = list(record.values())
        placeholders = ', '.join(['%s'] * len(fields))
        
        sql = f"""
            INSERT INTO {table_name} ({', '.join(fields)})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
            {', '.join([f"{field} = VALUES({field})" for field in fields])}
        """
        
        self.db_manager.execute_update(sql, values)
    
    def _upsert_his_record(self, table_name: str, record: Dict[str, Any]):
        """插入或更新HIS记录"""
        # 这里需要根据具体表结构实现
        # 示例实现
        fields = list(record.keys())
        values = list(record.values())
        placeholders = ', '.join(['%s'] * len(fields))
        
        sql = f"""
            INSERT INTO {table_name} ({', '.join(fields)})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
            {', '.join([f"{field} = VALUES({field})" for field in fields])}
        """
        
        self.his_db_manager.execute_update(sql, values)
    
    def _save_sync_task_result(self, task: SyncTask):
        """保存同步任务结果"""
        sql = """
            INSERT INTO data_sync_tasks 
            (task_id, table_name, sync_direction, sync_type, status, 
             total_records, synced_records, failed_records, conflict_records,
             created_at, started_at, completed_at, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            total_records = VALUES(total_records),
            synced_records = VALUES(synced_records),
            failed_records = VALUES(failed_records),
            conflict_records = VALUES(conflict_records),
            started_at = VALUES(started_at),
            completed_at = VALUES(completed_at),
            error_message = VALUES(error_message)
        """
        
        params = (
            task.task_id,
            task.table_name,
            task.sync_direction.value,
            task.sync_type,
            task.status.value,
            task.total_records,
            task.synced_records,
            task.failed_records,
            task.conflict_records,
            task.created_at,
            task.started_at,
            task.completed_at,
            task.error_message
        )
        
        self.db_manager.execute_update(sql, params)
    
    def _save_conflict_record(self, conflict: SyncConflict):
        """保存冲突记录"""
        sql = """
            INSERT INTO data_sync_conflicts 
            (conflict_id, table_name, primary_key, his_data, medical_data, 
             conflict_fields, created_at, resolved, resolution_strategy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            conflict.conflict_id,
            conflict.table_name,
            conflict.primary_key,
            json.dumps(conflict.his_data, ensure_ascii=False),
            json.dumps(conflict.medical_data, ensure_ascii=False),
            json.dumps(conflict.conflict_fields),
            conflict.created_at,
            conflict.resolved,
            conflict.resolution_strategy
        )
        
        self.db_manager.execute_update(sql, params)
    
    def _get_conflict_by_id(self, conflict_id: str) -> Optional[SyncConflict]:
        """根据ID获取冲突记录"""
        sql = """
            SELECT * FROM data_sync_conflicts 
            WHERE conflict_id = %s
        """
        result = self.db_manager.execute_query_one(sql, (conflict_id,))
        
        if result:
            return SyncConflict(
                conflict_id=result['conflict_id'],
                table_name=result['table_name'],
                primary_key=result['primary_key'],
                his_data=json.loads(result['his_data']),
                medical_data=json.loads(result['medical_data']),
                conflict_fields=json.loads(result['conflict_fields']),
                created_at=result['created_at'],
                resolved=result['resolved'],
                resolution_strategy=result['resolution_strategy']
            )
        
        return None
    
    def _apply_conflict_resolution(self, conflict: SyncConflict, resolved_data: Dict[str, Any]):
        """应用冲突解决方案"""
        # 更新两边的数据
        self._upsert_medical_record(conflict.table_name, resolved_data)
        
        table_config = self.config.sync_tables.get(conflict.table_name, {})
        his_table = table_config.get('his_table', conflict.table_name)
        self._upsert_his_record(his_table, resolved_data)
    
    def _update_conflict_status(self, conflict_id: str, resolved: bool, resolution_strategy: str):
        """更新冲突状态"""
        sql = """
            UPDATE data_sync_conflicts 
            SET resolved = %s, resolution_strategy = %s, resolved_at = %s
            WHERE conflict_id = %s
        """
        self.db_manager.execute_update(sql, (resolved, resolution_strategy, datetime.now(), conflict_id))
    
    def _resolve_by_latest_timestamp(self, conflict: SyncConflict) -> Dict[str, Any]:
        """根据最新时间戳解决冲突"""
        his_updated = conflict.his_data.get('updated_at')
        medical_updated = conflict.medical_data.get('updated_at')
        
        if his_updated and medical_updated:
            if his_updated > medical_updated:
                return conflict.his_data
            else:
                return conflict.medical_data
        elif his_updated:
            return conflict.his_data
        else:
            return conflict.medical_data
    
    def _save_consistency_check_result(self, table_name: str, result: Dict[str, Any]):
        """保存一致性检查结果"""
        sql = """
            INSERT INTO data_consistency_checks 
            (table_name, check_time, total_records, consistent_count, 
             inconsistent_count, his_only_count, medical_only_count, result_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            table_name,
            datetime.now(),
            result.get('total_records', 0),
            result.get('consistent_count', 0),
            result.get('inconsistent_count', 0),
            result.get('his_only_count', 0),
            result.get('medical_only_count', 0),
            json.dumps(result, ensure_ascii=False)
        )
        
        self.db_manager.execute_update(sql, params)
    
    def _resolve_by_latest_timestamp(self, conflict: SyncConflict) -> Dict[str, Any]:
        """根据最新时间戳解决冲突"""
        his_time = conflict.his_data.get('updated_at', datetime.min)
        medical_time = conflict.medical_data.get('updated_at', datetime.min)
        
        if isinstance(his_time, str):
            his_time = datetime.fromisoformat(his_time.replace('Z', '+00:00'))
        if isinstance(medical_time, str):
            medical_time = datetime.fromisoformat(medical_time.replace('Z', '+00:00'))
        
        return conflict.his_data if his_time > medical_time else conflict.medical_data
    
    def _save_consistency_check_result(self, table_name: str, result: Dict[str, Any]):
        """保存一致性检查结果"""
        sql = """
            INSERT INTO data_consistency_checks 
            (table_name, check_time, total_records, consistent_count, 
             inconsistent_count, his_only_count, medical_only_count, check_result)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # 处理datetime序列化问题
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        params = (
            table_name,
            datetime.now(),
            result['total_records'],
            result['consistent_count'],
            result['inconsistent_count'],
            result['his_only_count'],
            result['medical_only_count'],
            json.dumps(result, ensure_ascii=False, default=datetime_serializer)
        )
        
        self.db_manager.execute_update(sql, params)
    
    def _perform_consistency_checks(self):
        """执行一致性检查"""
        for table_name in self.config.sync_tables.keys():
            try:
                self.check_data_consistency(table_name)
                self.logger.info(f"一致性检查完成: {table_name}")
            except Exception as e:
                self.logger.error(f"一致性检查失败 {table_name}: {e}")
    
    def _perform_consistency_checks(self):
        """执行一致性检查"""
        for table_name in self.config.sync_tables.keys():
            try:
                self.check_data_consistency(table_name)
            except Exception as e:
                self.logger.error(f"一致性检查失败 {table_name}: {e}")
    
    def close(self):
        """关闭数据同步服务"""
        self.stop_sync_service()
        
        if self.his_db_manager:
            self.his_db_manager.close()
        
        self.logger.info("数据同步服务已关闭")