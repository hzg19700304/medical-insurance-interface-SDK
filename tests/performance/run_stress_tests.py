#!/usr/bin/env python3
"""
医保SDK压力测试执行脚本
快速执行压力测试并生成报告
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_insurance_sdk.client import MedicalInsuranceClient
from medical_insurance_sdk.core.database import DatabaseConfig
from medical_insurance_sdk.config.models import SDKConfig
from tests.test_performance_stress import StressTestSuite, StressTestRunner


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'stress_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def run_quick_stress_test():
    """运行快速压力测试"""
    print("开始执行快速压力测试...")
    
    try:
        # 创建客户端
        db_config = DatabaseConfig.from_env()
        sdk_config = SDKConfig(database_config=db_config)
        client = MedicalInsuranceClient(sdk_config)
        
        runner = StressTestRunner(client)
        
        print("\n1. 测试并发接口调用 (1101接口)...")
        result_1101 = runner.run_concurrent_interface_test(
            api_code='1101',
            concurrent_users=5,
            requests_per_user=2,
            ramp_up_time=1
        )
        print(f"   结果: {result_1101.successful_requests}/{result_1101.total_requests} 成功, "
              f"平均响应时间: {result_1101.average_response_time:.3f}s, "
              f"RPS: {result_1101.requests_per_second:.1f}")
        
        print("\n2. 测试数据库连接池性能...")
        db_result = runner.run_database_connection_pool_test(
            concurrent_connections=10,
            operations_per_connection=5,
            test_duration=10
        )
        print(f"   结果: {db_result.successful_requests}/{db_result.total_requests} 成功, "
              f"平均响应时间: {db_result.average_response_time:.3f}s, "
              f"RPS: {db_result.requests_per_second:.1f}")
        
        print("\n3. 测试缓存系统效果...")
        cache_result = runner.run_cache_system_test(
            concurrent_operations=10,
            operations_per_worker=20,
            cache_hit_ratio=0.6
        )
        print(f"   结果: {cache_result.successful_requests}/{cache_result.total_requests} 成功, "
              f"平均响应时间: {cache_result.average_response_time:.3f}s, "
              f"RPS: {cache_result.requests_per_second:.1f}")
        
        # 计算总体结果
        total_requests = result_1101.total_requests + db_result.total_requests + cache_result.total_requests
        total_successful = result_1101.successful_requests + db_result.successful_requests + cache_result.successful_requests
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n=== 快速压力测试总结 ===")
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {total_successful}")
        print(f"成功率: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 80:
            print("✅ 压力测试通过！系统性能良好")
            return True
        else:
            print("❌ 压力测试未通过，系统性能需要优化")
            return False
            
    except Exception as e:
        print(f"❌ 压力测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_full_stress_test():
    """运行完整压力测试"""
    print("开始执行完整压力测试套件...")
    
    try:
        # 创建客户端
        db_config = DatabaseConfig.from_env()
        sdk_config = SDKConfig(database_config=db_config)
        client = MedicalInsuranceClient(sdk_config)
        
        # 运行完整测试套件
        suite = StressTestSuite()
        report = suite.run_all_tests(client)
        
        # 保存测试报告
        report_filename = f'stress_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 完整压力测试报告 ===")
        print(f"测试时间: {report['test_summary']['test_time']}")
        print(f"测试总数: {report['test_summary']['total_tests']}")
        print(f"整体状态: {report['test_summary']['overall_status']}")
        print(f"总请求数: {report['performance_analysis']['total_requests']}")
        print(f"成功请求: {report['performance_analysis']['total_successful']}")
        print(f"失败请求: {report['performance_analysis']['total_failed']}")
        print(f"整体错误率: {report['performance_analysis']['overall_error_rate']:.2f}%")
        print(f"平均RPS: {report['performance_analysis']['average_rps']:.2f}")
        
        print(f"\n=== 详细测试结果 ===")
        for result in report['test_results']:
            print(f"测试: {result['test_name']}")
            print(f"  请求数: {result['total_requests']}")
            print(f"  成功率: {100 - result['error_rate']:.1f}%")
            print(f"  平均响应时间: {result['average_response_time']:.3f}s")
            print(f"  RPS: {result['requests_per_second']:.1f}")
            print(f"  P95响应时间: {result['p95_response_time']:.3f}s")
            print()
        
        print(f"=== 优化建议 ===")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        print(f"\n详细报告已保存到: {report_filename}")
        
        return report['test_summary']['overall_status'] == 'PASSED'
        
    except Exception as e:
        print(f"❌ 完整压力测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    setup_logging()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        success = run_full_stress_test()
    else:
        success = run_quick_stress_test()
    
    if success:
        print("\n🎉 压力测试完成！")
        sys.exit(0)
    else:
        print("\n💥 压力测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()