#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK完整使用示例

本示例提供了医保接口SDK的完整使用指南，包括：
- 基础使用方法
- 高级功能使用
- 实际业务场景
- 错误处理策略
- 性能优化技巧
- 最佳实践建议

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加SDK路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk import MedicalInsuranceClient, DataHelper
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    NetworkException, 
    BusinessException,
    ConfigurationException
)


class MedicalInsuranceSDKExamples:
    """医保接口SDK完整使用示例"""
    
    def __init__(self):
        """初始化示例类"""
        self.setup_logging()
        self.client = self.setup_client()
        self.org_code = "H43010000001"  # 默认机构编码
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('examples/sdk_examples.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_client(self) -> MedicalInsuranceClient:
        """设置SDK客户端"""
        try:
            # 方式1: 从配置文件初始化
            if os.path.exists('config/development.json'):
                client = MedicalInsuranceClient.from_config_file('config/development.json')
                self.logger.info("从配置文件初始化SDK客户端成功")
            else:
                # 方式2: 直接配置初始化
                client = MedicalInsuranceClient(
                    database_url="mysql://user:password@localhost:3306/medical_insurance",
                    redis_url="redis://localhost:6379/0",
                    log_level="INFO"
                )
                self.logger.info("直接配置初始化SDK客户端成功")
            
            return client
            
        except Exception as e:
            self.logger.error(f"初始化SDK客户端失败: {str(e)}")
            raise

    # ==================== 基础使用示例 ====================
    
    def example_basic_person_query(self):
        """基础示例: 人员信息查询"""
        print("\n" + "="*60)
        print("基础示例: 人员信息查询 (1101接口)")
        print("="*60)
        
        try:
            # 准备查询参数
            query_data = {
                "mdtrt_cert_type": "02",  # 身份证
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",    # 身份证
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
            
            self.logger.info(f"开始查询人员信息: {query_data['psn_name']}")
            
            # 调用接口
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
                print(f"  人员编号: {person_info.get('person_id', 'N/A')}")
                print(f"  身份证号: {person_info.get('id_card', 'N/A')}")
                print(f"  性别: {person_info.get('gender', 'N/A')}")
                print(f"  出生日期: {person_info.get('birth_date', 'N/A')}")
                print(f"  年龄: {person_info.get('age', 'N/A')}")
                
                # 使用DataHelper提取信息
                basic_info = DataHelper.extract_person_basic_info(person_info)
                insurance_info = DataHelper.extract_insurance_info(person_info)
                total_balance = DataHelper.calculate_total_balance(insurance_info)
                
                print(f"\n参保信息:")
                print(f"  参保险种数: {len(insurance_info)}")
                print(f"  总余额: ¥{total_balance}")
                
                for idx, insurance in enumerate(insurance_info, 1):
                    print(f"  {idx}. 险种: {insurance.get('type', 'N/A')}")
                    print(f"     余额: ¥{insurance.get('balance', 0)}")
                    print(f"     状态: {insurance.get('status', 'N/A')}")
                
                self.logger.info(f"人员信息查询成功: {person_info.get('person_name')}")
                return person_info
                
            else:
                error_msg = result.get('error_message', '未知错误')
                print(f"✗ 查询失败: {error_msg}")
                self.logger.error(f"人员信息查询失败: {error_msg}")
                return None
                
        except ValidationException as e:
            print(f"✗ 数据验证失败: {e.message}")
            if hasattr(e, 'details') and e.details:
                for field, errors in e.details.get('errors', {}).items():
                    print(f"  {field}: {', '.join(errors)}")
            self.logger.error(f"数据验证失败: {e.message}")
            
        except NetworkException as e:
            print(f"✗ 网络请求失败: {e.message}")
            self.logger.error(f"网络请求失败: {e.message}")
            
        except BusinessException as e:
            print(f"✗ 业务处理失败: {e.message}")
            self.logger.error(f"业务处理失败: {e.message}")
            
        except Exception as e:
            print(f"✗ 系统错误: {str(e)}")
            self.logger.error(f"系统错误: {str(e)}")
            
        return None

    def run_all_examples(self):
        """运行所有示例"""
        print("医保接口SDK完整使用示例")
        print("="*80)
        
        try:
            # 基础使用示例
            print("\n" + "🔹" * 20 + " 基础使用示例 " + "🔹" * 20)
            self.example_basic_person_query()
            
        except Exception as e:
            print(f"示例执行异常: {str(e)}")
            self.logger.error(f"示例执行异常: {str(e)}")
        
        print("\n" + "="*80)
        print("所有示例执行完成！")


def main():
    """主函数"""
    examples = MedicalInsuranceSDKExamples()
    examples.run_all_examples()


if __name__ == "__main__":
    main()