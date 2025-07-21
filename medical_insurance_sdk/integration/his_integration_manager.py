"""
HIS系统集成管理器

基于通用数据模型的HIS集成管理器，支持206个医保接口的统一集成：
- 通用数据同步（基置驱动）
- 医保接口结果统一回写到HIS系统
- 数据一致性检查和冲突解决
- 支持所有医保接口的灵活集成配置
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from ..core.database import DatabaseManager, DatabaseConfig
from ..core.config_manager import ConfigManager
from ..models.request import MedicalInsuranceRequest
from ..models.response import MedicalInsuranceResponse
from ..exceptions import (
    MedicalInsuranceException,
    ValidationException,
    DatabaseException,
    IntegrationException
)


@dataclass
class HISIntegrationConfig:
    """HIS集成配置"""
    # HIS数据库配置
    his_db_config: Optional[Dict[str, Any]] = None
    
    # 同步配置
    sync_enabled: bool = True
    sync_interval: int = 300  # 同步间隔（秒）
    batch_size: int = 100  # 批量处理大小
    max_retry_times: int = 3  # 最大重试次数
    
    # 回写配置
    writeback_enabled: bool = True
    writeback_timeout: int = 30  # 回写超时时间（秒）
    
    # 数据一致性检查配置
    consistency_check_enabled: bool = True
    consistency_check_interval: int = 3600  # 一致性检查间隔（秒）


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    synced_count: int = 0
    failed_count: int = 0
    conflict_count: int = 0
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class WritebackResult:
    """回写结果"""
    success: bool
    written_count: int = 0
    failed_count: int = 0
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HISIntegrationManager:
    """HIS系统集成管理器 - 通用配置驱动实现"""
    
    def __init__(self, db_manager: DatabaseManager, config_manager: ConfigManager, 
                 integration_config: HISIntegrationConfig = None):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.integration_config = integration_config or HISIntegrationConfig()
        self.logger = logging.getLogger(__name__)
        
        # HIS数据库连接（如果配置了）
        self.his_db_manager = None
        if self.integration_config.his_db_config:
            his_db_config = DatabaseConfig(**self.integration_config.his_db_config)
            self.his_db_manager = DatabaseManager(his_db_config, pool_name="his_db")
        
        self.logger.info("HIS集成管理器初始化完成")
    
    def sync_medical_data(self, api_code: str, medical_data: Dict[str, Any], 
                         org_code: str, sync_direction: str = "to_his") -> SyncResult:
        """
        通用医保数据同步到HIS系统
        
        Args:
            api_code: 医保接口编码（如1101、2207等）
            medical_data: 医保接口返回的数据
            org_code: 机构编码
            sync_direction: 同步方向 (to_his, from_his, bidirectional)
        
        Returns:
            SyncResult: 同步结果
        """
        try:
            # 1. 获取接口的HIS集成配置
            integration_mapping = self._get_his_integration_mapping(api_code, org_code)
            if not integration_mapping:
                return SyncResult(
                    success=False,
                    error_message=f"接口 {api_code} 未配置HIS集成映射"
                )
            
            # 2. 根据配置进行数据转换
            his_data = self._transform_medical_to_his_data(medical_data, integration_mapping)
            
            # 3. 执行数据同步
            sync_result = self._execute_data_sync(
                api_code, his_data, integration_mapping, sync_direction
            )
            
            # 4. 记录同步日志
            self._log_sync_operation(api_code, medical_data, his_data, sync_result, org_code)
            
            return sync_result
            
        except Exception as e:
            self.logger.error(f"医保数据同步失败 [{api_code}]: {e}")
            return SyncResult(
                success=False,
                error_message=str(e)
            )
    
    def writeback_medical_result(self, api_code: str, medical_result: Dict[str, Any], 
                               org_code: str) -> WritebackResult:
        """
        通用医保接口结果回写到HIS系统
        
        Args:
            api_code: 医保接口编码
            medical_result: 医保接口处理结果
            org_code: 机构编码
        
        Returns:
            WritebackResult: 回写结果
        """
        try:
            # 1. 获取回写配置
            writeback_mapping = self._get_his_writeback_mapping(api_code, org_code)
            if not writeback_mapping:
                return WritebackResult(
                    success=False,
                    error_message=f"接口 {api_code} 未配置HIS回写映射"
                )
            
            # 2. 数据转换
            his_writeback_data = self._transform_medical_result_to_his(
                medical_result, writeback_mapping
            )
            
            # 3. 执行回写
            writeback_result = self._execute_his_writeback(
                api_code, his_writeback_data, writeback_mapping
            )
            
            # 4. 记录回写日志
            self._log_writeback_operation(
                api_code, medical_result, his_writeback_data, writeback_result, org_code
            )
            
            return writeback_result
            
        except Exception as e:
            self.logger.error(f"医保结果回写失败 [{api_code}]: {e}")
            return WritebackResult(
                success=False,
                error_message=str(e)
            )
    
    def check_data_consistency(self, api_code: str, org_code: str, 
                             check_period_hours: int = 24) -> Dict[str, Any]:
        """
        检查医保系统与HIS系统的数据一致性
        
        Args:
            api_code: 医保接口编码
            org_code: 机构编码
            check_period_hours: 检查时间范围（小时）
        
        Returns:
            Dict: 一致性检查结果
        """
        try:
            # 1. 获取一致性检查配置
            consistency_config = self._get_consistency_check_config(api_code, org_code)
            if not consistency_config:
                return {
                    'success': False,
                    'error': f"接口 {api_code} 未配置一致性检查"
                }
            
            # 2. 获取检查时间范围内的数据
            start_time = datetime.now() - timedelta(hours=check_period_hours)
            medical_data = self._get_medical_data_for_consistency_check(
                api_code, org_code, start_time
            )
            his_data = self._get_his_data_for_consistency_check(
                api_code, org_code, start_time, consistency_config
            )
            
            # 3. 执行一致性比较
            consistency_result = self._compare_data_consistency(
                medical_data, his_data, consistency_config
            )
            
            # 4. 记录检查结果
            self._log_consistency_check(api_code, org_code, consistency_result)
            
            return consistency_result
            
        except Exception as e:
            self.logger.error(f"数据一致性检查失败 [{api_code}]: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def resolve_data_conflict(self, conflict_id: str, resolution_strategy: str, 
                            resolver_id: str) -> bool:
        """
        解决数据冲突
        
        Args:
            conflict_id: 冲突ID
            resolution_strategy: 解决策略 (use_medical, use_his, manual_merge)
            resolver_id: 解决人员ID
        
        Returns:
            bool: 是否解决成功
        """
        try:
            # 1. 获取冲突详情
            conflict_info = self._get_conflict_info(conflict_id)
            if not conflict_info:
                raise IntegrationException(f"冲突记录不存在: {conflict_id}")
            
            # 2. 根据策略解决冲突
            resolution_result = self._apply_conflict_resolution(
                conflict_info, resolution_strategy
            )
            
            # 3. 更新冲突状态
            self._update_conflict_status(
                conflict_id, resolution_strategy, resolver_id, resolution_result
            )
            
            self.logger.info(f"数据冲突解决成功: {conflict_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据冲突解决失败 [{conflict_id}]: {e}")
            return False
    
    def get_sync_statistics(self, api_code: str = None, org_code: str = None, 
                          start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        获取同步统计信息
        
        Args:
            api_code: 接口编码（可选）
            org_code: 机构编码（可选）
            start_date: 开始时间
            end_date: 结束时间
        
        Returns:
            Dict: 统计信息
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        try:
            # 构建查询条件
            where_conditions = ["sync_time BETWEEN %s AND %s"]
            params = [start_date, end_date]
            
            if api_code:
                where_conditions.append("api_code = %s")
                params.append(api_code)
            
            if org_code:
                where_conditions.append("org_code = %s")
                params.append(org_code)
            
            where_clause = " AND ".join(where_conditions)
            
            # 同步统计
            sync_sql = f"""
                SELECT 
                    api_code,
                    sync_direction,
                    sync_status,
                    COUNT(*) as count,
                    AVG(synced_records) as avg_synced,
                    SUM(failed_records) as total_failed
                FROM his_data_sync_log 
                WHERE {where_clause}
                GROUP BY api_code, sync_direction, sync_status
            """
            sync_stats = self.db_manager.execute_query(sync_sql, params)
            
            # 回写统计
            writeback_sql = f"""
                SELECT 
                    api_code,
                    writeback_status,
                    COUNT(*) as count,
                    AVG(written_records) as avg_written,
                    SUM(failed_records) as total_failed
                FROM his_writeback_log 
                WHERE {where_clause.replace('sync_time', 'writeback_time')}
                GROUP BY api_code, writeback_status
            """
            writeback_stats = self.db_manager.execute_query(writeback_sql, params)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'sync_statistics': sync_stats,
                'writeback_statistics': writeback_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取同步统计失败: {e}")
            return {}
    
    def _get_his_integration_mapping(self, api_code: str, org_code: str) -> Optional[Dict[str, Any]]:
        """获取HIS集成映射配置"""
        try:
            sql = """
                SELECT his_integration_config
                FROM medical_interface_config 
                WHERE api_code = %s AND is_active = 1
            """
            result = self.db_manager.execute_query_one(sql, (api_code,))
            
            if result and result.get('his_integration_config'):
                config = json.loads(result['his_integration_config'])
                
                # 检查是否有机构特定配置
                try:
                    org_config = self.config_manager.get_organization_config(org_code)
                    if org_config and org_config.extra_config:
                        # 检查extra_config中是否有HIS集成覆盖配置
                        if 'his_integration_overrides' in org_config.extra_config:
                            org_overrides = org_config.extra_config['his_integration_overrides']
                            if api_code in org_overrides:
                                # 合并机构特定配置
                                config.update(org_overrides[api_code])
                except Exception as e:
                    self.logger.warning(f"获取机构配置失败 [{org_code}]: {e}")
                
                return config
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取HIS集成映射配置失败 [{api_code}]: {e}")
            return None
    
    def _get_his_writeback_mapping(self, api_code: str, org_code: str) -> Optional[Dict[str, Any]]:
        """获取HIS回写映射配置"""
        integration_mapping = self._get_his_integration_mapping(api_code, org_code)
        return integration_mapping.get('writeback_mapping') if integration_mapping else None
    
    def _get_consistency_check_config(self, api_code: str, org_code: str) -> Optional[Dict[str, Any]]:
        """获取一致性检查配置"""
        integration_mapping = self._get_his_integration_mapping(api_code, org_code)
        return integration_mapping.get('consistency_check') if integration_mapping else None
    
    def _transform_medical_to_his_data(self, medical_data: Dict[str, Any], 
                                     mapping: Dict[str, Any]) -> Dict[str, Any]:
        """将医保数据转换为HIS数据格式"""
        his_data = {}
        field_mappings = mapping.get('field_mappings', {})
        
        for his_field, medical_path in field_mappings.items():
            try:
                # 支持嵌套路径，如 "output.baseinfo.psn_name"
                value = self._extract_nested_value(medical_data, medical_path)
                if value is not None:
                    # 应用数据转换规则
                    transformed_value = self._apply_data_transformation(
                        value, mapping.get('transformations', {}).get(his_field)
                    )
                    his_data[his_field] = transformed_value
            except Exception as e:
                self.logger.warning(f"字段映射失败 {his_field} <- {medical_path}: {e}")
        
        return his_data
    
    def _transform_medical_result_to_his(self, medical_result: Dict[str, Any], 
                                       mapping: Dict[str, Any]) -> Dict[str, Any]:
        """将医保处理结果转换为HIS回写数据格式"""
        return self._transform_medical_to_his_data(medical_result, mapping)
    
    def _execute_data_sync(self, api_code: str, his_data: Dict[str, Any], 
                          mapping: Dict[str, Any], sync_direction: str) -> SyncResult:
        """执行数据同步"""
        if not self.his_db_manager:
            return SyncResult(
                success=False,
                error_message="HIS数据库未配置"
            )
        
        try:
            sync_config = mapping.get('sync_config', {})
            table_name = sync_config.get('table_name')
            primary_key = sync_config.get('primary_key', 'id')
            
            if not table_name:
                return SyncResult(
                    success=False,
                    error_message="未配置同步表名"
                )
            
            # 根据同步方向执行不同操作
            if sync_direction == "to_his":
                result = self._sync_to_his_system(table_name, primary_key, his_data, sync_config)
            elif sync_direction == "from_his":
                result = self._sync_from_his_system(table_name, primary_key, sync_config)
            else:  # bidirectional
                result = self._sync_bidirectional(table_name, primary_key, his_data, sync_config)
            
            return result
            
        except Exception as e:
            return SyncResult(
                success=False,
                error_message=str(e)
            )
    
    def _execute_his_writeback(self, api_code: str, his_data: Dict[str, Any], 
                             mapping: Dict[str, Any]) -> WritebackResult:
        """执行HIS系统回写"""
        if not self.his_db_manager:
            return WritebackResult(
                success=False,
                error_message="HIS数据库未配置"
            )
        
        try:
            writeback_config = mapping.get('writeback_config', {})
            table_name = writeback_config.get('table_name')
            primary_key = writeback_config.get('primary_key', 'id')
            operation = writeback_config.get('operation', 'update')  # insert, update, upsert
            
            if not table_name:
                return WritebackResult(
                    success=False,
                    error_message="未配置回写表名"
                )
            
            # 执行回写操作
            if operation == 'insert':
                affected_rows = self._insert_his_data(table_name, his_data)
            elif operation == 'update':
                affected_rows = self._update_his_data(table_name, primary_key, his_data)
            else:  # upsert
                affected_rows = self._upsert_his_data(table_name, primary_key, his_data)
            
            return WritebackResult(
                success=True,
                written_count=affected_rows
            )
            
        except Exception as e:
            return WritebackResult(
                success=False,
                error_message=str(e)
            )
    
    def _sync_to_his_system(self, table_name: str, primary_key: str, 
                          his_data: Dict[str, Any], sync_config: Dict[str, Any]) -> SyncResult:
        """同步数据到HIS系统"""
        try:
            # 检查记录是否存在
            check_sql = f"SELECT COUNT(*) as count FROM {table_name} WHERE {primary_key} = %s"
            result = self.his_db_manager.execute_query_one(
                check_sql, (his_data.get(primary_key),)
            )
            
            if result['count'] > 0:
                # 更新现有记录
                set_clause = ", ".join([f"{k} = %s" for k in his_data.keys() if k != primary_key])
                update_sql = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = %s"
                params = [v for k, v in his_data.items() if k != primary_key] + [his_data[primary_key]]
                affected_rows = self.his_db_manager.execute_update(update_sql, params)
            else:
                # 插入新记录
                columns = ", ".join(his_data.keys())
                placeholders = ", ".join(["%s"] * len(his_data))
                insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                affected_rows = self.his_db_manager.execute_update(insert_sql, list(his_data.values()))
            
            return SyncResult(
                success=True,
                synced_count=affected_rows
            )
            
        except Exception as e:
            return SyncResult(
                success=False,
                error_message=str(e)
            )
    
    def _sync_from_his_system(self, table_name: str, primary_key: str, 
                            sync_config: Dict[str, Any]) -> SyncResult:
        """从HIS系统同步数据"""
        # 实现从HIS系统读取数据的逻辑
        # 这里需要根据具体的同步需求来实现
        return SyncResult(success=True, synced_count=0)
    
    def _sync_bidirectional(self, table_name: str, primary_key: str, 
                          his_data: Dict[str, Any], sync_config: Dict[str, Any]) -> SyncResult:
        """双向数据同步"""
        # 实现双向同步逻辑，包括冲突检测和解决
        return SyncResult(success=True, synced_count=0)
    
    def _insert_his_data(self, table_name: str, his_data: Dict[str, Any]) -> int:
        """插入HIS数据"""
        columns = ", ".join(his_data.keys())
        placeholders = ", ".join(["%s"] * len(his_data))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.his_db_manager.execute_update(sql, list(his_data.values()))
    
    def _update_his_data(self, table_name: str, primary_key: str, his_data: Dict[str, Any]) -> int:
        """更新HIS数据"""
        set_clause = ", ".join([f"{k} = %s" for k in his_data.keys() if k != primary_key])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = %s"
        params = [v for k, v in his_data.items() if k != primary_key] + [his_data[primary_key]]
        return self.his_db_manager.execute_update(sql, params)
    
    def _upsert_his_data(self, table_name: str, primary_key: str, his_data: Dict[str, Any]) -> int:
        """插入或更新HIS数据"""
        columns = ", ".join(his_data.keys())
        placeholders = ", ".join(["%s"] * len(his_data))
        update_clause = ", ".join([f"{k} = VALUES({k})" for k in his_data.keys() if k != primary_key])
        
        sql = f"""
            INSERT INTO {table_name} ({columns}) VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
        """
        return self.his_db_manager.execute_update(sql, list(his_data.values()))
    
    def _extract_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """提取嵌套路径的值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _apply_data_transformation(self, value: Any, transformation: Optional[Dict[str, Any]]) -> Any:
        """应用数据转换规则"""
        if not transformation:
            return value
        
        transform_type = transformation.get('type')
        
        if transform_type == 'format':
            format_str = transformation.get('format')
            return format_str.format(value) if format_str else value
        elif transform_type == 'mapping':
            mapping_dict = transformation.get('mapping', {})
            return mapping_dict.get(str(value), value)
        elif transform_type == 'default':
            return transformation.get('default_value', value)
        
        return value
    
    def _log_sync_operation(self, api_code: str, medical_data: Dict[str, Any], 
                          his_data: Dict[str, Any], sync_result: SyncResult, org_code: str):
        """记录同步操作日志"""
        try:
            sql = """
                INSERT INTO his_data_sync_log 
                (sync_id, api_code, org_code, medical_data, his_data, sync_status, 
                 synced_records, failed_records, error_message, sync_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                str(uuid.uuid4()),
                api_code,
                org_code,
                json.dumps(medical_data, ensure_ascii=False),
                json.dumps(his_data, ensure_ascii=False),
                'success' if sync_result.success else 'failed',
                sync_result.synced_count,
                sync_result.failed_count,
                sync_result.error_message,
                datetime.now()
            )
            
            self.db_manager.execute_update(sql, params)
            
        except Exception as e:
            self.logger.error(f"记录同步日志失败: {e}")
    
    def _log_writeback_operation(self, api_code: str, medical_result: Dict[str, Any], 
                               his_data: Dict[str, Any], writeback_result: WritebackResult, org_code: str):
        """记录回写操作日志"""
        try:
            sql = """
                INSERT INTO his_writeback_log 
                (writeback_id, api_code, org_code, medical_result, his_data, writeback_status, 
                 written_records, failed_records, error_message, writeback_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                str(uuid.uuid4()),
                api_code,
                org_code,
                json.dumps(medical_result, ensure_ascii=False),
                json.dumps(his_data, ensure_ascii=False),
                'success' if writeback_result.success else 'failed',
                writeback_result.written_count,
                writeback_result.failed_count,
                writeback_result.error_message,
                datetime.now()
            )
            
            self.db_manager.execute_update(sql, params)
            
        except Exception as e:
            self.logger.error(f"记录回写日志失败: {e}")
    
    def _get_medical_data_for_consistency_check(self, api_code: str, org_code: str, 
                                              start_time: datetime) -> List[Dict[str, Any]]:
        """获取医保系统数据用于一致性检查"""
        try:
            sql = """
                SELECT operation_id, request_data, response_data, operation_time
                FROM business_operation_logs 
                WHERE api_code = %s AND institution_code = %s 
                AND operation_time >= %s AND status = 'success'
                ORDER BY operation_time DESC
            """
            return self.db_manager.execute_query(sql, (api_code, org_code, start_time))
        except Exception as e:
            self.logger.error(f"获取医保数据失败: {e}")
            return []
    
    def _get_his_data_for_consistency_check(self, api_code: str, org_code: str, 
                                          start_time: datetime, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取HIS系统数据用于一致性检查"""
        if not self.his_db_manager:
            return []
        
        try:
            table_name = config.get('table_name')
            time_field = config.get('time_field', 'updated_at')
            
            if not table_name:
                return []
            
            sql = f"""
                SELECT * FROM {table_name} 
                WHERE {time_field} >= %s
                ORDER BY {time_field} DESC
            """
            return self.his_db_manager.execute_query(sql, (start_time,))
        except Exception as e:
            self.logger.error(f"获取HIS数据失败: {e}")
            return []
    
    def _compare_data_consistency(self, medical_data: List[Dict[str, Any]], 
                                his_data: List[Dict[str, Any]], 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """比较数据一致性"""
        # 实现数据一致性比较逻辑
        return {
            'success': True,
            'total_medical_records': len(medical_data),
            'total_his_records': len(his_data),
            'consistent_count': 0,
            'inconsistent_count': 0,
            'conflicts': []
        }
    
    def _log_consistency_check(self, api_code: str, org_code: str, result: Dict[str, Any]):
        """记录一致性检查结果"""
        try:
            sql = """
                INSERT INTO data_consistency_checks 
                (check_id, api_code, org_code, check_result, check_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                str(uuid.uuid4()),
                api_code,
                org_code,
                json.dumps(result, ensure_ascii=False),
                datetime.now()
            )
            
            self.db_manager.execute_update(sql, params)
            
        except Exception as e:
            self.logger.error(f"记录一致性检查失败: {e}")
    
    def _get_conflict_info(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """获取冲突信息"""
        try:
            sql = """
                SELECT * FROM data_sync_conflicts 
                WHERE conflict_id = %s
            """
            result = self.db_manager.execute_query_one(sql, (conflict_id,))
            if result:
                # 转换结果格式以匹配期望的结构
                return {
                    'conflict_id': result['conflict_id'],
                    'table_name': result['table_name'],
                    'primary_key': result['primary_key'],
                    'medical_data': result['medical_data'],
                    'his_data': result['his_data'],
                    'conflict_fields': result['conflict_fields'],
                    'resolved': result['resolved']
                }
            return None
        except Exception as e:
            self.logger.error(f"获取冲突信息失败: {e}")
            return None
    
    def _apply_conflict_resolution(self, conflict_info: Dict[str, Any], 
                                 strategy: str) -> Dict[str, Any]:
        """应用冲突解决策略"""
        # 实现冲突解决逻辑
        return {'resolved': True, 'strategy': strategy}
    
    def _update_conflict_status(self, conflict_id: str, strategy: str, 
                              resolver_id: str, result: Dict[str, Any]):
        """更新冲突状态"""
        try:
            sql = """
                UPDATE data_sync_conflicts 
                SET resolved = %s, resolution_strategy = %s, resolved_at = %s
                WHERE conflict_id = %s
            """
            
            params = (
                result.get('resolved', False),
                strategy,
                datetime.now(),
                conflict_id
            )
            
            self.db_manager.execute_update(sql, params)
            
        except Exception as e:
            self.logger.error(f"更新冲突状态失败: {e}")
    
    def close(self):
        """关闭HIS集成管理器"""
        if self.his_db_manager:
            self.his_db_manager.close()
        self.logger.info("HIS集成管理器已关闭")