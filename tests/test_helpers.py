"""
测试辅助工具
提供测试中需要使用的通用函数和数据
"""

from medical_insurance_sdk.core.data_manager import DataManager
from medical_insurance_sdk.core.database import DatabaseManager, DatabaseConfig


def get_test_data_from_db():
    """
    从数据库获取测试数据
    
    Returns:
        dict: 包含测试数据的字典，包括人员信息、结算信息和保险信息
    """
    try:
        # 创建数据库配置
        db_config = DatabaseConfig.from_env()
        
        # 创建数据库管理器
        db_manager = DatabaseManager(db_config)
        
        # 创建数据管理器
        data_manager = DataManager(db_manager)
        
        # 获取测试用的人员信息 (使用TEST001作为测试ID)
        person_query = """
        SELECT * FROM person_info WHERE psn_no = 'TEST001' LIMIT 1
        """
        person_data = db_manager.execute_query_one(person_query)
        
        # 获取测试用的结算信息
        settlement_query = """
        SELECT * FROM settlement_info WHERE psn_no = 'TEST001' LIMIT 1
        """
        settlement_data = db_manager.execute_query_one(settlement_query)
        
        # 获取测试用的保险信息
        insurance_query = """
        SELECT * FROM insurance_info WHERE psn_no = 'TEST001' LIMIT 1
        """
        insurance_data = db_manager.execute_query_one(insurance_query)
        
        # 如果数据库中没有测试数据，则提供默认测试数据
        if not person_data:
            person_data = {
                "psn_no": "TEST001",
                "psn_name": "测试用户",
                "certno": "430123199001011234",
                "gend": "1",
                "brdy": "1990-01-01",
                "tel": "13800138000",
                "addr": "测试地址"
            }
        
        if not settlement_data:
            settlement_data = {
                "setl_id": "SETL001",
                "psn_no": "TEST001",
                "setl_totlnum": 1000.00,
                "hifp_pay": 800.00,
                "psn_pay": 200.00,
                "setl_time": "2024-01-15 10:30:00"
            }
        
        if not insurance_data:
            insurance_data = {
                "psn_no": "TEST001",
                "insutype": "310",
                "balc": 5000.00,
                "psn_insu_stas": "1",
                "psn_insu_date": "2023-01-01",
                "psn_insu_rlts_date": "2025-12-31"
            }
        
        return {
            "person": person_data,
            "settlement": settlement_data,
            "insurance": insurance_data
        }
    except Exception as e:
        print(f"获取测试数据失败: {e}")
        # 返回默认测试数据
        return {
            "person": {
                "psn_no": "TEST001",
                "psn_name": "测试用户",
                "certno": "430123199001011234",
                "gend": "1",
                "brdy": "1990-01-01",
                "tel": "13800138000",
                "addr": "测试地址"
            },
            "settlement": {
                "setl_id": "SETL001",
                "psn_no": "TEST001",
                "setl_totlnum": 1000.00,
                "hifp_pay": 800.00,
                "psn_pay": 200.00,
                "setl_time": "2024-01-15 10:30:00"
            },
            "insurance": {
                "psn_no": "TEST001",
                "insutype": "310",
                "balc": 5000.00,
                "psn_insu_stas": "1",
                "psn_insu_date": "2023-01-01",
                "psn_insu_rlts_date": "2025-12-31"
            }
        }