#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK综合使用指南

本指南提供了医保接口SDK的综合使用方法，包括：
- 快速入门指南
- 常用功能示例
- 高级特性使用
- 故障排除指南
- 性能优化建议
- 最佳实践总结

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加SDK路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk import MedicalInsuranceClient, DataHelper
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    NetworkException, 
    BusinessException
)


class ComprehensiveUsageGuide:
    """医保接口SDK综合使用指南"""
    
    def __init__(self):
        """初始化指南"""
        self.client = None
        self.org_code = "H43010000001"
    
    def print_section(self, title: str, level: int = 1):
        """打印章节标题"""
        if level == 1:
            print("\n" + "="*80)
            print(f" {title} ")
            print("="*80)
        elif level == 2:
            print("\n" + "-"*60)
            print(f" {title} ")
            print("-"*60)
        else:
            print(f"\n📌 {title}")
    
    def section_01_quick_start(self):
        """第1章: 快速入门"""
        self.print_section("第1章: 快速入门指南", 1)
        
        print("""
医保接口SDK是一个通用的医保接口调用工具，支持174个医保接口的统一调用。
本章将帮助您快速上手使用SDK。
        """)
        
        self.print_section("1.1 安装和初始化", 2)
        
        print("""
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入数据库和Redis配置

# 3. 初始化数据库
python scripts/initialize_config_data.py

# 4. 验证安装
python -c "from medical_insurance_sdk import MedicalInsuranceClient; print('安装成功')"
        """)
        
        self.print_section("1.2 第一个示例", 2)
        
        print("让我们从一个简单的人员信息查询开始：")
        
        try:
            # 初始化客户端
            self.client = MedicalInsuranceClient()
            print("✓ SDK客户端初始化成功")
            
            # 准备查询数据
            query_data = {
                "mdtrt_cert_type": "02",  # 身份证
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
            
            print("\n查询参数:")
            for key, value in query_data.items():
                print(f"  {key}: {value}")
            
            # 调用接口
            print("\n正在调用1101接口...")
            result = self.client.call_interface(
                api_code="1101",
                input_data=query_data,
                org_code=self.org_code
            )
            
            # 处理结果
            if result.get('success'):
                person_info = result.get('data', {})
                print("✓ 查询成功!")
                print(f"  姓名: {person_info.get('person_name', 'N/A')}")
                print(f"  性别: {person_info.get('gender', 'N/A')}")
                print(f"  年龄: {person_info.get('age', 'N/A')}")
            else:
                print(f"✗ 查询失败: {result.get('error_message', '未知错误')}")
                
        except Exception as e:
            print(f"✗ 示例执行失败: {str(e)}")
            print("请检查配置和网络连接")
    
    def section_02_common_functions(self):
        """第2章: 常用功能"""
        self.print_section("第2章: 常用功能示例", 1)
        
        self.print_section("2.1 人员信息查询 (1101)", 2)
        self._demo_person_query()
        
        self.print_section("2.2 门诊结算 (2201)", 2)
        self._demo_outpatient_settlement()
        
        self.print_section("2.3 药品目录查询 (1301)", 2)
        self._demo_drug_catalog_query()
        
        self.print_section("2.4 机构信息查询 (1201)", 2)
        self._demo_institution_query()
    
    def _demo_person_query(self):
        """演示人员信息查询"""
        print("""
人员信息查询是最常用的功能之一，用于获取参保人员的基本信息和参保状态。

使用场景:
- 患者挂号时验证医保身份
- 查询参保状态和余额
- 获取人员基本信息
        """)
        
        # 示例代码
        example_code = '''
# 人员信息查询示例
query_data = {
    "mdtrt_cert_type": "02",    # 就诊凭证类型: 02-身份证
    "mdtrt_cert_no": "身份证号",  # 就诊凭证编号
    "psn_cert_type": "01",      # 人员证件类型: 01-身份证
    "certno": "身份证号",        # 证件号码
    "psn_name": "姓名"          # 人员姓名
}

result = client.call_interface(
    api_code="1101",
    input_data=query_data,
    org_code="机构编码"
)

if result.get('success'):
    person_info = result.get('data', {})
    # 使用DataHelper提取信息
    basic_info = DataHelper.extract_person_basic_info(person_info)
    insurance_info = DataHelper.extract_insurance_info(person_info)
    total_balance = DataHelper.calculate_total_balance(insurance_info)
        '''
        
        print("示例代码:")
        print(example_code)
        
        print("\n返回数据结构:")
        print("""
{
    "success": true,
    "data": {
        "person_name": "张三",
        "person_id": "43012319900101123456789012",
        "id_card": "430123199001011234",
        "gender": "1",
        "birth_date": "1990-01-01",
        "age": 34,
        "insurance_info": [
            {
                "type": "310",
                "balance": 1500.00,
                "status": "1"
            }
        ]
    }
}
        """)
    
    def _demo_outpatient_settlement(self):
        """演示门诊结算"""
        print("""
门诊结算用于处理门诊费用的医保结算，是核心业务功能。

使用场景:
- 门诊费用结算
- 计算医保支付金额
- 生成结算单据
        """)
        
        example_code = '''
# 门诊结算示例
settlement_data = {
    "mdtrt_id": "就医登记号",      # 就医登记号
    "psn_no": "人员编号",         # 人员编号
    "chrg_bchno": "收费批次号",    # 收费批次号
    "acct_used_flag": "1",       # 个人账户使用标志: 0-不使用, 1-使用
    "insutype": "310",           # 险种类型: 310-职工基本医疗保险
    "invono": "发票号"           # 发票号
}

result = client.call_interface(
    api_code="2201",
    input_data=settlement_data,
    org_code="机构编码"
)

if result.get('success'):
    settlement_info = result.get('data', {})
    # 使用DataHelper格式化结算摘要
    summary = DataHelper.format_settlement_summary(settlement_info)
        '''
        
        print("示例代码:")
        print(example_code)
    
    def _demo_drug_catalog_query(self):
        """演示药品目录查询"""
        print("""
药品目录查询用于获取医保药品目录信息，支持处方开具和费用计算。

使用场景:
- 查询药品医保编码
- 验证药品是否在医保目录内
- 获取药品价格信息
        """)
        
        print("注意: 1301接口通常用于批量下载药品目录，实际使用中可能需要分页处理。")
    
    def _demo_institution_query(self):
        """演示机构信息查询"""
        print("""
机构信息查询用于获取定点医药机构的详细信息。

使用场景:
- 查询机构基本信息
- 验证机构资质
- 获取机构联系方式
        """)
    
    def section_03_advanced_features(self):
        """第3章: 高级特性"""
        self.print_section("第3章: 高级特性使用", 1)
        
        self.print_section("3.1 批量处理", 2)
        self._demo_batch_processing()
        
        self.print_section("3.2 异步处理", 2)
        self._demo_async_processing()
        
        self.print_section("3.3 缓存机制", 2)
        self._demo_cache_mechanism()
        
        self.print_section("3.4 错误处理", 2)
        self._demo_error_handling()
    
    def _demo_batch_processing(self):
        """演示批量处理"""
        print("""
批量处理可以提高大量数据处理的效率，减少网络开销。

适用场景:
- 批量查询患者信息
- 批量上传费用明细
- 批量处理结算数据
        """)
        
        example_code = '''
# 批量处理示例
patient_list = [
    {"certno": "430123199001011234", "psn_name": "张三"},
    {"certno": "430123199002021234", "psn_name": "李四"},
    {"certno": "430123199003031234", "psn_name": "王五"}
]

results = []
for patient in patient_list:
    query_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": patient["certno"],
        "psn_cert_type": "01",
        "certno": patient["certno"],
        "psn_name": patient["psn_name"]
    }
    
    result = client.call_interface(
        api_code="1101",
        input_data=query_data,
        org_code=org_code
    )
    
    results.append({
        "patient": patient,
        "result": result,
        "success": result.get('success', False)
    })

# 统计结果
success_count = sum(1 for r in results if r['success'])
print(f"批量处理完成: 成功 {success_count}/{len(patient_list)}")
        '''
        
        print("示例代码:")
        print(example_code)
    
    def _demo_async_processing(self):
        """演示异步处理"""
        print("""
异步处理适用于耗时较长的操作，可以避免阻塞主线程。

适用场景:
- 大文件上传
- 复杂数据处理
- 长时间运行的任务
        """)
        
        example_code = '''
# 异步处理示例
import asyncio

async def async_query_example():
    # 提交异步任务
    task_id = client.call_interface_async(
        api_code="1101",
        input_data=query_data,
        org_code=org_code
    )
    
    print(f"异步任务已提交: {task_id}")
    
    # 轮询任务状态
    while True:
        status = client.get_task_status(task_id)
        
        if status.get('status') == 'completed':
            result = status.get('result', {})
            print("异步任务完成!")
            return result
        elif status.get('status') == 'failed':
            print(f"异步任务失败: {status.get('error')}")
            return None
        
        await asyncio.sleep(2)  # 等待2秒后再次检查

# 运行异步任务
result = asyncio.run(async_query_example())
        '''
        
        print("示例代码:")
        print(example_code)
    
    def _demo_cache_mechanism(self):
        """演示缓存机制"""
        print("""
SDK内置了智能缓存机制，可以提高频繁查询的性能。

缓存策略:
- 接口配置缓存 (TTL: 1小时)
- 机构配置缓存 (TTL: 2小时)
- 查询结果缓存 (TTL: 5分钟)
        """)
        
        example_code = '''
# 缓存使用示例

# 获取缓存统计
cache_stats = client.get_cache_statistics()
print(f"缓存命中率: {cache_stats.get('hit_rate', 0):.2%}")
print(f"缓存大小: {cache_stats.get('cache_size', 0)} 项")

# 清理缓存
client.clear_cache()  # 清理所有缓存
client.clear_cache('interface_config')  # 清理特定类型缓存

# 预加载热点数据
hot_interfaces = ["1101", "2201", "1301"]
for api_code in hot_interfaces:
    config = client.get_interface_config(api_code)
    print(f"预加载接口配置: {api_code}")
        '''
        
        print("示例代码:")
        print(example_code)
    
    def _demo_error_handling(self):
        """演示错误处理"""
        print("""
完善的错误处理是生产环境的必要条件。SDK提供了多层次的异常处理机制。

异常类型:
- ValidationException: 数据验证错误
- NetworkException: 网络连接错误
- BusinessException: 业务逻辑错误
        """)
        
        example_code = '''
# 错误处理示例
try:
    result = client.call_interface(
        api_code="1101",
        input_data=query_data,
        org_code=org_code
    )
    
except ValidationException as e:
    print(f"数据验证失败: {e.message}")
    # 显示具体的验证错误
    for field, errors in e.details.get('errors', {}).items():
        print(f"  {field}: {', '.join(errors)}")
    
except NetworkException as e:
    print(f"网络请求失败: {e.message}")
    # 可以实现重试机制
    
except BusinessException as e:
    print(f"业务处理失败: {e.message}")
    print(f"错误代码: {e.error_code}")
    
except Exception as e:
    print(f"系统错误: {str(e)}")
    # 记录详细日志，通知管理员
        '''
        
        print("示例代码:")
        print(example_code)
    
    def section_04_troubleshooting(self):
        """第4章: 故障排除"""
        self.print_section("第4章: 故障排除指南", 1)
        
        self.print_section("4.1 常见问题", 2)
        
        problems = [
            {
                "问题": "数据库连接失败",
                "原因": ["数据库服务未启动", "连接参数错误", "网络不通"],
                "解决方案": [
                    "检查数据库服务状态",
                    "验证连接参数",
                    "测试网络连通性",
                    "检查防火墙设置"
                ]
            },
            {
                "问题": "接口调用超时",
                "原因": ["网络延迟", "服务器负载高", "超时设置过短"],
                "解决方案": [
                    "增加超时时间",
                    "检查网络状况",
                    "优化查询参数",
                    "使用异步调用"
                ]
            },
            {
                "问题": "数据验证失败",
                "原因": ["参数格式错误", "必填参数缺失", "参数值不合法"],
                "解决方案": [
                    "检查参数格式",
                    "补充必填参数",
                    "验证参数值范围",
                    "查看接口文档"
                ]
            }
        ]
        
        for problem in problems:
            print(f"\n🔍 {problem['问题']}")
            print("可能原因:")
            for reason in problem['原因']:
                print(f"  • {reason}")
            print("解决方案:")
            for solution in problem['解决方案']:
                print(f"  ✓ {solution}")
        
        self.print_section("4.2 诊断工具", 2)
        
        print("""
SDK提供了多种诊断工具帮助排查问题:

1. 系统状态检查
   client.get_system_status()

2. 连接池状态
   client.get_connection_pool_stats()

3. 缓存统计
   client.get_cache_statistics()

4. 调用统计
   client.get_call_statistics()

5. 日志查看
   tail -f logs/medical_insurance_sdk.log
        """)
        
        self.print_section("4.3 性能监控", 2)
        
        print("""
建议监控以下指标:

• 响应时间: 平均 < 3秒，95% < 5秒
• 成功率: > 99%
• 并发数: 根据业务需求设定
• 内存使用: < 512MB
• CPU使用: < 80%
• 数据库连接: 使用率 < 80%
        """)
    
    def section_05_performance_optimization(self):
        """第5章: 性能优化"""
        self.print_section("第5章: 性能优化建议", 1)
        
        self.print_section("5.1 数据库优化", 2)
        
        print("""
数据库是性能的关键因素，以下是优化建议:

连接池配置:
• 初始连接数: 5-10
• 最大连接数: 20-50
• 连接超时: 30秒
• 空闲超时: 300秒

索引优化:
• 为常用查询字段创建索引
• 定期分析查询性能
• 避免过多索引影响写入性能

分区策略:
• 按时间分区存储日志数据
• 定期清理历史数据
• 使用分区表提高查询性能
        """)
        
        self.print_section("5.2 缓存优化", 2)
        
        print("""
合理使用缓存可以显著提高性能:

缓存策略:
• 接口配置: 长期缓存 (1-2小时)
• 机构配置: 中期缓存 (30分钟-1小时)
• 查询结果: 短期缓存 (5-15分钟)

Redis配置:
• 内存大小: 根据数据量设定
• 持久化: 启用RDB和AOF
• 淘汰策略: allkeys-lru
• 连接池: 最大连接数50-100
        """)
        
        self.print_section("5.3 应用优化", 2)
        
        print("""
应用层面的优化建议:

并发处理:
• 使用连接池管理数据库连接
• 合理设置线程池大小
• 避免长时间占用连接

批量操作:
• 批量查询减少网络开销
• 批量插入提高写入性能
• 合理设置批次大小

异步处理:
• 耗时操作使用异步处理
• 避免阻塞主线程
• 合理设置任务队列大小
        """)
    
    def section_06_best_practices(self):
        """第6章: 最佳实践"""
        self.print_section("第6章: 最佳实践总结", 1)
        
        self.print_section("6.1 开发最佳实践", 2)
        
        practices = [
            "始终进行数据验证，不信任外部输入",
            "使用配置文件管理环境差异",
            "实现完善的错误处理和日志记录",
            "编写单元测试和集成测试",
            "使用版本控制管理代码变更",
            "定期更新依赖包和安全补丁",
            "遵循代码规范和最佳实践",
            "进行代码审查和质量检查"
        ]
        
        for i, practice in enumerate(practices, 1):
            print(f"{i}. {practice}")
        
        self.print_section("6.2 部署最佳实践", 2)
        
        deployment_practices = [
            "使用容器化部署提高可移植性",
            "配置健康检查和自动重启",
            "实施蓝绿部署或滚动更新",
            "配置负载均衡和故障转移",
            "建立完善的监控和告警机制",
            "定期备份数据和配置",
            "制定应急响应和恢复计划",
            "进行定期的安全审计"
        ]
        
        for i, practice in enumerate(deployment_practices, 1):
            print(f"{i}. {practice}")
        
        self.print_section("6.3 运维最佳实践", 2)
        
        operation_practices = [
            "建立标准化的运维流程",
            "定期检查系统性能指标",
            "及时处理告警和异常",
            "保持文档的及时更新",
            "定期进行系统维护",
            "建立知识库和FAQ",
            "培训相关技术人员",
            "持续改进和优化"
        ]
        
        for i, practice in enumerate(operation_practices, 1):
            print(f"{i}. {practice}")
    
    def section_07_summary(self):
        """第7章: 总结"""
        self.print_section("第7章: 总结", 1)
        
        print("""
🎉 恭喜您完成了医保接口SDK综合使用指南的学习！

通过本指南，您应该已经掌握了:

✅ SDK的基本使用方法
✅ 常用功能的实现方式
✅ 高级特性的使用技巧
✅ 故障排除的方法
✅ 性能优化的策略
✅ 开发和部署的最佳实践

📚 进一步学习资源:
• API文档: docs/api-documentation.md
• 配置指南: docs/configuration-guide.md
• 故障排除: docs/troubleshooting-guide.md
• 示例代码: examples/
• 测试用例: tests/

🔗 获取帮助:
• GitHub Issues: 报告问题和建议
• 技术文档: 查看详细文档
• 示例代码: 参考实际使用案例

💡 持续改进:
SDK会持续更新和改进，请关注版本更新和新功能发布。
您的反馈和建议对我们非常重要！

祝您使用愉快！ 🚀
        """)
    
    def run_comprehensive_guide(self):
        """运行综合使用指南"""
        print("医保接口SDK综合使用指南")
        print("="*80)
        print("本指南将全面介绍医保接口SDK的使用方法和最佳实践。")
        
        # 运行所有章节
        self.section_01_quick_start()
        self.section_02_common_functions()
        self.section_03_advanced_features()
        self.section_04_troubleshooting()
        self.section_05_performance_optimization()
        self.section_06_best_practices()
        self.section_07_summary()


def main():
    """主函数"""
    guide = ComprehensiveUsageGuide()
    guide.run_comprehensive_guide()


if __name__ == "__main__":
    main()