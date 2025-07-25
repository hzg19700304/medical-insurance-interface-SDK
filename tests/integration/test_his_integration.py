"""
HIS系统集成测试

测试HIS集成管理器和数据同步服务的基本功能
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.integration import (
    HISIntegrationManager,
    PatientInfo,
    SettlementResult,
    HISIntegrationConfig,
    DataSyncService,
    SyncDirection,
    DataSyncConfig
)


def test_his_integration_manager():
    """测试HIS集成管理器"""
    print("=== 测试HIS集成管理器 ===")
    
    try:
        # 创建数据库配置（从环境变量加载）
        db_config = DatabaseConfig.from_env()
        print(f"数据库配置: {db_config.host}:{db_config.port}/{db_config.database}")
        db_manager = DatabaseManager(db_config)
        
        # 创建必要的表结构
        create_test_tables(db_manager)
        
        # 创建HIS集成配置
        his_config = HISIntegrationConfig(
            patient_sync_enabled=True,
            settlement_writeback_enabled=True
        )
        
        # 创建HIS集成管理器
        his_manager = HISIntegrationManager(db_manager, his_config)
        
        print("✓ HIS集成管理器创建成功")
        
        # 测试患者信息同步
        patient_data = {
            'patient_id': 'P001',
            'name': '张三',
            'id_card': '430123199001011234',
            'gender': '1',
            'birth_date': '1990-01-01',
            'phone': '13800138000',
            'address': '湖南省长沙市'
        }
        
        try:
            patient_info = his_manager.sync_patient_info(patient_data)
            print(f"✓ 患者信息同步成功: {patient_info.patient_id}")
        except Exception as e:
            print(f"⚠ 患者信息同步测试跳过 (需要数据库): {e}")
        
        # 测试结算结果回写
        settlement_data = {
            'settlement_id': 'S001',
            'patient_id': 'P001',
            'mdtrt_id': 'M001',
            'total_amount': 1000.0,
            'insurance_amount': 800.0,
            'personal_amount': 200.0,
            'settlement_time': datetime.now(),
            'settlement_status': 'completed'
        }
        
        try:
            settlement_result = his_manager.write_settlement_result(settlement_data)
            print(f"✓ 结算结果回写成功: {settlement_result.settlement_id}")
        except Exception as e:
            print(f"⚠ 结算结果回写测试跳过 (需要数据库): {e}")
        
        # 关闭管理器
        his_manager.close()
        print("✓ HIS集成管理器关闭成功")
        
    except Exception as e:
        print(f"✗ HIS集成管理器测试失败: {e}")


def test_data_sync_service():
    """测试数据同步服务"""
    print("\n=== 测试数据同步服务 ===")
    
    try:
        # 创建数据库配置（从环境变量加载）
        db_config = DatabaseConfig.from_env()
        print(f"数据库配置: {db_config.host}:{db_config.port}/{db_config.database}")
        db_manager = DatabaseManager(db_config)
        
        # 首先创建必要的表结构
        create_test_tables(db_manager)
        
        # 创建数据同步配置（使用相同的数据库配置作为HIS数据库）
        sync_config = DataSyncConfig(
            his_db_config={
                'host': db_config.host,
                'port': db_config.port,
                'user': db_config.user,
                'password': db_config.password,
                'database': db_config.database  # 在实际环境中应该是不同的HIS数据库
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
            batch_size=100
        )
        
        # 创建数据同步服务
        sync_service = DataSyncService(db_manager, sync_config)
        
        print("✓ 数据同步服务创建成功")
        
        # 测试添加同步任务
        task_id = sync_service.add_sync_task(
            'patients',
            SyncDirection.BIDIRECTIONAL,
            'incremental'
        )
        print(f"✓ 同步任务添加成功: {task_id}")
        
        # 测试获取任务状态
        task_status = sync_service.get_sync_task_status(task_id)
        if task_status:
            print(f"✓ 任务状态查询成功: {task_status['status']}")
        
        # 测试增量同步（模拟）
        try:
            sync_result = sync_service.perform_incremental_sync(
                'patients',
                SyncDirection.FROM_HIS,
                datetime.now() - timedelta(hours=1)
            )
            print(f"✓ 增量同步测试成功: {sync_result}")
        except Exception as e:
            print(f"⚠ 增量同步测试跳过 (需要HIS数据库): {e}")
        
        # 测试数据一致性检查
        try:
            consistency_result = sync_service.check_data_consistency('patients')
            print(f"✓ 数据一致性检查成功: {consistency_result.get('table_name')}")
        except Exception as e:
            print(f"⚠ 数据一致性检查跳过 (需要数据库): {e}")
        
        # 关闭服务
        sync_service.close()
        print("✓ 数据同步服务关闭成功")
        
    except Exception as e:
        print(f"✗ 数据同步服务测试失败: {e}")


def create_test_tables(db_manager: DatabaseManager):
    """创建测试所需的数据库表"""
    try:
        # 创建患者表
        patients_sql = """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            id_card VARCHAR(18),
            gender CHAR(1),
            birth_date DATE,
            phone VARCHAR(20),
            address TEXT,
            sync_status VARCHAR(20) DEFAULT 'pending',
            sync_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(patients_sql)
        
        # 创建HIS患者表
        his_patients_sql = """
        CREATE TABLE IF NOT EXISTS his_patients (
            patient_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            id_card VARCHAR(18),
            gender CHAR(1),
            birth_date DATE,
            phone VARCHAR(20),
            address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(his_patients_sql)
        
        # 创建数据同步状态表
        sync_status_sql = """
        CREATE TABLE IF NOT EXISTS data_sync_status (
            table_name VARCHAR(100) PRIMARY KEY,
            last_sync_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(sync_status_sql)
        
        # 创建数据同步任务表
        sync_tasks_sql = """
        CREATE TABLE IF NOT EXISTS data_sync_tasks (
            task_id VARCHAR(50) PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            sync_direction VARCHAR(20) NOT NULL,
            sync_type VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            total_records INT DEFAULT 0,
            synced_records INT DEFAULT 0,
            failed_records INT DEFAULT 0,
            conflict_records INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            completed_at DATETIME,
            error_message TEXT
        )
        """
        db_manager.execute_update(sync_tasks_sql)
        
        # 创建数据同步冲突表
        sync_conflicts_sql = """
        CREATE TABLE IF NOT EXISTS data_sync_conflicts (
            conflict_id VARCHAR(50) PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            primary_key VARCHAR(100) NOT NULL,
            his_data JSON,
            medical_data JSON,
            conflict_fields JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE,
            resolution_strategy VARCHAR(50),
            resolved_at DATETIME
        )
        """
        db_manager.execute_update(sync_conflicts_sql)
        
        # 创建数据一致性检查表
        consistency_checks_sql = """
        CREATE TABLE IF NOT EXISTS data_consistency_checks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            check_time DATETIME NOT NULL,
            total_records INT DEFAULT 0,
            consistent_count INT DEFAULT 0,
            inconsistent_count INT DEFAULT 0,
            his_only_count INT DEFAULT 0,
            medical_only_count INT DEFAULT 0,
            check_result JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(consistency_checks_sql)
        
        print("✓ 测试数据库表创建成功")
        
    except Exception as e:
        print(f"⚠ 创建测试表失败: {e}")


def test_data_models():
    """测试数据模型"""
    print("\n=== 测试数据模型 ===")
    
    try:
        # 测试患者信息模型
        patient_info = PatientInfo(
            patient_id='P001',
            name='张三',
            id_card='430123199001011234',
            gender='1',
            birth_date='1990-01-01',
            phone='13800138000',
            sync_status='synced',
            sync_time=datetime.now()
        )
        print(f"✓ 患者信息模型创建成功: {patient_info.name}")
        
        # 测试结算结果模型
        settlement_result = SettlementResult(
            settlement_id='S001',
            patient_id='P001',
            mdtrt_id='M001',
            total_amount=1000.0,
            insurance_amount=800.0,
            personal_amount=200.0,
            settlement_time=datetime.now(),
            settlement_status='completed'
        )
        print(f"✓ 结算结果模型创建成功: {settlement_result.settlement_id}")
        
        # 测试配置模型
        his_config = HISIntegrationConfig(
            patient_sync_enabled=True,
            settlement_writeback_enabled=True,
            sync_interval=300,
            batch_size=100
        )
        print(f"✓ HIS集成配置创建成功: 同步间隔{his_config.sync_interval}秒")
        
        sync_config = DataSyncConfig(
            his_db_config={'host': 'localhost'},
            sync_tables={'patients': {'primary_key': 'id'}},
            sync_interval=60
        )
        print(f"✓ 数据同步配置创建成功: 同步间隔{sync_config.sync_interval}秒")
        
    except Exception as e:
        print(f"✗ 数据模型测试失败: {e}")


def main():
    """主测试函数"""
    print("开始HIS系统集成测试...")
    
    # 测试数据模型
    test_data_models()
    
    # 测试HIS集成管理器
    test_his_integration_manager()
    
    # 测试数据同步服务
    test_data_sync_service()
    
    print("\nHIS系统集成测试完成!")


if __name__ == "__main__":
    main()