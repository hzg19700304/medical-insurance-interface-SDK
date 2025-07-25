#!/usr/bin/env python3
"""
数据库模拟数据插入脚本

为医保接口SDK的所有数据库表插入模拟数据，用于测试和开发
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
import uuid
import random

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


class MockDataInserter:
    """模拟数据插入器"""
    
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
    
    def insert_interface_configs(self):
        """插入接口配置数据"""
        logger.info("插入接口配置数据...")
        
        # 常用医保接口配置
        interface_configs = [
            {
                'api_code': '1101',
                'api_name': '人员信息获取',
                'business_category': '查询类',
                'business_type': '人员查询',
                'required_params': {
                    'psn_no': {'type': 'string', 'description': '人员编号'}
                },
                'his_integration_config': {
                    'field_mappings': {
                        'patient_id': 'output.baseinfo.psn_no',
                        'patient_name': 'output.baseinfo.psn_name',
                        'id_card': 'output.baseinfo.certno',
                        'gender': 'output.baseinfo.gend',
                        'birth_date': 'output.baseinfo.brdy',
                        'phone': 'output.baseinfo.tel'
                    },
                    'sync_config': {
                        'table_name': 'his_patients',
                        'primary_key': 'patient_id',
                        'operation': 'upsert'
                    }
                }
            },
            {
                'api_code': '1201',
                'api_name': '医药机构信息获取',
                'business_category': '查询类',
                'business_type': '机构查询',
                'required_params': {
                    'fixmedins_code': {'type': 'string', 'description': '定点医药机构编号'}
                },
                'his_integration_config': {}
            },
            {
                'api_code': '2207',
                'api_name': '门诊结算',
                'business_category': '结算类',
                'business_type': '门诊结算',
                'required_params': {
                    'mdtrt_id': {'type': 'string', 'description': '就医登记号'}
                },
                'his_integration_config': {
                    'writeback_mapping': {
                        'field_mappings': {
                            'settlement_id': 'output.setlinfo.setl_id',
                            'total_amount': 'output.setlinfo.setl_totlnum',
                            'insurance_amount': 'output.setlinfo.hifp_pay',
                            'personal_amount': 'output.setlinfo.psn_pay'
                        },
                        'writeback_config': {
                            'table_name': 'his_settlements',
                            'primary_key': 'settlement_id',
                            'operation': 'insert'
                        }
                    }
                }
            },
            {
                'api_code': '2208',
                'api_name': '住院结算',
                'business_category': '结算类',
                'business_type': '住院结算',
                'required_params': {
                    'mdtrt_id': {'type': 'string', 'description': '就医登记号'}
                },
                'his_integration_config': {}
            },
            {
                'api_code': '5203',
                'api_name': '医保电子凭证信息获取',
                'business_category': '查询类',
                'business_type': '电子凭证',
                'required_params': {
                    'ecToken': {'type': 'string', 'description': '电子凭证令牌'}
                },
                'his_integration_config': {}
            }
        ]
        
        for config in interface_configs:
            self.db_manager.execute_update("""
                INSERT INTO medical_interface_config 
                (api_code, api_name, business_category, business_type, 
                 required_params, his_integration_config, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                api_name = VALUES(api_name),
                business_category = VALUES(business_category),
                business_type = VALUES(business_type),
                required_params = VALUES(required_params),
                his_integration_config = VALUES(his_integration_config)
            """, (
                config['api_code'],
                config['api_name'],
                config['business_category'],
                config['business_type'],
                json.dumps(config['required_params'], ensure_ascii=False),
                json.dumps(config['his_integration_config'], ensure_ascii=False),
                True
            ))
        
        logger.info(f"插入了 {len(interface_configs)} 条接口配置数据")
    
    def insert_organization_configs(self):
        """插入机构配置数据"""
        logger.info("插入机构配置数据...")
        
        organizations = [
            {
                'org_code': 'H43010001001',
                'org_name': '湖南省人民医院',
                'org_type': 'hospital',
                'province_code': '430000',
                'city_code': '430100',
                'app_id': 'hn_people_hospital_001',
                'app_secret': 'secret_hn_people_001',
                'base_url': 'https://api.hnybj.gov.cn',
                'extra_config': {
                    'his_integration_overrides': {
                        '1101': {
                            'field_mappings': {
                                'patient_id': 'output.baseinfo.psn_no',
                                'patient_name': 'output.baseinfo.psn_name',
                                'hospital_patient_id': 'output.baseinfo.psn_no'
                            }
                        }
                    }
                }
            },
            {
                'org_code': 'H43010002001',
                'org_name': '中南大学湘雅医院',
                'org_type': 'hospital',
                'province_code': '430000',
                'city_code': '430100',
                'app_id': 'xiangya_hospital_001',
                'app_secret': 'secret_xiangya_001',
                'base_url': 'https://api.hnybj.gov.cn',
                'extra_config': {}
            },
            {
                'org_code': 'H43020001001',
                'org_name': '株洲市中心医院',
                'org_type': 'hospital',
                'province_code': '430000',
                'city_code': '430200',
                'app_id': 'zhuzhou_center_001',
                'app_secret': 'secret_zhuzhou_001',
                'base_url': 'https://api.hnybj.gov.cn',
                'extra_config': {}
            },
            {
                'org_code': 'TEST001',
                'org_name': '测试医院',
                'org_type': 'hospital',
                'province_code': '430000',
                'city_code': '430100',
                'app_id': 'test_hospital_001',
                'app_secret': 'test_secret_001',
                'base_url': 'http://test.api.com',
                'extra_config': {}
            }
        ]
        
        for org in organizations:
            self.db_manager.execute_update("""
                INSERT INTO medical_organization_config 
                (org_code, org_name, org_type, province_code, city_code, 
                 app_id, app_secret, base_url, extra_config, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                org_name = VALUES(org_name),
                org_type = VALUES(org_type),
                province_code = VALUES(province_code),
                city_code = VALUES(city_code),
                app_id = VALUES(app_id),
                app_secret = VALUES(app_secret),
                base_url = VALUES(base_url),
                extra_config = VALUES(extra_config)
            """, (
                org['org_code'],
                org['org_name'],
                org['org_type'],
                org['province_code'],
                org['city_code'],
                org['app_id'],
                org['app_secret'],
                org['base_url'],
                json.dumps(org['extra_config'], ensure_ascii=False),
                True
            ))
        
        logger.info(f"插入了 {len(organizations)} 条机构配置数据")
    
    def insert_business_operation_logs(self):
        """插入业务操作日志数据"""
        logger.info("插入业务操作日志数据...")
        
        # 生成最近7天的操作日志
        base_time = datetime.now() - timedelta(days=7)
        
        api_codes = ['1101', '1201', '2207', '2208', '5203']
        org_codes = ['H43010001001', 'H43010002001', 'H43020001001', 'TEST001']
        statuses = ['success', 'failed', 'pending']
        
        logs = []
        for i in range(100):  # 生成100条日志
            operation_time = base_time + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            api_code = random.choice(api_codes)
            org_code = random.choice(org_codes)
            status = random.choice(statuses)
            
            # 根据接口类型生成不同的请求和响应数据
            if api_code == '1101':
                request_data = {
                    'input': {
                        'psn_no': f'43012319{random.randint(800101, 991231):06d}{random.randint(1000, 9999)}'
                    }
                }
                if status == 'success':
                    response_data = {
                        'infcode': 0,
                        'output': {
                            'baseinfo': {
                                'psn_no': request_data['input']['psn_no'],
                                'psn_name': random.choice(['张三', '李四', '王五', '赵六', '钱七']),
                                'certno': request_data['input']['psn_no'],
                                'gend': random.choice(['1', '2']),
                                'brdy': f'{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                                'tel': f'138{random.randint(10000000, 99999999)}'
                            }
                        }
                    }
                else:
                    response_data = {
                        'infcode': -1,
                        'err_msg': '人员信息不存在'
                    }
            elif api_code == '2207':
                request_data = {
                    'input': {
                        'mdtrt_id': f'MDT{random.randint(100000000, 999999999)}'
                    }
                }
                if status == 'success':
                    total_amount = random.uniform(100, 2000)
                    insurance_amount = total_amount * random.uniform(0.6, 0.9)
                    response_data = {
                        'infcode': 0,
                        'output': {
                            'setlinfo': {
                                'setl_id': f'SETL{random.randint(100000000, 999999999)}',
                                'setl_totlnum': round(total_amount, 2),
                                'hifp_pay': round(insurance_amount, 2),
                                'psn_pay': round(total_amount - insurance_amount, 2),
                                'setl_time': operation_time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                        }
                    }
                else:
                    response_data = {
                        'infcode': -1,
                        'err_msg': '结算失败'
                    }
            else:
                request_data = {'input': {'test': 'data'}}
                response_data = {'infcode': 0 if status == 'success' else -1}
            
            log = {
                'operation_id': str(uuid.uuid4()),
                'api_code': api_code,
                'api_name': {
                    '1101': '人员信息获取',
                    '1201': '医药机构信息获取',
                    '2207': '门诊结算',
                    '2208': '住院结算',
                    '5203': '医保电子凭证信息获取'
                }[api_code],
                'business_category': '查询类' if api_code in ['1101', '1201', '5203'] else '结算类',
                'business_type': '人员查询' if api_code == '1101' else '门诊结算' if api_code == '2207' else '其他',
                'institution_code': org_code,
                'request_data': request_data,
                'response_data': response_data,
                'status': status,
                'operation_time': operation_time,
                'response_time_ms': random.randint(100, 3000),
                'trace_id': str(uuid.uuid4())
            }
            logs.append(log)
        
        # 批量插入
        for log in logs:
            self.db_manager.execute_update("""
                INSERT INTO business_operation_logs 
                (operation_id, api_code, api_name, business_category, business_type,
                 institution_code, request_data, response_data, status, operation_time,
                 response_time_ms, trace_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log['operation_id'],
                log['api_code'],
                log['api_name'],
                log['business_category'],
                log['business_type'],
                log['institution_code'],
                json.dumps(log['request_data'], ensure_ascii=False),
                json.dumps(log['response_data'], ensure_ascii=False),
                log['status'],
                log['operation_time'],
                log['response_time_ms'],
                log['trace_id']
            ))
        
        logger.info(f"插入了 {len(logs)} 条业务操作日志数据")
    
    def insert_institution_info(self):
        """插入医药机构信息数据"""
        logger.info("插入医药机构信息数据...")
        
        institutions = [
            {
                'fixmedins_code': 'H43010001001',
                'fixmedins_name': '湖南省人民医院',
                'uscc': '12430000444906565X',
                'fixmedins_type': '1',
                'hosp_lv': '3'
            },
            {
                'fixmedins_code': 'H43010002001',
                'fixmedins_name': '中南大学湘雅医院',
                'uscc': '12430000445906565Y',
                'fixmedins_type': '1',
                'hosp_lv': '3'
            },
            {
                'fixmedins_code': 'H43020001001',
                'fixmedins_name': '株洲市中心医院',
                'uscc': '12430200446906565Z',
                'fixmedins_type': '1',
                'hosp_lv': '3'
            },
            {
                'fixmedins_code': 'P43010001001',
                'fixmedins_name': '湖南省人民医院药房',
                'uscc': '12430000447906565A',
                'fixmedins_type': '2',
                'hosp_lv': None
            }
        ]
        
        for inst in institutions:
            self.db_manager.execute_update("""
                INSERT INTO medical_institution_info 
                (fixmedins_code, fixmedins_name, uscc, fixmedins_type, hosp_lv)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                fixmedins_name = VALUES(fixmedins_name),
                uscc = VALUES(uscc),
                fixmedins_type = VALUES(fixmedins_type),
                hosp_lv = VALUES(hosp_lv)
            """, (
                inst['fixmedins_code'],
                inst['fixmedins_name'],
                inst['uscc'],
                inst['fixmedins_type'],
                inst['hosp_lv']
            ))
        
        logger.info(f"插入了 {len(institutions)} 条医药机构信息数据")
    
    def insert_interface_stats(self):
        """插入接口调用统计数据"""
        logger.info("插入接口调用统计数据...")
        
        # 生成最近30天的统计数据
        base_date = datetime.now().date() - timedelta(days=30)
        
        api_codes = ['1101', '1201', '2207', '2208', '5203']
        org_codes = ['H43010001001', 'H43010002001', 'H43020001001', 'TEST001']
        
        stats = []
        for i in range(30):  # 30天
            stat_date = base_date + timedelta(days=i)
            
            for api_code in api_codes:
                for org_code in org_codes:
                    total_calls = random.randint(10, 200)
                    success_calls = int(total_calls * random.uniform(0.8, 0.98))
                    failed_calls = total_calls - success_calls
                    
                    stat = {
                        'stat_date': stat_date,
                        'institution_code': org_code,
                        'api_code': api_code,
                        'business_category': '查询类' if api_code in ['1101', '1201', '5203'] else '结算类',
                        'business_type': '人员查询' if api_code == '1101' else '门诊结算' if api_code == '2207' else '其他',
                        'total_calls': total_calls,
                        'success_calls': success_calls,
                        'failed_calls': failed_calls,
                        'avg_response_time': random.uniform(200, 1500),
                        'max_response_time': random.randint(1000, 5000),
                        'min_response_time': random.randint(50, 300),
                        'success_rate': round((success_calls / total_calls) * 100, 2)
                    }
                    stats.append(stat)
        
        # 批量插入
        for stat in stats:
            self.db_manager.execute_update("""
                INSERT INTO medical_interface_stats 
                (stat_date, institution_code, api_code, business_category, business_type,
                 total_calls, success_calls, failed_calls, avg_response_time,
                 max_response_time, min_response_time, success_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                total_calls = VALUES(total_calls),
                success_calls = VALUES(success_calls),
                failed_calls = VALUES(failed_calls),
                avg_response_time = VALUES(avg_response_time),
                max_response_time = VALUES(max_response_time),
                min_response_time = VALUES(min_response_time),
                success_rate = VALUES(success_rate)
            """, (
                stat['stat_date'],
                stat['institution_code'],
                stat['api_code'],
                stat['business_category'],
                stat['business_type'],
                stat['total_calls'],
                stat['success_calls'],
                stat['failed_calls'],
                stat['avg_response_time'],
                stat['max_response_time'],
                stat['min_response_time'],
                stat['success_rate']
            ))
        
        logger.info(f"插入了 {len(stats)} 条接口统计数据")
    
    def insert_his_sync_logs(self):
        """插入HIS同步日志数据"""
        logger.info("插入HIS同步日志数据...")
        
        # 生成最近7天的同步日志
        base_time = datetime.now() - timedelta(days=7)
        
        logs = []
        for i in range(50):  # 生成50条同步日志
            sync_time = base_time + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            log = {
                'sync_id': str(uuid.uuid4()),
                'api_code': random.choice(['1101', '2207']),
                'org_code': random.choice(['H43010001001', 'H43010002001', 'TEST001']),
                'medical_data': {
                    'psn_name': random.choice(['张三', '李四', '王五']),
                    'psn_no': f'43012319{random.randint(800101, 991231):06d}{random.randint(1000, 9999)}'
                },
                'his_data': {
                    'patient_name': random.choice(['张三', '李四', '王五']),
                    'patient_id': f'43012319{random.randint(800101, 991231):06d}{random.randint(1000, 9999)}'
                },
                'sync_status': random.choice(['success', 'failed']),
                'synced_records': random.randint(1, 5),
                'failed_records': random.randint(0, 2),
                'sync_time': sync_time
            }
            logs.append(log)
        
        for log in logs:
            self.db_manager.execute_update("""
                INSERT INTO his_data_sync_log 
                (sync_id, api_code, org_code, medical_data, his_data, 
                 sync_status, synced_records, failed_records, sync_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log['sync_id'],
                log['api_code'],
                log['org_code'],
                json.dumps(log['medical_data'], ensure_ascii=False),
                json.dumps(log['his_data'], ensure_ascii=False),
                log['sync_status'],
                log['synced_records'],
                log['failed_records'],
                log['sync_time']
            ))
        
        logger.info(f"插入了 {len(logs)} 条HIS同步日志数据")
    
    def insert_his_writeback_logs(self):
        """插入HIS回写日志数据"""
        logger.info("插入HIS回写日志数据...")
        
        # 生成最近7天的回写日志
        base_time = datetime.now() - timedelta(days=7)
        
        logs = []
        for i in range(30):  # 生成30条回写日志
            writeback_time = base_time + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            log = {
                'writeback_id': str(uuid.uuid4()),
                'api_code': '2207',
                'org_code': random.choice(['H43010001001', 'H43010002001', 'TEST001']),
                'medical_result': {
                    'setl_id': f'SETL{random.randint(100000000, 999999999)}',
                    'setl_totlnum': round(random.uniform(100, 2000), 2),
                    'hifp_pay': round(random.uniform(60, 1800), 2)
                },
                'his_data': {
                    'settlement_id': f'SETL{random.randint(100000000, 999999999)}',
                    'total_amount': round(random.uniform(100, 2000), 2)
                },
                'writeback_status': random.choice(['success', 'failed']),
                'written_records': random.randint(1, 3),
                'failed_records': random.randint(0, 1),
                'writeback_time': writeback_time
            }
            logs.append(log)
        
        for log in logs:
            self.db_manager.execute_update("""
                INSERT INTO his_writeback_log 
                (writeback_id, api_code, org_code, medical_result, his_data, 
                 writeback_status, written_records, failed_records, writeback_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log['writeback_id'],
                log['api_code'],
                log['org_code'],
                json.dumps(log['medical_result'], ensure_ascii=False),
                json.dumps(log['his_data'], ensure_ascii=False),
                log['writeback_status'],
                log['written_records'],
                log['failed_records'],
                log['writeback_time']
            ))
        
        logger.info(f"插入了 {len(logs)} 条HIS回写日志数据")
    
    def insert_consistency_checks(self):
        """插入数据一致性检查数据"""
        logger.info("插入数据一致性检查数据...")
        
        # 生成最近7天的一致性检查记录
        base_time = datetime.now() - timedelta(days=7)
        
        checks = []
        for i in range(20):  # 生成20条检查记录
            check_time = base_time + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            total_records = random.randint(50, 500)
            consistent = random.randint(40, total_records - 10)
            inconsistent = random.randint(0, 20)
            his_only = random.randint(0, 10)
            medical_only = random.randint(0, 10)
            
            check = {
                'table_name': random.choice(['his_patients', 'his_settlements']),
                'check_time': check_time,
                'total_records': total_records,
                'consistent_count': consistent,
                'inconsistent_count': inconsistent,
                'his_only_count': his_only,
                'medical_only_count': medical_only,
                'check_result': {
                    'summary': '数据一致性检查完成',
                    'details': {
                        'checked_records': total_records,
                        'consistent_records': consistent,
                        'inconsistent_records': inconsistent,
                        'his_only_records': his_only,
                        'medical_only_records': medical_only
                    }
                }
            }
            checks.append(check)
        
        for check in checks:
            self.db_manager.execute_update("""
                INSERT INTO data_consistency_checks 
                (table_name, check_time, total_records, consistent_count,
                 inconsistent_count, his_only_count, medical_only_count, check_result)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                check['table_name'],
                check['check_time'],
                check['total_records'],
                check['consistent_count'],
                check['inconsistent_count'],
                check['his_only_count'],
                check['medical_only_count'],
                json.dumps(check['check_result'], ensure_ascii=False)
            ))
        
        logger.info(f"插入了 {len(checks)} 条数据一致性检查记录")
    
    def insert_sync_conflicts(self):
        """插入数据同步冲突数据"""
        logger.info("插入数据同步冲突数据...")
        
        conflicts = []
        for i in range(10):  # 生成10条冲突记录
            conflict = {
                'conflict_id': f'CONFLICT_{i+1:03d}',
                'table_name': random.choice(['his_patients', 'his_settlements']),
                'primary_key': f'key_{random.randint(1000, 9999)}',
                'medical_data': {
                    'psn_name': '张三',
                    'psn_no': '430123199001011234'
                },
                'his_data': {
                    'patient_name': '张三丰',
                    'patient_id': '430123199001011234'
                },
                'conflict_fields': ['patient_name'],
                'resolved': random.choice([True, False])
            }
            conflicts.append(conflict)
        
        for conflict in conflicts:
            self.db_manager.execute_update("""
                INSERT INTO data_sync_conflicts 
                (conflict_id, table_name, primary_key, medical_data, his_data, 
                 conflict_fields, resolved)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                resolved = VALUES(resolved)
            """, (
                conflict['conflict_id'],
                conflict['table_name'],
                conflict['primary_key'],
                json.dumps(conflict['medical_data'], ensure_ascii=False),
                json.dumps(conflict['his_data'], ensure_ascii=False),
                json.dumps(conflict['conflict_fields'], ensure_ascii=False),
                conflict['resolved']
            ))
        
        logger.info(f"插入了 {len(conflicts)} 条数据同步冲突记录")
    
    def run_all_insertions(self):
        """运行所有数据插入操作"""
        logger.info("开始插入模拟数据...")
        
        try:
            # 按依赖顺序插入数据
            self.insert_interface_configs()
            self.insert_organization_configs()
            self.insert_business_operation_logs()
            self.insert_institution_info()
            self.insert_interface_stats()
            self.insert_his_sync_logs()
            self.insert_his_writeback_logs()
            self.insert_consistency_checks()
            self.insert_sync_conflicts()
            
            logger.info("✅ 所有模拟数据插入完成！")
            
            # 显示插入统计
            self.show_data_statistics()
            
        except Exception as e:
            logger.error(f"插入模拟数据失败: {e}")
            raise
        
        finally:
            self.cleanup()
    
    def show_data_statistics(self):
        """显示数据统计信息"""
        logger.info("=== 数据库表统计信息 ===")
        
        tables = [
            'medical_interface_config',
            'medical_organization_config',
            'business_operation_logs',
            'medical_institution_info',
            'medical_interface_stats',
            'his_data_sync_log',
            'his_writeback_log',
            'data_consistency_checks',
            'data_sync_conflicts'
        ]
        
        for table in tables:
            try:
                result = self.db_manager.execute_query_one(
                    f"SELECT COUNT(*) as count FROM {table}"
                )
                count = result['count'] if result else 0
                logger.info(f"{table}: {count} 条记录")
            except Exception as e:
                logger.warning(f"获取 {table} 统计失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.db_manager.close()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


def main():
    """主函数"""
    print("医保接口SDK数据库模拟数据插入工具")
    print("=" * 50)
    
    inserter = MockDataInserter()
    inserter.run_all_insertions()
    
    print("\n✅ 模拟数据插入完成！")
    print("现在可以使用这些数据进行测试和开发了。")
    
    return 0


if __name__ == "__main__":
    exit(main())