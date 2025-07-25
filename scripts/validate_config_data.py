#!/usr/bin/env python3
"""
医保接口SDK配置数据验证脚本
验证数据库中的配置数据完整性和正确性
"""

import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Tuple

import pymysql
from pymysql.cursors import DictCursor


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            self.logger.info(f"成功连接到数据库 {self.host}:{self.port}/{self.database}")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.logger.info("数据库连接已关闭")
    
    def validate_interface_config(self) -> Tuple[bool, List[str]]:
        """验证接口配置"""
        errors = []
        
        try:
            with self.connection.cursor() as cursor:
                # 检查接口配置表是否存在
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = 'medical_interface_config'
                """, (self.database,))
                
                if cursor.fetchone()['count'] == 0:
                    errors.append("接口配置表 medical_interface_config 不存在")
                    return False, errors
                
                # 检查配置数据
                cursor.execute("SELECT * FROM medical_interface_config WHERE is_active = 1")
                configs = cursor.fetchall()
                
                if not configs:
                    errors.append("没有找到活跃的接口配置")
                    return False, errors
                
                # 验证每个配置
                for config in configs:
                    config_errors = self._validate_single_interface_config(config)
                    errors.extend(config_errors)
                
                self.logger.info(f"验证了 {len(configs)} 个接口配置")
                
        except Exception as e:
            errors.append(f"验证接口配置时发生错误: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_single_interface_config(self, config: Dict) -> List[str]:
        """验证单个接口配置"""
        errors = []
        api_code = config.get('api_code', 'unknown')
        
        # 检查必填字段
        required_fields = ['api_code', 'api_name', 'business_category', 'business_type']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"接口 {api_code}: 缺少必填字段 {field}")
        
        # 验证JSON字段
        json_fields = ['required_params', 'optional_params', 'default_values', 
                      'request_template', 'response_mapping', 'validation_rules']
        
        for field in json_fields:
            if config.get(field):
                try:
                    json.loads(config[field])
                except json.JSONDecodeError as e:
                    errors.append(f"接口 {api_code}: {field} JSON格式错误 - {str(e)}")
        
        # 验证业务分类
        valid_categories = [
            '基础信息业务', '医保服务业务', '机构管理业务', '信息采集业务',
            '信息查询业务', '线上支付业务', '电子处方业务', '场景监控业务',
            '其他业务', '电子票据业务'
        ]
        
        if config.get('business_category') not in valid_categories:
            errors.append(f"接口 {api_code}: 无效的业务分类 {config.get('business_category')}")
        
        # 验证超时和重试配置
        timeout = config.get('timeout_seconds', 0)
        if timeout <= 0 or timeout > 300:
            errors.append(f"接口 {api_code}: 超时时间配置异常 {timeout}")
        
        retry_times = config.get('max_retry_times', 0)
        if retry_times < 0 or retry_times > 10:
            errors.append(f"接口 {api_code}: 重试次数配置异常 {retry_times}")
        
        return errors
    
    def validate_organization_config(self) -> Tuple[bool, List[str]]:
        """验证机构配置"""
        errors = []
        
        try:
            with self.connection.cursor() as cursor:
                # 检查机构配置表是否存在
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = 'medical_organization_config'
                """, (self.database,))
                
                if cursor.fetchone()['count'] == 0:
                    errors.append("机构配置表 medical_organization_config 不存在")
                    return False, errors
                
                # 检查配置数据
                cursor.execute("SELECT * FROM medical_organization_config WHERE is_active = 1")
                configs = cursor.fetchall()
                
                if not configs:
                    errors.append("没有找到活跃的机构配置")
                    return False, errors
                
                # 验证每个配置
                for config in configs:
                    config_errors = self._validate_single_organization_config(config)
                    errors.extend(config_errors)
                
                self.logger.info(f"验证了 {len(configs)} 个机构配置")
                
        except Exception as e:
            errors.append(f"验证机构配置时发生错误: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_single_organization_config(self, config: Dict) -> List[str]:
        """验证单个机构配置"""
        errors = []
        org_code = config.get('org_code', 'unknown')
        
        # 检查必填字段
        required_fields = ['org_code', 'org_name', 'app_id', 'app_secret', 'base_url']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"机构 {org_code}: 缺少必填字段 {field}")
        
        # 验证URL格式
        base_url = config.get('base_url', '')
        if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
            errors.append(f"机构 {org_code}: base_url格式错误 {base_url}")
        
        # 验证加密类型
        valid_crypto_types = ['SM4', 'AES', 'DES']
        crypto_type = config.get('crypto_type', '')
        if crypto_type and crypto_type not in valid_crypto_types:
            errors.append(f"机构 {org_code}: 无效的加密类型 {crypto_type}")
        
        # 验证签名类型
        valid_sign_types = ['SM3', 'SHA1', 'SHA256', 'MD5']
        sign_type = config.get('sign_type', '')
        if sign_type and sign_type not in valid_sign_types:
            errors.append(f"机构 {org_code}: 无效的签名类型 {sign_type}")
        
        # 验证JSON字段
        json_fields = ['timeout_config', 'region_specific']
        for field in json_fields:
            if config.get(field):
                try:
                    json.loads(config[field])
                except json.JSONDecodeError as e:
                    errors.append(f"机构 {org_code}: {field} JSON格式错误 - {str(e)}")
        
        return errors
    
    def validate_database_structure(self) -> Tuple[bool, List[str]]:
        """验证数据库结构"""
        errors = []
        
        try:
            with self.connection.cursor() as cursor:
                # 检查必要的表
                required_tables = [
                    'medical_interface_config',
                    'medical_organization_config',
                    'business_operation_logs',
                    'medical_institution_info',
                    'medical_interface_stats'
                ]
                
                for table in required_tables:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    """, (self.database, table))
                    
                    if cursor.fetchone()['count'] == 0:
                        errors.append(f"缺少必要的表: {table}")
                
                # 检查索引
                cursor.execute("""
                    SELECT table_name, index_name, column_name
                    FROM information_schema.statistics 
                    WHERE table_schema = %s AND index_name != 'PRIMARY'
                    ORDER BY table_name, index_name
                """, (self.database,))
                
                indexes = cursor.fetchall()
                self.logger.info(f"找到 {len(indexes)} 个索引")
                
                # 检查约束
                cursor.execute("""
                    SELECT table_name, constraint_name, constraint_type
                    FROM information_schema.table_constraints 
                    WHERE table_schema = %s
                    ORDER BY table_name, constraint_type
                """, (self.database,))
                
                constraints = cursor.fetchall()
                self.logger.info(f"找到 {len(constraints)} 个约束")
                
        except Exception as e:
            errors.append(f"验证数据库结构时发生错误: {str(e)}")
        
        return len(errors) == 0, errors
    
    def validate_data_consistency(self) -> Tuple[bool, List[str]]:
        """验证数据一致性"""
        errors = []
        
        try:
            with self.connection.cursor() as cursor:
                # 检查接口配置和机构配置的关联性
                cursor.execute("""
                    SELECT DISTINCT api_code 
                    FROM business_operation_logs 
                    WHERE api_code NOT IN (
                        SELECT api_code FROM medical_interface_config WHERE is_active = 1
                    )
                    LIMIT 10
                """)
                
                missing_configs = cursor.fetchall()
                for config in missing_configs:
                    errors.append(f"操作日志中存在未配置的接口: {config['api_code']}")
                
                # 检查机构配置的完整性
                cursor.execute("""
                    SELECT DISTINCT institution_code 
                    FROM business_operation_logs 
                    WHERE institution_code NOT IN (
                        SELECT org_code FROM medical_organization_config WHERE is_active = 1
                    )
                    LIMIT 10
                """)
                
                missing_orgs = cursor.fetchall()
                for org in missing_orgs:
                    errors.append(f"操作日志中存在未配置的机构: {org['institution_code']}")
                
                # 检查数据完整性
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM business_operation_logs 
                    WHERE request_data IS NULL OR response_data IS NULL
                """)
                
                incomplete_logs = cursor.fetchone()['count']
                if incomplete_logs > 0:
                    errors.append(f"存在 {incomplete_logs} 条不完整的操作日志")
                
        except Exception as e:
            errors.append(f"验证数据一致性时发生错误: {str(e)}")
        
        return len(errors) == 0, errors
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        report = {
            'timestamp': str(sys.modules['datetime'].datetime.now()),
            'database': f"{self.host}:{self.port}/{self.database}",
            'results': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'total_errors': 0
            }
        }
        
        # 执行各项验证
        checks = [
            ('database_structure', self.validate_database_structure),
            ('interface_config', self.validate_interface_config),
            ('organization_config', self.validate_organization_config),
            ('data_consistency', self.validate_data_consistency)
        ]
        
        for check_name, check_func in checks:
            self.logger.info(f"执行检查: {check_name}")
            
            try:
                success, errors = check_func()
                report['results'][check_name] = {
                    'passed': success,
                    'errors': errors,
                    'error_count': len(errors)
                }
                
                report['summary']['total_checks'] += 1
                if success:
                    report['summary']['passed_checks'] += 1
                else:
                    report['summary']['failed_checks'] += 1
                report['summary']['total_errors'] += len(errors)
                
            except Exception as e:
                self.logger.error(f"检查 {check_name} 时发生异常: {e}")
                report['results'][check_name] = {
                    'passed': False,
                    'errors': [f"检查异常: {str(e)}"],
                    'error_count': 1
                }
                report['summary']['total_checks'] += 1
                report['summary']['failed_checks'] += 1
                report['summary']['total_errors'] += 1
        
        return report
    
    def validate_all(self) -> bool:
        """执行完整验证"""
        self.logger.info("开始配置数据验证...")
        
        self.connect()
        
        try:
            report = self.generate_report()
            
            # 输出报告
            print("\n" + "="*60)
            print("医保接口SDK配置验证报告")
            print("="*60)
            print(f"数据库: {report['database']}")
            print(f"验证时间: {report['timestamp']}")
            print()
            
            # 输出摘要
            summary = report['summary']
            print("验证摘要:")
            print(f"  总检查项: {summary['total_checks']}")
            print(f"  通过检查: {summary['passed_checks']}")
            print(f"  失败检查: {summary['failed_checks']}")
            print(f"  总错误数: {summary['total_errors']}")
            print()
            
            # 输出详细结果
            for check_name, result in report['results'].items():
                status = "✓ 通过" if result['passed'] else "✗ 失败"
                print(f"{check_name}: {status}")
                
                if result['errors']:
                    for error in result['errors']:
                        print(f"  - {error}")
                print()
            
            # 总体结果
            overall_success = summary['failed_checks'] == 0
            if overall_success:
                print("✓ 配置验证通过！")
            else:
                print("✗ 配置验证失败，请修复上述错误")
            
            return overall_success
            
        finally:
            self.disconnect()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='医保接口SDK配置数据验证')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', type=int, default=3306, help='数据库端口')
    parser.add_argument('--user', default='root', help='数据库用户')
    parser.add_argument('--password', required=True, help='数据库密码')
    parser.add_argument('--database', default='medical_insurance_sdk', help='数据库名')
    parser.add_argument('--json', action='store_true', help='输出JSON格式报告')
    
    args = parser.parse_args()
    
    try:
        validator = ConfigValidator(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database
        )
        
        if args.json:
            # JSON格式输出
            validator.connect()
            try:
                report = validator.generate_report()
                print(json.dumps(report, ensure_ascii=False, indent=2))
            finally:
                validator.disconnect()
        else:
            # 标准格式输出
            success = validator.validate_all()
            sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"验证失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()