"""
根据接口文档添加2201门诊挂号接口配置
"""

import sys
import os
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager

def add_2201_registration_config():
    """添加2201门诊挂号接口配置"""
    
    # 从环境变量创建数据库配置
    db_config = DatabaseConfig.from_env()
    
    # 创建数据库管理器
    with DatabaseManager(db_config) as db:
        
        # 检查2201接口配置是否已存在
        existing = db.execute_query_one(
            "SELECT api_code FROM medical_interface_config WHERE api_code = %s",
            ("2201",)
        )
        
        if existing:
            print("2201接口配置已存在，将更新配置")
            
            # 更新配置
            db.execute_update("""
                UPDATE medical_interface_config SET
                    api_name = %s,
                    api_description = %s,
                    business_category = %s,
                    business_type = %s,
                    required_params = %s,
                    optional_params = %s,
                    validation_rules = %s,
                    response_mapping = %s,
                    updated_at = NOW()
                WHERE api_code = %s
            """, (
                "门诊挂号",
                "通过此交易进行门诊挂号",
                "门诊业务",
                "门诊挂号",
                '''{
                    "psn_no": {"type": "string", "length": 30, "description": "人员编号", "required": true},
                    "insutype": {"type": "string", "length": 6, "description": "险种类型", "required": true},
                    "begntime": {"type": "datetime", "description": "开始时间", "required": true, "format": "yyyy-MM-dd HH:mm:ss"},
                    "mdtrt_cert_type": {"type": "string", "length": 3, "description": "就诊凭证类型", "required": true},
                    "mdtrt_cert_no": {"type": "string", "length": 50, "description": "就诊凭证编号", "required": true},
                    "psn_cert_type": {"type": "string", "length": 3, "description": "证件类型", "required": true},
                    "certno": {"type": "string", "length": 20, "description": "证件号码", "required": true},
                    "psn_type": {"type": "string", "length": 3, "description": "人员类别", "required": true},
                    "psn_name": {"type": "string", "length": 20, "description": "人员姓名", "required": true},
                    "ipt_otp_no": {"type": "string", "length": 30, "description": "住院/门诊号", "required": true},
                    "dept_code": {"type": "string", "length": 30, "description": "科室编码", "required": true},
                    "dept_name": {"type": "string", "length": 100, "description": "科室名称", "required": true},
                    "caty": {"type": "string", "length": 10, "description": "科别", "required": true}
                }''',
                '''{
                    "card_sn": {"type": "string", "length": 32, "description": "卡识别码", "condition": "就诊凭证类型为03时必填"},
                    "atddr_no": {"type": "string", "length": 30, "description": "医师编码"},
                    "dr_name": {"type": "string", "length": 50, "description": "医师姓名"},
                    "exp_content": {"type": "string", "length": 4000, "description": "字段扩展"}
                }''',
                '''{
                    "psn_no": {"required": true, "pattern": "^[0-9A-Za-z]{1,30}$"},
                    "insutype": {"required": true, "pattern": "^[0-9]{1,6}$"},
                    "begntime": {"required": true, "pattern": "^\\\\d{4}-\\\\d{2}-\\\\d{2} \\\\d{2}:\\\\d{2}:\\\\d{2}$"},
                    "mdtrt_cert_type": {"required": true, "enum": ["01", "02", "03"]},
                    "mdtrt_cert_no": {"required": true, "minLength": 1, "maxLength": 50},
                    "psn_cert_type": {"required": true, "pattern": "^[0-9]{2}$"},
                    "certno": {"required": true, "minLength": 1, "maxLength": 20},
                    "psn_type": {"required": true, "pattern": "^[0-9]{1,3}$"},
                    "psn_name": {"required": true, "minLength": 1, "maxLength": 20},
                    "ipt_otp_no": {"required": true, "minLength": 1, "maxLength": 30},
                    "dept_code": {"required": true, "minLength": 1, "maxLength": 30},
                    "dept_name": {"required": true, "minLength": 1, "maxLength": 100},
                    "caty": {"required": true, "pattern": "^[0-9A-Za-z]{1,10}$"}
                }''',
                '''{
                    "mdtrt_id": "output.mdtrt_id",
                    "psn_no": "output.psn_no", 
                    "ipt_otp_no": "output.ipt_otp_no",
                    "exp_content": "output.exp_content",
                    "registration_result": {
                        "mdtrt_id": "output.mdtrt_id",
                        "psn_no": "output.psn_no",
                        "ipt_otp_no": "output.ipt_otp_no"
                    }
                }''',
                "2201"
            ))
            
        else:
            print("添加新的2201门诊挂号接口配置")
            
            # 插入新配置
            db.execute_update("""
                INSERT INTO medical_interface_config (
                    api_code, api_name, api_description, business_category, business_type,
                    required_params, optional_params, validation_rules, response_mapping,
                    is_active, requires_auth, supports_batch, max_retry_times, timeout_seconds,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                "2201",
                "门诊挂号",
                "通过此交易进行门诊挂号",
                "门诊业务",
                "门诊挂号",
                '''{
                    "psn_no": {"type": "string", "length": 30, "description": "人员编号", "required": true},
                    "insutype": {"type": "string", "length": 6, "description": "险种类型", "required": true},
                    "begntime": {"type": "datetime", "description": "开始时间", "required": true, "format": "yyyy-MM-dd HH:mm:ss"},
                    "mdtrt_cert_type": {"type": "string", "length": 3, "description": "就诊凭证类型", "required": true},
                    "mdtrt_cert_no": {"type": "string", "length": 50, "description": "就诊凭证编号", "required": true},
                    "psn_cert_type": {"type": "string", "length": 3, "description": "证件类型", "required": true},
                    "certno": {"type": "string", "length": 20, "description": "证件号码", "required": true},
                    "psn_type": {"type": "string", "length": 3, "description": "人员类别", "required": true},
                    "psn_name": {"type": "string", "length": 20, "description": "人员姓名", "required": true},
                    "ipt_otp_no": {"type": "string", "length": 30, "description": "住院/门诊号", "required": true},
                    "dept_code": {"type": "string", "length": 30, "description": "科室编码", "required": true},
                    "dept_name": {"type": "string", "length": 100, "description": "科室名称", "required": true},
                    "caty": {"type": "string", "length": 10, "description": "科别", "required": true}
                }''',
                '''{
                    "card_sn": {"type": "string", "length": 32, "description": "卡识别码", "condition": "就诊凭证类型为03时必填"},
                    "atddr_no": {"type": "string", "length": 30, "description": "医师编码"},
                    "dr_name": {"type": "string", "length": 50, "description": "医师姓名"},
                    "exp_content": {"type": "string", "length": 4000, "description": "字段扩展"}
                }''',
                '''{
                    "psn_no": {"required": true, "pattern": "^[0-9A-Za-z]{1,30}$"},
                    "insutype": {"required": true, "pattern": "^[0-9]{1,6}$"},
                    "begntime": {"required": true, "pattern": "^\\\\d{4}-\\\\d{2}-\\\\d{2} \\\\d{2}:\\\\d{2}:\\\\d{2}$"},
                    "mdtrt_cert_type": {"required": true, "enum": ["01", "02", "03"]},
                    "mdtrt_cert_no": {"required": true, "minLength": 1, "maxLength": 50},
                    "psn_cert_type": {"required": true, "pattern": "^[0-9]{2}$"},
                    "certno": {"required": true, "minLength": 1, "maxLength": 20},
                    "psn_type": {"required": true, "pattern": "^[0-9]{1,3}$"},
                    "psn_name": {"required": true, "minLength": 1, "maxLength": 20},
                    "ipt_otp_no": {"required": true, "minLength": 1, "maxLength": 30},
                    "dept_code": {"required": true, "minLength": 1, "maxLength": 30},
                    "dept_name": {"required": true, "minLength": 1, "maxLength": 100},
                    "caty": {"required": true, "pattern": "^[0-9A-Za-z]{1,10}$"}
                }''',
                '''{
                    "mdtrt_id": "output.mdtrt_id",
                    "psn_no": "output.psn_no", 
                    "ipt_otp_no": "output.ipt_otp_no",
                    "exp_content": "output.exp_content",
                    "registration_result": {
                        "mdtrt_id": "output.mdtrt_id",
                        "psn_no": "output.psn_no",
                        "ipt_otp_no": "output.ipt_otp_no"
                    }
                }''',
                1,  # is_active
                1,  # requires_auth
                0,  # supports_batch
                3,  # max_retry_times
                30  # timeout_seconds
            ))
        
        print("✅ 2201门诊挂号接口配置添加/更新成功")
        
        # 验证配置
        config = db.execute_query_one(
            "SELECT * FROM medical_interface_config WHERE api_code = %s",
            ("2201",)
        )
        
        if config:
            print(f"✅ 验证成功:")
            print(f"   - 接口代码: {config['api_code']}")
            print(f"   - 接口名称: {config['api_name']}")
            print(f"   - 业务类型: {config['business_type']}")
            print(f"   - 接口描述: {config['api_description']}")
            print(f"   - 是否激活: {config['is_active']}")
        else:
            print("❌ 验证失败：无法找到刚添加的配置")

if __name__ == "__main__":
    try:
        add_2201_registration_config()
    except Exception as e:
        print(f"❌ 添加配置失败: {e}")