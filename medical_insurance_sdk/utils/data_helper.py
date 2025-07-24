"""
数据处理工具类
提供常用的数据提取、格式化和处理方法
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation


class DataHelper:
    """数据处理辅助工具类 - 提供常用的数据处理方法"""
    
    # 常用的数据提取方法
    
    @staticmethod
    def extract_person_basic_info(response_data: dict) -> dict:
        """提取人员基本信息的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            dict: 格式化的人员基本信息
        """
        # 支持多种数据结构
        person_info = response_data.get('person_info', {})
        if not person_info:
            person_info = response_data.get('baseinfo', {})
        if not person_info:
            person_info = response_data.get('output', {}).get('baseinfo', {})
        
        # 如果没有找到嵌套结构，直接从根级别获取
        if not person_info:
            person_info = response_data
        
        return {
            'name': person_info.get('psn_name', person_info.get('person_name', '')),
            'id': person_info.get('psn_no', person_info.get('person_id', '')),
            'id_card': person_info.get('certno', person_info.get('id_card', '')),
            'gender': person_info.get('gend', person_info.get('gender', '')),
            'birth_date': person_info.get('brdy', person_info.get('birth_date', '')),
            'age': DataHelper._safe_int(person_info.get('age', 0)),
            'phone': person_info.get('tel', person_info.get('phone', '')),
            'address': person_info.get('addr', person_info.get('address', '')),
            'nationality': person_info.get('naty', person_info.get('nationality', '')),
            'ethnic': person_info.get('nwb', person_info.get('ethnic', ''))
        }
    
    @staticmethod
    def extract_insurance_info(response_data: dict) -> List[dict]:
        """提取参保信息的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            List[dict]: 参保信息列表
        """
        # 支持多种数据结构
        insurance_list = response_data.get('insurance_list', [])
        if not insurance_list:
            insurance_list = response_data.get('insuinfo', [])
        if not insurance_list:
            insurance_list = response_data.get('output', {}).get('insuinfo', [])
        
        formatted_list = []
        for item in insurance_list:
            formatted_item = {
                'type': item.get('insutype', item.get('type', '')),
                'insurance_type_name': DataHelper._get_insurance_type_name(item.get('insutype', item.get('type', ''))),
                'person_type': item.get('psn_type', ''),
                'balance': DataHelper._safe_float(item.get('balc', item.get('balance', 0))),
                'status': item.get('psn_insu_stas', ''),
                'status_name': DataHelper._get_insurance_status_name(item.get('psn_insu_stas', '')),
                'start_date': DataHelper._format_date(item.get('psn_insu_date', '')),
                'end_date': DataHelper._format_date(item.get('psn_insu_rlts_date', '')),
                'org_code': item.get('insuplc_admdvs', ''),
                'org_name': item.get('insuplc_admdvs_name', '')
            }
            formatted_list.append(formatted_item)
        
        return formatted_list
    
    @staticmethod
    def extract_identity_info(response_data: dict) -> List[dict]:
        """提取身份信息的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            List[dict]: 身份信息列表
        """
        identity_list = response_data.get('identity_list', [])
        if not identity_list:
            identity_list = response_data.get('idetinfo', [])
        if not identity_list:
            identity_list = response_data.get('output', {}).get('idetinfo', [])
        
        formatted_list = []
        for item in identity_list:
            formatted_item = {
                'identity_type': item.get('psn_idet_type', ''),
                'identity_name': DataHelper._get_identity_type_name(item.get('psn_idet_type', '')),
                'level': item.get('psn_type_lv', ''),
                'start_time': DataHelper._format_datetime(item.get('begntime', '')),
                'end_time': DataHelper._format_datetime(item.get('endtime', '')),
                'memo': item.get('memo', '')
            }
            formatted_list.append(formatted_item)
        
        return formatted_list
    
    @staticmethod
    def calculate_total_balance(insurance_list: List[dict]) -> float:
        """计算总余额的便捷方法
        
        Args:
            insurance_list: 参保信息列表
            
        Returns:
            float: 总余额
        """
        total = 0.0
        for item in insurance_list:
            balance = item.get('balance', 0)
            if isinstance(balance, (int, float)):
                total += balance
            elif isinstance(balance, str):
                try:
                    total += float(balance)
                except ValueError:
                    continue
        return round(total, 2)
    
    @staticmethod
    def format_settlement_summary(response_data: dict) -> dict:
        """格式化结算摘要的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            dict: 格式化的结算摘要
        """
        # 支持多种数据结构
        settlement_info = response_data.get('settlement_result', {})
        if not settlement_info:
            settlement_info = response_data.get('setlinfo', {})
        if not settlement_info:
            settlement_info = response_data.get('output', {}).get('setlinfo', {})
        
        # 如果没有找到嵌套结构，直接从根级别获取
        if not settlement_info:
            settlement_info = response_data
        
        return {
            'settlement_id': settlement_info.get('setl_id', settlement_info.get('settlement_id', '')),
            'total': DataHelper._safe_float(settlement_info.get('setl_totlnum', settlement_info.get('total_amount', 0))),
            'insurance_pay': DataHelper._safe_float(settlement_info.get('hifp_pay', settlement_info.get('insurance_amount', 0))),
            'personal_pay': DataHelper._safe_float(settlement_info.get('psn_pay', settlement_info.get('personal_amount', 0))),
            'account_amount': DataHelper._safe_float(settlement_info.get('acct_pay', 0)),
            'cash_amount': DataHelper._safe_float(settlement_info.get('psn_cash_pay', 0)),
            'settlement_time': settlement_info.get('setl_time', settlement_info.get('settlement_time', '')),
            'medical_type': settlement_info.get('med_type', ''),
            'settlement_type': settlement_info.get('setl_type', ''),
            'invoice_no': settlement_info.get('invono', ''),
            'receipt_no': settlement_info.get('recp_no', '')
        }
    
    @staticmethod
    def extract_error_info(response_data: dict) -> dict:
        """提取错误信息的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            dict: 错误信息
        """
        return {
            'error_code': response_data.get('infcode', ''),
            'error_message': response_data.get('err_msg', ''),
            'warning_message': response_data.get('warn_msg', ''),
            'is_success': str(response_data.get('infcode', '')).strip() == '0',
            'response_time': response_data.get('respond_time', ''),
            'ref_msg_id': response_data.get('inf_refmsgid', '')
        }
    
    @staticmethod
    def format_medical_record(response_data: dict) -> dict:
        """格式化医疗记录的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            dict: 格式化的医疗记录
        """
        return {
            'record_id': response_data.get('mdtrt_id', ''),
            'person_no': response_data.get('psn_no', ''),
            'visit_date': DataHelper._format_datetime(response_data.get('begntime', '')),
            'end_date': DataHelper._format_datetime(response_data.get('endtime', '')),
            'diagnosis_code': response_data.get('dise_codg', ''),
            'diagnosis_name': response_data.get('dise_name', ''),
            'hospital_code': response_data.get('fixmedins_code', ''),
            'hospital_name': response_data.get('fixmedins_name', ''),
            'department_code': response_data.get('dept_codg', ''),
            'department_name': response_data.get('dept_name', ''),
            'doctor_code': response_data.get('dr_codg', ''),
            'doctor_name': response_data.get('dr_name', ''),
            'medical_type': response_data.get('med_type', ''),
            'visit_type': response_data.get('mdtrt_type', '')
        }
    
    @staticmethod
    def extract_drug_list(response_data: dict) -> List[dict]:
        """提取药品列表的便捷方法
        
        Args:
            response_data: 接口响应数据
            
        Returns:
            List[dict]: 药品信息列表
        """
        drug_list = response_data.get('drug_list', [])
        if not drug_list:
            drug_list = response_data.get('feedetail', [])
        if not drug_list:
            drug_list = response_data.get('output', {}).get('feedetail', [])
        
        formatted_list = []
        for item in drug_list:
            formatted_item = {
                'drug_code': item.get('med_list_codg', ''),
                'drug_name': item.get('med_list_name', ''),
                'drug_spec': item.get('drug_spec', ''),
                'drug_dosage': item.get('drug_dosage', ''),
                'drug_form': item.get('drug_form', ''),
                'unit': item.get('min_unit', ''),
                'price': DataHelper._safe_float(item.get('pric', 0)),
                'quantity': DataHelper._safe_float(item.get('cnt', 0)),
                'total_amount': DataHelper._safe_float(item.get('det_item_fee_sumamt', 0)),
                'insurance_amount': DataHelper._safe_float(item.get('hifp_pay', 0)),
                'personal_amount': DataHelper._safe_float(item.get('psn_pay', 0)),
                'manufacturer': item.get('prodname', ''),
                'approval_number': item.get('drug_aprvno', '')
            }
            formatted_list.append(formatted_item)
        
        return formatted_list
    
    # 数据验证方法
    
    @staticmethod
    def validate_id_card(id_card: str) -> bool:
        """验证身份证号码格式
        
        Args:
            id_card: 身份证号码
            
        Returns:
            bool: 是否有效
        """
        if not id_card or not isinstance(id_card, str):
            return False
        
        id_card = id_card.strip()
        
        if len(id_card) == 18:
            # 18位身份证
            pattern = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]$'
            if not re.match(pattern, id_card):
                return False
            
            # 校验码验证
            return DataHelper._validate_id_card_checksum(id_card)
        
        elif len(id_card) == 15:
            # 15位身份证
            pattern = r'^[1-9]\d{5}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}$'
            return bool(re.match(pattern, id_card))
        
        return False
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """验证手机号码格式
        
        Args:
            phone: 手机号码
            
        Returns:
            bool: 是否有效
        """
        if not phone or not isinstance(phone, str):
            return False
        
        phone = phone.strip()
        # 支持11位手机号和带区号的固定电话
        mobile_pattern = r'^1[3-9]\d{9}$'
        landline_pattern = r'^0\d{2,3}-?\d{7,8}$'
        
        return bool(re.match(mobile_pattern, phone) or re.match(landline_pattern, phone))
    
    @staticmethod
    def validate_organization_code(org_code: str) -> bool:
        """验证机构编码格式
        
        Args:
            org_code: 机构编码
            
        Returns:
            bool: 是否有效
        """
        if not org_code or not isinstance(org_code, str):
            return False
        
        org_code = org_code.strip()
        # 医保机构编码通常是12位数字
        pattern = r'^\d{12}$'
        return bool(re.match(pattern, org_code))
    
    # 数据格式化方法
    
    @staticmethod
    def format_amount(amount: Any, decimals: int = 2) -> str:
        """格式化金额
        
        Args:
            amount: 金额值
            decimals: 小数位数
            
        Returns:
            str: 格式化后的金额字符串
        """
        try:
            if amount is None or amount == '':
                return "0.00"
            
            # 使用Decimal确保精度
            decimal_amount = Decimal(str(amount))
            format_str = f"{{:.{decimals}f}}"
            return format_str.format(float(decimal_amount))
        except (ValueError, TypeError, InvalidOperation):
            return "0.00"
    
    @staticmethod
    def format_currency(amount: Any, currency: str = '¥') -> str:
        """格式化货币
        
        Args:
            amount: 金额值
            currency: 货币符号
            
        Returns:
            str: 格式化后的货币字符串
        """
        formatted_amount = DataHelper.format_amount(amount)
        return f"{currency}{formatted_amount}"
    
    @staticmethod
    def parse_date_string(date_str: str, input_format: str = '%Y-%m-%d', output_format: str = '%Y%m%d') -> str:
        """解析日期字符串
        
        Args:
            date_str: 日期字符串
            input_format: 输入格式
            output_format: 输出格式
            
        Returns:
            str: 格式化后的日期字符串
        """
        if not date_str:
            return ''
        
        try:
            date_obj = datetime.strptime(str(date_str).strip(), input_format)
            return date_obj.strftime(output_format)
        except (ValueError, TypeError):
            # 尝试其他常见格式
            common_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y-%m-%d %H:%M:%S']
            for fmt in common_formats:
                try:
                    date_obj = datetime.strptime(str(date_str).strip(), fmt)
                    return date_obj.strftime(output_format)
                except ValueError:
                    continue
            return str(date_str)
    
    @staticmethod
    def format_datetime(datetime_str: str, output_format: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化日期时间字符串
        
        Args:
            datetime_str: 日期时间字符串
            output_format: 输出格式
            
        Returns:
            str: 格式化后的日期时间字符串
        """
        return DataHelper._format_datetime(datetime_str, output_format)
    
    @staticmethod
    def normalize_data(data: dict, field_mappings: Dict[str, str] = None) -> dict:
        """标准化数据字段名
        
        Args:
            data: 原始数据
            field_mappings: 字段映射关系
            
        Returns:
            dict: 标准化后的数据
        """
        if not field_mappings:
            return data
        
        normalized_data = {}
        for old_key, new_key in field_mappings.items():
            if old_key in data:
                normalized_data[new_key] = data[old_key]
        
        # 保留未映射的字段
        for key, value in data.items():
            if key not in field_mappings and key not in normalized_data:
                normalized_data[key] = value
        
        return normalized_data
    
    @staticmethod
    def extract_nested_value(data: dict, path: str, default: Any = None) -> Any:
        """从嵌套字典中提取值
        
        Args:
            data: 数据字典
            path: 路径，如 'output.baseinfo.psn_name'
            default: 默认值
            
        Returns:
            Any: 提取的值
        """
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
        except (AttributeError, KeyError, TypeError):
            return default
    
    @staticmethod
    def flatten_dict(data: dict, parent_key: str = '', sep: str = '.') -> dict:
        """扁平化嵌套字典
        
        Args:
            data: 嵌套字典
            parent_key: 父键名
            sep: 分隔符
            
        Returns:
            dict: 扁平化后的字典
        """
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(DataHelper.flatten_dict(value, new_key, sep).items())
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(DataHelper.flatten_dict(item, f"{new_key}[{i}]", sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """安全的JSON解析
        
        Args:
            json_str: JSON字符串
            default: 解析失败时的默认值
            
        Returns:
            Any: 解析结果
        """
        if not json_str:
            return default
        
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(data: Any, default: str = '{}') -> str:
        """安全的JSON序列化
        
        Args:
            data: 要序列化的数据
            default: 序列化失败时的默认值
            
        Returns:
            str: JSON字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return default
    
    # 医保业务专用方法
    
    @staticmethod
    def generate_message_id() -> str:
        """生成医保接口报文ID
        
        Returns:
            str: 30位报文ID
        """
        import time
        import random
        import string
        
        # 时间戳(13位) + 随机字符(17位)
        timestamp = str(int(time.time() * 1000))
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        return timestamp + random_chars
    
    @staticmethod
    def generate_operation_id() -> str:
        """生成操作ID
        
        Returns:
            str: 唯一操作ID
        """
        import uuid
        return str(uuid.uuid4()).replace('-', '')
    
    @staticmethod
    def calculate_age_from_id_card(id_card: str) -> int:
        """从身份证号码计算年龄
        
        Args:
            id_card: 身份证号码
            
        Returns:
            int: 年龄
        """
        if not DataHelper.validate_id_card(id_card):
            return 0
        
        try:
            if len(id_card) == 18:
                birth_year = int(id_card[6:10])
                birth_month = int(id_card[10:12])
                birth_day = int(id_card[12:14])
            elif len(id_card) == 15:
                birth_year = int('19' + id_card[6:8])
                birth_month = int(id_card[8:10])
                birth_day = int(id_card[10:12])
            else:
                return 0
            
            from datetime import date
            today = date.today()
            birth_date = date(birth_year, birth_month, birth_day)
            
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            
            return max(0, age)
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def get_gender_from_id_card(id_card: str) -> str:
        """从身份证号码获取性别
        
        Args:
            id_card: 身份证号码
            
        Returns:
            str: 性别 ('1'-男, '2'-女)
        """
        if not DataHelper.validate_id_card(id_card):
            return ''
        
        try:
            if len(id_card) == 18:
                gender_digit = int(id_card[16])
            elif len(id_card) == 15:
                gender_digit = int(id_card[14])
            else:
                return ''
            
            return '1' if gender_digit % 2 == 1 else '2'
        except (ValueError, IndexError):
            return ''
    
    @staticmethod
    def format_medical_record_number(record_number: str, prefix: str = 'MR') -> str:
        """格式化病历号
        
        Args:
            record_number: 原始病历号
            prefix: 前缀
            
        Returns:
            str: 格式化后的病历号
        """
        if not record_number:
            return ''
        
        # 移除非数字字符
        clean_number = re.sub(r'[^\d]', '', str(record_number))
        if not clean_number:
            return str(record_number)
        
        # 补零到8位
        padded_number = clean_number.zfill(8)
        return f"{prefix}{padded_number}"
    
    @staticmethod
    def parse_medical_insurance_response(response_data: dict) -> dict:
        """解析医保接口通用响应格式
        
        Args:
            response_data: 响应数据
            
        Returns:
            dict: 解析后的标准格式
        """
        return {
            'success': str(response_data.get('infcode', '')).strip() == '0',
            'code': response_data.get('infcode', ''),
            'message': response_data.get('err_msg', ''),
            'warning': response_data.get('warn_msg', ''),
            'data': response_data.get('output', {}),
            'response_time': response_data.get('respond_time', ''),
            'ref_msg_id': response_data.get('inf_refmsgid', ''),
            'ca_info': response_data.get('cainfo', ''),
            'sign_type': response_data.get('signtype', '')
        }
    
    @staticmethod
    def build_standard_request(api_code: str, input_data: dict, org_config: dict) -> dict:
        """构建标准医保接口请求格式
        
        Args:
            api_code: 接口编码
            input_data: 输入数据
            org_config: 机构配置
            
        Returns:
            dict: 标准请求格式
        """
        from datetime import datetime
        
        return {
            'infno': api_code,
            'msgid': DataHelper.generate_message_id(),
            'mdtrtarea_admvs': org_config.get('mdtrtarea_admvs', ''),
            'insuplc_admdvs': org_config.get('insuplc_admdvs', ''),
            'recer_sys_code': org_config.get('recer_sys_code', '99'),
            'dev_no': org_config.get('dev_no', 'null'),
            'dev_safe_info': org_config.get('dev_safe_info', 'null'),
            'cainfo': org_config.get('cainfo', 'null'),
            'signtype': org_config.get('signtype', 'SM2'),
            'infver': org_config.get('infver', '1.0.0'),
            'opter_type': org_config.get('opter_type', '1'),
            'opter': org_config.get('opter', ''),
            'opter_name': org_config.get('opter_name', ''),
            'inf_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fixmedins_code': org_config.get('fixmedins_code', ''),
            'fixmedins_name': org_config.get('fixmedins_name', ''),
            'sign_no': org_config.get('sign_no', 'null'),
            'input': input_data
        }
    
    @staticmethod
    def mask_sensitive_data(data: dict, sensitive_fields: List[str] = None) -> dict:
        """脱敏敏感数据
        
        Args:
            data: 原始数据
            sensitive_fields: 敏感字段列表
            
        Returns:
            dict: 脱敏后的数据
        """
        if sensitive_fields is None:
            sensitive_fields = [
                'certno', 'id_card', 'psn_no', 'tel', 'phone', 
                'addr', 'address', 'card_sn', 'app_secret'
            ]
        
        masked_data = data.copy()
        
        def mask_value(value: str) -> str:
            if not value or len(value) <= 4:
                return '*' * len(value) if value else ''
            return value[:2] + '*' * (len(value) - 4) + value[-2:]
        
        def mask_dict(d: dict) -> dict:
            result = {}
            for key, value in d.items():
                if key.lower() in [field.lower() for field in sensitive_fields]:
                    if isinstance(value, str):
                        result[key] = mask_value(value)
                    else:
                        result[key] = '***'
                elif isinstance(value, dict):
                    result[key] = mask_dict(value)
                elif isinstance(value, list):
                    result[key] = [mask_dict(item) if isinstance(item, dict) else item for item in value]
                else:
                    result[key] = value
            return result
        
        return mask_dict(masked_data)
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[str]) -> Dict[str, List[str]]:
        """验证必填字段
        
        Args:
            data: 数据字典
            required_fields: 必填字段列表
            
        Returns:
            Dict[str, List[str]]: 验证结果，包含missing和empty字段
        """
        result = {
            'missing': [],  # 缺失的字段
            'empty': []     # 空值的字段
        }
        
        for field in required_fields:
            if field not in data:
                result['missing'].append(field)
            elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                result['empty'].append(field)
        
        return result
    
    @staticmethod
    def clean_data_for_logging(data: dict, max_length: int = 1000) -> dict:
        """清理数据用于日志记录
        
        Args:
            data: 原始数据
            max_length: 最大长度限制
            
        Returns:
            dict: 清理后的数据
        """
        # 先脱敏
        cleaned_data = DataHelper.mask_sensitive_data(data)
        
        # 转换为JSON字符串并检查长度
        json_str = DataHelper.safe_json_dumps(cleaned_data)
        
        if len(json_str) > max_length:
            # 如果太长，只保留关键信息
            key_fields = ['infno', 'msgid', 'infcode', 'err_msg', 'psn_name', 'fixmedins_code']
            simplified_data = {}
            
            def extract_key_fields(d: dict, prefix: str = '') -> None:
                for key, value in d.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if key in key_fields or full_key in key_fields:
                        simplified_data[full_key] = value
                    elif isinstance(value, dict):
                        extract_key_fields(value, full_key)
            
            extract_key_fields(cleaned_data)
            simplified_data['_truncated'] = True
            simplified_data['_original_length'] = len(json_str)
            
            return simplified_data
        
        return cleaned_data
    
    # 私有辅助方法
    
    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        """安全转换为整数"""
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """格式化日期"""
        if not date_str:
            return ''
        
        try:
            # 尝试多种日期格式
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(str(date_str).strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return str(date_str)
        except:
            return str(date_str)
    
    @staticmethod
    def _format_datetime(datetime_str: str, output_format: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化日期时间"""
        if not datetime_str:
            return ''
        
        try:
            # 尝试多种日期时间格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y%m%d%H%M%S',
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y%m%d'
            ]
            
            for fmt in formats:
                try:
                    dt_obj = datetime.strptime(str(datetime_str).strip(), fmt)
                    return dt_obj.strftime(output_format)
                except ValueError:
                    continue
            return str(datetime_str)
        except:
            return str(datetime_str)
    
    @staticmethod
    def _format_gender(gender_code: str) -> str:
        """格式化性别"""
        gender_map = {
            '1': '男',
            '2': '女',
            'M': '男',
            'F': '女',
            '男': '男',
            '女': '女'
        }
        return gender_map.get(str(gender_code).strip(), str(gender_code))
    
    @staticmethod
    def _get_insurance_type_name(insurance_type: str) -> str:
        """获取险种类型名称"""
        type_map = {
            '310': '职工基本医疗保险',
            '320': '城乡居民基本医疗保险',
            '330': '公务员医疗补助',
            '340': '新农合',
            '350': '城镇居民医疗保险',
            '390': '其他医疗保险'
        }
        return type_map.get(str(insurance_type).strip(), str(insurance_type))
    
    @staticmethod
    def _validate_id_card_checksum(id_card: str) -> bool:
        """验证18位身份证校验码
        
        Args:
            id_card: 18位身份证号码
            
        Returns:
            bool: 校验码是否正确
        """
        if len(id_card) != 18:
            return False
        
        # 权重因子
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码对应表
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        try:
            # 计算前17位的加权和
            sum_value = 0
            for i in range(17):
                sum_value += int(id_card[i]) * weights[i]
            
            # 计算校验码
            remainder = sum_value % 11
            expected_check_code = check_codes[remainder]
            
            # 比较校验码（不区分大小写）
            return id_card[17].upper() == expected_check_code.upper()
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def _get_insurance_status_name(status_code: str) -> str:
        """获取参保状态名称"""
        status_map = {
            '1': '正常参保',
            '2': '暂停参保',
            '3': '终止参保',
            '4': '转移',
            '9': '其他'
        }
        return status_map.get(str(status_code).strip(), str(status_code))
    
    @staticmethod
    def _get_identity_type_name(identity_type: str) -> str:
        """获取身份类型名称"""
        type_map = {
            '1': '普通参保人员',
            '2': '离休人员',
            '3': '退休人员',
            '4': '在职人员',
            '5': '残疾人',
            '6': '低保人员',
            '7': '特困人员',
            '8': '建档立卡贫困人口',
            '9': '其他'
        }
        return type_map.get(str(identity_type).strip(), str(identity_type))
    
    @staticmethod
    def _validate_id_card_checksum(id_card: str) -> bool:
        """验证18位身份证校验码"""
        if len(id_card) != 18:
            return False
        
        try:
            # 权重因子
            weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
            # 校验码对应表
            check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
            
            # 计算校验码
            sum_value = 0
            for i in range(17):
                sum_value += int(id_card[i]) * weights[i]
            
            check_index = sum_value % 11
            expected_check_code = check_codes[check_index]
            
            return id_card[17].upper() == expected_check_code
        except (ValueError, IndexError):
            return False