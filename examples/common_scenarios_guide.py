#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK常见场景实现指南

本指南提供了医保接口SDK在实际业务中的常见使用场景和实现方案，包括：
- 患者就诊流程
- 门诊结算流程
- 住院管理流程
- 药品管理流程
- 异常处理场景
- 性能优化场景

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 添加SDK路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from medical_insurance_sdk import MedicalInsuranceClient, DataHelper
from medical_insurance_sdk.exceptions import (
    ValidationException, 
    NetworkException, 
    BusinessException
)


class PatientStatus(Enum):
    """患者状态枚举"""
    REGISTERED = "registered"      # 已登记
    CHECKED_IN = "checked_in"      # 已签到
    DIAGNOSED = "diagnosed"        # 已诊断
    SETTLED = "settled"           # 已结算
    DISCHARGED = "discharged"     # 已出院


@dataclass
class PatientInfo:
    """患者信息"""
    psn_no: str                   # 人员编号
    psn_name: str                 # 姓名
    certno: str                   # 身份证号
    gend: str                     # 性别
    brdy: str                     # 出生日期
    tel: str                      # 电话
    addr: str                     # 地址
    insurance_info: List[Dict]    # 参保信息
    status: PatientStatus = PatientStatus.REGISTERED


@dataclass
class MedicalVisit:
    """就医记录"""
    mdtrt_id: str                 # 就医登记号
    patient_info: PatientInfo     # 患者信息
    visit_type: str               # 就诊类型 (门诊/住院)
    dept_code: str                # 科室编码
    dept_name: str                # 科室名称
    doctor_code: str              # 医生编码
    doctor_name: str              # 医生姓名
    visit_time: datetime          # 就诊时间
    diagnosis: List[str] = None   # 诊断信息
    prescriptions: List[Dict] = None  # 处方信息
    charges: List[Dict] = None    # 费用信息
    settlement_info: Dict = None  # 结算信息


class MedicalInsuranceScenarios:
    """医保接口常见场景实现"""
    
    def __init__(self, org_code: str = "H43010000001"):
        """
        初始化场景处理器
        
        Args:
            org_code: 机构编码
        """
        self.client = MedicalInsuranceClient()
        self.org_code = org_code
        
    def scenario_01_patient_registration_flow(self) -> PatientInfo:
        """
        场景01: 患者登记流程
        
        完整的患者登记流程，包括：
        1. 患者信息验证
        2. 医保信息查询
        3. 参保状态检查
        4. 登记信息保存
        
        Returns:
            PatientInfo: 患者信息对象
        """
        print("\n" + "="*60)
        print("场景01: 患者登记流程")
        print("="*60)
        
        # 步骤1: 收集患者基本信息
        patient_data = {
            "certno": "430123199001011234",
            "psn_name": "张三",
            "tel": "13800138000"
        }
        
        print(f"步骤1: 收集患者信息 - {patient_data['psn_name']}")
        
        try:
            # 步骤2: 调用1101接口查询患者医保信息
            print("步骤2: 查询患者医保信息...")
            
            query_data = {
                "mdtrt_cert_type": "02",  # 身份证
                "mdtrt_cert_no": patient_data["certno"],
                "psn_cert_type": "01",
                "certno": patient_data["certno"],
                "psn_name": patient_data["psn_name"]
            }
            
            result = self.client.call_interface(
                api_code="1101",
                input_data=query_data,
                org_code=self.org_code
            )
            
            if not result.get('success'):
                raise BusinessException(f"患者医保信息查询失败: {result.get('error_message')}")
            
            # 步骤3: 解析患者信息
            person_data = result.get('data', {})
            insurance_info = person_data.get('insurance_info', [])
            
            print(f"✓ 查询成功 - 姓名: {person_data.get('person_name')}")
            print(f"  人员编号: {person_data.get('person_id')}")
            print(f"  参保险种数: {len(insurance_info)}")
            
            # 步骤4: 检查参保状态
            print("步骤3: 检查参保状态...")
            
            active_insurance = [ins for ins in insurance_info if ins.get('status') == '1']
            if not active_insurance:
                raise BusinessException("患者无有效参保信息")
            
            print(f"✓ 有效参保险种: {len(active_insurance)}")
            for ins in active_insurance:
                print(f"  - 险种: {ins.get('type')}, 余额: ¥{ins.get('balance', 0)}")
            
            # 步骤5: 创建患者信息对象
            patient_info = PatientInfo(
                psn_no=person_data.get('person_id', ''),
                psn_name=person_data.get('person_name', ''),
                certno=person_data.get('id_card', ''),
                gend=person_data.get('gender', ''),
                brdy=person_data.get('birth_date', ''),
                tel=patient_data.get('tel', ''),
                addr=person_data.get('address', ''),
                insurance_info=insurance_info,
                status=PatientStatus.REGISTERED
            )
            
            print("✓ 患者登记完成")
            return patient_info
            
        except Exception as e:
            print(f"✗ 患者登记失败: {str(e)}")
            raise

    def scenario_02_outpatient_visit_flow(self, patient_info: PatientInfo) -> MedicalVisit:
        """
        场景02: 门诊就诊流程
        
        完整的门诊就诊流程，包括：
        1. 门诊登记
        2. 科室分配
        3. 医生诊断
        4. 处方开具
        
        Args:
            patient_info: 患者信息
            
        Returns:
            MedicalVisit: 就医记录
        """
        print("\n" + "="*60)
        print("场景02: 门诊就诊流程")
        print("="*60)
        
        # 步骤1: 生成就医登记号
        mdtrt_id = f"{self.org_code}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"步骤1: 生成就医登记号 - {mdtrt_id}")
        
        # 步骤2: 门诊登记 (模拟调用2001接口)
        print("步骤2: 门诊登记...")
        
        try:
            # 这里应该调用2001门诊登记接口，此处模拟
            registration_data = {
                "psn_no": patient_info.psn_no,
                "mdtrt_id": mdtrt_id,
                "med_type": "11",  # 门诊
                "medfee_sumamt": "0",  # 初始费用为0
                "psn_setlway": "01"    # 个人结算方式
            }
            
            print("✓ 门诊登记成功")
            
            # 步骤3: 创建就医记录
            medical_visit = MedicalVisit(
                mdtrt_id=mdtrt_id,
                patient_info=patient_info,
                visit_type="outpatient",
                dept_code="001",
                dept_name="内科",
                doctor_code="DOC001",
                doctor_name="李医生",
                visit_time=datetime.now()
            )
            
            # 步骤4: 模拟诊断过程
            print("步骤3: 医生诊断...")
            medical_visit.diagnosis = [
                "感冒 (J00.900)",
                "咳嗽 (R05.x00)"
            ]
            
            # 步骤5: 模拟开具处方
            print("步骤4: 开具处方...")
            medical_visit.prescriptions = [
                {
                    "drug_code": "A01AA01",
                    "drug_name": "阿莫西林胶囊",
                    "spec": "0.25g*24粒",
                    "quantity": 2,
                    "unit_price": 15.50,
                    "total_price": 31.00
                },
                {
                    "drug_code": "R05CB01",
                    "drug_name": "复方甘草片",
                    "spec": "100片",
                    "quantity": 1,
                    "unit_price": 8.80,
                    "total_price": 8.80
                }
            ]
            
            # 计算总费用
            total_amount = sum(item['total_price'] for item in medical_visit.prescriptions)
            medical_visit.charges = [{
                "charge_type": "药品费",
                "amount": total_amount
            }]
            
            print(f"✓ 处方开具完成，总费用: ¥{total_amount}")
            print("✓ 门诊就诊流程完成")
            
            return medical_visit
            
        except Exception as e:
            print(f"✗ 门诊就诊流程失败: {str(e)}")
            raise

    def scenario_03_outpatient_settlement_flow(self, medical_visit: MedicalVisit) -> Dict:
        """
        场景03: 门诊结算流程
        
        完整的门诊结算流程，包括：
        1. 费用明细上传
        2. 结算预算
        3. 结算确认
        4. 结算撤销（如需要）
        
        Args:
            medical_visit: 就医记录
            
        Returns:
            Dict: 结算结果
        """
        print("\n" + "="*60)
        print("场景03: 门诊结算流程")
        print("="*60)
        
        try:
            # 步骤1: 费用明细上传 (模拟调用2204接口)
            print("步骤1: 上传费用明细...")
            
            charge_details = []
            for idx, prescription in enumerate(medical_visit.prescriptions, 1):
                charge_details.append({
                    "feedetl_sn": f"{medical_visit.mdtrt_id}_{idx:03d}",
                    "med_chrgitm": prescription['drug_code'],
                    "med_chrgitm_name": prescription['drug_name'],
                    "cnt": prescription['quantity'],
                    "pric": prescription['unit_price'],
                    "det_item_fee_sumamt": prescription['total_price']
                })
            
            print(f"✓ 上传{len(charge_details)}条费用明细")
            
            # 步骤2: 结算预算 (模拟调用2206接口)
            print("步骤2: 结算预算...")
            
            total_amount = sum(item['det_item_fee_sumamt'] for item in charge_details)
            
            # 模拟预算结果
            pre_settlement = {
                "total_amount": total_amount,
                "insurance_amount": total_amount * 0.7,  # 医保支付70%
                "personal_amount": total_amount * 0.3    # 个人支付30%
            }
            
            print(f"✓ 预算完成 - 总费用: ¥{pre_settlement['total_amount']}")
            print(f"  医保支付: ¥{pre_settlement['insurance_amount']}")
            print(f"  个人支付: ¥{pre_settlement['personal_amount']}")
            
            # 步骤3: 结算确认 (调用2201接口)
            print("步骤3: 结算确认...")
            
            settlement_data = {
                "mdtrt_id": medical_visit.mdtrt_id,
                "psn_no": medical_visit.patient_info.psn_no,
                "chrg_bchno": f"BATCH_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "acct_used_flag": "1",  # 使用个人账户
                "insutype": "310",      # 职工基本医疗保险
                "invono": f"INV_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            result = self.client.call_interface(
                api_code="2201",
                input_data=settlement_data,
                org_code=self.org_code
            )
            
            if result.get('success'):
                settlement_info = result.get('data', {})
                print("✓ 结算成功!")
                print(f"  结算单号: {settlement_info.get('settlement_id', 'N/A')}")
                print(f"  实际总费用: ¥{settlement_info.get('total_amount', 0)}")
                print(f"  实际医保支付: ¥{settlement_info.get('insurance_amount', 0)}")
                print(f"  实际个人支付: ¥{settlement_info.get('personal_amount', 0)}")
                
                # 更新就医记录
                medical_visit.settlement_info = settlement_info
                medical_visit.patient_info.status = PatientStatus.SETTLED
                
                return settlement_info
            else:
                raise BusinessException(f"结算失败: {result.get('error_message')}")
                
        except Exception as e:
            print(f"✗ 门诊结算流程失败: {str(e)}")
            raise

    def scenario_04_prescription_management_flow(self) -> List[Dict]:
        """
        场景04: 处方管理流程
        
        处方管理相关流程，包括：
        1. 药品目录查询
        2. 处方审核
        3. 处方流转
        4. 药品配送
        
        Returns:
            List[Dict]: 处方列表
        """
        print("\n" + "="*60)
        print("场景04: 处方管理流程")
        print("="*60)
        
        try:
            # 步骤1: 查询药品目录 (模拟调用1301接口)
            print("步骤1: 查询药品目录...")
            
            # 模拟药品目录数据
            drug_catalog = [
                {
                    "med_list_codg": "A01AA01",
                    "med_list_name": "阿莫西林胶囊",
                    "dosform": "胶囊剂",
                    "spec": "0.25g*24粒",
                    "pacmatl": "铝塑包装",
                    "minuseunit": "盒",
                    "pric": 15.50,
                    "wubi": "AMXL",
                    "pinyin": "AMXLJN"
                },
                {
                    "med_list_codg": "R05CB01",
                    "med_list_name": "复方甘草片",
                    "dosform": "片剂",
                    "spec": "100片",
                    "pacmatl": "瓶装",
                    "minuseunit": "瓶",
                    "pric": 8.80,
                    "wubi": "FFGCP",
                    "pinyin": "FFGCP"
                }
            ]
            
            print(f"✓ 查询到{len(drug_catalog)}种药品")
            
            # 步骤2: 处方开具
            print("步骤2: 开具处方...")
            
            prescriptions = []
            for drug in drug_catalog:
                prescription = {
                    "prescription_id": f"RX_{datetime.now().strftime('%Y%m%d%H%M%S')}_{drug['med_list_codg']}",
                    "drug_info": drug,
                    "quantity": 2 if drug['med_list_codg'] == 'A01AA01' else 1,
                    "usage": "口服",
                    "frequency": "每日3次" if drug['med_list_codg'] == 'A01AA01' else "每日2次",
                    "duration": "7天",
                    "doctor_advice": "饭后服用",
                    "status": "待审核"
                }
                prescriptions.append(prescription)
            
            print(f"✓ 开具{len(prescriptions)}张处方")
            
            # 步骤3: 处方审核
            print("步骤3: 处方审核...")
            
            for prescription in prescriptions:
                # 模拟审核逻辑
                drug_name = prescription['drug_info']['med_list_name']
                
                # 检查药品相互作用
                if "阿莫西林" in drug_name:
                    print(f"  审核 {drug_name}: 检查过敏史...")
                
                # 检查用药剂量
                if prescription['quantity'] > 5:
                    print(f"  审核 {drug_name}: 用药剂量过大，需要调整")
                    prescription['quantity'] = 3
                
                prescription['status'] = "审核通过"
                prescription['audit_time'] = datetime.now().isoformat()
                prescription['auditor'] = "药师001"
            
            print("✓ 处方审核完成")
            
            # 步骤4: 处方流转 (模拟电子处方流转)
            print("步骤4: 处方流转...")
            
            for prescription in prescriptions:
                prescription['flow_status'] = "已流转"
                prescription['flow_time'] = datetime.now().isoformat()
                prescription['target_pharmacy'] = "中心药房"
            
            print("✓ 处方流转完成")
            
            # 步骤5: 配药准备
            print("步骤5: 配药准备...")
            
            total_cost = 0
            for prescription in prescriptions:
                cost = prescription['drug_info']['pric'] * prescription['quantity']
                prescription['total_cost'] = cost
                total_cost += cost
                prescription['status'] = "配药中"
            
            print(f"✓ 配药准备完成，总费用: ¥{total_cost}")
            
            return prescriptions
            
        except Exception as e:
            print(f"✗ 处方管理流程失败: {str(e)}")
            raise

    def scenario_05_error_recovery_flow(self):
        """
        场景05: 异常恢复流程
        
        处理各种异常情况的恢复流程，包括：
        1. 网络异常恢复
        2. 业务异常处理
        3. 数据不一致修复
        4. 系统故障恢复
        """
        print("\n" + "="*60)
        print("场景05: 异常恢复流程")
        print("="*60)
        
        # 测试场景1: 网络超时重试
        print("测试场景1: 网络超时重试...")
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                print(f"  尝试第 {attempt + 1} 次调用...")
                
                # 模拟可能超时的调用
                query_data = {
                    "mdtrt_cert_type": "02",
                    "mdtrt_cert_no": "430123199001011234",
                    "psn_cert_type": "01",
                    "certno": "430123199001011234",
                    "psn_name": "张三"
                }
                
                result = self.client.call_interface(
                    api_code="1101",
                    input_data=query_data,
                    org_code=self.org_code
                )
                
                if result.get('success'):
                    print("  ✓ 调用成功")
                    break
                else:
                    raise NetworkException("模拟网络异常")
                    
            except NetworkException as e:
                print(f"  ✗ 网络异常: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"  等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    print("  ✗ 重试次数已用完，调用失败")
        
        # 测试场景2: 业务异常处理
        print("\n测试场景2: 业务异常处理...")
        
        try:
            # 模拟业务异常：无效的身份证号
            invalid_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "invalid_id_number",
                "psn_cert_type": "01",
                "certno": "invalid_id_number",
                "psn_name": "测试用户"
            }
            
            result = self.client.call_interface(
                api_code="1101",
                input_data=invalid_data,
                org_code=self.org_code
            )
            
        except ValidationException as e:
            print("  ✓ 捕获到验证异常，进行数据修正...")
            
            # 数据修正
            corrected_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": "430123199001011234",
                "psn_cert_type": "01",
                "certno": "430123199001011234",
                "psn_name": "张三"
            }
            
            print("  ✓ 使用修正后的数据重新调用")
            
        except BusinessException as e:
            print(f"  ✓ 捕获到业务异常: {str(e)}")
            print("  ✓ 记录异常日志，通知相关人员处理")
        
        # 测试场景3: 数据一致性检查
        print("\n测试场景3: 数据一致性检查...")
        
        # 模拟检查结算数据一致性
        settlement_records = [
            {"id": "001", "amount": 100.00, "status": "completed"},
            {"id": "002", "amount": 200.00, "status": "pending"},
            {"id": "003", "amount": 150.00, "status": "failed"}
        ]
        
        print("  检查结算记录一致性...")
        
        for record in settlement_records:
            if record['status'] == 'pending':
                print(f"  发现待处理记录: {record['id']}")
                # 模拟重新处理
                record['status'] = 'completed'
                print(f"  ✓ 记录 {record['id']} 已重新处理完成")
            elif record['status'] == 'failed':
                print(f"  发现失败记录: {record['id']}")
                # 模拟错误修复
                record['status'] = 'completed'
                print(f"  ✓ 记录 {record['id']} 已修复完成")
        
        print("  ✓ 数据一致性检查完成")
        
        # 测试场景4: 系统健康检查
        print("\n测试场景4: 系统健康检查...")
        
        try:
            health_status = self.client.get_system_status()
            
            if health_status.get('status') == 'healthy':
                print("  ✓ 系统状态正常")
            else:
                print("  ⚠ 系统状态异常，启动恢复流程...")
                
                # 模拟恢复操作
                print("  - 重启连接池...")
                print("  - 清理缓存...")
                print("  - 重新加载配置...")
                print("  ✓ 系统恢复完成")
                
        except Exception as e:
            print(f"  ✗ 健康检查失败: {str(e)}")
            print("  启动紧急恢复模式...")

    def scenario_06_performance_optimization_flow(self):
        """
        场景06: 性能优化流程
        
        性能优化相关场景，包括：
        1. 批量处理优化
        2. 缓存策略优化
        3. 连接池优化
        4. 异步处理优化
        """
        print("\n" + "="*60)
        print("场景06: 性能优化流程")
        print("="*60)
        
        # 优化场景1: 批量处理
        print("优化场景1: 批量处理...")
        
        # 模拟需要查询的患者列表
        patient_list = [
            {"certno": f"43012319900101{i:04d}", "psn_name": f"患者{i:03d}"}
            for i in range(1, 21)  # 20个患者
        ]
        
        print(f"需要查询 {len(patient_list)} 个患者信息")
        
        # 方式1: 逐个查询（低效）
        start_time = time.time()
        sequential_results = []
        
        print("  方式1: 逐个查询...")
        for i, patient in enumerate(patient_list[:5], 1):  # 只测试前5个
            try:
                query_data = {
                    "mdtrt_cert_type": "02",
                    "mdtrt_cert_no": patient["certno"],
                    "psn_cert_type": "01",
                    "certno": patient["certno"],
                    "psn_name": patient["psn_name"]
                }
                
                result = self.client.call_interface(
                    api_code="1101",
                    input_data=query_data,
                    org_code=self.org_code
                )
                
                sequential_results.append(result)
                
            except Exception as e:
                print(f"    患者{i}查询失败: {str(e)}")
        
        sequential_time = time.time() - start_time
        print(f"  逐个查询耗时: {sequential_time:.2f}秒")
        
        # 方式2: 批量查询（高效）
        print("  方式2: 批量查询...")
        start_time = time.time()
        
        # 模拟批量查询实现
        batch_size = 10
        batch_results = []
        
        for i in range(0, len(patient_list), batch_size):
            batch = patient_list[i:i + batch_size]
            print(f"    处理批次 {i//batch_size + 1}: {len(batch)} 个患者")
            
            # 这里应该调用批量查询接口，此处模拟
            batch_result = {
                'success': True,
                'data': [{'person_name': p['psn_name']} for p in batch]
            }
            batch_results.append(batch_result)
        
        batch_time = time.time() - start_time
        print(f"  批量查询耗时: {batch_time:.2f}秒")
        print(f"  性能提升: {(sequential_time/batch_time if batch_time > 0 else 0):.1f}倍")
        
        # 优化场景2: 缓存策略
        print("\n优化场景2: 缓存策略...")
        
        # 模拟缓存使用
        cache_stats = self.client.get_cache_statistics()
        print(f"  当前缓存命中率: {cache_stats.get('hit_rate', 0):.2%}")
        print(f"  缓存大小: {cache_stats.get('cache_size', 0)} 项")
        
        # 模拟热点数据预加载
        print("  预加载热点数据...")
        hot_interfaces = ["1101", "2201", "1301"]
        for api_code in hot_interfaces:
            try:
                config = self.client.get_interface_config(api_code)
                print(f"    预加载接口配置: {api_code} - {config.get('api_name', 'N/A')}")
            except Exception as e:
                print(f"    预加载失败: {api_code} - {str(e)}")
        
        # 优化场景3: 连接池优化
        print("\n优化场景3: 连接池优化...")
        
        pool_stats = self.client.get_connection_pool_stats()
        print(f"  活跃连接: {pool_stats.get('active_connections', 0)}")
        print(f"  空闲连接: {pool_stats.get('idle_connections', 0)}")
        print(f"  最大连接数: {pool_stats.get('max_connections', 0)}")
        
        # 连接池健康检查
        if pool_stats.get('active_connections', 0) > pool_stats.get('max_connections', 0) * 0.8:
            print("  ⚠ 连接池使用率过高，建议增加连接数")
        else:
            print("  ✓ 连接池状态正常")
        
        # 优化场景4: 异步处理
        print("\n优化场景4: 异步处理...")
        
        # 模拟异步任务提交
        async_tasks = []
        for i in range(3):
            query_data = {
                "mdtrt_cert_type": "02",
                "mdtrt_cert_no": f"43012319900101{i:04d}",
                "psn_cert_type": "01",
                "certno": f"43012319900101{i:04d}",
                "psn_name": f"异步患者{i:03d}"
            }
            
            try:
                task_id = self.client.call_interface_async(
                    api_code="1101",
                    input_data=query_data,
                    org_code=self.org_code
                )
                async_tasks.append(task_id)
                print(f"  提交异步任务: {task_id}")
            except Exception as e:
                print(f"  异步任务提交失败: {str(e)}")
        
        # 等待异步任务完成
        print("  等待异步任务完成...")
        completed_tasks = 0
        
        for task_id in async_tasks:
            try:
                status = self.client.get_task_status(task_id)
                if status.get('status') == 'completed':
                    completed_tasks += 1
                    print(f"    任务 {task_id} 完成")
            except Exception as e:
                print(f"    任务 {task_id} 状态查询失败: {str(e)}")
        
        print(f"  异步任务完成率: {completed_tasks}/{len(async_tasks)}")

    def run_all_scenarios(self):
        """运行所有场景"""
        print("医保接口SDK常见场景实现指南")
        print("="*80)
        
        try:
            # 场景01: 患者登记
            patient_info = self.scenario_01_patient_registration_flow()
            
            # 场景02: 门诊就诊
            medical_visit = self.scenario_02_outpatient_visit_flow(patient_info)
            
            # 场景03: 门诊结算
            settlement_result = self.scenario_03_outpatient_settlement_flow(medical_visit)
            
            # 场景04: 处方管理
            prescriptions = self.scenario_04_prescription_management_flow()
            
            # 场景05: 异常恢复
            self.scenario_05_error_recovery_flow()
            
            # 场景06: 性能优化
            self.scenario_06_performance_optimization_flow()
            
        except Exception as e:
            print(f"场景执行异常: {str(e)}")
        
        print("\n" + "="*80)
        print("所有场景演示完成！")
        print("\n场景总结:")
        print("1. 患者登记流程 - 完整的患者信息查询和验证")
        print("2. 门诊就诊流程 - 从登记到诊断的完整流程")
        print("3. 门诊结算流程 - 费用计算和医保结算")
        print("4. 处方管理流程 - 药品查询、处方审核和流转")
        print("5. 异常恢复流程 - 各种异常情况的处理方案")
        print("6. 性能优化流程 - 提升系统性能的最佳实践")
        print("\n这些场景涵盖了医保接口SDK在实际业务中的主要应用场景。")


def main():
    """主函数"""
    scenarios = MedicalInsuranceScenarios()
    scenarios.run_all_scenarios()


if __name__ == "__main__":
    main()