"""
专门检查2201接口的response_mapping配置
"""

import sys
import os
import json
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 加载环境变量
load_dotenv()

from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager

def check_2201_response_mapping():
    """检查2201接口的response_mapping配置"""
    
    try:
        # 从环境变量创建数据库配置
        db_config = DatabaseConfig.from_env()
        
        # 创建数据库管理器
        with DatabaseManager(db_config) as db:
            
            print("🔍 检查2201接口的response_mapping配置...")
            
            # 查询2201接口的完整配置
            config = db.execute_query_one("""
                SELECT 
                    api_code,
                    api_name,
                    response_mapping,
                    created_at,
                    updated_at
                FROM medical_interface_config 
                WHERE api_code = %s
            """, ("2201",))
            
            if not config:
                print("❌ 2201接口配置不存在")
                return
            
            print(f"✅ 找到2201接口配置:")
            print(f"   - 接口代码: {config['api_code']}")
            print(f"   - 接口名称: {config['api_name']}")
            print(f"   - 创建时间: {config['created_at']}")
            print(f"   - 更新时间: {config['updated_at']}")
            
            # 解析response_mapping
            response_mapping_str = config['response_mapping']
            print(f"\n📋 原始response_mapping字符串:")
            print(f"   长度: {len(response_mapping_str) if response_mapping_str else 0}")
            print(f"   内容: {response_mapping_str}")
            
            if response_mapping_str:
                try:
                    response_mapping = json.loads(response_mapping_str)
                    print(f"\n✅ response_mapping解析成功:")
                    print(json.dumps(response_mapping, ensure_ascii=False, indent=4))
                    
                    # 分析映射配置
                    print(f"\n🔍 映射配置分析:")
                    print(f"   - 映射字段数量: {len(response_mapping)}")
                    
                    for key, value in response_mapping.items():
                        if isinstance(value, dict):
                            print(f"   - {key}: 复杂映射")
                            for sub_key, sub_value in value.items():
                                print(f"     * {sub_key}: {sub_value}")
                        else:
                            print(f"   - {key}: 简单路径映射 -> {value}")
                    
                    # 模拟Apifox返回数据，测试映射
                    print(f"\n🧪 测试映射配置:")
                    mock_response = {
                        "infcode": 0,
                        "output": {
                            "mdtrt_id": "MDTRT201908069131",
                            "psn_no": "5485",
                            "ipt_otp_no": "OPT197808048636",
                            "exp_content": ""
                        }
                    }
                    
                    print(f"   模拟响应数据: {json.dumps(mock_response, ensure_ascii=False)}")
                    
                    # 手动测试每个映射路径
                    def extract_by_path(data, path):
                        if not path or not isinstance(data, dict):
                            return None
                        
                        path_parts = path.split('.')
                        current_data = data
                        
                        for part in path_parts:
                            if isinstance(current_data, dict) and part in current_data:
                                current_data = current_data[part]
                            else:
                                return None
                        
                        return current_data
                    
                    print(f"\n   📋 映射测试结果:")
                    for key, value in response_mapping.items():
                        if isinstance(value, str):  # 简单路径映射
                            extracted_value = extract_by_path(mock_response, value)
                            print(f"   - {key} (路径: {value}): '{extracted_value}' (类型: {type(extracted_value)})")
                            if extracted_value is None:
                                print(f"     ❌ 路径 {value} 无法提取数据")
                            elif extracted_value == "":
                                print(f"     ⚠️  路径 {value} 提取到空字符串")
                            else:
                                print(f"     ✅ 路径 {value} 提取成功")
                        elif isinstance(value, dict):  # 复杂映射
                            print(f"   - {key}: 复杂映射")
                            for sub_key, sub_path in value.items():
                                if isinstance(sub_path, str):
                                    extracted_value = extract_by_path(mock_response, sub_path)
                                    print(f"     * {sub_key} (路径: {sub_path}): '{extracted_value}'")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ response_mapping JSON解析失败: {e}")
                    print(f"   可能的问题:")
                    print(f"   1. JSON格式错误")
                    print(f"   2. 特殊字符转义问题")
                    print(f"   3. 引号不匹配")
            else:
                print(f"❌ response_mapping为空")
            
            # 检查是否有其他相关配置
            print(f"\n🔍 检查其他相关配置...")
            
            # 查询所有接口的response_mapping，对比格式
            all_configs = db.execute_query("""
                SELECT api_code, api_name, response_mapping
                FROM medical_interface_config 
                WHERE response_mapping IS NOT NULL AND response_mapping != ''
                ORDER BY api_code
            """)
            
            print(f"\n📋 所有接口的response_mapping对比:")
            for cfg in all_configs:
                print(f"   - {cfg['api_code']} ({cfg['api_name']}):")
                try:
                    mapping = json.loads(cfg['response_mapping'])
                    print(f"     ✅ JSON有效，字段数: {len(mapping)}")
                    # 显示前3个字段作为示例
                    sample_fields = list(mapping.items())[:3]
                    for key, value in sample_fields:
                        if isinstance(value, str):
                            print(f"       - {key}: {value}")
                        else:
                            print(f"       - {key}: 复杂映射")
                except:
                    print(f"     ❌ JSON无效")
                    
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_2201_response_mapping()