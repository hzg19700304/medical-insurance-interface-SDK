#!/usr/bin/env python3
"""
HIS集成管理器综合测试脚本

测试HIS集成管理器的核心功能：
1. 患者信息同步功能
2. 医保结算结果回写
3. 数据一致性检查
4. 冲突解决机制
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HISIntegrationTester:
    """HIS集成管理器测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        # 从环境变量读取数据库配置
        self.db_config = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USERNAME', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'medical_insurance'),
            charset=os.getenv('DB_CHARSET', 'utf8mb4')
        )
        
        # 初始化组件
        self.db_manager = DatabaseManager(self.db_config)
        self.config_manager = ConfigManager(self.db_config)
        
        # HIS集成配置（使用相同的数据库进行测试）
        self.his_integration_config = HISIntegrationConfig(
            his_db_config={
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'user': os.getenv('DB_USERNAME', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_DATABASE', 'medical_insurance'),  # 使用相同数据库进行测试
                'charset': os.getenv('DB_CHARSET', 'utf8mb4')
            },
            sync_enabled=True,
            writeback_enabled=True,
            consistency_check_enabled=True
        )
        
        # 初始化HIS集成管理器
        self.his_manager = HISIntegrationManager(
            self.db_manager,
            self.config_manager,
            self.his_integration_config
        )
        
        logger.info("HIS集成管理器测试环境初始化完成")
    
    def setup_test_data(self):
        """设置测试数据"""
        logger.info("设置测试数据...")
        
        # 1. 插入接口配置（包含HIS集成配置）
        his_integration_config = {
            "field_mappings": {
                "patient_id": "output.baseinfo.psn_no",
                "patient_name": "output.baseinfo.psn_name",
                "id_card": "output.baseinfo.certno",
                "gender": "output.baseinfo.gend",
                "birth_date": "output.baseinfo.brdy",
                "phone": "output.baseinfo.tel"
            },
            "sync_config": {
                "table_name": "his_patients",
                "primary_key": "patient_id",
                "operation": "upsert"
            },
            "writeback_mapping": {
                "field_mappings": {
                    "settlement_id": "settlement_result.setl_id",
                    "total_amount": "settlement_result.setl_totlnum",
                    "insurance_amount": "settlement_result.hifp_pay",
                    "personal_amount": "settlement_result.psn_pay",
                    "settlement_time": "settlement_result.setl_time"
                },
                "writeback_config": {
                    "table_name": "his_settlements",
                    "primary_key": "settlement_id",
                    "operation": "insert"
                }
            },
            "consistency_check": {
                "table_name": "his_patients",
                "time_field": "updated_at",
                "key_fields": ["patient_id", "patient_name", "id_card"]
            }
        }
        
        # 插入1101接口配置
        self.db_manager.execute_update("""
            INSERT INTO medical_interface_config 
            (api_code, api_name, business_category, business_type, 
             required_params, his_integration_config, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            his_integration_config = VALUES(his_integration_config)
        """, (
            '1101', '人员信息获取', '查询类', '人员查询',
            '{"psn_no": {"type": "string"}}',
            json.dumps(his_integration_config, ensure_ascii=False),
            True
        ))
        
        # 插入2207接口配置
        self.db_manager.execute_update("""
            INSERT INTO medical_interface_config 
            (api_code, api_name, business_category, business_type, 
             required_params, his_integration_config, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            his_integration_config = VALUES(his_integration_config)
        """, (
            '2207', '门诊结算', '结算类', '门诊结算',
            '{"mdtrt_id": {"type": "string"}}',
            json.dumps(his_integration_config, ensure_ascii=False),
            True
        ))
        
        # 2. 插入机构配置
        self.db_manager.execute_update("""
            INSERT INTO medical_organization_config 
            (org_code, org_name, org_type, province_code, city_code, 
             app_id, app_secret, base_url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            org_name = VALUES(org_name)
        """, (
            'TEST001', '测试医院', 'hospital', '430000', '430100',
            'test_app_id', 'test_app_secret', 'http://test.api.com', True
        ))
        
        logger.info("测试数据设置完成")
    
    def test_patient_info_sync(self):
        """测试患者信息同步功能"""
        logger.info("=== 测试患者信息同步功能 ===")
        
        # 模拟1101接口返回的患者信息
        medical_data = {
            "infcode": 0,
            "output": {
                "baseinfo": {
                    "psn_no": "430123199001011234",
                    "psn_name": "张三",
                    "certno": "430123199001011234",
                    "gend": "1",
                    "brdy": "1990-01-01",
                    "tel": "13800138000"
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
        
        # 执行同步
        sync_result = self.his_manager.sync_medical_data(
            api_code='1101',
            medical_data=medical_data,
            org_code='TEST001',
            sync_direction='to_his'
        )
        
        # 验证结果
        if sync_result.success:
            logger.info(f"患者信息同步成功: 同步记录数={sync_result.synced_count}")
        else:
            logger.error(f"患者信息同步失败: {sync_result.error_message}")
        
        return sync_result.success
    
    def test_settlement_result_writeback(self):
        """测试医保结算结果回写"""
        logger.info("=== 测试医保结算结果回写 ===")
        
        # 模拟2207接口返回的结算结果
        medical_result = {
            "infcode": 0,
            "output": {
                "setlinfo": {
                    "setl_id": "SETL20240115001",
                    "setl_totlnum": 500.00,
                    "hifp_pay": 350.00,
                    "psn_pay": 150.00,
                    "setl_time": "2024-01-15 10:30:00"
                }
            }
        }
        
        # 执行回写
        writeback_result = self.his_manager.writeback_medical_result(
            api_code='2207',
            medical_result=medical_result,
            org_code='TEST001'
        )
        
        # 验证结果
        if writeback_result.success:
            logger.info(f"结算结果回写成功: 回写记录数={writeback_result.written_count}")
        else:
            logger.error(f"结算结果回写失败: {writeback_result.error_message}")
        
        return writeback_result.success
    
    def test_data_consistency_check(self):
        """测试数据一致性检查"""
        logger.info("=== 测试数据一致性检查 ===")
        
        # 执行一致性检查
        consistency_result = self.his_manager.check_data_consistency(
            api_code='1101',
            org_code='TEST001',
            check_period_hours=24
        )
        
        # 验证结果
        if consistency_result.get('success'):
            logger.info("数据一致性检查成功")
            logger.info(f"医保记录数: {consistency_result.get('total_medical_records', 0)}")
            logger.info(f"HIS记录数: {consistency_result.get('total_his_records', 0)}")
            logger.info(f"一致记录数: {consistency_result.get('consistent_count', 0)}")
            logger.info(f"不一致记录数: {consistency_result.get('inconsistent_count', 0)}")
        else:
            logger.error(f"数据一致性检查失败: {consistency_result.get('error')}")
        
        return consistency_result.get('success', False)
    
    def test_conflict_resolution(self):
        """测试冲突解决机制"""
        logger.info("=== 测试冲突解决机制 ===")
        
        # 模拟创建一个冲突记录
        conflict_id = "CONFLICT_TEST_001"
        
        # 插入测试冲突记录
        self.db_manager.execute_update("""
            INSERT INTO data_sync_conflicts 
            (conflict_id, table_name, primary_key, medical_data, his_data, 
             conflict_fields, resolved)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            resolved = VALUES(resolved)
        """, (
            conflict_id, 'his_patients', 'patient_id',
            '{"psn_name": "张三"}', '{"patient_name": "张三丰"}',
            '["patient_name"]', False
        ))
        
        # 解决冲突
        resolution_success = self.his_manager.resolve_data_conflict(
            conflict_id=conflict_id,
            resolution_strategy='use_medical',
            resolver_id='TEST_USER'
        )
        
        if resolution_success:
            logger.info("冲突解决成功")
        else:
            logger.error("冲突解决失败")
        
        return resolution_success
    
    def test_sync_statistics(self):
        """测试同步统计功能"""
        logger.info("=== 测试同步统计功能 ===")
        
        # 获取同步统计
        stats = self.his_manager.get_sync_statistics(
            api_code='1101',
            org_code='TEST001',
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        if stats:
            logger.info("同步统计获取成功")
            logger.info(f"统计期间: {stats.get('period', {})}")
            logger.info(f"同步统计: {len(stats.get('sync_statistics', []))} 条记录")
            logger.info(f"回写统计: {len(stats.get('writeback_statistics', []))} 条记录")
        else:
            logger.warning("同步统计为空")
        
        return bool(stats)
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始HIS集成管理器综合测试")
        
        try:
            # 设置测试数据
            self.setup_test_data()
            
            # 运行测试
            test_results = {
                'patient_sync': self.test_patient_info_sync(),
                'settlement_writeback': self.test_settlement_result_writeback(),
                'consistency_check': self.test_data_consistency_check(),
                'conflict_resolution': self.test_conflict_resolution(),
                'sync_statistics': self.test_sync_statistics()
            }
            
            # 输出测试结果
            logger.info("=== 测试结果汇总 ===")
            for test_name, result in test_results.items():
                status = "✓ 通过" if result else "✗ 失败"
                logger.info(f"{test_name}: {status}")
            
            # 计算通过率
            passed_count = sum(test_results.values())
            total_count = len(test_results)
            pass_rate = (passed_count / total_count) * 100
            
            logger.info(f"测试通过率: {passed_count}/{total_count} ({pass_rate:.1f}%)")
            
            if pass_rate == 100:
                logger.info("🎉 所有测试通过！HIS集成管理器功能正常")
            else:
                logger.warning("⚠️  部分测试失败，请检查相关功能")
            
            return pass_rate == 100
            
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            return False
        
        finally:
            # 清理资源
            self.cleanup()
    
    def cleanup(self):
        """清理测试资源"""
        try:
            self.his_manager.close()
            self.db_manager.close()
            logger.info("测试资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


def main():
    """主函数"""
    print("HIS集成管理器综合测试")
    print("=" * 50)
    
    tester = HISIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 测试完成：HIS集成管理器功能正常")
        return 0
    else:
        print("\n❌ 测试失败：请检查HIS集成管理器实现")
        return 1


if __name__ == "__main__":
    exit(main())