# 医保接口SDK使用示例

## 概述

本文档提供医保接口SDK的详细使用示例，涵盖常见的业务场景和最佳实践。

## 基础使用示例

### 1. 环境准备

```python
# requirements.txt
mysql-connector-python>=8.0.0
redis>=4.0.0
requests>=2.25.0
celery>=5.2.0
```

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_database_fixed.py

# 插入测试数据
python insert_test_organization.py
python insert_test_interfaces.py
```

### 2. 基本配置

```python
# config.py
from medical_insurance_sdk.config import SDKConfig

# 开发环境配置
dev_config = SDKConfig(
    database_url="mysql://root:password@localhost/medical_insurance",
    redis_url="redis://localhost:6379/0",
    log_level="DEBUG",
    cache_enabled=True
)

# 生产环境配置
prod_config = SDKConfig(
    database_url="mysql://user:pass@prod-db:3306/medical_insurance",
    redis_url="redis://prod-redis:6379/0",
    log_level="INFO",
    cache_enabled=True,
    cache_ttl=600,
    http_timeout=30,
    database_pool_size=20
)
```

### 3. 客户端初始化

```python
# client_setup.py
from medical_insurance_sdk import MedicalInsuranceClient
from config import dev_config

# 创建客户端实例
client = MedicalInsuranceClient(dev_config)

# 或使用默认配置
client = MedicalInsuranceClient()
```

## 常见业务场景示例

### 场景1: 人员信息查询

```python
# examples/person_info_query.py
from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.exceptions import ValidationException, BusinessException

def query_person_info(id_card, name, org_code="H43010300001"):
    """查询人员基本信息"""
    client = MedicalInsuranceClient()
    
    try:
        # 构建查询参数
        input_data = {
            "mdtrt_cert_type": "02",  # 身份证
            "mdtrt_cert_no": id_card,
            "psn_cert_type": "01",
            "certno": id_card,
            "psn_name": name
        }
        
        # 调用接口
        result = client.call_interface(
            api_code="1101",
            input_data=input_data,
            org_code=org_code
        )
        
        # 处理结果
        if result:
            print(f"查询成功: {result['person_name']}")
            print(f"人员编号: {result['person_id']}")
            print(f"性别: {'男' if result['gender'] == '1' else '女'}")
            print(f"出生日期: {result['birth_date']}")
            
            # 显示参保信息
            if result['insurance_list']:
                print("\n参保信息:")
                for insurance in result['insurance_list']:
                    print(f"  险种: {insurance['insurance_type']}")
                    print(f"  余额: {insurance['balance']}")
                    print(f"  状态: {insurance['status']}")
            
            return result
        else:
            print("未查询到人员信息")
            return None
            
    except ValidationException as e:
        print(f"数据验证失败: {e.message}")
        print(f"错误详情: {e.details}")
        return None
        
    except BusinessException as e:
        print(f"业务异常: {e.message}")
        print(f"错误代码: {e.error_code}")
        return None
        
    except Exception as e:
        print(f"系统异常: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 查询测试用户
    result = query_person_info("430123199001011234", "张三")
    
    if result:
        # 使用数据处理工具
        from medical_insurance_sdk.utils import DataHelper
        
        # 提取基本信息
        basic_info = DataHelper.extract_person_basic_info(result)
        print(f"基本信息: {basic_info}")
        
        # 计算总余额
        total_balance = DataHelper.calculate_total_balance(result['insurance_list'])
        print(f"总余额: {total_balance}")
```

### 场景2: 门诊结算

```python
# examples/outpatient_settlement.py
from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.utils import DataHelper
import uuid
from datetime import datetime

def outpatient_settlement(patient_id, person_no, charges, org_code="H43010300001"):
    """门诊结算处理"""
    client = MedicalInsuranceClient()
    
    try:
        # 生成批次号
        batch_no = f"CHG{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:6]}"
        
        # 构建结算参数
        input_data = {
            "mdtrt_id": patient_id,
            "psn_no": person_no,
            "chrg_bchno": batch_no,
            "acct_used_flag": "0",  # 不使用个人账户
            "insutype": "310"       # 城镇职工基本医疗保险
        }
        
        print(f"开始门诊结算: 患者ID={patient_id}, 批次号={batch_no}")
        
        # 调用结算接口
        result = client.call_interface(
            api_code="2201",
            input_data=input_data,
            org_code=org_code
        )
        
        if result:
            # 使用数据处理工具格式化结算信息
            settlement_info = DataHelper.format_settlement_summary(result)
            
            print("结算成功!")
            print(f"结算单号: {settlement_info['settlement_id']}")
            print(f"总费用: ¥{settlement_info['total']:.2f}")
            print(f"医保支付: ¥{settlement_info['insurance_pay']:.2f}")
            print(f"个人支付: ¥{settlement_info['personal_pay']:.2f}")
            print(f"结算时间: {settlement_info['settlement_time']}")
            
            return settlement_info
        else:
            print("结算失败")
            return None
            
    except Exception as e:
        print(f"结算异常: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 模拟门诊结算
    charges = [
        {"item": "挂号费", "amount": 10.00},
        {"item": "诊疗费", "amount": 50.00},
        {"item": "药费", "amount": 120.00}
    ]
    
    settlement = outpatient_settlement(
        patient_id="MDT20240115001",
        person_no="430123199001011234",
        charges=charges
    )
```

### 场景3: 批量数据处理

```python
# examples/batch_processing.py
from medical_insurance_sdk import MedicalInsuranceClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import csv

def batch_query_person_info(person_list, org_code="H43010300001", max_workers=5):
    """批量查询人员信息"""
    client = MedicalInsuranceClient()
    results = []
    
    def query_single_person(person):
        """查询单个人员信息"""
        try:
            input_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": person['id_card'],
                "psn_cert_type": "01",
                "certno": person['id_card'],
                "psn_name": person['name']
            }
            
            result = client.call_interface("1101", input_data, org_code)
            return {
                'input': person,
                'result': result,
                'status': 'success',
                'error': None
            }
        except Exception as e:
            return {
                'input': person,
                'result': None,
                'status': 'failed',
                'error': str(e)
            }
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务
        future_to_person = {
            executor.submit(query_single_person, person): person 
            for person in person_list
        }
        
        # 收集结果
        for future in as_completed(future_to_person):
            result = future.result()
            results.append(result)
            
            # 显示进度
            print(f"已完成: {len(results)}/{len(person_list)}")
    
    return results

def save_results_to_csv(results, filename="batch_results.csv"):
    """保存结果到CSV文件"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'id_card', 'status', 'person_id', 'gender', 'birth_date', 'total_balance', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in results:
            row = {
                'name': item['input']['name'],
                'id_card': item['input']['id_card'],
                'status': item['status']
            }
            
            if item['status'] == 'success' and item['result']:
                result = item['result']
                row.update({
                    'person_id': result.get('person_id', ''),
                    'gender': '男' if result.get('gender') == '1' else '女',
                    'birth_date': result.get('birth_date', ''),
                    'total_balance': result.get('total_balance', 0)
                })
            else:
                row['error'] = item['error']
            
            writer.writerow(row)

# 使用示例
if __name__ == "__main__":
    # 准备测试数据
    person_list = [
        {"name": "张三", "id_card": "430123199001011234"},
        {"name": "李四", "id_card": "430123199002022345"},
        {"name": "王五", "id_card": "430123199003033456"},
        # ... 更多人员
    ]
    
    print(f"开始批量查询 {len(person_list)} 个人员信息...")
    start_time = time.time()
    
    # 执行批量查询
    results = batch_query_person_info(person_list, max_workers=10)
    
    end_time = time.time()
    print(f"批量查询完成，耗时: {end_time - start_time:.2f}秒")
    
    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count
    
    print(f"成功: {success_count}, 失败: {failed_count}")
    
    # 保存结果
    save_results_to_csv(results)
    print("结果已保存到 batch_results.csv")
```

### 场景4: 异步处理

```python
# examples/async_processing.py
from medical_insurance_sdk import MedicalInsuranceClient
import time
import asyncio

def async_interface_call_example():
    """异步接口调用示例"""
    client = MedicalInsuranceClient()
    
    # 提交异步任务
    input_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    print("提交异步任务...")
    task_id = client.call_interface_async(
        api_code="1101",
        input_data=input_data,
        org_code="H43010300001"
    )
    
    print(f"任务ID: {task_id}")
    
    # 轮询任务状态
    while True:
        status = client.get_async_task_status(task_id)
        print(f"任务状态: {status}")
        
        if status == "completed":
            result = client.get_async_task_result(task_id)
            print("任务完成!")
            print(f"结果: {result}")
            break
        elif status == "failed":
            error = client.get_async_task_error(task_id)
            print(f"任务失败: {error}")
            break
        else:
            print("任务处理中，等待1秒...")
            time.sleep(1)

async def async_batch_processing():
    """异步批量处理示例"""
    client = MedicalInsuranceClient()
    
    # 准备多个任务
    tasks = []
    person_list = [
        {"name": "张三", "id_card": "430123199001011234"},
        {"name": "李四", "id_card": "430123199002022345"},
        {"name": "王五", "id_card": "430123199003033456"}
    ]
    
    # 提交所有异步任务
    for person in person_list:
        input_data = {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": person['id_card'],
            "psn_cert_type": "01",
            "certno": person['id_card'],
            "psn_name": person['name']
        }
        
        task_id = client.call_interface_async("1101", input_data, "H43010300001")
        tasks.append({
            'task_id': task_id,
            'person': person
        })
    
    print(f"已提交 {len(tasks)} 个异步任务")
    
    # 等待所有任务完成
    completed_tasks = []
    while len(completed_tasks) < len(tasks):
        for task in tasks:
            if task['task_id'] not in [t['task_id'] for t in completed_tasks]:
                status = client.get_async_task_status(task['task_id'])
                
                if status in ["completed", "failed"]:
                    if status == "completed":
                        result = client.get_async_task_result(task['task_id'])
                        task['result'] = result
                        task['status'] = 'success'
                    else:
                        error = client.get_async_task_error(task['task_id'])
                        task['error'] = error
                        task['status'] = 'failed'
                    
                    completed_tasks.append(task)
                    print(f"任务完成: {task['person']['name']} - {task['status']}")
        
        if len(completed_tasks) < len(tasks):
            await asyncio.sleep(1)
    
    return completed_tasks

# 使用示例
if __name__ == "__main__":
    # 同步异步调用
    print("=== 同步异步调用示例 ===")
    async_interface_call_example()
    
    # 异步批量处理
    print("\n=== 异步批量处理示例 ===")
    results = asyncio.run(async_batch_processing())
    
    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"批量处理完成: 成功 {success_count}/{len(results)}")
```

### 场景5: 错误处理和重试

```python
# examples/error_handling.py
from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    NetworkException, 
    BusinessException,
    AuthenticationException
)
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def robust_interface_call(api_code, input_data, org_code, max_retries=3):
    """带重试机制的接口调用"""
    client = MedicalInsuranceClient()
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"尝试调用接口 {api_code}，第 {attempt + 1} 次")
            
            result = client.call_interface(api_code, input_data, org_code)
            logger.info("接口调用成功")
            return result
            
        except ValidationException as e:
            # 数据验证错误，不重试
            logger.error(f"数据验证失败: {e.message}")
            logger.error(f"错误详情: {e.details}")
            raise e
            
        except AuthenticationException as e:
            # 认证错误，不重试
            logger.error(f"认证失败: {e.message}")
            raise e
            
        except NetworkException as e:
            # 网络错误，可重试
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 指数退避
                logger.warning(f"网络异常，{wait_time}秒后重试: {e.message}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"网络异常，重试次数已用完: {e.message}")
                raise e
                
        except BusinessException as e:
            # 业务错误，根据错误码决定是否重试
            if e.error_code in ["-1", "999"]:  # 可重试的错误码
                if attempt < max_retries:
                    wait_time = 1
                    logger.warning(f"业务异常，{wait_time}秒后重试: {e.message}")
                    time.sleep(wait_time)
                    continue
            
            logger.error(f"业务异常: {e.message} (错误码: {e.error_code})")
            raise e
            
        except Exception as e:
            # 其他异常
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"未知异常，{wait_time}秒后重试: {e}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"未知异常，重试次数已用完: {e}")
                raise e
    
    raise Exception("接口调用失败，已达到最大重试次数")

def validate_and_call(api_code, input_data, org_code):
    """数据验证和接口调用"""
    try:
        # 预验证数据
        if api_code == "1101":
            required_fields = ["mdtrt_cert_type", "mdtrt_cert_no", "psn_name"]
            for field in required_fields:
                if not input_data.get(field):
                    raise ValueError(f"必填字段 {field} 不能为空")
            
            # 身份证号码格式检查
            id_card = input_data.get("certno", "")
            if len(id_card) != 18:
                raise ValueError("身份证号码长度必须为18位")
        
        # 调用接口
        return robust_interface_call(api_code, input_data, org_code)
        
    except ValueError as e:
        logger.error(f"数据预验证失败: {e}")
        return None
    except Exception as e:
        logger.error(f"接口调用失败: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 正常调用
    print("=== 正常调用示例 ===")
    input_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    result = validate_and_call("1101", input_data, "H43010300001")
    if result:
        print(f"查询成功: {result['person_name']}")
    
    # 错误数据测试
    print("\n=== 错误数据测试 ===")
    invalid_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "",  # 空值
        "psn_cert_type": "01",
        "certno": "123",      # 格式错误
        "psn_name": ""        # 空值
    }
    
    result = validate_and_call("1101", invalid_data, "H43010300001")
    if not result:
        print("数据验证失败，未调用接口")
```

## 高级使用场景

### 场景6: 自定义数据处理

```python
# examples/custom_data_processing.py
from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.utils import DataHelper

class CustomDataProcessor:
    """自定义数据处理器"""
    
    def __init__(self):
        self.client = MedicalInsuranceClient()
    
    def get_person_summary(self, id_card, name, org_code="H43010300001"):
        """获取人员信息摘要"""
        input_data = {
            "mdtrt_cert_type": "02",
            "mdtrt_cert_no": id_card,
            "psn_cert_type": "01",
            "certno": id_card,
            "psn_name": name
        }
        
        result = self.client.call_interface("1101", input_data, org_code)
        
        if not result:
            return None
        
        # 自定义数据处理
        summary = {
            'basic_info': {
                'name': result.get('person_name', ''),
                'id_card': result.get('id_card', ''),
                'gender_text': '男' if result.get('gender') == '1' else '女',
                'age': self._calculate_age(result.get('birth_date', '')),
                'age_group': result.get('age_group', '')
            },
            'insurance_summary': self._process_insurance_info(result.get('insurance_list', [])),
            'status': {
                'has_insurance': result.get('has_insurance', False),
                'total_balance': result.get('total_balance', 0),
                'active_insurances': len([i for i in result.get('insurance_list', []) if i.get('status') == '1'])
            }
        }
        
        return summary
    
    def _calculate_age(self, birth_date):
        """计算年龄"""
        if not birth_date:
            return 0
        
        from datetime import datetime
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth.year
            if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
                age -= 1
            return age
        except:
            return 0
    
    def _process_insurance_info(self, insurance_list):
        """处理参保信息"""
        if not insurance_list:
            return {'count': 0, 'types': [], 'total_balance': 0}
        
        insurance_types = {
            '310': '城镇职工基本医疗保险',
            '320': '城乡居民基本医疗保险',
            '330': '公务员医疗补助',
            '340': '企业补充医疗保险'
        }
        
        processed = {
            'count': len(insurance_list),
            'types': [],
            'total_balance': 0,
            'details': []
        }
        
        for insurance in insurance_list:
            insurance_type = insurance.get('insurance_type', '')
            type_name = insurance_types.get(insurance_type, f'未知险种({insurance_type})')
            balance = float(insurance.get('balance', 0))
            
            processed['types'].append(type_name)
            processed['total_balance'] += balance
            processed['details'].append({
                'type': type_name,
                'balance': balance,
                'status': '正常' if insurance.get('status') == '1' else '异常'
            })
        
        return processed

# 使用示例
if __name__ == "__main__":
    processor = CustomDataProcessor()
    
    # 获取人员摘要信息
    summary = processor.get_person_summary("430123199001011234", "张三")
    
    if summary:
        print("=== 人员信息摘要 ===")
        print(f"姓名: {summary['basic_info']['name']}")
        print(f"性别: {summary['basic_info']['gender_text']}")
        print(f"年龄: {summary['basic_info']['age']}岁 ({summary['basic_info']['age_group']})")
        
        print(f"\n=== 参保信息 ===")
        print(f"参保险种数: {summary['insurance_summary']['count']}")
        print(f"总余额: ¥{summary['insurance_summary']['total_balance']:.2f}")
        
        for detail in summary['insurance_summary']['details']:
            print(f"  {detail['type']}: ¥{detail['balance']:.2f} ({detail['status']})")
```

### 场景7: 监控和统计

```python
# examples/monitoring_stats.py
from medical_insurance_sdk import MedicalInsuranceClient
from medical_insurance_sdk.core.metrics_collector import MetricsCollector
from medical_insurance_sdk.core.data_manager import DataManager
import time
from datetime import datetime, timedelta

class InterfaceMonitor:
    """接口监控器"""
    
    def __init__(self):
        self.client = MedicalInsuranceClient()
        self.metrics = MetricsCollector()
        self.data_manager = DataManager()
    
    def get_interface_stats(self, api_code, org_code, days=7):
        """获取接口统计信息"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取基础统计
        stats = self.metrics.get_interface_stats(api_code, org_code)
        
        # 获取详细调用记录
        logs = self.data_manager.get_operation_logs({
            'api_code': api_code,
            'institution_code': org_code,
            'start_time': start_time,
            'end_time': end_time
        })
        
        # 计算成功率
        total_calls = len(logs)
        success_calls = len([log for log in logs if log.status == 'success'])
        success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0
        
        # 计算平均响应时间
        response_times = []
        for log in logs:
            if log.complete_time and log.operation_time:
                duration = (log.complete_time - log.operation_time).total_seconds() * 1000
                response_times.append(duration)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 错误统计
        error_stats = {}
        for log in logs:
            if log.status == 'failed' and log.error_code:
                error_stats[log.error_code] = error_stats.get(log.error_code, 0) + 1
        
        return {
            'api_code': api_code,
            'org_code': org_code,
            'period': f'{days}天',
            'total_calls': total_calls,
            'success_calls': success_calls,
            'failed_calls': total_calls - success_calls,
            'success_rate': f'{success_rate:.2f}%',
            'avg_response_time': f'{avg_response_time:.2f}ms',
            'error_distribution': error_stats
        }
    
    def generate_daily_report(self, org_code):
        """生成日报"""
        today = datetime.now().date()
        
        # 获取今日所有接口调用统计
        logs = self.data_manager.get_operation_logs({
            'institution_code': org_code,
            'start_time': datetime.combine(today, datetime.min.time()),
            'end_time': datetime.combine(today, datetime.max.time())
        })
        
        # 按接口分组统计
        interface_stats = {}
        for log in logs:
            api_code = log.api_code
            if api_code not in interface_stats:
                interface_stats[api_code] = {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'response_times': []
                }
            
            interface_stats[api_code]['total'] += 1
            if log.status == 'success':
                interface_stats[api_code]['success'] += 1
            else:
                interface_stats[api_code]['failed'] += 1
            
            if log.complete_time and log.operation_time:
                duration = (log.complete_time - log.operation_time).total_seconds() * 1000
                interface_stats[api_code]['response_times'].append(duration)
        
        # 生成报告
        report = {
            'date': today.strftime('%Y-%m-%d'),
            'org_code': org_code,
            'summary': {
                'total_calls': len(logs),
                'total_interfaces': len(interface_stats),
                'overall_success_rate': 0
            },
            'interface_details': []
        }
        
        total_success = sum(stats['success'] for stats in interface_stats.values())
        report['summary']['overall_success_rate'] = f'{(total_success / len(logs) * 100):.2f}%' if logs else '0%'
        
        for api_code, stats in interface_stats.items():
            avg_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            report['interface_details'].append({
                'api_code': api_code,
                'total_calls': stats['total'],
                'success_rate': f'{success_rate:.2f}%',
                'avg_response_time': f'{avg_time:.2f}ms'
            })
        
        return report
    
    def performance_test(self, api_code, input_data, org_code, test_count=100):
        """性能测试"""
        print(f"开始性能测试: {api_code}, 测试次数: {test_count}")
        
        results = []
        start_time = time.time()
        
        for i in range(test_count):
            test_start = time.time()
            try:
                result = self.client.call_interface(api_code, input_data, org_code)
                test_end = time.time()
                
                results.append({
                    'success': True,
                    'response_time': (test_end - test_start) * 1000,
                    'error': None
                })
            except Exception as e:
                test_end = time.time()
                results.append({
                    'success': False,
                    'response_time': (test_end - test_start) * 1000,
                    'error': str(e)
                })
            
            # 显示进度
            if (i + 1) % 10 == 0:
                print(f"已完成: {i + 1}/{test_count}")
        
        end_time = time.time()
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        failed_count = test_count - success_count
        response_times = [r['response_time'] for r in results if r['success']]
        
        performance_report = {
            'api_code': api_code,
            'test_count': test_count,
            'total_time': f'{(end_time - start_time):.2f}s',
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': f'{(success_count / test_count * 100):.2f}%',
            'avg_response_time': f'{(sum(response_times) / len(response_times)):.2f}ms' if response_times else 'N/A',
            'min_response_time': f'{min(response_times):.2f}ms' if response_times else 'N/A',
            'max_response_time': f'{max(response_times):.2f}ms' if response_times else 'N/A',
            'qps': f'{(success_count / (end_time - start_time)):.2f}'
        }
        
        return performance_report

# 使用示例
if __name__ == "__main__":
    monitor = InterfaceMonitor()
    
    # 获取接口统计
    print("=== 接口统计信息 ===")
    stats = monitor.get_interface_stats("1101", "H43010300001", days=7)
    print(f"接口: {stats['api_code']}")
    print(f"总调用次数: {stats['total_calls']}")
    print(f"成功率: {stats['success_rate']}")
    print(f"平均响应时间: {stats['avg_response_time']}")
    
    if stats['error_distribution']:
        print("错误分布:")
        for error_code, count in stats['error_distribution'].items():
            print(f"  {error_code}: {count}次")
    
    # 生成日报
    print("\n=== 日报 ===")
    report = monitor.generate_daily_report("H43010300001")
    print(f"日期: {report['date']}")
    print(f"总调用次数: {report['summary']['total_calls']}")
    print(f"涉及接口数: {report['summary']['total_interfaces']}")
    print(f"整体成功率: {report['summary']['overall_success_rate']}")
    
    print("\n接口详情:")
    for detail in report['interface_details']:
        print(f"  {detail['api_code']}: {detail['total_calls']}次, 成功率{detail['success_rate']}, 平均响应时间{detail['avg_response_time']}")
    
    # 性能测试
    print("\n=== 性能测试 ===")
    test_data = {
        "mdtrt_cert_type": "02",
        "mdtrt_cert_no": "430123199001011234",
        "psn_cert_type": "01",
        "certno": "430123199001011234",
        "psn_name": "张三"
    }
    
    perf_report = monitor.performance_test("1101", test_data, "H43010300001", test_count=50)
    print(f"测试接口: {perf_report['api_code']}")
    print(f"测试次数: {perf_report['test_count']}")
    print(f"总耗时: {perf_report['total_time']}")
    print(f"成功率: {perf_report['success_rate']}")
    print(f"平均响应时间: {perf_report['avg_response_time']}")
    print(f"QPS: {perf_report['qps']}")
```

## 最佳实践总结

### 1. 错误处理
- 始终使用try-catch处理异常
- 区分不同类型的异常并采取相应措施
- 对网络异常实施重试机制
- 记录详细的错误日志

### 2. 性能优化
- 使用连接池减少连接开销
- 启用缓存提高配置加载速度
- 对批量操作使用并发处理
- 合理设置超时时间

### 3. 数据验证
- 在调用接口前进行数据预验证
- 利用配置化的验证规则
- 提供友好的错误提示信息

### 4. 监控和日志
- 启用详细的调用日志
- 定期检查接口调用统计
- 设置性能监控和告警
- 保留足够的历史数据用于分析

### 5. 配置管理
- 区分开发、测试、生产环境配置
- 使用环境变量管理敏感信息
- 定期备份配置数据
- 实施配置变更审核流程

---

更多详细信息请参考：
- [API文档](api-documentation.md)
- [接口配置指南](interface-configuration-guide.md)
- [故障排除指南](troubleshooting-guide.md)