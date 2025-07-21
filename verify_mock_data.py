#!/usr/bin/env python3
"""
数据库模拟数据验证脚本

验证插入的模拟数据是否正确，并提供数据查看功能
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockDataVerifier:
    """模拟数据验证器"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.db_config = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USERNAME', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_DATABASE', 'medical_insurance'),
            charset=os.getenv('DB_CHARSET', 'utf8mb4')
        )
        
        self.db_manager = DatabaseManager(self.db_config)
        logger.info("数据库连接初始化完成")
    
    def verify_interface_configs(self):
        """验证接口配置数据"""
        logger.info("=== 验证接口配置数据 ===")
        
        configs = self.db_manager.execute_query("""
            SELECT api_code, api_name, business_category, business_type, 
                   JSON_LENGTH(his_integration_config) as his_config_size
            FROM medical_interface_config 
            ORDER BY api_code
        """)
        
        logger.info(f"接口配置总数: {len(configs)}")
        for config in configs:
            logger.info(f"  {config['api_code']}: {config['api_name']} "
                       f"({config['business_category']}/{config['business_type']}) "
                       f"HIS配置大小: {config['his_config_size']}")
        
        return len(configs) > 0
    
    def verify_organization_configs(self):
        """验证机构配置数据"""
        logger.info("=== 验证机构配置数据 ===")
        
        orgs = self.db_manager.execute_query("""
            SELECT org_code, org_name, province_code, city_code, is_active
            FROM medical_organization_config 
            ORDER BY org_code
        """)
        
        logger.info(f"机构配置总数: {len(orgs)}")
        for org in orgs:
            status = "✓" if org['is_active'] else "✗"
            logger.info(f"  {status} {org['org_code']}: {org['org_name']} "
                       f"({org['province_code']}/{org['city_code']})")
        
        return len(orgs) > 0
    
    def verify_business_logs(self):
        """验证业务操作日志数据"""
        logger.info("=== 验证业务操作日志数据 ===")
        
        # 总体统计
        total_logs = self.db_manager.execute_query_one("""
            SELECT COUNT(*) as total FROM business_operation_logs
        """)
        logger.info(f"业务日志总数: {total_logs['total']}")
        
        # 按接口统计
        api_stats = self.db_manager.execute_query("""
            SELECT api_code, api_name, COUNT(*) as count,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                   AVG(response_time_ms) as avg_response_time
            FROM business_operation_logs 
            GROUP BY api_code, api_name
            ORDER BY count DESC
        """)
        
        logger.info("按接口统计:")
        for stat in api_stats:
            success_rate = (stat['success_count'] / stat['count']) * 100
            avg_time = stat['avg_response_time'] or 0
            logger.info(f"  {stat['api_code']}: {stat['count']} 次调用, "
                       f"成功率 {success_rate:.1f}%, "
                       f"平均响应时间 {avg_time:.0f}ms")
        
        # 按机构统计
        org_stats = self.db_manager.execute_query("""
            SELECT institution_code, COUNT(*) as count
            FROM business_operation_logs 
            GROUP BY institution_code
            ORDER BY count DESC
        """)
        
        logger.info("按机构统计:")
        for stat in org_stats:
            logger.info(f"  {stat['institution_code']}: {stat['count']} 次调用")
        
        return total_logs['total'] > 0
    
    def verify_his_sync_logs(self):
        """验证HIS同步日志数据"""
        logger.info("=== 验证HIS同步日志数据 ===")
        
        # 总体统计
        total_syncs = self.db_manager.execute_query_one("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN sync_status = 'success' THEN 1 ELSE 0 END) as success_count,
                   SUM(synced_records) as total_synced,
                   SUM(failed_records) as total_failed
            FROM his_data_sync_log
        """)
        
        success_rate = (total_syncs['success_count'] / total_syncs['total']) * 100 if total_syncs['total'] > 0 else 0
        
        logger.info(f"HIS同步日志总数: {total_syncs['total']}")
        logger.info(f"同步成功率: {success_rate:.1f}%")
        logger.info(f"总同步记录数: {total_syncs['total_synced']}")
        logger.info(f"总失败记录数: {total_syncs['total_failed']}")
        
        # 按接口统计
        api_stats = self.db_manager.execute_query("""
            SELECT api_code, COUNT(*) as count,
                   SUM(CASE WHEN sync_status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM his_data_sync_log 
            GROUP BY api_code
            ORDER BY count DESC
        """)
        
        logger.info("按接口统计:")
        for stat in api_stats:
            success_rate = (stat['success_count'] / stat['count']) * 100
            logger.info(f"  {stat['api_code']}: {stat['count']} 次同步, 成功率 {success_rate:.1f}%")
        
        return total_syncs['total'] > 0
    
    def verify_his_writeback_logs(self):
        """验证HIS回写日志数据"""
        logger.info("=== 验证HIS回写日志数据 ===")
        
        # 总体统计
        total_writebacks = self.db_manager.execute_query_one("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN writeback_status = 'success' THEN 1 ELSE 0 END) as success_count,
                   SUM(written_records) as total_written,
                   SUM(failed_records) as total_failed
            FROM his_writeback_log
        """)
        
        success_rate = (total_writebacks['success_count'] / total_writebacks['total']) * 100 if total_writebacks['total'] > 0 else 0
        
        logger.info(f"HIS回写日志总数: {total_writebacks['total']}")
        logger.info(f"回写成功率: {success_rate:.1f}%")
        logger.info(f"总回写记录数: {total_writebacks['total_written']}")
        logger.info(f"总失败记录数: {total_writebacks['total_failed']}")
        
        return total_writebacks['total'] > 0
    
    def verify_consistency_checks(self):
        """验证数据一致性检查数据"""
        logger.info("=== 验证数据一致性检查数据 ===")
        
        # 总体统计
        total_checks = self.db_manager.execute_query_one("""
            SELECT COUNT(*) as total,
                   SUM(total_records) as total_records,
                   SUM(consistent_count) as total_consistent,
                   SUM(inconsistent_count) as total_inconsistent
            FROM data_consistency_checks
        """)
        
        logger.info(f"一致性检查总数: {total_checks['total']}")
        logger.info(f"检查记录总数: {total_checks['total_records']}")
        logger.info(f"一致记录总数: {total_checks['total_consistent']}")
        logger.info(f"不一致记录总数: {total_checks['total_inconsistent']}")
        
        # 按表统计
        table_stats = self.db_manager.execute_query("""
            SELECT table_name, COUNT(*) as check_count,
                   AVG(consistent_count) as avg_consistent,
                   AVG(inconsistent_count) as avg_inconsistent
            FROM data_consistency_checks 
            GROUP BY table_name
            ORDER BY check_count DESC
        """)
        
        logger.info("按表统计:")
        for stat in table_stats:
            avg_consistent = stat['avg_consistent'] or 0
            avg_inconsistent = stat['avg_inconsistent'] or 0
            logger.info(f"  {stat['table_name']}: {stat['check_count']} 次检查, "
                       f"平均一致 {avg_consistent:.1f}, "
                       f"平均不一致 {avg_inconsistent:.1f}")
        
        return total_checks['total'] > 0
    
    def verify_sync_conflicts(self):
        """验证数据同步冲突数据"""
        logger.info("=== 验证数据同步冲突数据 ===")
        
        # 总体统计
        total_conflicts = self.db_manager.execute_query_one("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved_count
            FROM data_sync_conflicts
        """)
        
        resolved_rate = (total_conflicts['resolved_count'] / total_conflicts['total']) * 100 if total_conflicts['total'] > 0 else 0
        
        logger.info(f"同步冲突总数: {total_conflicts['total']}")
        logger.info(f"已解决冲突数: {total_conflicts['resolved_count']}")
        logger.info(f"解决率: {resolved_rate:.1f}%")
        
        # 按表统计
        table_stats = self.db_manager.execute_query("""
            SELECT table_name, COUNT(*) as count,
                   SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved_count
            FROM data_sync_conflicts 
            GROUP BY table_name
            ORDER BY count DESC
        """)
        
        logger.info("按表统计:")
        for stat in table_stats:
            resolved_rate = (stat['resolved_count'] / stat['count']) * 100
            logger.info(f"  {stat['table_name']}: {stat['count']} 个冲突, 解决率 {resolved_rate:.1f}%")
        
        return total_conflicts['total'] > 0
    
    def verify_interface_stats(self):
        """验证接口统计数据"""
        logger.info("=== 验证接口统计数据 ===")
        
        # 总体统计
        total_stats = self.db_manager.execute_query_one("""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT api_code) as unique_apis,
                   COUNT(DISTINCT institution_code) as unique_orgs,
                   SUM(total_calls) as total_calls,
                   AVG(success_rate) as avg_success_rate
            FROM medical_interface_stats
        """)
        
        logger.info(f"统计记录总数: {total_stats['total_records']}")
        logger.info(f"涉及接口数: {total_stats['unique_apis']}")
        logger.info(f"涉及机构数: {total_stats['unique_orgs']}")
        logger.info(f"总调用次数: {total_stats['total_calls']}")
        avg_success_rate = total_stats['avg_success_rate'] or 0
        logger.info(f"平均成功率: {avg_success_rate:.1f}%")
        
        # 最近7天的统计
        recent_stats = self.db_manager.execute_query("""
            SELECT api_code, SUM(total_calls) as total_calls,
                   AVG(success_rate) as avg_success_rate,
                   AVG(avg_response_time) as avg_response_time
            FROM medical_interface_stats 
            WHERE stat_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY api_code
            ORDER BY total_calls DESC
        """)
        
        logger.info("最近7天接口统计:")
        for stat in recent_stats:
            avg_success = stat['avg_success_rate'] or 0
            avg_time = stat['avg_response_time'] or 0
            logger.info(f"  {stat['api_code']}: {stat['total_calls']} 次调用, "
                       f"成功率 {avg_success:.1f}%, "
                       f"平均响应时间 {avg_time:.0f}ms")
        
        return total_stats['total_records'] > 0
    
    def show_sample_data(self):
        """显示样本数据"""
        logger.info("=== 样本数据展示 ===")
        
        # 显示最近的业务操作日志
        recent_logs = self.db_manager.execute_query("""
            SELECT operation_id, api_code, api_name, institution_code, 
                   status, operation_time, response_time_ms
            FROM business_operation_logs 
            ORDER BY operation_time DESC 
            LIMIT 5
        """)
        
        logger.info("最近5条业务操作日志:")
        for log in recent_logs:
            logger.info(f"  {log['operation_time']} | {log['api_code']} | "
                       f"{log['institution_code']} | {log['status']} | "
                       f"{log['response_time_ms']}ms")
        
        # 显示最近的HIS同步日志
        recent_syncs = self.db_manager.execute_query("""
            SELECT sync_id, api_code, org_code, sync_status, 
                   synced_records, sync_time
            FROM his_data_sync_log 
            ORDER BY sync_time DESC 
            LIMIT 3
        """)
        
        logger.info("最近3条HIS同步日志:")
        for sync in recent_syncs:
            logger.info(f"  {sync['sync_time']} | {sync['api_code']} | "
                       f"{sync['org_code']} | {sync['sync_status']} | "
                       f"同步{sync['synced_records']}条")
    
    def run_all_verifications(self):
        """运行所有验证"""
        logger.info("开始验证模拟数据...")
        
        try:
            # 运行所有验证
            verification_results = {
                'interface_configs': self.verify_interface_configs(),
                'organization_configs': self.verify_organization_configs(),
                'business_logs': self.verify_business_logs(),
                'his_sync_logs': self.verify_his_sync_logs(),
                'his_writeback_logs': self.verify_his_writeback_logs(),
                'consistency_checks': self.verify_consistency_checks(),
                'sync_conflicts': self.verify_sync_conflicts(),
                'interface_stats': self.verify_interface_stats()
            }
            
            # 显示样本数据
            self.show_sample_data()
            
            # 输出验证结果
            logger.info("=== 验证结果汇总 ===")
            passed_count = 0
            for test_name, result in verification_results.items():
                status = "✓ 通过" if result else "✗ 失败"
                logger.info(f"{test_name}: {status}")
                if result:
                    passed_count += 1
            
            total_count = len(verification_results)
            pass_rate = (passed_count / total_count) * 100
            
            logger.info(f"验证通过率: {passed_count}/{total_count} ({pass_rate:.1f}%)")
            
            if pass_rate == 100:
                logger.info("🎉 所有数据验证通过！模拟数据已准备就绪")
            else:
                logger.warning("⚠️  部分数据验证失败，请检查数据插入")
            
            return pass_rate == 100
            
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        try:
            self.db_manager.close()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


def main():
    """主函数"""
    print("医保接口SDK数据库模拟数据验证工具")
    print("=" * 50)
    
    verifier = MockDataVerifier()
    success = verifier.run_all_verifications()
    
    if success:
        print("\n✅ 数据验证完成：所有模拟数据正常")
        print("现在可以使用这些数据进行HIS集成管理器的测试了！")
        return 0
    else:
        print("\n❌ 数据验证失败：请检查模拟数据")
        return 1


if __name__ == "__main__":
    exit(main())