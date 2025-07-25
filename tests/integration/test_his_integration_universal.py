"""
通用HIS集成管理器测试

测试基于配置驱动的通用HIS集成功能，支持206个医保接口
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig
from medical_insurance_sdk.core.config_manager import ConfigManager
from medical_insurance_sdk.integration.his_integration_manager import (
    HISIntegrationManager,
    HISIntegrationConfig,
    SyncResult,
    WritebackResult
)


def test_universal_his_integration():
    """测试通用HIS集成管理器"""
    print("=== 测试通用HIS集成管理器 ===")
    
    try:
        # 创建数据库配置
        db_config = DatabaseConfig.from_env()
        print(f"数据库配置: {db_config.host}:{db_config.port}/{db_config.database}")
        db_manager = DatabaseManager(db_config)
        
        # 创建配置管理器
        config_manager = ConfigManager(db_config)
        
        # 创建HIS集成配置
        his_config = HISIntegrationConfig(
            sync_enabled=True,
            writeback_enabled=True,
            consistency_check_enabled=True
        )
        
        # 创建HIS集成管理器
        his_manager = HISIntegrationManager(db_manager, config_manager, his_config)
        
        print("✓ 通用HIS集成管理器创建成功")
        
        # 测试1：人员信息查询接口(1101)的数据同步
        test_patient_info_sync(his_manager)
        
        # 测试2：门诊结算接口(2207)的结果回写
        test_settlement_writeback(his_manager)
        
        # 测试3：数据一致性检查
        test_data_consistency_check(his_manager)
        
        # 测试4：获取同步统计
        test_sync_statistics(his_manager)
        
        # 关闭管理器
        his_manager.close()
        print("✓ HIS集成管理器关闭成功")
        
    except Exception as e:
        print(f"✗ 通用HIS集成管理器测试失败: {e}")


def test_patient_info_sync(his_manager: HISIntegrationManager):
    """测试患者信息同步（1101接口）"""
    print("\n--- 测试患者信息同步 (1101接口) ---")
    
    try:
        # 模拟1101接口返回的医保数据
        medical_data = {
            "infcode": 0,
            "output": {
                "baseinfo": {
                    "psn_no": "43012319900101001",
                    "psn_name": "张三",
                    "certno": "430123199001011234",
                    "gend": "1",
                    "brdy": "1990-01-01",
                    "age": 34
                },
                "insuinfo": [
                    {
                        "insutype": "310",
                        "psn_type": "1",
                        "balc": 1500.00,
                        "psn_insu_stas": "1",
                        "psn_insu_date": "2020-01-01"
                    }
                ]
            }
        }
        
        # 执行数据同步
        sync_result = his_manager.sync_medical_data(
            api_code="1101",
            medical_data=medical_data,
            org_code="H43010000001",
            sync_direction="to_his"
        )
        
        if sync_result.success:
            print(f"✓ 患者信息同步成功: 同步{sync_result.synced_count}条记录")
        else:
            print(f"⚠ 患者信息同步失败: {sync_result.error_message}")
        
    except Exception as e:
        print(f"✗ 患者信息同步测试失败: {e}")


def test_settlement_writeback(his_manager: HISIntegrationManager):
    """测试结算结果回写（2207接口）"""
    print("\n--- 测试结算结果回写 (2207接口) ---")
    
    try:
        # 模拟2207接口返回的结算结果
        settlement_result = {
            "infcode": 0,
            "output": {
                "setlinfo": {
                    "setl_id": "S202401150001",
                    "mdtrt_id": "M202401150001",
                    "psn_no": "43012319900101001",
                    "setl_totlnum": 1000.00,
                    "hifp_pay": 800.00,
                    "psn_pay": 200.00,
                    "acct_pay": 0.00,
                    "setl_time": "2024-01-15 10:30:00"
                }
            }
        }
        
        # 执行结果回写
        writeback_result = his_manager.writeback_medical_result(
            api_code="2207",
            medical_result=settlement_result,
            org_code="H43010000001"
        )
        
        if writeback_result.success:
            print(f"✓ 结算结果回写成功: 回写{writeback_result.written_count}条记录")
        else:
            print(f"⚠ 结算结果回写失败: {writeback_result.error_message}")
        
    except Exception as e:
        print(f"✗ 结算结果回写测试失败: {e}")


def test_data_consistency_check(his_manager: HISIntegrationManager):
    """测试数据一致性检查"""
    print("\n--- 测试数据一致性检查 ---")
    
    try:
        # 执行一致性检查
        consistency_result = his_manager.check_data_consistency(
            api_code="1101",
            org_code="H43010000001",
            check_period_hours=24
        )
        
        if consistency_result.get('success'):
            print(f"✓ 数据一致性检查完成")
            print(f"  医保记录数: {consistency_result.get('total_medical_records', 0)}")
            print(f"  HIS记录数: {consistency_result.get('total_his_records', 0)}")
            print(f"  一致记录数: {consistency_result.get('consistent_count', 0)}")
            print(f"  不一致记录数: {consistency_result.get('inconsistent_count', 0)}")
        else:
            print(f"⚠ 数据一致性检查失败: {consistency_result.get('error')}")
        
    except Exception as e:
        print(f"✗ 数据一致性检查测试失败: {e}")


def test_sync_statistics(his_manager: HISIntegrationManager):
    """测试同步统计"""
    print("\n--- 测试同步统计 ---")
    
    try:
        # 获取同步统计
        stats = his_manager.get_sync_statistics(
            api_code="1101",
            org_code="H43010000001",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        if stats:
            print("✓ 同步统计获取成功")
            print(f"  统计期间: {stats.get('period', {}).get('start_date')} 到 {stats.get('period', {}).get('end_date')}")
            print(f"  同步统计: {len(stats.get('sync_statistics', []))} 条记录")
            print(f"  回写统计: {len(stats.get('writeback_statistics', []))} 条记录")
        else:
            print("⚠ 同步统计为空")
        
    except Exception as e:
        print(f"✗ 同步统计测试失败: {e}")


def setup_test_his_integration_config():
    """设置测试用的HIS集成配置"""
    print("\n--- 设置测试HIS集成配置 ---")
    
    try:
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 1101接口的HIS集成配置
        his_integration_config_1101 = {
            "field_mappings": {
                "patient_id": "output.baseinfo.psn_no",
                "patient_name": "output.baseinfo.psn_name",
                "id_card": "output.baseinfo.certno",
                "gender": "output.baseinfo.gend",
                "birth_date": "output.baseinfo.brdy",
                "age": "output.baseinfo.age"
            },
            "transformations": {
                "gender": {
                    "type": "mapping",
                    "mapping": {"1": "M", "2": "F"}
                },
                "birth_date": {
                    "type": "format",
                    "format": "{}"
                }
            },
            "sync_config": {
                "table_name": "his_patients",
                "primary_key": "patient_id",
                "operation": "upsert"
            },
            "consistency_check": {
                "table_name": "his_patients",
                "time_field": "updated_at",
                "key_fields": ["patient_id", "id_card"]
            }
        }
        
        # 2207接口的HIS集成配置
        his_integration_config_2207 = {
            "writeback_mapping": {
                "field_mappings": {
                    "settlement_id": "output.setlinfo.setl_id",
                    "patient_id": "output.setlinfo.psn_no",
                    "total_amount": "output.setlinfo.setl_totlnum",
                    "insurance_amount": "output.setlinfo.hifp_pay",
                    "personal_amount": "output.setlinfo.psn_pay",
                    "account_amount": "output.setlinfo.acct_pay",
                    "settlement_time": "output.setlinfo.setl_time"
                },
                "writeback_config": {
                    "table_name": "his_settlements",
                    "primary_key": "settlement_id",
                    "operation": "upsert"
                }
            }
        }
        
        # 更新接口配置
        update_sql = """
            UPDATE medical_interface_config 
            SET his_integration_config = %s 
            WHERE api_code = %s
        """
        
        # 更新1101接口配置
        db_manager.execute_update(
            update_sql, 
            (json.dumps(his_integration_config_1101, ensure_ascii=False), "1101")
        )
        
        # 更新2207接口配置
        db_manager.execute_update(
            update_sql, 
            (json.dumps(his_integration_config_2207, ensure_ascii=False), "2207")
        )
        
        print("✓ HIS集成配置设置完成")
        
    except Exception as e:
        print(f"✗ HIS集成配置设置失败: {e}")


def create_test_tables():
    """创建测试所需的数据库表"""
    print("\n--- 创建测试数据库表 ---")
    
    try:
        db_config = DatabaseConfig.from_env()
        db_manager = DatabaseManager(db_config)
        
        # 创建HIS患者表
        his_patients_sql = """
        CREATE TABLE IF NOT EXISTS his_patients (
            patient_id VARCHAR(50) PRIMARY KEY,
            patient_name VARCHAR(100) NOT NULL,
            id_card VARCHAR(18),
            gender CHAR(1),
            birth_date DATE,
            age INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(his_patients_sql)
        
        # 创建HIS结算表
        his_settlements_sql = """
        CREATE TABLE IF NOT EXISTS his_settlements (
            settlement_id VARCHAR(50) PRIMARY KEY,
            patient_id VARCHAR(50),
            total_amount DECIMAL(12,2),
            insurance_amount DECIMAL(12,2),
            personal_amount DECIMAL(12,2),
            account_amount DECIMAL(12,2),
            settlement_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(his_settlements_sql)
        
        # 创建HIS数据同步日志表
        his_sync_log_sql = """
        CREATE TABLE IF NOT EXISTS his_data_sync_log (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            sync_id VARCHAR(50) NOT NULL,
            api_code VARCHAR(10) NOT NULL,
            org_code VARCHAR(20) NOT NULL,
            sync_direction VARCHAR(20) DEFAULT 'to_his',
            medical_data JSON,
            his_data JSON,
            sync_status VARCHAR(20),
            synced_records INT DEFAULT 0,
            failed_records INT DEFAULT 0,
            error_message TEXT,
            sync_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(his_sync_log_sql)
        
        # 创建HIS回写日志表
        his_writeback_log_sql = """
        CREATE TABLE IF NOT EXISTS his_writeback_log (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            writeback_id VARCHAR(50) NOT NULL,
            api_code VARCHAR(10) NOT NULL,
            org_code VARCHAR(20) NOT NULL,
            medical_result JSON,
            his_data JSON,
            writeback_status VARCHAR(20),
            written_records INT DEFAULT 0,
            failed_records INT DEFAULT 0,
            error_message TEXT,
            writeback_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(his_writeback_log_sql)
        
        # 创建数据一致性检查表
        consistency_check_sql = """
        CREATE TABLE IF NOT EXISTS data_consistency_checks (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            check_id VARCHAR(50) NOT NULL,
            api_code VARCHAR(10) NOT NULL,
            org_code VARCHAR(20) NOT NULL,
            check_result JSON,
            check_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_update(consistency_check_sql)
        
        print("✓ 测试数据库表创建成功")
        
    except Exception as e:
        print(f"✗ 创建测试表失败: {e}")


def main():
    """主测试函数"""
    print("开始通用HIS集成管理器测试...")
    
    # 创建测试表
    create_test_tables()
    
    # 设置测试配置
    setup_test_his_integration_config()
    
    # 测试通用HIS集成管理器
    test_universal_his_integration()
    
    print("\n通用HIS集成管理器测试完成!")


if __name__ == "__main__":
    main()