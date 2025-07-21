"""
HIS系统集成模块

提供与医院信息系统(HIS)的集成功能，包括：
- 患者信息同步
- 医保结算结果回写
- 数据同步服务
"""

from .his_integration_manager import (
    HISIntegrationManager,
    HISIntegrationConfig,
    SyncResult,
    WritebackResult
)
from .data_sync_service import (
    DataSyncService,
    SyncDirection,
    SyncStatus,
    SyncTask,
    DataRecord,
    SyncConflict,
    DataSyncConfig
)

__all__ = [
    'HISIntegrationManager',
    'HISIntegrationConfig',
    'SyncResult',
    'WritebackResult',
    'DataSyncService',
    'SyncDirection',
    'SyncStatus',
    'SyncTask',
    'DataRecord',
    'SyncConflict',
    'DataSyncConfig'
]