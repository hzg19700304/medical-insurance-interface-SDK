"""数据管理器模块"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from .database import DatabaseManager, DatabaseConfig
from ..models.log import OperationLog
from ..models.statistics import InterfaceStatistics, SystemStatistics


@dataclass
class LogQuery:
    """日志查询条件"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    api_code: Optional[str] = None
    institution_code: Optional[str] = None
    business_category: Optional[str] = None
    business_type: Optional[str] = None
    status: Optional[str] = None
    psn_no: Optional[str] = None
    mdtrt_id: Optional[str] = None
    trace_id: Optional[str] = None
    operation_id: Optional[str] = None
    limit: int = 100
    offset: int = 0
    order_by: str = "operation_time"
    order_direction: str = "DESC"


@dataclass
class StatQuery:
    """统计查询条件"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    api_code: Optional[str] = None
    institution_code: Optional[str] = None
    business_category: Optional[str] = None
    business_type: Optional[str] = None
    group_by: str = "api_code"  # api_code, institution_code, business_category, date
    time_granularity: str = "day"  # hour, day, week, month


@dataclass
class StatResult:
    """统计结果"""
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = 0.0
    details: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []
        
        # 计算成功率
        if self.total_count > 0:
            self.success_rate = (self.success_count / self.total_count) * 100


class DataManager:
    """数据管理器 - 负责操作日志的保存、查询和统计数据生成"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # 确保必要的表存在
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """确保必要的数据表存在"""
        try:
            # 检查business_operation_logs表是否存在
            check_sql = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'business_operation_logs'
            """
            result = self.db.execute_query_one(check_sql)
            
            if result and result['count'] == 0:
                self.logger.warning("business_operation_logs表不存在，请先运行数据库初始化脚本")
            
        except Exception as e:
            self.logger.error(f"检查数据表时发生错误: {e}")
    
    def save_operation_log(self, operation_log: OperationLog) -> bool:
        """
        保存操作日志到数据库
        
        Args:
            operation_log: 操作日志对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 如果没有operation_id，生成一个
            if not operation_log.operation_id:
                operation_log.operation_id = str(uuid.uuid4())
            
            # 如果没有trace_id，生成一个
            if not operation_log.trace_id:
                operation_log.trace_id = str(uuid.uuid4())
            
            # 如果没有操作时间，设置为当前时间
            if not operation_log.operation_time:
                operation_log.operation_time = datetime.now()
            
            insert_sql = """
            INSERT INTO business_operation_logs (
                operation_id, api_code, api_name, business_category, business_type,
                institution_code, psn_no, mdtrt_id, request_data, response_data,
                status, error_code, error_message, operation_time, complete_time,
                operator_id, operator_name, trace_id, client_ip, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            params = (
                operation_log.operation_id,
                operation_log.api_code,
                operation_log.api_name,
                operation_log.business_category,
                operation_log.business_type,
                operation_log.institution_code,
                operation_log.psn_no,
                operation_log.mdtrt_id,
                json.dumps(operation_log.request_data, ensure_ascii=False) if operation_log.request_data else None,
                json.dumps(operation_log.response_data, ensure_ascii=False) if operation_log.response_data else None,
                operation_log.status,
                operation_log.error_code,
                operation_log.error_message,
                operation_log.operation_time,
                operation_log.complete_time,
                operation_log.operator_id,
                getattr(operation_log, 'operator_name', None),
                operation_log.trace_id,
                operation_log.client_ip,
                datetime.now(),
                datetime.now()
            )
            
            affected_rows = self.db.execute_update(insert_sql, params)
            
            if affected_rows > 0:
                self.logger.debug(f"操作日志保存成功: {operation_log.operation_id}")
                return True
            else:
                self.logger.warning(f"操作日志保存失败，未影响任何行: {operation_log.operation_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"保存操作日志时发生错误: {e}")
            return False
    
    def update_operation_log(self, operation_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新操作日志
        
        Args:
            operation_id: 操作ID
            updates: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not updates:
                return True
            
            # 构建更新SQL
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field in ['request_data', 'response_data'] and isinstance(value, dict):
                    set_clauses.append(f"{field} = %s")
                    params.append(json.dumps(value, ensure_ascii=False))
                else:
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
            
            # 添加更新时间
            set_clauses.append("updated_at = %s")
            params.append(datetime.now())
            
            # 添加WHERE条件
            params.append(operation_id)
            
            update_sql = f"""
            UPDATE business_operation_logs 
            SET {', '.join(set_clauses)}
            WHERE operation_id = %s
            """
            
            affected_rows = self.db.execute_update(update_sql, tuple(params))
            
            if affected_rows > 0:
                self.logger.debug(f"操作日志更新成功: {operation_id}")
                return True
            else:
                self.logger.warning(f"操作日志更新失败，未找到记录: {operation_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新操作日志时发生错误: {e}")
            return False
    
    def get_operation_logs(self, query: LogQuery) -> List[OperationLog]:
        """
        查询操作日志
        
        Args:
            query: 查询条件
            
        Returns:
            List[OperationLog]: 操作日志列表
        """
        try:
            # 构建查询SQL
            where_clauses = []
            params = []
            
            if query.start_time:
                where_clauses.append("operation_time >= %s")
                params.append(query.start_time)
            
            if query.end_time:
                where_clauses.append("operation_time <= %s")
                params.append(query.end_time)
            
            if query.api_code:
                where_clauses.append("api_code = %s")
                params.append(query.api_code)
            
            if query.institution_code:
                where_clauses.append("institution_code = %s")
                params.append(query.institution_code)
            
            if query.business_category:
                where_clauses.append("business_category = %s")
                params.append(query.business_category)
            
            if query.business_type:
                where_clauses.append("business_type = %s")
                params.append(query.business_type)
            
            if query.status:
                where_clauses.append("status = %s")
                params.append(query.status)
            
            if query.psn_no:
                where_clauses.append("psn_no = %s")
                params.append(query.psn_no)
            
            if query.mdtrt_id:
                where_clauses.append("mdtrt_id = %s")
                params.append(query.mdtrt_id)
            
            if query.trace_id:
                where_clauses.append("trace_id = %s")
                params.append(query.trace_id)
            
            if query.operation_id:
                where_clauses.append("operation_id = %s")
                params.append(query.operation_id)
            
            # 构建完整SQL
            base_sql = "SELECT * FROM business_operation_logs"
            
            if where_clauses:
                base_sql += " WHERE " + " AND ".join(where_clauses)
            
            base_sql += f" ORDER BY {query.order_by} {query.order_direction}"
            base_sql += f" LIMIT %s OFFSET %s"
            
            # 添加LIMIT和OFFSET参数
            params.extend([query.limit, query.offset])
            
            # 执行查询
            results = self.db.execute_query(base_sql, tuple(params))
            
            # 转换为OperationLog对象
            operation_logs = []
            for row in results:
                # 解析JSON字段
                if row.get('request_data'):
                    try:
                        row['request_data'] = json.loads(row['request_data'])
                    except (json.JSONDecodeError, TypeError):
                        row['request_data'] = {}
                
                if row.get('response_data'):
                    try:
                        row['response_data'] = json.loads(row['response_data'])
                    except (json.JSONDecodeError, TypeError):
                        row['response_data'] = {}
                
                # 转换日期时间字段为字符串格式
                if row.get('operation_time') and hasattr(row['operation_time'], 'isoformat'):
                    row['operation_time'] = row['operation_time'].isoformat()
                if row.get('complete_time') and hasattr(row['complete_time'], 'isoformat'):
                    row['complete_time'] = row['complete_time'].isoformat()
                
                operation_log = OperationLog.from_dict(row)
                operation_logs.append(operation_log)
            
            return operation_logs
            
        except Exception as e:
            self.logger.error(f"查询操作日志时发生错误: {e}")
            return []
    
    def get_operation_log_by_id(self, operation_id: str) -> Optional[OperationLog]:
        """
        根据操作ID获取单个操作日志
        
        Args:
            operation_id: 操作ID
            
        Returns:
            Optional[OperationLog]: 操作日志对象或None
        """
        query = LogQuery(operation_id=operation_id, limit=1)
        logs = self.get_operation_logs(query)
        return logs[0] if logs else None
    
    def get_statistics(self, stat_query: StatQuery) -> StatResult:
        """
        获取统计数据
        
        Args:
            stat_query: 统计查询条件
            
        Returns:
            StatResult: 统计结果
        """
        try:
            # 构建基础WHERE条件
            where_clauses = []
            params = []
            
            if stat_query.start_time:
                where_clauses.append("operation_time >= %s")
                params.append(stat_query.start_time)
            
            if stat_query.end_time:
                where_clauses.append("operation_time <= %s")
                params.append(stat_query.end_time)
            
            if stat_query.api_code:
                where_clauses.append("api_code = %s")
                params.append(stat_query.api_code)
            
            if stat_query.institution_code:
                where_clauses.append("institution_code = %s")
                params.append(stat_query.institution_code)
            
            if stat_query.business_category:
                where_clauses.append("business_category = %s")
                params.append(stat_query.business_category)
            
            if stat_query.business_type:
                where_clauses.append("business_type = %s")
                params.append(stat_query.business_type)
            
            where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # 获取总体统计
            total_sql = f"""
            SELECT 
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                AVG(CASE 
                    WHEN complete_time IS NOT NULL AND operation_time IS NOT NULL 
                    THEN TIMESTAMPDIFF(MICROSECOND, operation_time, complete_time) / 1000000.0 
                    ELSE NULL 
                END) as avg_response_time,
                MAX(CASE 
                    WHEN complete_time IS NOT NULL AND operation_time IS NOT NULL 
                    THEN TIMESTAMPDIFF(MICROSECOND, operation_time, complete_time) / 1000000.0 
                    ELSE NULL 
                END) as max_response_time,
                MIN(CASE 
                    WHEN complete_time IS NOT NULL AND operation_time IS NOT NULL 
                    THEN TIMESTAMPDIFF(MICROSECOND, operation_time, complete_time) / 1000000.0 
                    ELSE NULL 
                END) as min_response_time
            FROM business_operation_logs
            {where_clause}
            """
            
            total_result = self.db.execute_query_one(total_sql, tuple(params))
            
            # 获取分组统计详情
            group_by_field = stat_query.group_by
            if group_by_field == "date":
                if stat_query.time_granularity == "hour":
                    group_by_field = "DATE_FORMAT(operation_time, '%Y-%m-%d %H:00:00')"
                elif stat_query.time_granularity == "day":
                    group_by_field = "DATE(operation_time)"
                elif stat_query.time_granularity == "week":
                    group_by_field = "DATE_FORMAT(operation_time, '%Y-%u')"
                elif stat_query.time_granularity == "month":
                    group_by_field = "DATE_FORMAT(operation_time, '%Y-%m')"
            
            detail_sql = f"""
            SELECT 
                {group_by_field} as group_key,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                AVG(CASE 
                    WHEN complete_time IS NOT NULL AND operation_time IS NOT NULL 
                    THEN TIMESTAMPDIFF(MICROSECOND, operation_time, complete_time) / 1000000.0 
                    ELSE NULL 
                END) as avg_response_time
            FROM business_operation_logs
            {where_clause}
            GROUP BY {group_by_field}
            ORDER BY group_key DESC
            LIMIT 100
            """
            
            detail_results = self.db.execute_query(detail_sql, tuple(params))
            
            # 构建统计结果
            stat_result = StatResult(
                total_count=total_result.get('total_count', 0) if total_result else 0,
                success_count=total_result.get('success_count', 0) if total_result else 0,
                failed_count=total_result.get('failed_count', 0) if total_result else 0,
                avg_response_time=float(total_result.get('avg_response_time', 0) or 0) if total_result else 0.0,
                max_response_time=float(total_result.get('max_response_time', 0) or 0) if total_result else 0.0,
                min_response_time=float(total_result.get('min_response_time', 0) or 0) if total_result else 0.0,
                details=[
                    {
                        'group_key': str(row['group_key']),
                        'count': row['count'],
                        'success_count': row['success_count'],
                        'failed_count': row['failed_count'],
                        'success_rate': (row['success_count'] / row['count'] * 100) if row['count'] > 0 else 0,
                        'avg_response_time': float(row['avg_response_time'] or 0)
                    }
                    for row in detail_results
                ]
            )
            
            return stat_result
            
        except Exception as e:
            self.logger.error(f"获取统计数据时发生错误: {e}")
            return StatResult()
    
    def get_interface_statistics(self, api_code: str, days: int = 7) -> InterfaceStatistics:
        """
        获取特定接口的统计信息
        
        Args:
            api_code: 接口编码
            days: 统计天数
            
        Returns:
            InterfaceStatistics: 接口统计信息
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        query = StatQuery(
            start_time=start_time,
            end_time=end_time,
            api_code=api_code,
            group_by="date",
            time_granularity="day"
        )
        
        stat_result = self.get_statistics(query)
        
        return InterfaceStatistics(
            stat_date=datetime.now().date(),
            institution_code="ALL",
            api_code=api_code,
            api_name=f"接口{api_code}",
            total_calls=stat_result.total_count,
            success_calls=stat_result.success_count,
            failed_calls=stat_result.failed_count,
            avg_response_time=stat_result.avg_response_time,
            max_response_time=stat_result.max_response_time,
            min_response_time=stat_result.min_response_time
        )
    
    def get_system_statistics(self, days: int = 7) -> SystemStatistics:
        """
        获取系统整体统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            SystemStatistics: 系统统计信息
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        query = StatQuery(
            start_time=start_time,
            end_time=end_time,
            group_by="api_code"
        )
        
        stat_result = self.get_statistics(query)
        
        # 获取活跃接口数量
        active_interfaces_sql = """
        SELECT COUNT(DISTINCT api_code) as active_count
        FROM business_operation_logs
        WHERE operation_time >= %s AND operation_time <= %s
        """
        
        active_result = self.db.execute_query_one(
            active_interfaces_sql, 
            (start_time, end_time)
        )
        
        # 获取活跃机构数量
        active_orgs_sql = """
        SELECT DISTINCT institution_code
        FROM business_operation_logs
        WHERE operation_time >= %s AND operation_time <= %s
        """
        
        org_results = self.db.execute_query(
            active_orgs_sql, 
            (start_time, end_time)
        )
        
        active_institutions = [row['institution_code'] for row in org_results]
        
        return SystemStatistics(
            stat_date=datetime.now().date(),
            total_calls=stat_result.total_count,
            total_success=stat_result.success_count,
            total_failed=stat_result.failed_count,
            avg_response_time=stat_result.avg_response_time,
            total_apis=active_result.get('active_count', 0) if active_result else 0,
            active_institutions=active_institutions
        )
    
    def cleanup_old_logs(self, days_to_keep: int = 365) -> int:
        """
        清理旧的日志记录
        
        Args:
            days_to_keep: 保留天数
            
        Returns:
            int: 删除的记录数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            delete_sql = """
            DELETE FROM business_operation_logs 
            WHERE operation_time < %s
            """
            
            affected_rows = self.db.execute_update(delete_sql, (cutoff_date,))
            
            if affected_rows > 0:
                self.logger.info(f"清理了 {affected_rows} 条旧日志记录")
            
            return affected_rows
            
        except Exception as e:
            self.logger.error(f"清理旧日志时发生错误: {e}")
            return 0
    
    def get_error_summary(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取错误摘要统计
        
        Args:
            hours: 统计时间范围(小时)
            
        Returns:
            List[Dict[str, Any]]: 错误摘要列表
        """
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            error_sql = """
            SELECT 
                api_code,
                api_name,
                error_code,
                error_message,
                COUNT(*) as error_count,
                MAX(operation_time) as last_occurrence
            FROM business_operation_logs
            WHERE status = 'failed' 
            AND operation_time >= %s
            AND error_code IS NOT NULL
            GROUP BY api_code, api_name, error_code, error_message
            ORDER BY error_count DESC, last_occurrence DESC
            LIMIT 50
            """
            
            results = self.db.execute_query(error_sql, (start_time,))
            
            return [
                {
                    'api_code': row['api_code'],
                    'api_name': row['api_name'],
                    'error_code': row['error_code'],
                    'error_message': row['error_message'],
                    'error_count': row['error_count'],
                    'last_occurrence': row['last_occurrence'].isoformat() if row['last_occurrence'] else None
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"获取错误摘要时发生错误: {e}")
            return []
    
    def batch_save_operation_logs(self, operation_logs: List[OperationLog]) -> int:
        """
        批量保存操作日志
        
        Args:
            operation_logs: 操作日志列表
            
        Returns:
            int: 成功保存的记录数
        """
        if not operation_logs:
            return 0
        
        try:
            insert_sql = """
            INSERT INTO business_operation_logs (
                operation_id, api_code, api_name, business_category, business_type,
                institution_code, psn_no, mdtrt_id, request_data, response_data,
                status, error_code, error_message, operation_time, complete_time,
                operator_id, operator_name, trace_id, client_ip, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            params_list = []
            for log in operation_logs:
                # 确保必要字段有值
                if not log.operation_id:
                    log.operation_id = str(uuid.uuid4())
                if not log.trace_id:
                    log.trace_id = str(uuid.uuid4())
                if not log.operation_time:
                    log.operation_time = datetime.now()
                
                params = (
                    log.operation_id,
                    log.api_code,
                    log.api_name,
                    log.business_category,
                    log.business_type,
                    log.institution_code,
                    log.psn_no,
                    log.mdtrt_id,
                    json.dumps(log.request_data, ensure_ascii=False) if log.request_data else None,
                    json.dumps(log.response_data, ensure_ascii=False) if log.response_data else None,
                    log.status,
                    log.error_code,
                    log.error_message,
                    log.operation_time,
                    log.complete_time,
                    log.operator_id,
                    getattr(log, 'operator_name', None),
                    log.trace_id,
                    log.client_ip,
                    datetime.now(),
                    datetime.now()
                )
                params_list.append(params)
            
            affected_rows = self.db.execute_batch_update(insert_sql, params_list)
            
            self.logger.info(f"批量保存操作日志成功: {affected_rows} 条记录")
            return affected_rows
            
        except Exception as e:
            self.logger.error(f"批量保存操作日志时发生错误: {e}")
            return 0