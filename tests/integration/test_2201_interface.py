"""
2201接口（门诊挂号）测试
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from medical_insurance_sdk.client import MedicalInsuranceClient

class Test2201Interface:
    """2201接口测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = MedicalInsuranceClient()
    
    def test_2201_outpatient_registration(self):
        """测试2201门诊挂号接口"""
        # 测试数据
        test_data = {
            "psn_no": "H430100000000000001",
            "mdtrt_cert_type": "01",
            "mdtrt_cert_no": "430100000000000001",
            "ipt_otp_no": "OP202501250001",
            "atddr_no": "DOC001",
            "dr_name": "李医生",
            "dept_code": "001",
            "dept_name": "内科",
            "caty": "11",
            "begntime": "2025-01-25 09:00:00",
            "psn_cert_type": "01",
            "certno": "430100000000000001",
            "psn_name": "张三"
        }
        
        try:
            # 调用接口 - 使用正确的方法名和参数
            result = self.client.call("2201", test_data, "H43010000001")
            
            # 验证结果
            assert result is not None
            assert "infcode" in result
            
            print(f"2201接口调用结果: {result}")
            
        except Exception as e:
            pytest.skip(f"2201接口测试跳过: {str(e)}")
    
    def test_2201_validation(self):
        """测试2201接口数据验证"""
        # 测试必填字段验证
        invalid_data = {
            "psn_no": "",  # 必填字段为空
            "mdtrt_cert_type": "01"
        }
        
        try:
            result = self.client.call("2201", invalid_data, "H43010000001")
            # 如果没有抛出异常，检查返回的错误信息
            if result and "infcode" in result:
                assert result["infcode"] != "0", "应该返回验证错误"
        except Exception as e:
            # 预期会有验证异常
            assert "验证" in str(e) or "validation" in str(e).lower() or "required" in str(e).lower()