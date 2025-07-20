# 医保接口SDK完整API规范文档（完善版）

## 一、API基础信息

### 1.1 基本信息
- **API版本**: v1.0.0
- **协议**: HTTP/HTTPS
- **编码**: UTF-8
- **数据格式**: JSON
- **Base URL**: `http://localhost:8000/api/v1/medical-insurance/`
- **支持接口数量**: 206个医保接口全覆盖
- **接口分类**: 11大业务分类

### 1.2 认证方式
- **认证类型**: API Key认证 + JWT Token（可选）
- **请求头**:
  - `Content-Type: application/json`
  - `X-API-Key: [your_api_key]`
  - `Authorization: Bearer [jwt_token]` (可选)
  - `X-Institution-Code: [institution_code]` (机构代码)

### 1.3 通用响应格式
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "error": null,
  "error_code": null,
  "timestamp": "2025-07-14T10:30:00Z",
  "request_id": "REQ20250714001",
  "version": "1.0.0",
  "interface_info": {
    "interface_type": "patient_query",
    "infno": "1101",
    "category": "基础信息服务"
  }
}
```

### 1.4 分页响应格式
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "total_pages": 50,
    "has_next": true,
    "has_previous": false
  },
  "message": "查询成功"
}
```

## 二、206个医保接口完整API规范

### 2.1 基础信息服务接口 (31个接口)

#### 2.1.1 人员信息管理接口 (1个)

##### 【1101】人员基本信息获取
```yaml
POST /api/v1/medical-insurance/basic/person-info
```

**请求参数**:
```json
{
  "mdtrt_cert_type": "01",        // 就诊凭证类型
  "mdtrt_cert_no": "43028119900101001", // 就诊凭证编号
  "psn_cert_type": "01",          // 人员证件类型
  "certno": "43028119900101001",  // 证件号码
  "psn_name": "张三",             // 人员姓名（可选）
  "need_baseinfo": true,          // 是否需要基本信息
  "need_insuinfo": true           // 是否需要参保信息
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "baseinfo": {
      "psn_no": "43000030281000128715",
      "psn_name": "张三",
      "gend": "1",
      "brdy": "1990-01-01 00:00:00",
      "age": 35,
      "naty": "01",
      "poolarea": "4302",
      "emp_name": "湘潭市第一人民医院",
      "tel": "13800138000"
    },
    "insuinfo": [
      {
        "balc": 1500.00,
        "insutype": "310",
        "psn_insu_stas": "1",
        "psn_type": "1101",
        "cvlserv_flag": "0"
      }
    ]
  },
  "interface_info": {
    "interface_type": "person_info",
    "infno": "1101",
    "category": "基础信息服务"
  }
}
```

#### 2.1.2 机构信息管理接口 (1个)

##### 【1201】医药机构信息获取
```yaml
POST /api/v1/medical-insurance/basic/institution-info
```

**请求参数**:
```json
{
  "fixmedins_code": "H43028110001",  // 定点医药机构编号
  "fixmedins_name": "",              // 定点医药机构名称（可选）
  "query_type": "code"               // 查询类型：code-按编号，name-按名称
}
```

#### 2.1.3 目录数据下载接口 (28个)

##### 【1301】西药中成药目录下载
```yaml
POST /api/v1/medical-insurance/catalog/drug-download
```

**请求参数**:
```json
{
  "ver": "1.0.0",                   // 版本号
  "download_type": "full",          // 下载类型：full-全量，incr-增量
  "last_update_time": ""            // 上次更新时间（增量下载时使用）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "file_info": {
      "file_qury_no": "FQ20250714001",
      "filename": "1301_20250714.zip",
      "dld_end_time": "2025-07-15",
      "data_cnt": 15000,
      "file_size": 52428800,
      "file_url": "/api/v1/files/download/FQ20250714001"
    },
    "preview_data": [
      {
        "list_id": "A01010001",
        "list_name": "阿司匹林片",
        "list_type": "201",
        "med_list_codg": "A01010001",
        "med_list_name": "阿司匹林片",
        "dosform": "1",
        "spec": "100mg*100片",
        "pacspec": "瓶装",
        "memo": ""
      }
    ]
  }
}
```

##### 【1302】中药饮片目录下载
```yaml
POST /api/v1/medical-insurance/catalog/tcm-download
```

##### 【1303-1327】其他目录下载接口
- 【1303】医疗机构制剂目录下载
- 【1304】民族药品目录查询  
- 【1305】医疗服务项目目录下载
- 【1306】医用耗材目录下载
- 【1306A】27位医用耗材目录下载
- 【1307】疾病与诊断目录下载
- 【1308】手术操作目录下载
- 【1309】门诊慢特病种目录下载
- 【1310】按病种付费病种目录下载
- 【1311】日间手术治疗病种目录下载
- 【1312】医保目录信息下载
- 【1313】肿瘤形态学目录下载
- 【1314】中医疾病目录下载
- 【1315】中医证候目录下载
- 【1316】医疗目录与医保目录匹配信息查询
- 【1317】医药机构目录匹配信息查询
- 【1318】医保目录限价信息查询
- 【1319】医保目录先自付比例信息查询
- 【1320】中药配方颗粒目录下载
- 【1321】医疗服务项目（新）目录下载
- 【1322】体外诊断试剂产品信息下载
- 【1323】产品信息与注册证关联信息下载
- 【1324】检测指标信息下载
- 【1325】产品信息编码下载
- 【1326】注册证信息下载
- 【1327】分类目录下载

#### 2.1.4 字典数据管理接口 (1个)

##### 【1901】字典表下载
```yaml
POST /api/v1/medical-insurance/basic/dictionary-download
```

### 2.2 医保业务服务接口 (43个接口)

#### 2.2.1 待遇检查服务接口 (1个)

##### 【2001】人员待遇享受检查
```yaml
POST /api/v1/medical-insurance/business/benefit-check
```

**请求参数**:
```json
{
  "psn_no": "43000030281000128715",
  "check_items": ["drug_limit", "treatment_limit", "hospitalization"],
  "check_date": "2025-07-14"
}
```

#### 2.2.2 药店业务服务接口 (3个)

##### 【2101】药店预结算
```yaml
POST /api/v1/medical-insurance/business/pharmacy/pre-settle
```

##### 【2102】药店结算
```yaml
POST /api/v1/medical-insurance/business/pharmacy/settle
```

##### 【2103】药店结算撤销
```yaml
POST /api/v1/medical-insurance/business/pharmacy/settle-cancel
```

#### 2.2.3 异地就医购药服务接口 (12个)

##### 【2161-2181】异地就医购药系列接口
```yaml
# 获取人员信息
POST /api/v1/medical-insurance/business/remote/person-info

# 购药退费
POST /api/v1/medical-insurance/business/remote/refund

# 购药试算
POST /api/v1/medical-insurance/business/remote/pre-calculate

# 取消订单
POST /api/v1/medical-insurance/business/remote/cancel-order

# 订单查询
GET /api/v1/medical-insurance/business/remote/orders

# 结算信息查询
GET /api/v1/medical-insurance/business/remote/settlement-info

# 月结算申报汇总数据查询
GET /api/v1/medical-insurance/business/remote/monthly-summary

# 月结算申报业务明细数据查询  
GET /api/v1/medical-insurance/business/remote/monthly-detail

# 月结申报基金分项数据查询
GET /api/v1/medical-insurance/business/remote/fund-detail

# 药店账务明细查询
GET /api/v1/medical-insurance/business/remote/pharmacy-detail

# 药店账务汇总查询
GET /api/v1/medical-insurance/business/remote/pharmacy-summary

# 冲正交易
POST /api/v1/medical-insurance/business/remote/reversal
```

#### 2.2.4 门急诊业务服务接口 (9个)

##### 【2201-2208】门急诊系列接口
```yaml
# 门诊挂号
POST /api/v1/medical-insurance/business/outpatient/register

# 门诊挂号撤销
POST /api/v1/medical-insurance/business/outpatient/register-cancel

# 门诊就诊信息上传
POST /api/v1/medical-insurance/business/outpatient/visit-upload

# 药店门诊就诊信息上传
POST /api/v1/medical-insurance/business/outpatient/pharmacy-visit-upload

# 门诊费用明细上传
POST /api/v1/medical-insurance/business/outpatient/expense-upload

# 门诊费用明细撤销
POST /api/v1/medical-insurance/business/outpatient/expense-cancel

# 门诊预结算
POST /api/v1/medical-insurance/business/outpatient/pre-settle

# 门诊结算
POST /api/v1/medical-insurance/business/outpatient/settle

# 门诊结算撤销
POST /api/v1/medical-insurance/business/outpatient/settle-cancel
```

#### 2.2.5 住院业务服务接口 (10个)

##### 【2301-2305】住院结算服务接口
```yaml
# 住院费用明细上传
POST /api/v1/medical-insurance/business/inpatient/expense-upload

# 住院费用明细撤销
POST /api/v1/medical-insurance/business/inpatient/expense-cancel

# 住院预结算
POST /api/v1/medical-insurance/business/inpatient/pre-settle

# 住院结算
POST /api/v1/medical-insurance/business/inpatient/settle

# 住院结算撤销
POST /api/v1/medical-insurance/business/inpatient/settle-cancel
```

##### 【2401-2405】住院办理服务接口
```yaml
# 入院办理
POST /api/v1/medical-insurance/business/inpatient/admission

# 出院办理
POST /api/v1/medical-insurance/business/inpatient/discharge

# 入院信息变更
POST /api/v1/medical-insurance/business/inpatient/admission-update

# 入院撤销
POST /api/v1/medical-insurance/business/inpatient/admission-cancel

# 出院撤销
POST /api/v1/medical-insurance/business/inpatient/discharge-cancel
```

#### 2.2.6 人员备案服务接口 (7个)

##### 【2501-2507】人员备案系列接口
```yaml
# 转院备案
POST /api/v1/medical-insurance/business/record/transfer

# 转院备案撤销
POST /api/v1/medical-insurance/business/record/transfer-cancel

# 人员慢特病备案
POST /api/v1/medical-insurance/business/record/chronic-disease

# 人员慢特病备案撤销
POST /api/v1/medical-insurance/business/record/chronic-disease-cancel

# 人员定点备案
POST /api/v1/medical-insurance/business/record/designated-hospital

# 人员定点备案撤销
POST /api/v1/medical-insurance/business/record/designated-hospital-cancel

# 人员意外伤害备案
POST /api/v1/medical-insurance/business/record/accident-injury
```

#### 2.2.7 事务补偿业务接口 (1个)

##### 【2601】冲正交易
```yaml
POST /api/v1/medical-insurance/business/transaction/reversal
```

### 2.3 医药机构管理接口 (47个接口)

#### 2.3.1 明细审核管理接口 (3个)

##### 【3101-3103】明细审核系列接口
```yaml
# 明细审核分析服务
POST /api/v1/medical-insurance/institution/audit/detail-analysis

# 明细审核事中分析服务
POST /api/v1/medical-insurance/institution/audit/real-time-analysis

# 事前事中服务反馈服务
POST /api/v1/medical-insurance/institution/audit/feedback
```

#### 2.3.2 费用结算管理接口 (2个)

##### 【3201-3202】费用结算接口
```yaml
# 医药机构费用结算对总账
POST /api/v1/medical-insurance/institution/settlement/general-ledger

# 医药机构费用结算对明细账
POST /api/v1/medical-insurance/institution/settlement/detail-ledger
```

#### 2.3.3 目录对照管理接口 (2个)

##### 【3301-3302】目录对照接口
```yaml
# 目录对照上传
POST /api/v1/medical-insurance/institution/catalog/mapping-upload

# 目录对照撤销
POST /api/v1/medical-insurance/institution/catalog/mapping-cancel
```

#### 2.3.4 科室管理服务接口 (4个)

##### 【3401-3403】科室管理接口
```yaml
# 科室信息上传
POST /api/v1/medical-insurance/institution/department/upload

# 批量科室信息上传
POST /api/v1/medical-insurance/institution/department/batch-upload

# 科室信息变更
POST /api/v1/medical-insurance/institution/department/update

# 科室信息撤销
POST /api/v1/medical-insurance/institution/department/cancel
```

#### 2.3.5 进销存管理接口 (21个)

##### 【3501-3507】基础进销存操作接口
```yaml
# 商品盘存上传（单个/批量）
POST /api/v1/medical-insurance/institution/inventory/stock-count
POST /api/v1/medical-insurance/institution/inventory/stock-count-batch

# 商品库存变更（单个/批量）
POST /api/v1/medical-insurance/institution/inventory/stock-change
POST /api/v1/medical-insurance/institution/inventory/stock-change-batch

# 商品采购（单个/批量）
POST /api/v1/medical-insurance/institution/inventory/purchase
POST /api/v1/medical-insurance/institution/inventory/purchase-batch

# 商品采购退货（单个/批量）
POST /api/v1/medical-insurance/institution/inventory/purchase-return
POST /api/v1/medical-insurance/institution/inventory/purchase-return-batch

# 商品销售（单个/批量）
POST /api/v1/medical-insurance/institution/inventory/sale
POST /api/v1/medical-insurance/institution/inventory/sale-batch

# 商品销售退货（单个/批量）
POST /api/v1/medical-insurance/institution/inventory/sale-return
POST /api/v1/medical-insurance/institution/inventory/sale-return-batch

# 商品信息删除（单个/批量）
DELETE /api/v1/medical-insurance/institution/inventory/product
DELETE /api/v1/medical-insurance/institution/inventory/product-batch
```

##### 【3508-3513】进销存查询接口
```yaml
# 商品库存信息查询
GET /api/v1/medical-insurance/institution/inventory/stock-info

# 商品库存变更记录查询
GET /api/v1/medical-insurance/institution/inventory/stock-change-records

# 商品采购信息查询
GET /api/v1/medical-insurance/institution/inventory/purchase-info

# 商品销售信息查询
GET /api/v1/medical-insurance/institution/inventory/sale-info

# 入库药品追溯信息查询
GET /api/v1/medical-insurance/institution/inventory/inbound-trace

# 销售药品追溯信息查询
GET /api/v1/medical-insurance/institution/inventory/sale-trace
```

##### 【3592B】药品追溯管理接口
```yaml
# 获取虚拟药品追溯码
POST /api/v1/medical-insurance/institution/inventory/virtual-trace-code
```

#### 2.3.6 分组付费管理接口 (11个)

##### 【3601-3605,3610-3611】DRG分组付费接口
```yaml
# DRG申请退出列表查询
GET /api/v1/medical-insurance/institution/drg/exit-applications

# DRG退出申请保存
POST /api/v1/medical-insurance/institution/drg/exit-application

# DRG退出申请修改/撤销
PUT /api/v1/medical-insurance/institution/drg/exit-application
DELETE /api/v1/medical-insurance/institution/drg/exit-application

# DRG申请审核意见和预结算基金分项查询
GET /api/v1/medical-insurance/institution/drg/audit-opinion

# DRG分组结果查询
GET /api/v1/medical-insurance/institution/drg/grouping-results

# DRG分组结果统计汇总查询
GET /api/v1/medical-insurance/institution/drg/statistics-summary

# DRG分组结果统计查询
GET /api/v1/medical-insurance/institution/drg/statistics
```

##### 【3606,3608-3609】DIP分组付费接口
```yaml
# DIP分组结果查询
GET /api/v1/medical-insurance/institution/dip/grouping-results

# DIP分组结果统计汇总查询
GET /api/v1/medical-insurance/institution/dip/statistics-summary

# DIP分组结果统计查询
GET /api/v1/medical-insurance/institution/dip/statistics
```

##### 【3607】质控结果管理接口
```yaml
# 结算清单质控结果查询
GET /api/v1/medical-insurance/institution/quality/settlement-check-results
```

#### 2.3.7 申诉合议管理接口 (4个)

##### 【3701-3704】申诉合议接口
```yaml
# 审核申诉、扣款节点查询
GET /api/v1/medical-insurance/institution/appeal/audit-deduction-nodes

# 申诉提交
POST /api/v1/medical-insurance/institution/appeal/submit

# 申请合议提交
POST /api/v1/medical-insurance/institution/appeal/collegial-request

# 附件上传
POST /api/v1/medical-insurance/institution/appeal/attachment-upload
```

### 2.4 信息采集上传接口 (28个接口)

#### 2.4.1 医疗保障基金结算清单接口 (8个)

##### 【4101-4105】结算清单系列接口
```yaml
# 医疗保障基金结算清单信息上传
POST /api/v1/medical-insurance/upload/settlement-list

# 医疗保障基金结算清单状态修改
PUT /api/v1/medical-insurance/upload/settlement-list-status

# 医疗保障基金结算清单信息查询
GET /api/v1/medical-insurance/upload/settlement-list-info

# 医疗保障基金结算清单质控结果查询
GET /api/v1/medical-insurance/upload/settlement-list-quality

# 医疗保障基金结算清单数量统计查询
GET /api/v1/medical-insurance/upload/settlement-list-statistics
```

##### 【4261-4263】自费病人相关接口
```yaml
# 自费病人费用明细信息上传
POST /api/v1/medical-insurance/upload/self-pay-expense

# 已上传费用对账
POST /api/v1/medical-insurance/upload/expense-reconciliation

# 自费病人零报金额不符查询
GET /api/v1/medical-insurance/upload/self-pay-zero-amount-mismatch
```

#### 2.4.2 门急诊业务数据上传接口 (2个)

##### 【4301-4302】门急诊上传接口
```yaml
# 门急诊诊疗记录上传
POST /api/v1/medical-insurance/upload/outpatient-treatment-record

# 急诊留观手术及抢救信息上传
POST /api/v1/medical-insurance/upload/emergency-surgery-rescue-info
```

#### 2.4.3 住院业务数据上传接口 (3个)

##### 【4401-4402A】住院上传接口
```yaml
# 住院病案首页信息上传
POST /api/v1/medical-insurance/upload/inpatient-case-summary

# 住院医嘱记录上传
POST /api/v1/medical-insurance/upload/inpatient-medical-order

# 住院医嘱记录上传（包含医生信息）
POST /api/v1/medical-insurance/upload/inpatient-medical-order-with-doctor
```

#### 2.4.4 临床辅助业务数据上传接口 (12个)

##### 【4501-4506】临床检查检验上传接口
```yaml
# 临床检查记录上传
POST /api/v1/medical-insurance/upload/clinical-examination

# 临床检验记录上传
POST /api/v1/medical-insurance/upload/clinical-test

# 细菌培养报告记录上传
POST /api/v1/medical-insurance/upload/bacterial-culture

# 药敏记录报告记录上传
POST /api/v1/medical-insurance/upload/drug-sensitivity

# 病理检查报告记录上传
POST /api/v1/medical-insurance/upload/pathology-report

# 非结构化报告记录上传
POST /api/v1/medical-insurance/upload/unstructured-report
```

##### 【4507-4512】临床检查检验查询接口
```yaml
# 临床检查报告记录查询
GET /api/v1/medical-insurance/query/clinical-examination-report

# 临床检验报告记录查询
GET /api/v1/medical-insurance/query/clinical-test-report

# 细菌培养报告记录查询
GET /api/v1/medical-insurance/query/bacterial-culture-report

# 药敏检查报告记录查询
GET /api/v1/medical-insurance/query/drug-sensitivity-report

# 病理检查报告记录查询
GET /api/v1/medical-insurance/query/pathology-report

# 非结构化报告记录查询
GET /api/v1/medical-insurance/query/unstructured-report
```

#### 2.4.5 医疗管理业务数据上传接口 (2个)

##### 【4601-4602】医疗管理上传接口
```yaml
# 输血信息上传
POST /api/v1/medical-insurance/upload/blood-transfusion-info

# 护理操作生命体征测量记录上传
POST /api/v1/medical-insurance/upload/nursing-vital-signs
```

#### 2.4.6 电子病历上传接口 (1个)

##### 【4701】电子病历上传接口
```yaml
POST /api/v1/medical-insurance/upload/electronic-medical-record
```

**请求示例**:
```json
{
  "patient_info": {
    "mdtrt_sn": "202401010001",
    "mdtrt_id": "MDT123456789",
    "psn_no": "43000030281000128715",
    "name": "张三",
    "gend": "1"
  },
  "admission_info": {
    "adm_rec_no": "IP20240101001",
    "wardarea_name": "内科一病区",
    "dept_code": "001",
    "dept_name": "心血管内科",
    "bedno": "001",
    "adm_time": "2024-01-01 08:30:00"
  },
  "diagnosis_info": [
    {
      "inout_diag_type": "1",
      "maindiag_flag": "1",
      "diag_seq": 1,
      "diag_time": "2024-01-01 10:00:00",
      "wm_diag_code": "I25.101",
      "wm_diag_name": "急性心肌梗死",
      "vali_flag": "1"
    }
  ],
  "course_records": [
    {
      "dept_code": "001",
      "dept_name": "心血管内科",
      "rcd_time": "2024-01-01 14:00:00",
      "cas_ftur": "患者主因胸痛3小时入院...",
      "dise_plan": "1.心电监护 2.抗凝治疗..."
    }
  ]
}
```

### 2.5 信息查询服务接口 (15个接口)

#### 2.5.1 基础信息查询接口 (2个)

##### 【5101-5102】基础查询接口
```yaml
# 科室信息查询
GET /api/v1/medical-insurance/query/department-info

# 医执人员信息查询
GET /api/v1/medical-insurance/query/medical-staff-info
```

#### 2.5.2 医保服务查询接口 (6个)

##### 【5201-5206】医保查询接口
```yaml
# 就诊信息查询
GET /api/v1/medical-insurance/query/visit-info

# 诊断信息查询
GET /api/v1/medical-insurance/query/diagnosis-info

# 结算信息查询
GET /api/v1/medical-insurance/query/settlement-info

# 费用明细查询
GET /api/v1/medical-insurance/query/expense-detail

# 人员慢特病用药记录查询
GET /api/v1/medical-insurance/query/chronic-disease-medication

# 人员累计信息查询
GET /api/v1/medical-insurance/query/person-cumulative-info
```

#### 2.5.3 医药机构服务查询接口 (4个)

##### 【5301-5304】机构查询接口
```yaml
# 人员慢特病备案查询
GET /api/v1/medical-insurance/query/chronic-disease-record

# 人员定点信息查询
GET /api/v1/medical-insurance/query/designated-hospital-info

# 在院信息查询
GET /api/v1/medical-insurance/query/hospitalized-patients

# 转院信息查询
GET /api/v1/medical-insurance/query/transfer-info
```

#### 2.5.4 检查检验互认结果查询接口 (3个)

##### 【5401-5461】互认查询接口
```yaml
# 项目互认信息查询
GET /api/v1/medical-insurance/query/mutual-recognition-info

# 报告明细信息查询
GET /api/v1/medical-insurance/query/report-detail-info

# 检查检验结果互认查询授权申请
POST /api/v1/medical-insurance/query/mutual-recognition-auth
```

### 2.6 线上支付服务接口 (8个接口)

#### 2.6.1 医保电子凭证接口 (1个)

##### 【6101】电子凭证解析接口
```yaml
POST /api/v1/medical-insurance/payment/electronic-voucher-parse
```

**请求参数**:
```json
{
  "qr_code": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "parse_type": "qr_code"
}
```

#### 2.6.2 订单支付管理接口 (4个)

##### 【6201-6204】订单支付接口
```yaml
# 费用明细上传
POST /api/v1/medical-insurance/payment/expense-upload

# 支付下单
POST /api/v1/medical-insurance/payment/create-order

# 医保退费
POST /api/v1/medical-insurance/payment/refund

# 医保订单信息同步
POST /api/v1/medical-insurance/payment/order-sync
```

#### 2.6.3 订单查询接口 (2个)

##### 【6301-6302】订单查询接口
```yaml
# 医保订单结算结果查询
GET /api/v1/medical-insurance/payment/settlement-result-query

# 医保结算结果通知
POST /api/v1/medical-insurance/payment/settlement-result-notify
```

#### 2.6.4 订单撤销接口 (1个)

##### 【6401】订单撤销接口
```yaml
POST /api/v1/medical-insurance/payment/expense-upload-cancel
```

### 2.7 医保电子处方服务接口 (20个接口)

#### 2.7.1 医疗机构电子处方业务接口 (9个)

##### 【7101-7109】医疗机构处方接口
```yaml
# 电子处方上传预核验
POST /api/v1/medical-insurance/prescription/medical/pre-verify

# 电子处方医保电子签名
POST /api/v1/medical-insurance/prescription/medical/electronic-signature

# 电子处方上传
POST /api/v1/medical-insurance/prescription/medical/upload

# 电子处方撤销
POST /api/v1/medical-insurance/prescription/medical/cancel

# 电子处方信息查询
GET /api/v1/medical-insurance/prescription/medical/info-query

# 电子处方审核结果查询
GET /api/v1/medical-insurance/prescription/medical/audit-result-query

# 电子处方结算结果查询
GET /api/v1/medical-insurance/prescription/medical/settlement-result-query

# 电子处方审核结果通知
POST /api/v1/medical-insurance/prescription/medical/audit-result-notify

# 电子处方结算结果通知
POST /api/v1/medical-insurance/prescription/medical/settlement-result-notify
```

#### 2.7.2 医药机构电子处方业务接口 (11个)

##### 【7201-7211】医药机构处方接口
```yaml
# 电子处方线下流转授权
POST /api/v1/medical-insurance/prescription/pharmacy/offline-auth

# 电子处方线上流转查询
GET /api/v1/medical-insurance/prescription/pharmacy/online-flow-query

# 电子处方二维码解码
POST /api/v1/medical-insurance/prescription/pharmacy/qr-decode

# 电子处方下载
GET /api/v1/medical-insurance/prescription/pharmacy/download

# 电子处方信息核验
POST /api/v1/medical-insurance/prescription/pharmacy/info-verify

# 电子处方审方信息上传
POST /api/v1/medical-insurance/prescription/pharmacy/review-upload

# 药品销售出库明细上传
POST /api/v1/medical-insurance/prescription/pharmacy/sale-detail-upload

# 药品销售出库明细撤销
POST /api/v1/medical-insurance/prescription/pharmacy/sale-detail-cancel

# 药品配送信息同步
POST /api/v1/medical-insurance/prescription/pharmacy/delivery-sync

# 药品配送签收确认
POST /api/v1/medical-insurance/prescription/pharmacy/delivery-confirm

# 电子处方药品目录查询
GET /api/v1/medical-insurance/prescription/pharmacy/drug-catalog-query
```

### 2.8 场景监控接口 (5个接口)

#### 2.8.1 人脸认证与监控接口 (5个)

##### 【9601-9605】场景监控接口
```yaml
# 人脸认证
POST /api/v1/medical-insurance/monitoring/face-authentication

# 特殊登记
POST /api/v1/medical-insurance/monitoring/special-registration

# 人脸建模
POST /api/v1/medical-insurance/monitoring/face-modeling

# 远程查床任务查询
GET /api/v1/medical-insurance/monitoring/remote-bed-check-query

# 远程查床申诉
POST /api/v1/medical-insurance/monitoring/remote-bed-check-appeal
```

### 2.9 其他功能接口 (4个接口)

#### 2.9.1 签到签退管理接口 (2个)

##### 【9001-9002】签到签退接口
```yaml
# 签到
POST /api/v1/medical-insurance/other/sign-in

# 签退
POST /api/v1/medical-insurance/other/sign-out
```

#### 2.9.2 文件传输管理接口 (2个)

##### 【9101-9102】文件传输接口
```yaml
# 文件上传
POST /api/v1/medical-insurance/other/file-upload

# 文件下载
GET /api/v1/medical-insurance/other/file-download
```

### 2.10 电子票据接口 (4个接口)

#### 2.10.1 电子结算凭证管理接口 (4个)

##### 【5501,4901-4902,4905】电子票据接口
```yaml
# 查询电子结算凭证状态
GET /api/v1/medical-insurance/ticket/electronic-voucher-status

# 医疗机构上传电子结算凭证
POST /api/v1/medical-insurance/ticket/electronic-voucher-upload

# 医疗机构电子结算凭证上传结果查询
GET /api/v1/medical-insurance/ticket/electronic-voucher-upload-result

# 医疗机构重新上传电子结算凭证
POST /api/v1/medical-insurance/ticket/electronic-voucher-reupload
```

### 2.11 政策管理接口 (1个接口)

#### 2.11.1 政策项查询接口 (1个)

##### 【100001】政策项查询接口
```yaml
GET /api/v1/medical-insurance/policy/policy-item-query
```

## 三、通用功能接口

### 3.1 接口配置管理

#### 3.1.1 获取支持的接口列表
```yaml
GET /api/v1/medical-insurance/config/interface-schema
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_interfaces": 206,
    "categories": {
      "基础信息服务": {
        "count": 31,
        "interfaces": {
          "person_info": {
            "infno": "1101",
            "name": "人员基本信息获取",
            "category": "基础信息服务"
          }
        }
      },
      "医保业务服务": {
        "count": 43,
        "interfaces": {...}
      }
    }
  }
}
```

#### 3.1.2 获取特定接口配置
```yaml
GET /api/v1/medical-insurance/config/interface-schema/{interface_type}
```

#### 3.1.3 批量接口配置更新
```yaml
PUT /api/v1/medical-insurance/config/interface-schema/batch
```

### 3.2 批量操作接口

#### 3.2.1 批量数据上传
```yaml
POST /api/v1/medical-insurance/batch/data-upload
```

**请求示例**:
```json
{
  "batch_id": "BATCH20250714001",
  "operations": [
    {
      "interface_type": "outpatient_expense_upload",
      "data": {...},
      "sequence": 1
    },
    {
      "interface_type": "outpatient_settle",
      "data": {...},
      "sequence": 2
    }
  ],
  "options": {
    "stop_on_error": true,
    "max_concurrent": 5
  }
}
```

#### 3.2.2 批量目录下载
```yaml
POST /api/v1/medical-insurance/batch/catalog-download
```

#### 3.2.3 批量操作状态查询
```yaml
GET /api/v1/medical-insurance/batch/status/{batch_id}
```

### 3.3 异步处理接口

#### 3.3.1 创建异步任务
```yaml
POST /api/v1/medical-insurance/async/create-task
```

#### 3.3.2 查询异步任务状态
```yaml
GET /api/v1/medical-insurance/async/task-status/{task_id}
```

#### 3.3.3 获取异步任务结果
```yaml
GET /api/v1/medical-insurance/async/task-result/{task_id}
```

### 3.4 文件处理接口

#### 3.4.1 文件上传处理
```yaml
POST /api/v1/medical-insurance/file/upload
Content-Type: multipart/form-data
```

#### 3.4.2 文件解析
```yaml
POST /api/v1/medical-insurance/file/parse
```

#### 3.4.3 文件下载
```yaml
GET /api/v1/medical-insurance/file/download/{file_id}
```

### 3.5 数据查询与统计接口

#### 3.5.1 通用数据查询
```yaml
POST /api/v1/medical-insurance/query/universal
```

**请求示例**:
```json
{
  "query_type": "interface_data",
  "filters": {
    "interface_type": ["patient_query", "drug_catalog"],
    "data_status": "active",
    "date_range": {
      "start": "2025-07-01",
      "end": "2025-07-14"
    }
  },
  "pagination": {
    "page": 1,
    "page_size": 20
  },
  "sort": [
    {"field": "created_at", "order": "desc"}
  ]
}
```

#### 3.5.2 接口调用统计
```yaml
GET /api/v1/medical-insurance/statistics/interface-calls
```

#### 3.5.3 系统使用统计
```yaml
GET /api/v1/medical-insurance/statistics/system-usage
```

### 3.6 监控与健康检查接口

#### 3.6.1 系统健康检查
```yaml
GET /api/v1/medical-insurance/health/check
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-14T10:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "medical_api": "ok",
    "file_storage": "ok"
  },
  "version": "1.0.0",
  "uptime": "15d 7h 23m"
}
```

#### 3.6.2 系统性能监控
```yaml
GET /api/v1/medical-insurance/monitoring/performance
```

#### 3.6.3 错误日志查询
```yaml
GET /api/v1/medical-insurance/monitoring/error-logs
```

## 四、完整数据模型定义

### 4.1 206个接口数据模型映射表

| 接口编号 | 接口名称 | 数据模型 | 主要字段 |
|---------|----------|----------|----------|
| 1101 | 人员基本信息获取 | PersonInfo | psn_no, psn_name, gend, brdy |
| 1201 | 医药机构信息获取 | InstitutionInfo | fixmedins_code, fixmedins_name |
| 1301 | 西药中成药目录下载 | DrugCatalog | list_id, list_name, spec, price |
| 1302 | 中药饮片目录下载 | TCMCatalog | tcmdrug_code, tcmdrug_name |
| ... | ... | ... | ... |
| 9605 | 远程查床申诉 | RemoteBedCheckAppeal | appeal_id, appeal_reason |

### 4.2 通用接口数据表结构

```sql
-- 通用接口数据表
CREATE TABLE interface_data (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL,
    interface_type VARCHAR(50) NOT NULL,
    infno VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    business_key VARCHAR(100),
    data_type VARCHAR(50) NOT NULL,
    raw_data JSONB NOT NULL,
    parsed_data JSONB,
    data_version VARCHAR(20) DEFAULT '1.0',
    data_status VARCHAR(20) DEFAULT 'active',
    call_log_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expired_at TIMESTAMP,
    
    -- 索引
    INDEX idx_institution_interface (institution_id, interface_type),
    INDEX idx_business_key (business_key),
    INDEX idx_category_status (category, data_status),
    INDEX idx_created_time (created_at),
    GIN INDEX idx_parsed_data (parsed_data)
);

-- 接口调用日志表
CREATE TABLE interface_call_log (
    id BIGSERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL,
    interface_type VARCHAR(50) NOT NULL,
    infno VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    request_id VARCHAR(50) UNIQUE NOT NULL,
    request_data JSONB,
    response_data JSONB,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    error_code VARCHAR(20),
    response_time INTEGER,
    call_time TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_institution_call_time (institution_id, call_time),
    INDEX idx_interface_success (interface_type, success),
    INDEX idx_request_id (request_id)
);

-- 批量操作记录表
CREATE TABLE batch_operation_log (
    id BIGSERIAL PRIMARY KEY,
    batch_id VARCHAR(50) UNIQUE NOT NULL,
    institution_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    error_message TEXT,
    
    INDEX idx_batch_id (batch_id),
    INDEX idx_institution_status (institution_id, status)
);

-- 异步任务表
CREATE TABLE async_task (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(50) UNIQUE NOT NULL,
    institution_id INTEGER NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    task_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    progress INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    INDEX idx_task_id (task_id),
    INDEX idx_institution_status (institution_id, status)
);
```

## 五、完整错误码规范

### 5.1 HTTP状态码映射
- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `202 Accepted`: 请求已接受，异步处理中
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `405 Method Not Allowed`: 请求方法不允许
- `409 Conflict`: 资源冲突
- `422 Unprocessable Entity`: 数据验证失败
- `429 Too Many Requests`: 请求频率过高
- `500 Internal Server Error`: 服务器内部错误
- `502 Bad Gateway`: 医保局接口异常
- `503 Service Unavailable`: 服务不可用
- `504 Gateway Timeout`: 医保局接口超时

### 5.2 业务错误码体系

#### 5.2.1 通用错误码 (10000-19999)
```python
COMMON_ERRORS = {
    10001: {"message": "请求参数缺失", "retry": False},
    10002: {"message": "请求参数格式错误", "retry": False},
    10003: {"message": "请求数据过大", "retry": False},
    10004: {"message": "请求频率过高", "retry": True, "retry_after": 60},
    10005: {"message": "服务暂时不可用", "retry": True, "retry_after": 300},
    10006: {"message": "接口版本不支持", "retry": False},
    10007: {"message": "机构信息无效", "retry": False},
    10008: {"message": "认证信息过期", "retry": False},
    10009: {"message": "权限不足", "retry": False},
    10010: {"message": "系统维护中", "retry": True, "retry_after": 1800}
}
```

#### 5.2.2 接口相关错误码 (20000-29999)
```python
INTERFACE_ERRORS = {
    20001: {"message": "不支持的接口类型", "retry": False},
    20002: {"message": "接口配置不存在", "retry": False},
    20003: {"message": "接口调用失败", "retry": True, "max_retry": 3},
    20004: {"message": "接口响应格式错误", "retry": False},
    20005: {"message": "接口超时", "retry": True, "max_retry": 3},
    20006: {"message": "医保局接口异常", "retry": True, "max_retry": 3},
    20007: {"message": "报文ID重复", "retry": True, "max_retry": 1},
    20008: {"message": "签名验证失败", "retry": False},
    20009: {"message": "AK/SK配置错误", "retry": False},
    20010: {"message": "接口版本不匹配", "retry": False}
}
```

#### 5.2.3 数据相关错误码 (30000-39999)
```python
DATA_ERRORS = {
    30001: {"message": "数据节点缺失", "retry": False},
    30002: {"message": "必填字段缺失", "retry": False},
    30003: {"message": "字段格式错误", "retry": False},
    30004: {"message": "字段长度超限", "retry": False},
    30005: {"message": "数据关联性错误", "retry": False},
    30006: {"message": "数据重复", "retry": False},
    30007: {"message": "数据不存在", "retry": False},
    30008: {"message": "数据已过期", "retry": False},
    30009: {"message": "数据解析失败", "retry": False},
    30010: {"message": "数据验证失败", "retry": False}
}
```

#### 5.2.4 文件相关错误码 (40000-49999)
```python
FILE_ERRORS = {
    40001: {"message": "文件不存在", "retry": False},
    40002: {"message": "文件格式不支持", "retry": False},
    40003: {"message": "文件大小超限", "retry": False},
    40004: {"message": "文件下载失败", "retry": True, "max_retry": 3},
    40005: {"message": "文件解析失败", "retry": False},
    40006: {"message": "文件已过期", "retry": False},
    40007: {"message": "文件上传失败", "retry": True, "max_retry": 3},
    40008: {"message": "文件损坏", "retry": False},
    40009: {"message": "文件查询号无效", "retry": False},
    40010: {"message": "文件压缩解压失败", "retry": False}
}
```

#### 5.2.5 业务流程错误码 (50000-59999)
```python
BUSINESS_ERRORS = {
    50001: {"message": "患者信息不存在", "retry": False},
    50002: {"message": "医保状态异常", "retry": False},
    50003: {"message": "医保余额不足", "retry": False},
    50004: {"message": "超出医保限额", "retry": False},
    50005: {"message": "药品不在医保目录", "retry": False},
    50006: {"message": "诊疗项目不支持", "retry": False},
    50007: {"message": "结算状态错误", "retry": False},
    50008: {"message": "重复结算", "retry": False},
    50009: {"message": "结算已撤销", "retry": False},
    50010: {"message": "业务流程异常", "retry": False}
}
```

#### 5.2.6 系统相关错误码 (60000-69999)
```python
SYSTEM_ERRORS = {
    60001: {"message": "数据库连接失败", "retry": True, "max_retry": 3},
    60002: {"message": "缓存服务异常", "retry": True, "max_retry": 3},
    60003: {"message": "消息队列异常", "retry": True, "max_retry": 3},
    60004: {"message": "文件存储异常", "retry": True, "max_retry": 3},
    60005: {"message": "网络连接异常", "retry": True, "max_retry": 3},
    60006: {"message": "内存不足", "retry": True, "retry_after": 60},
    60007: {"message": "磁盘空间不足", "retry": False},
    60008: {"message": "CPU使用率过高", "retry": True, "retry_after": 30},
    60009: {"message": "系统负载过高", "retry": True, "retry_after": 60},
    60010: {"message": "服务进程异常", "retry": True, "max_retry": 1}
}
```

## 六、性能与限制规范

### 6.1 接口性能指标

#### 6.1.1 响应时间要求
```python
PERFORMANCE_TARGETS = {
    # 基础信息服务 (31个接口)
    "person_info": {"target": "≤ 2秒", "timeout": 10},
    "institution_info": {"target": "≤ 2秒", "timeout": 10},
    "catalog_download": {"target": "≤ 30秒", "timeout": 120},
    "dictionary_download": {"target": "≤ 10秒", "timeout": 30},
    
    # 医保业务服务 (43个接口)
    "benefit_check": {"target": "≤ 3秒", "timeout": 15},
    "pharmacy_settle": {"target": "≤ 5秒", "timeout": 30},
    "outpatient_settle": {"target": "≤ 5秒", "timeout": 30},
    "inpatient_settle": {"target": "≤ 10秒", "timeout": 60},
    
    # 医药机构管理 (47个接口)
    "inventory_upload": {"target": "≤ 5秒", "timeout": 30},
    "drg_query": {"target": "≤ 5秒", "timeout": 30},
    "appeal_submit": {"target": "≤ 3秒", "timeout": 15},
    
    # 信息采集上传 (28个接口)
    "medical_record_upload": {"target": "≤ 30秒", "timeout": 120},
    "clinical_data_upload": {"target": "≤ 10秒", "timeout": 60},
    
    # 信息查询服务 (15个接口)
    "info_query": {"target": "≤ 3秒", "timeout": 15},
    
    # 线上支付服务 (8个接口)
    "payment_order": {"target": "≤ 5秒", "timeout": 30},
    
    # 电子处方服务 (20个接口)
    "prescription_upload": {"target": "≤ 5秒", "timeout": 30},
    
    # 场景监控 (5个接口)
    "face_auth": {"target": "≤ 10秒", "timeout": 30},
    
    # 其他功能 (4个接口)
    "file_upload": {"target": "≤ 60秒", "timeout": 300},
    
    # 电子票据 (4个接口)
    "ticket_upload": {"target": "≤ 5秒", "timeout": 30},
    
    # 政策管理 (1个接口)
    "policy_query": {"target": "≤ 2秒", "timeout": 10}
}
```

#### 6.1.2 并发性能指标
```python
CONCURRENCY_LIMITS = {
    "total_concurrent_requests": 500,
    "per_institution_concurrent": 50,
    "per_interface_type_concurrent": {
        "catalog_download": 10,
        "file_upload": 20,
        "data_upload": 30,
        "query": 100,
        "settle": 50
    },
    "database_connection_pool": 100,
    "redis_connection_pool": 50
}
```

### 6.2 接口限制规范

#### 6.2.1 请求频率限制
```python
RATE_LIMITS = {
    "global": {
        "requests_per_minute": 1000,
        "requests_per_hour": 30000,
        "requests_per_day": 500000
    },
    "per_institution": {
        "requests_per_minute": 100,
        "requests_per_hour": 5000,
        "requests_per_day": 50000
    },
    "per_interface_category": {
        "catalog_download": {
            "requests_per_hour": 50,
            "requests_per_day": 200
        },
        "file_upload": {
            "requests_per_minute": 20,
            "requests_per_hour": 500
        },
        "data_query": {
            "requests_per_minute": 50,
            "requests_per_hour": 2000
        },
        "settlement": {
            "requests_per_minute": 30,
            "requests_per_hour": 1000
        }
    }
}
```

#### 6.2.2 数据大小限制
```python
SIZE_LIMITS = {
    "request_body_max_size": "50MB",
    "upload_file_max_size": "500MB",
    "download_file_max_size": "2GB",
    "batch_operation_max_records": 10000,
    "single_interface_max_records": {
        "expense_detail": 1000,
        "diagnosis_info": 50,
        "course_record": 100,
        "inventory_data": 5000
    },
    "json_field_max_size": "10MB",
    "text_field_max_length": 10000
}
```

## 七、安全与认证规范

### 7.1 多层次认证体系

#### 7.1.1 API Key认证
```python
class APIKeyAuth:
    """API Key认证机制"""
    
    def __init__(self, api_key: str, institution_code: str):
        self.api_key = api_key
        self.institution_code = institution_code
    
    def authenticate(self, request_headers: Dict[str, str]) -> bool:
        provided_key = request_headers.get('X-API-Key')
        provided_institution = request_headers.get('X-Institution-Code')
        
        return (provided_key == self.api_key and 
                provided_institution == self.institution_code)
```

#### 7.1.2 JWT Token认证
```python
class JWTAuth:
    """JWT Token认证机制"""
    
    def generate_token(self, payload: Dict, expires_in: int = 3600) -> str:
        payload['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token: str) -> Dict:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
```

#### 7.1.3 医保接口签名认证
```python
def generate_medical_signature(
    api_name: str, 
    api_version: str, 
    timestamp: int, 
    ak: str, 
    sk: str
) -> str:
    """生成医保接口签名"""
    params = {
        '_api_access_key': ak,
        '_api_name': api_name,
        '_api_timestamp': str(timestamp),
        '_api_version': api_version
    }
    
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(sk.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha1).digest()
    return base64.b64encode(signature).decode('utf-8')
```

### 7.2 权限控制体系

#### 7.2.1 基于角色的权限控制 (RBAC)
```python
class Permission:
    """权限定义"""
    
    # 206个接口权限定义
    INTERFACE_PERMISSIONS = {
        # 基础信息服务权限
        'person_info:read': '人员信息查询',
        'catalog:download': '目录下载',
        
        # 医保业务服务权限
        'settlement:create': '结算创建',
        'settlement:cancel': '结算撤销',
        
        # 医药机构管理权限
        'inventory:manage': '进销存管理',
        'drg:query': 'DRG查询',
        
        # 数据上传权限
        'medical_record:upload': '病历上传',
        'clinical_data:upload': '临床数据上传',
        
        # 查询权限
        'info:query': '信息查询',
        
        # 支付权限
        'payment:create': '支付创建',
        'payment:query': '支付查询',
        
        # 处方权限
        'prescription:upload': '处方上传',
        'prescription:query': '处方查询',
        
        # 监控权限
        'monitoring:access': '监控访问',
        
        # 文件权限
        'file:upload': '文件上传',
        'file:download': '文件下载',
        
        # 票据权限
        'ticket:manage': '票据管理',
        
        # 政策权限
        'policy:query': '政策查询'
    }

class Role:
    """角色定义"""
    
    ROLES = {
        'admin': {
            'name': '系统管理员',
            'permissions': ['*']  # 所有权限
        },
        'hospital_operator': {
            'name': '医院操作员',
            'permissions': [
                'person_info:read', 'settlement:create', 'settlement:cancel',
                'medical_record:upload', 'info:query', 'prescription:upload'
            ]
        },
        'pharmacy_operator': {
            'name': '药店操作员',
            'permissions': [
                'person_info:read', 'inventory:manage', 'prescription:query',
                'payment:create', 'payment:query'
            ]
        },
        'data_analyst': {
            'name': '数据分析员',
            'permissions': [
                'info:query', 'drg:query', 'policy:query', 'catalog:download'
            ]
        }
    }
```

### 7.3 数据安全保护

#### 7.3.1 数据加密存储
```python
class DataEncryption:
    """数据加密处理"""
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        """加密敏感数据"""
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8')
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str) -> str:
        """解密敏感数据"""
        data = base64.b64decode(encrypted_data.encode('utf-8'))
        nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
```

#### 7.3.2 数据脱敏处理
```python
class DataMasking:
    """数据脱敏处理"""
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if len(id_card) == 18:
            return id_card[:6] + '********' + id_card[-4:]
        return id_card
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if len(phone) == 11:
            return phone[:3] + '****' + phone[-4:]
        return phone
    
    @staticmethod
    def mask_name(name: str) -> str:
        """姓名脱敏"""
        if len(name) <= 2:
            return name[0] + '*'
        return name[0] + '*' * (len(name) - 2) + name[-1]
```

## 八、监控与运维规范

### 8.1 全方位监控体系

#### 8.1.1 206个接口监控指标
```python
MONITORING_METRICS = {
    "interface_metrics": {
        "call_count": "接口调用次数",
        "success_rate": "接口成功率",
        "avg_response_time": "平均响应时间",
        "error_rate": "错误率",
        "timeout_rate": "超时率"
    },
    "category_metrics": {
        "基础信息服务": {"interfaces": 31, "weight": 0.15},
        "医保业务服务": {"interfaces": 43, "weight": 0.25},
        "医药机构管理": {"interfaces": 47, "weight": 0.25},
        "信息采集上传": {"interfaces": 28, "weight": 0.15},
        "信息查询服务": {"interfaces": 15, "weight": 0.10},
        "线上支付服务": {"interfaces": 8, "weight": 0.05},
        "电子处方服务": {"interfaces": 20, "weight": 0.10},
        "场景监控": {"interfaces": 5, "weight": 0.02},
        "其他功能": {"interfaces": 4, "weight": 0.02},
        "电子票据": {"interfaces": 4, "weight": 0.02},
        "政策管理": {"interfaces": 1, "weight": 0.01}
    }
}
```

#### 8.1.2 智能告警规则
```python
ALERT_RULES = {
    "critical": {
        "system_down": {"condition": "health_check_fail", "duration": "1m"},
        "database_down": {"condition": "db_connection_fail", "duration": "30s"},
        "high_error_rate": {"condition": "error_rate > 10%", "duration": "5m"}
    },
    "warning": {
        "high_response_time": {"condition": "avg_response_time > 5s", "duration": "10m"},
        "low_success_rate": {"condition": "success_rate < 95%", "duration": "15m"},
        "high_memory_usage": {"condition": "memory_usage > 80%", "duration": "10m"}
    },
    "info": {
        "high_traffic": {"condition": "qps > 500", "duration": "5m"},
        "new_error_type": {"condition": "new_error_detected", "duration": "1m"}
    }
}
```

### 8.2 日志规范

#### 8.2.1 结构化日志格式
```json
{
  "timestamp": "2025-07-14T10:30:00.123Z",
  "level": "INFO",
  "logger": "medical_insurance_api",
  "request_id": "REQ20250714001",
  "institution_id": 1001,
  "interface_type": "person_info",
  "infno": "1101",
  "category": "基础信息服务",
  "method": "POST",
  "path": "/api/v1/medical-insurance/basic/person-info",
  "status_code": 200,
  "response_time": 1.234,
  "user_agent": "MedicalInsuranceSDK/1.0.0",
  "ip_address": "192.168.1.100",
  "message": "Patient info query successful",
  "extra": {
    "patient_id": "43000030281000128715",
    "query_params": {"cert_type": "01"}
  }
}
```

#### 8.2.2 日志分级策略
```python
LOG_LEVELS = {
    "DEBUG": {
        "description": "详细的调试信息",
        "retention": "7天",
        "includes": ["参数详情", "中间处理过程", "调试变量"]
    },
    "INFO": {
        "description": "一般的操作信息",
        "retention": "30天", 
        "includes": ["接口调用", "业务操作", "状态变更"]
    },
    "WARNING": {
        "description": "警告信息",
        "retention": "90天",
        "includes": ["性能警告", "业务异常", "配置问题"]
    },
    "ERROR": {
        "description": "错误信息",
        "retention": "1年",
        "includes": ["接口错误", "系统异常", "数据错误"]
    },
    "CRITICAL": {
        "description": "严重错误",
        "retention": "永久",
        "includes": ["系统崩溃", "数据丢失", "安全事件"]
    }
}
```

## 九、SDK开发规范

### 9.1 多语言SDK统一接口设计

#### 9.1.1 Python SDK接口规范
```python
class MedicalInsuranceSDK:
    """Python SDK主类"""
    
    def __init__(self, config_path: str = None, **kwargs):
        """初始化SDK"""
        pass
    
    # 基础信息服务 (31个接口)
    def query_person_info(self, cert_type: str, cert_no: str, **kwargs) -> PersonInfo:
        """1101 - 人员基本信息获取"""
        pass
    
    def query_institution_info(self, institution_code: str) -> InstitutionInfo:
        """1201 - 医药机构信息获取"""
        pass
    
    def download_drug_catalog(self, version: str = "1.0") -> List[DrugInfo]:
        """1301 - 西药中成药目录下载"""
        pass
    
    # 医保业务服务 (43个接口)
    def benefit_check(self, person_no: str, check_items: List[str]) -> BenefitCheckResult:
        """2001 - 人员待遇享受检查"""
        pass
    
    def pharmacy_pre_settle(self, settlement_data: Dict) -> PreSettleResult:
        """2101 - 药店预结算"""
        pass
    
    # 异步接口支持
    async def query_person_info_async(self, cert_type: str, cert_no: str, **kwargs) -> PersonInfo:
        """异步版本的人员信息查询"""
        pass
    
    # 批量操作支持
    def batch_upload(self, operations: List[Dict]) -> BatchResult:
        """批量数据上传"""
        pass
```

#### 9.1.2 Java SDK接口规范
```java
public class MedicalInsuranceSDK {
    
    public MedicalInsuranceSDK(String configPath) {
        // 初始化SDK
    }
    
    // 基础信息服务
    public PersonInfo queryPersonInfo(String certType, String certNo) 
        throws MedicalInsuranceException {
        // 1101 - 人员基本信息获取
    }
    
    public CompletableFuture<PersonInfo> queryPersonInfoAsync(String certType, String certNo) {
        // 异步版本
    }
    
    // 医保业务服务
    public BenefitCheckResult benefitCheck(String personNo, List<String> checkItems) 
        throws MedicalInsuranceException {
        // 2001 - 人员待遇享受检查
    }
    
    // 批量操作
    public BatchResult batchUpload(List<Operation> operations) 
        throws MedicalInsuranceException {
        // 批量数据上传
    }
}
```

#### 9.1.3 C# SDK接口规范
```csharp
public class MedicalInsuranceSDK
{
    public MedicalInsuranceSDK(string configPath)
    {
        // 初始化SDK
    }
    
    // 基础信息服务
    public PersonInfo QueryPersonInfo(string certType, string certNo)
    {
        // 1101 - 人员基本信息获取
    }
    
    public async Task<PersonInfo> QueryPersonInfoAsync(string certType, string certNo)
    {
        // 异步版本
    }
    
    // 医保业务服务
    public BenefitCheckResult BenefitCheck(string personNo, List<string> checkItems)
    {
        // 2001 - 人员待遇享受检查
    }
    
    // 批量操作
    public BatchResult BatchUpload(List<Operation> operations)
    {
        // 批量数据上传
    }
}
```

### 9.2 SDK配置管理

#### 9.2.1 配置文件格式 (JSON)
```json
{
  "medical_insurance": {
    "api_base_url": "http://localhost:8000/api/v1/medical-insurance/",
    "api_key": "your_api_key_here",
    "institution_code": "H43028110001",
    "timeout": 30,
    "retry": {
      "max_attempts": 3,
      "backoff_factor": 1.5
    },
    "cache": {
      "enabled": true,
      "ttl": 300
    },
    "logging": {
      "level": "INFO",
      "file": "medical_insurance_sdk.log"
    }
  },
  "medical_bureau": {
    "ak": "your_access_key",
    "sk": "your_secret_key",
    "api_url": "https://fuwu.nhsa.gov.cn/",
    "timeout": 30
  }
}
```

#### 9.2.2 环境变量配置
```bash
# 基础配置
MEDICAL_INSURANCE_API_URL=http://localhost:8000/api/v1/medical-insurance/
MEDICAL_INSURANCE_API_KEY=your_api_key_here
MEDICAL_INSURANCE_INSTITUTION_CODE=H43028110001

# 医保局配置
MEDICAL_BUREAU_AK=your_access_key
MEDICAL_BUREAU_SK=your_secret_key
MEDICAL_BUREAU_API_URL=https://fuwu.nhsa.gov.cn/

# 性能配置
MEDICAL_INSURANCE_TIMEOUT=30
MEDICAL_INSURANCE_MAX_RETRIES=3
MEDICAL_INSURANCE_CACHE_TTL=300
```

## 十、部署与运维规范

### 10.1 容器化部署完整配置

#### 10.1.1 Docker Compose生产环境配置
```yaml
version: '3.8'

services:
  medical-insurance-api:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://medical_user:${DB_PASSWORD}@postgres:5432/medical_insurance
      - REDIS_URL=redis://redis:6379/0
      - MEDICAL_BUREAU_AK=${MEDICAL_BUREAU_AK}
      - MEDICAL_BUREAU_SK=${MEDICAL_BUREAU_SK}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: medical_insurance
      POSTGRES_USER: medical_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - ./sql/indexes.sql:/docker-entrypoint-initdb.d/indexes.sql:ro
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./static:/var/www/static:ro
    depends_on:
      - medical-insurance-api
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  celery-worker:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A config worker --loglevel=info --concurrency=4
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://medical_user:${DB_PASSWORD}@postgres:5432/medical_insurance
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  celery-beat:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://medical_user:${DB_PASSWORD}@postgres:5432/medical_insurance
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 10.2 监控配置

#### 10.2.1 Prometheus监控配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'medical-insurance-api'
    static_configs:
      - targets: ['medical-insurance-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### 10.2.2 Grafana仪表板配置
```json
{
  "dashboard": {
    "title": "医保接口SDK监控面板",
    "panels": [
      {
        "title": "206个接口调用统计",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(medical_insurance_requests_total[5m]))",
            "legendFormat": "总调用率"
          }
        ]
      },
      {
        "title": "11大类接口成功率",
        "type": "bargauge",
        "targets": [
          {
            "expr": "sum(rate(medical_insurance_requests_total{status=\"success\"}[5m])) by (category) / sum(rate(medical_insurance_requests_total[5m])) by (category) * 100",
            "legendFormat": "{{category}}"
          }
        ]
      },
      {
        "title": "接口响应时间分布",
        "type": "heatmap",
        "targets": [
          {
            "expr": "sum(rate(medical_insurance_request_duration_seconds_bucket[5m])) by (le)",
            "format": "heatmap"
          }
        ]
      }
    ]
  }
}
```

## 十一、文档与支持规范

### 11.1 完整文档体系

#### 11.1.1 文档分类结构
```
docs/
├── api/
│   ├── 206个接口详细文档/
│   │   ├── 基础信息服务(31个).md
│   │   ├── 医保业务服务(43个).md
│   │   ├── 医药机构管理(47个).md
│   │   ├── 信息采集上传(28个).md
│   │   ├── 信息查询服务(15个).md
│   │   ├── 线上支付服务(8个).md
│   │   ├── 电子处方服务(20个).md
│   │   ├── 场景监控(5个).md
│   │   ├── 其他功能(4个).md
│   │   ├── 电子票据(4个).md
│   │   └── 政策管理(1个).md
│   └── openapi.yaml
├── sdk/
│   ├── python-sdk-guide.md
│   ├── java-sdk-guide.md
│   ├── csharp-sdk-guide.md
│   ├── delphi-sdk-guide.md
│   ├── javascript-sdk-guide.md
│   └── php-sdk-guide.md
├── integration/
│   ├── 侵入式集成指南.md
│   ├── 无侵入式集成指南.md
│   ├── 数据库触发器方案.md
│   └── 代理服务方案.md
├── deployment/
│   ├── docker-deployment.md
│   ├── kubernetes-deployment.md
│   ├── production-deployment.md
│   └── monitoring-setup.md
├── examples/
│   ├── complete-examples/
│   ├── code-samples/
│   └── best-practices/
└── troubleshooting/
    ├── common-issues.md
    ├── error-codes.md
    └── performance-tuning.md
```

#### 11.1.2 API文档自动生成
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class PersonInfoViewSet(viewsets.ViewSet):
    """
    人员基本信息管理API
    
    支持206个医保接口中的人员信息相关功能。
    """
    
    @extend_schema(
        operation_id="query_person_info",
        summary="【1101】人员基本信息获取",
        description="查询参保人员的基本信息和参保状态，支持多种证件类型。",
        parameters=[
            OpenApiParameter(
                name="mdtrt_cert_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="就诊凭证类型：01-身份证，02-社保卡，03-医保电子凭证",
                required=True
            ),
        ],
        responses={
            200: PersonInfoSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=["基础信息服务"]
    )
    def query_person_info(self, request):
        """查询人员基本信息"""
        pass
```

### 11.2 SDK示例代码库

#### 11.2.1 Python SDK完整示例
```python
# examples/python/complete_medical_insurance_example.py
"""
医保接口SDK完整使用示例
演示206个接口中的核心业务流程
"""

import asyncio
from medical_insurance_sdk import MedicalInsuranceSDK
from medical_insurance_sdk.exceptions import MedicalInsuranceException

def main():
    # 初始化SDK
    sdk = MedicalInsuranceSDK(config_path="config.json")
    
    try:
        # 1. 基础信息服务示例 (31个接口)
        basic_info_examples(sdk)
        
        # 2. 医保业务服务示例 (43个接口)
        business_service_examples(sdk)
        
        # 3. 医药机构管理示例 (47个接口)
        institution_management_examples(sdk)
        
        # 4. 信息采集上传示例 (28个接口)
        data_upload_examples(sdk)
        
        # 5. 信息查询服务示例 (15个接口)
        query_service_examples(sdk)
        
        # 6. 线上支付服务示例 (8个接口)
        payment_service_examples(sdk)
        
        # 7. 电子处方服务示例 (20个接口)
        prescription_service_examples(sdk)
        
        # 8. 其他服务示例 (13个接口)
        other_service_examples(sdk)
        
    except MedicalInsuranceException as e:
        print(f"医保接口调用失败: {e}")

def basic_info_examples(sdk):
    """基础信息服务示例 - 31个接口"""
    print("=== 基础信息服务示例 ===")
    
    # 【1101】人员基本信息获取
    patient = sdk.query_person_info(
        cert_type="01",
        cert_no="430281199001010001",
        name="张三"
    )
    print(f"患者信息: {patient.name}, 医保余额: {patient.insurance_balance}")
    
    # 【1201】医药机构信息获取
    institution = sdk.query_institution_info("H43028110001")
    print(f"机构信息: {institution.name}, 等级: {institution.level}")
    
    # 【1301】西药中成药目录下载
    drug_catalog = sdk.download_drug_catalog(version="1.0")
    print(f"药品目录: 共{len(drug_catalog)}条记录")
    
    # 【1302】中药饮片目录下载
    tcm_catalog = sdk.download_tcm_catalog(version="1.0")
    print(f"中药目录: 共{len(tcm_catalog)}条记录")
    
    # 更多目录下载示例...
    catalogs = [
        ("medical_institution_preparations", "1303", "医疗机构制剂目录"),
        ("ethnic_drugs", "1304", "民族药品目录"),
        ("medical_service_items", "1305", "医疗服务项目目录"),
        ("medical_consumables", "1306", "医用耗材目录"),
        ("disease_diagnosis", "1307", "疾病与诊断目录"),
        ("surgical_operations", "1308", "手术操作目录")
    ]
    
    for catalog_type, infno, name in catalogs:
        catalog_data = sdk.download_catalog(catalog_type, version="1.0")
        print(f"{name} ({infno}): 共{len(catalog_data)}条记录")

def business_service_examples(sdk):
    """医保业务服务示例 - 43个接口"""
    print("=== 医保业务服务示例 ===")
    
    # 【2001】人员待遇享受检查
    benefit_result = sdk.benefit_check(
        person_no="43000030281000128715",
        check_items=["drug_limit", "treatment_limit"]
    )
    print(f"待遇检查结果: {benefit_result.status}")
    
    # 药店业务流程 (2101-2103)
    pharmacy_examples(sdk)
    
    # 异地就医购药流程 (2161-2181)
    remote_medical_examples(sdk)
    
    # 门急诊业务流程 (2201-2208)
    outpatient_examples(sdk)
    
    # 住院业务流程 (2301-2305, 2401-2405)
    inpatient_examples(sdk)
    
    # 人员备案流程 (2501-2507)
    record_management_examples(sdk)

def pharmacy_examples(sdk):
    """药店业务示例"""
    print("--- 药店业务流程 ---")
    
    # 构建药店销售数据
    pharmacy_data = {
        "person_no": "43000030281000128715",
        "items": [
            {
                "drug_code": "A01010001",
                "drug_name": "阿司匹林片",
                "quantity": 2,
                "unit_price": 12.50
            }
        ]
    }
    
    # 【2101】药店预结算
    pre_settle_result = sdk.pharmacy_pre_settle(pharmacy_data)
    print(f"预结算结果: 医保支付 {pre_settle_result.insurance_amount}")
    
    # 【2102】药店结算
    settle_result = sdk.pharmacy_settle(pharmacy_data)
    print(f"结算完成: 结算单号 {settle_result.settlement_id}")
    
    # 如果需要撤销
    # 【2103】药店结算撤销
    # cancel_result = sdk.pharmacy_settle_cancel(settle_result.settlement_id)

def outpatient_examples(sdk):
    """门急诊业务示例"""
    print("--- 门急诊业务流程 ---")
    
    # 【2201】门诊挂号
    register_result = sdk.outpatient_register({
        "person_no": "43000030281000128715",
        "dept_code": "001",
        "doctor_code": "DOC001"
    })
    print(f"挂号成功: 挂号单号 {register_result.register_id}")
    
    # 【2203】门诊就诊信息上传
    visit_data = {
        "visit_id": register_result.register_id,
        "diagnosis_info": [
            {
                "diag_code": "I25.101",
                "diag_name": "急性心肌梗死",
                "main_diag_flag": "1"
            }
        ]
    }
    sdk.outpatient_visit_upload(visit_data)
    
    # 【2204】门诊费用明细上传
    expense_data = {
        "visit_id": register_result.register_id,
        "expense_items": [
            {
                "item_code": "A01010001",
                "item_name": "阿司匹林片",
                "quantity": 2,
                "unit_price": 12.50
            }
        ]
    }
    sdk.outpatient_expense_upload(expense_data)
    
    # 【2206】门诊预结算
    pre_settle_result = sdk.outpatient_pre_settle(register_result.register_id)
    print(f"门诊预结算: 医保支付 {pre_settle_result.insurance_amount}")
    
    # 【2207】门诊结算
    settle_result = sdk.outpatient_settle(register_result.register_id)
    print(f"门诊结算完成: {settle_result.settlement_id}")

def inpatient_examples(sdk):
    """住院业务示例"""
    print("--- 住院业务流程 ---")
    
    # 【2401】入院办理
    admission_result = sdk.inpatient_admission({
        "person_no": "43000030281000128715",
        "dept_code": "001",
        "ward_code": "W001",
        "bed_no": "001-01"
    })
    print(f"入院办理完成: 住院号 {admission_result.admission_id}")
    
    # 【2301】住院费用明细上传
    expense_data = {
        "admission_id": admission_result.admission_id,
        "expense_items": [
            {
                "item_code": "A01010001",
                "item_name": "阿司匹林片",
                "quantity": 10,
                "unit_price": 12.50,
                "expense_date": "2025-07-14"
            }
        ]
    }
    sdk.inpatient_expense_upload(expense_data)
    
    # 【2402】出院办理
    discharge_result = sdk.inpatient_discharge({
        "admission_id": admission_result.admission_id,
        "discharge_date": "2025-07-20"
    })
    
    # 【2304】住院结算
    settle_result = sdk.inpatient_settle(admission_result.admission_id)
    print(f"住院结算完成: {settle_result.settlement_id}")

def data_upload_examples(sdk):
    """信息采集上传示例 - 28个接口"""
    print("=== 信息采集上传示例 ===")
    
    # 【4701】电子病历上传
    medical_record = {
        "admission_info": {
            "mdtrt_sn": "202401010001",
            "mdtrt_id": "MDT123456789",
            "psn_no": "43000030281000128715",
            "name": "张三",
            "gend": "1",
            "adm_rec_no": "IP20240101001",
            "dept_code": "001",
            "dept_name": "心血管内科"
        },
        "diagnosis_info": [
            {
                "inout_diag_type": "1",
                "maindiag_flag": "1",
                "diag_seq": 1,
                "wm_diag_code": "I25.101",
                "wm_diag_name": "急性心肌梗死"
            }
        ]
    }
    
    upload_result = sdk.upload_electronic_medical_record(medical_record)
    print(f"电子病历上传完成: {upload_result.upload_id}")
    
    # 【4101】医疗保障基金结算清单上传
    settlement_list = {
        "settlement_id": "SET20250714001",
        "person_no": "43000030281000128715",
        "total_amount": 1000.00,
        "insurance_amount": 800.00,
        "personal_amount": 200.00
    }
    
    settlement_result = sdk.upload_settlement_list(settlement_list)
    print(f"结算清单上传完成: {settlement_result.list_id}")

def prescription_service_examples(sdk):
    """电子处方服务示例 - 20个接口"""
    print("=== 电子处方服务示例 ===")
    
    # 医疗机构端流程 (7101-7109)
    medical_prescription_examples(sdk)
    
    # 医药机构端流程 (7201-7211)
    pharmacy_prescription_examples(sdk)

def medical_prescription_examples(sdk):
    """医疗机构电子处方示例"""
    print("--- 医疗机构电子处方流程 ---")
    
    prescription_data = {
        "prescription_id": "RX20250714001",
        "person_no": "43000030281000128715",
        "doctor_code": "DOC001",
        "dept_code": "001",
        "drugs": [
            {
                "drug_code": "A01010001",
                "drug_name": "阿司匹林片",
                "quantity": 30,
                "usage": "口服，一次1片，一日3次"
            }
        ]
    }
    
    # 【7101】电子处方上传预核验
    pre_verify_result = sdk.prescription_pre_verify(prescription_data)
    print(f"处方预核验: {pre_verify_result.status}")
    
    # 【7103】电子处方上传
    upload_result = sdk.prescription_upload(prescription_data)
    print(f"处方上传完成: {upload_result.prescription_id}")

def pharmacy_prescription_examples(sdk):
    """医药机构电子处方示例"""
    print("--- 医药机构电子处方流程 ---")
    
    # 【7204】电子处方下载
    prescription = sdk.prescription_download("RX20250714001")
    print(f"处方下载: {prescription.prescription_id}")
    
    # 【7207】药品销售出库明细上传
    sale_data = {
        "prescription_id": "RX20250714001",
        "sale_items": [
            {
                "drug_code": "A01010001",
                "quantity": 30,
                "unit_price": 12.50,
                "batch_no": "20250701"
            }
        ]
    }
    
    sale_result = sdk.prescription_sale_upload(sale_data)
    print(f"销售明细上传完成: {sale_result.sale_id}")

async def async_examples():
    """异步操作示例"""
    print("=== 异步操作示例 ===")
    
    sdk = MedicalInsuranceSDK(config_path="config.json")
    
    # 异步并发查询多个患者信息
    patients = ["430281199001010001", "430281199001010002", "430281199001010003"]
    
    tasks = [
        sdk.query_person_info_async("01", cert_no, "")
        for cert_no in patients
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"患者{i+1}查询失败: {result}")
        else:
            print(f"患者{i+1}: {result.name}")

def batch_operations_example(sdk):
    """批量操作示例"""
    print("=== 批量操作示例 ===")
    
    # 批量上传多个接口数据
    batch_operations = [
        {
            "interface_type": "outpatient_expense_upload",
            "data": {"visit_id": "V001", "expenses": [...]},
            "sequence": 1
        },
        {
            "interface_type": "outpatient_settle",
            "data": {"visit_id": "V001"},
            "sequence": 2
        }
    ]
    
    batch_result = sdk.batch_upload(batch_operations)
    print(f"批量操作: {batch_result.success_count}/{batch_result.total_count} 成功")

if __name__ == "__main__":
    main()
    
    # 运行异步示例
    asyncio.run(async_examples())
```

#### 11.2.2 Java SDK完整示例
```java
// examples/java/CompleteMedicalInsuranceExample.java
package com.example.medical.insurance;

import com.medical.insurance.sdk.MedicalInsuranceSDK;
import com.medical.insurance.sdk.model.*;
import com.medical.insurance.sdk.exception.MedicalInsuranceException;

import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class CompleteMedicalInsuranceExample {
    
    private static final MedicalInsuranceSDK sdk = new MedicalInsuranceSDK("config.properties");
    
    public static void main(String[] args) {
        try {
            // 基础信息服务示例
            basicInfoExamples();
            
            // 医保业务服务示例
            businessServiceExamples();
            
            // 异步操作示例
            asyncExamples();
            
            // 批量操作示例
            batchOperationExamples();
            
        } catch (MedicalInsuranceException e) {
            System.err.println("医保接口调用失败: " + e.getMessage());
        }
    }
    
    private static void basicInfoExamples() throws MedicalInsuranceException {
        System.out.println("=== 基础信息服务示例 ===");
        
        // 【1101】人员基本信息获取
        PersonInfo patient = sdk.queryPersonInfo("01", "430281199001010001", "张三");
        System.out.println("患者信息: " + patient.getName() + ", 医保余额: " + patient.getInsuranceBalance());
        
        // 【1301】西药中成药目录下载
        List<DrugInfo> drugCatalog = sdk.downloadDrugCatalog("1.0");
        System.out.println("药品目录: 共" + drugCatalog.size() + "条记录");
        
        // 【1201】医药机构信息获取
        InstitutionInfo institution = sdk.queryInstitutionInfo("H43028110001");
        System.out.println("机构信息: " + institution.getName());
    }
    
    private static void businessServiceExamples() throws MedicalInsuranceException {
        System.out.println("=== 医保业务服务示例 ===");
        
        // 【2001】人员待遇享受检查
        BenefitCheckResult benefitResult = sdk.benefitCheck(
            "43000030281000128715", 
            Arrays.asList("drug_limit", "treatment_limit")
        );
        System.out.println("待遇检查结果: " + benefitResult.getStatus());
        
        // 门诊业务流程
        outpatientExamples();
        
        // 住院业务流程
        inpatientExamples();
    }
    
    private static void outpatientExamples() throws MedicalInsuranceException {
        System.out.println("--- 门诊业务流程 ---");
        
        // 【2201】门诊挂号
        OutpatientRegisterRequest registerRequest = OutpatientRegisterRequest.builder()
            .personNo("43000030281000128715")
            .deptCode("001")
            .doctorCode("DOC001")
            .build();
            
        OutpatientRegisterResult registerResult = sdk.outpatientRegister(registerRequest);
        System.out.println("挂号成功: " + registerResult.getRegisterId());
        
        // 【2207】门诊结算
        OutpatientSettleResult settleResult = sdk.outpatientSettle(registerResult.getRegisterId());
        System.out.println("门诊结算完成: " + settleResult.getSettlementId());
    }
    
    private static void inpatientExamples() throws MedicalInsuranceException {
        System.out.println("--- 住院业务流程 ---");
        
        // 【2401】入院办理
        InpatientAdmissionRequest admissionRequest = InpatientAdmissionRequest.builder()
            .personNo("43000030281000128715")
            .deptCode("001")
            .wardCode("W001")
            .bedNo("001-01")
            .build();
            
        InpatientAdmissionResult admissionResult = sdk.inpatientAdmission(admissionRequest);
        System.out.println("入院办理完成: " + admissionResult.getAdmissionId());
        
        // 【2304】住院结算
        InpatientSettleResult settleResult = sdk.inpatientSettle(admissionResult.getAdmissionId());
        System.out.println("住院结算完成: " + settleResult.getSettlementId());
    }
    
    private static void asyncExamples() {
        System.out.println("=== 异步操作示例 ===");
        
        List<String> patients = Arrays.asList(
            "430281199001010001", 
            "430281199001010002", 
            "430281199001010003"
        );
        
        List<CompletableFuture<PersonInfo>> futures = patients.stream()
            .map(certNo -> sdk.queryPersonInfoAsync("01", certNo, ""))
            .collect(Collectors.toList());
        
        CompletableFuture<Void> allFutures = CompletableFuture.allOf(
            futures.toArray(new CompletableFuture[0])
        );
        
        try {
            allFutures.get();
            
            for (int i = 0; i < futures.size(); i++) {
                PersonInfo patient = futures.get(i).get();
                System.out.println("患者" + (i + 1) + ": " + patient.getName());
            }
        } catch (InterruptedException | ExecutionException e) {
            System.err.println("异步操作失败: " + e.getMessage());
        }
    }
    
    private static void batchOperationExamples() throws MedicalInsuranceException {
        System.out.println("=== 批量操作示例 ===");
        
        List<BatchOperation> operations = Arrays.asList(
            BatchOperation.builder()
                .interfaceType("outpatient_expense_upload")
                .data(Map.of("visit_id", "V001"))
                .sequence(1)
                .build(),
            BatchOperation.builder()
                .interfaceType("outpatient_settle")
                .data(Map.of("visit_id", "V001"))
                .sequence(2)
                .build()
        );
        
        BatchResult batchResult = sdk.batchUpload(operations);
        System.out.println("批量操作: " + batchResult.getSuccessCount() + "/" + 
                          batchResult.getTotalCount() + " 成功");
    }
}
```

#### 11.2.3 C# SDK完整示例
```csharp
// examples/csharp/CompleteMedicalInsuranceExample.cs
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using MedicalInsurance.SDK;
using MedicalInsurance.SDK.Models;
using MedicalInsurance.SDK.Exceptions;

namespace MedicalInsurance.Examples
{
    class CompleteMedicalInsuranceExample
    {
        private static readonly MedicalInsuranceSDK sdk = new MedicalInsuranceSDK("config.json");
        
        static async Task Main(string[] args)
        {
            try
            {
                // 基础信息服务示例
                await BasicInfoExamples();
                
                // 医保业务服务示例
                await BusinessServiceExamples();
                
                // 异步操作示例
                await AsyncExamples();
                
                // 批量操作示例
                await BatchOperationExamples();
            }
            catch (MedicalInsuranceException ex)
            {
                Console.WriteLine($"医保接口调用失败: {ex.Message}");
            }
        }
        
        private static async Task BasicInfoExamples()
        {
            Console.WriteLine("=== 基础信息服务示例 ===");
            
            // 【1101】人员基本信息获取
            var patient = await sdk.QueryPersonInfoAsync("01", "430281199001010001", "张三");
            Console.WriteLine($"患者信息: {patient.Name}, 医保余额: {patient.InsuranceBalance}");
            
            // 【1301】西药中成药目录下载
            var drugCatalog = await sdk.DownloadDrugCatalogAsync("1.0");
            Console.WriteLine($"药品目录: 共{drugCatalog.Count}条记录");
            
            // 【1201】医药机构信息获取
            var institution = await sdk.QueryInstitutionInfoAsync("H43028110001");
            Console.WriteLine($"机构信息: {institution.Name}");
        }
        
        private static async Task BusinessServiceExamples()
        {
            Console.WriteLine("=== 医保业务服务示例 ===");
            
            // 【2001】人员待遇享受检查
            var benefitResult = await sdk.BenefitCheckAsync(
                "43000030281000128715", 
                new List<string> { "drug_limit", "treatment_limit" }
            );
            Console.WriteLine($"待遇检查结果: {benefitResult.Status}");
            
            // 门诊业务流程
            await OutpatientExamples();
            
            // 住院业务流程
            await InpatientExamples();
        }
        
        private static async Task OutpatientExamples()
        {
            Console.WriteLine("--- 门诊业务流程 ---");
            
            // 【2201】门诊挂号
            var registerRequest = new OutpatientRegisterRequest
            {
                PersonNo = "43000030281000128715",
                DeptCode = "001",
                DoctorCode = "DOC001"
            };
            
            var registerResult = await sdk.OutpatientRegisterAsync(registerRequest);
            Console.WriteLine($"挂号成功: {registerResult.RegisterId}");
            
            // 【2207】门诊结算
            var settleResult = await sdk.OutpatientSettleAsync(registerResult.RegisterId);
            Console.WriteLine($"门诊结算完成: {settleResult.SettlementId}");
        }
        
        private static async Task InpatientExamples()
        {
            Console.WriteLine("--- 住院业务流程 ---");
            
            // 【2401】入院办理
            var admissionRequest = new InpatientAdmissionRequest
            {
                PersonNo = "43000030281000128715",
                DeptCode = "001",
                WardCode = "W001",
                BedNo = "001-01"
            };
            
            var admissionResult = await sdk.InpatientAdmissionAsync(admissionRequest);
            Console.WriteLine($"入院办理完成: {admissionResult.AdmissionId}");
            
            // 【2304】住院结算
            var settleResult = await sdk.InpatientSettleAsync(admissionResult.AdmissionId);
            Console.WriteLine($"住院结算完成: {settleResult.SettlementId}");
        }
        
        private static async Task AsyncExamples()
        {
            Console.WriteLine("=== 异步操作示例 ===");
            
            var patients = new List<string>
            {
                "430281199001010001",
                "430281199001010002", 
                "430281199001010003"
            };
            
            var tasks = patients.Select(certNo => 
                sdk.QueryPersonInfoAsync("01", certNo, "")
            ).ToArray();
            
            var results = await Task.WhenAll(tasks);
            
            for (int i = 0; i < results.Length; i++)
            {
                Console.WriteLine($"患者{i + 1}: {results[i].Name}");
            }
        }
        
        private static async Task BatchOperationExamples()
        {
            Console.WriteLine("=== 批量操作示例 ===");
            
            var operations = new List<BatchOperation>
            {
                new BatchOperation
                {
                    InterfaceType = "outpatient_expense_upload",
                    Data = new Dictionary<string, object> { { "visit_id", "V001" } },
                    Sequence = 1
                },
                new BatchOperation
                {
                    InterfaceType = "outpatient_settle",
                    Data = new Dictionary<string, object> { { "visit_id", "V001" } },
                    Sequence = 2
                }
            };
            
            var batchResult = await sdk.BatchUploadAsync(operations);
            Console.WriteLine($"批量操作: {batchResult.SuccessCount}/{batchResult.TotalCount} 成功");
        }
    }
}
```

### 11.3 集成指南

#### 11.3.1 侵入式集成完整指南
```markdown
# 侵入式集成指南

## 概述
侵入式集成是指HIS系统主动调用医保接口SDK，需要修改HIS系统的源代码来集成医保功能。

## 集成步骤

### 1. 环境准备
- 安装对应语言的SDK包
- 配置医保局AK/SK密钥
- 配置SDK基础参数

### 2. 初始化SDK
​```python
# Python示例
from medical_insurance_sdk import MedicalInsuranceSDK

sdk = MedicalInsuranceSDK(config_path="config.json")
```

### 3. 业务流程集成

#### 3.1 门诊业务集成
```python
def outpatient_process(patient_info, treatment_info):
    """门诊业务完整流程"""
    
    # 1. 患者身份验证
    patient = sdk.query_person_info(
        cert_type=patient_info['cert_type'],
        cert_no=patient_info['cert_no'],
        name=patient_info['name']
    )
    
    # 2. 待遇检查
    benefit_result = sdk.benefit_check(
        person_no=patient.person_no,
        check_items=['drug_limit', 'treatment_limit']
    )
    
    # 3. 门诊挂号
    register_result = sdk.outpatient_register({
        'person_no': patient.person_no,
        'dept_code': treatment_info['dept_code'],
        'doctor_code': treatment_info['doctor_code']
    })
    
    # 4. 就诊信息上传
    sdk.outpatient_visit_upload({
        'visit_id': register_result.register_id,
        'diagnosis_info': treatment_info['diagnosis']
    })
    
    # 5. 费用明细上传
    sdk.outpatient_expense_upload({
        'visit_id': register_result.register_id,
        'expense_items': treatment_info['expenses']
    })
    
    # 6. 预结算
    pre_settle_result = sdk.outpatient_pre_settle(register_result.register_id)
    
    # 7. 正式结算
    if confirm_settlement(pre_settle_result):
        settle_result = sdk.outpatient_settle(register_result.register_id)
        return settle_result
    
    return None
```

### 4. 错误处理
```python
from medical_insurance_sdk.exceptions import MedicalInsuranceException

try:
    result = sdk.query_person_info("01", "430281199001010001")
except MedicalInsuranceException as e:
    if e.retry:
        # 可重试错误，等待后重试
        time.sleep(e.retry_after or 5)
        result = sdk.query_person_info("01", "430281199001010001")
    else:
        # 不可重试错误，记录日志并返回错误
        logger.error(f"医保接口调用失败: {e.message}")
        raise
```

### 5. 最佳实践
- 使用连接池管理HTTP连接
- 实现重试机制处理网络异常
- 缓存目录数据减少重复下载
- 记录详细的操作日志
- 定期同步医保目录数据
```

#### 11.3.2 无侵入式集成完整指南
​```markdown
# 无侵入式集成指南

## 概述
无侵入式集成不需要修改HIS系统源代码，通过数据库触发器、代理服务等方式自动调用医保接口。

## 方案一：数据库触发器方案

### 1. 触发器设计
​```sql
-- 门诊挂号触发器
CREATE OR REPLACE FUNCTION medical_insurance_outpatient_register()
RETURNS TRIGGER AS $
BEGIN
    -- 插入医保处理队列
    INSERT INTO medical_insurance_queue (
        operation_type,
        interface_type,
        data_json,
        created_at,
        status
    ) VALUES (
        'INSERT',
        'outpatient_register',
        json_build_object(
            'person_no', NEW.person_no,
            'dept_code', NEW.dept_code,
            'doctor_code', NEW.doctor_code,
            'register_id', NEW.register_id
        ),
        NOW(),
        'pending'
    );
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER trigger_outpatient_register
    AFTER INSERT ON outpatient_register
    FOR EACH ROW
    EXECUTE FUNCTION medical_insurance_outpatient_register();
```

### 2. 队列处理服务
```python
# medical_insurance_processor.py
import json
import time
from database import get_db_connection
from medical_insurance_sdk import MedicalInsuranceSDK

class MedicalInsuranceProcessor:
    def __init__(self):
        self.sdk = MedicalInsuranceSDK(config_path="config.json")
        self.db = get_db_connection()
    
    def process_queue(self):
        """处理医保队列"""
        while True:
            # 获取待处理的队列项
            queue_items = self.get_pending_queue_items()
            
            for item in queue_items:
                try:
                    self.process_queue_item(item)
                    self.mark_item_completed(item['id'])
                except Exception as e:
                    self.mark_item_failed(item['id'], str(e))
            
            time.sleep(5)  # 5秒后再次检查
    
    def process_queue_item(self, item):
        """处理单个队列项"""
        interface_type = item['interface_type']
        data = json.loads(item['data_json'])
        
        if interface_type == 'outpatient_register':
            result = self.sdk.outpatient_register(data)
            self.save_result(item['id'], result)
        elif interface_type == 'outpatient_settle':
            result = self.sdk.outpatient_settle(data['register_id'])
            self.save_result(item['id'], result)
        # 更多接口处理...
    
    def get_pending_queue_items(self):
        """获取待处理队列项"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, interface_type, data_json 
            FROM medical_insurance_queue 
            WHERE status = 'pending' 
            ORDER BY created_at 
            LIMIT 100
        """)
        return cursor.fetchall()
    
    def save_result(self, queue_id, result):
        """保存处理结果"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO medical_insurance_results (
                queue_id, result_json, created_at
            ) VALUES (%s, %s, NOW())
        """, (queue_id, json.dumps(result.__dict__)))
        self.db.commit()

if __name__ == "__main__":
    processor = MedicalInsuranceProcessor()
    processor.process_queue()
```

## 方案二：独立代理服务方案

### 1. 代理服务架构
```python
# medical_insurance_proxy.py
from flask import Flask, request, jsonify
from medical_insurance_sdk import MedicalInsuranceSDK
import logging

app = Flask(__name__)
sdk = MedicalInsuranceSDK(config_path="config.json")

@app.route('/api/medical-insurance/<interface_type>', methods=['POST'])
def proxy_medical_interface(interface_type):
    """代理医保接口调用"""
    try:
        data = request.json
        
        # 根据接口类型调用对应的SDK方法
        if interface_type == 'person_info':
            result = sdk.query_person_info(**data)
        elif interface_type == 'outpatient_register':
            result = sdk.outpatient_register(data)
        elif interface_type == 'outpatient_settle':
            result = sdk.outpatient_settle(data['register_id'])
        else:
            return jsonify({'error': '不支持的接口类型'}), 400
        
        return jsonify({
            'success': True,
            'data': result.__dict__,
            'message': '调用成功'
        })
        
    except Exception as e:
        logging.error(f"代理服务调用失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '调用失败'
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
```

### 2. HIS系统调用代理服务
```csharp
// HIS系统中的调用代码
public class MedicalInsuranceProxy
{
    private readonly HttpClient _httpClient;
    private readonly string _proxyUrl = "http://localhost:8080/api/medical-insurance";
    
    public MedicalInsuranceProxy()
    {
        _httpClient = new HttpClient();
    }
    
    public async Task<PersonInfo> QueryPersonInfo(string certType, string certNo)
    {
        var requestData = new
        {
            cert_type = certType,
            cert_no = certNo
        };
        
        var response = await _httpClient.PostAsJsonAsync(
            $"{_proxyUrl}/person_info", 
            requestData
        );
        
        if (response.IsSuccessStatusCode)
        {
            var result = await response.Content.ReadFromJsonAsync<ApiResponse<PersonInfo>>();
            return result.Data;
        }
        
        throw new Exception("医保接口调用失败");
    }
}
```

## 方案三：文件监控方案

### 1. 文件监控服务
```python
# file_monitor_service.py
import os
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from medical_insurance_sdk import MedicalInsuranceSDK

class MedicalInsuranceFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.sdk = MedicalInsuranceSDK(config_path="config.json")
    
    def on_created(self, event):
        """文件创建时处理"""
        if not event.is_directory and event.src_path.endswith('.json'):
            self.process_file(event.src_path)
    
    def process_file(self, file_path):
        """处理JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            interface_type = data.get('interface_type')
            request_data = data.get('data')
            
            # 根据接口类型调用对应方法
            if interface_type == 'outpatient_register':
                result = self.sdk.outpatient_register(request_data)
            elif interface_type == 'outpatient_settle':
                result = self.sdk.outpatient_settle(request_data['register_id'])
            
            # 保存结果
            result_file = file_path.replace('.json', '_result.json')
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result.__dict__, f, ensure_ascii=False, indent=2)
            
            # 删除原文件
            os.remove(file_path)
            
        except Exception as e:
            # 保存错误信息
            error_file = file_path.replace('.json', '_error.json')
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({'error': str(e)}, f, ensure_ascii=False, indent=2)

def main():
    event_handler = MedicalInsuranceFileHandler()
    observer = Observer()
    observer.schedule(event_handler, '/data/medical-insurance/input', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
```

### 2. HIS系统文件输出
```csharp
// HIS系统输出文件调用医保接口
public class FileBasedMedicalInsurance
{
    private readonly string _inputPath = @"C:\data\medical-insurance\input";
    private readonly string _outputPath = @"C:\data\medical-insurance\output";
    
    public async Task<string> CallMedicalInterface(string interfaceType, object data)
    {
        // 生成唯一文件名
        var fileName = $"{interfaceType}_{DateTime.Now:yyyyMMddHHmmss}_{Guid.NewGuid():N}.json";
        var inputFile = Path.Combine(_inputPath, fileName);
        var resultFile = Path.Combine(_outputPath, fileName.Replace(".json", "_result.json"));
        var errorFile = Path.Combine(_outputPath, fileName.Replace(".json", "_error.json"));
        
        // 写入请求文件
        var requestData = new
        {
            interface_type = interfaceType,
            data = data,
            request_id = Guid.NewGuid().ToString(),
            timestamp = DateTime.Now
        };
        
        await File.WriteAllTextAsync(inputFile, JsonSerializer.Serialize(requestData));
        
        // 等待结果文件
        var timeout = TimeSpan.FromSeconds(30);
        var startTime = DateTime.Now;
        
        while (DateTime.Now - startTime < timeout)
        {
            if (File.Exists(resultFile))
            {
                var result = await File.ReadAllTextAsync(resultFile);
                File.Delete(resultFile);
                return result;
            }
            
            if (File.Exists(errorFile))
            {
                var error = await File.ReadAllTextAsync(errorFile);
                File.Delete(errorFile);
                throw new Exception($"医保接口调用失败: {error}");
            }
            
            await Task.Delay(500);
        }
        
        throw new TimeoutException("医保接口调用超时");
    }
}
```
```

### 11.4 故障排除指南

#### 11.4.1 常见问题解决方案
​```markdown
# 医保接口SDK故障排除指南

## 常见问题分类

### 1. 认证相关问题

#### 问题：API Key认证失败
**错误信息**: `401 Unauthorized - Invalid API Key`
**解决方案**:
1. 检查配置文件中的API Key是否正确
2. 确认机构代码是否匹配
3. 检查请求头是否包含必要的认证信息

​```bash
# 检查配置
curl -H "X-API-Key: your_api_key" \
     -H "X-Institution-Code: H43028110001" \
     http://localhost:8000/api/v1/medical-insurance/health/check
```

#### 问题：医保局AK/SK签名失败
**错误信息**: `Medical bureau signature verification failed`
**解决方案**:
1. 确认AK/SK配置正确
2. 检查时间戳是否在有效范围内
3. 验证签名算法实现

```python
# 测试签名生成
from medical_insurance_sdk.utils import generate_signature

signature = generate_signature(
    api_name="1101",
    api_version="1.0.0", 
    timestamp=int(time.time() * 1000),
    ak="your_ak",
    sk="your_sk"
)
print(f"Generated signature: {signature}")
```

### 2. 网络连接问题

#### 问题：连接超时
**错误信息**: `ConnectionTimeout: Request timeout after 30 seconds`
**解决方案**:
1. 检查网络连接是否正常
2. 增加超时时间配置
3. 检查防火墙设置

```json
// 调整超时配置
{
  "timeout": {
    "connection": 30,
    "read": 60,
    "total": 120
  }
}
```

#### 问题：医保局接口不可用
**错误信息**: `502 Bad Gateway - Medical bureau service unavailable`
**解决方案**:
1. 检查医保局服务状态
2. 使用备用接口地址
3. 实施重试机制

### 3. 数据相关问题

#### 问题：必填字段缺失
**错误信息**: `30002 - 必填字段缺失: adminfo.mdtrt_sn`
**解决方案**:
1. 检查接口文档确认必填字段
2. 验证数据完整性
3. 使用SDK验证功能

```python
# 使用SDK验证
try:
    result = sdk.validate_medical_data("electronic_medical_record", data)
    if not result.success:
        print("验证失败:", result.errors)
except ValidationError as e:
    print("数据验证失败:", e.message)
```

#### 问题：数据格式错误
**错误信息**: `30003 - 字段格式错误: gend must be '1' or '2'`
**解决方案**:
1. 检查数据字典确认有效值
2. 进行数据格式转换
3. 使用枚举类型约束

### 4. 性能相关问题

#### 问题：接口响应慢
**现象**: 接口响应时间超过10秒
**解决方案**:
1. 启用缓存机制
2. 使用异步调用
3. 优化数据库查询

```python
# 启用缓存
sdk = MedicalInsuranceSDK(
    config_path="config.json",
    cache_enabled=True,
    cache_ttl=300
)

# 异步调用
result = await sdk.query_person_info_async("01", "430281199001010001")
```

#### 问题：并发限制
**错误信息**: `429 Too Many Requests - Rate limit exceeded`
**解决方案**:
1. 实施请求限流
2. 使用请求队列
3. 增加重试间隔

### 5. 系统集成问题

#### 问题：HIS系统集成失败
**现象**: 无法获取HIS系统数据
**解决方案**:
1. 检查数据库连接
2. 验证数据映射配置
3. 测试触发器功能

```sql
-- 测试触发器
INSERT INTO outpatient_register (person_no, dept_code, doctor_code) 
VALUES ('43000030281000128715', '001', 'DOC001');

-- 检查队列表
SELECT * FROM medical_insurance_queue WHERE status = 'pending';
```

## 诊断工具

### 1. 健康检查
```bash
# 系统健康检查
curl http://localhost:8000/api/v1/medical-insurance/health/check

# 接口连通性测试
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"test": true}' \
  http://localhost:8000/api/v1/medical-insurance/basic/person-info
```

### 2. 日志分析
```bash
# 查看错误日志
tail -f /app/logs/medical_insurance_error.log

# 搜索特定错误
grep "30002" /app/logs/medical_insurance.log

# 分析性能日志
awk '{print $NF}' /app/logs/performance.log | sort -n | tail -10
```

### 3. 数据库诊断
```sql
-- 检查接口调用统计
SELECT interface_type, COUNT(*), AVG(response_time) 
FROM interface_call_log 
WHERE call_time >= NOW() - INTERVAL '1 hour'
GROUP BY interface_type;

-- 查看失败的调用
SELECT * FROM interface_call_log 
WHERE success = false 
ORDER BY call_time DESC 
LIMIT 10;
```

## 十二、总结

本完善版的医保接口SDK API规范文档涵盖了以下核心内容：

### 📋 **完整覆盖206个医保接口**
- **基础信息服务**: 31个接口 (人员信息、机构信息、28个目录下载、字典数据)
- **医保业务服务**: 43个接口 (待遇检查、药店业务、异地就医、门急诊、住院、备案)
- **医药机构管理**: 47个接口 (审核、结算、对照、科室、进销存、分组付费、申诉)
- **信息采集上传**: 28个接口 (结算清单、门急诊、住院、临床、电子病历)
- **信息查询服务**: 15个接口 (基础查询、医保查询、机构查询、互认查询)
- **线上支付服务**: 8个接口 (电子凭证、订单管理、查询、撤销)
- **电子处方服务**: 20个接口 (医疗机构9个 + 医药机构11个)
- **场景监控**: 5个接口 (人脸认证、建模、查床)
- **其他功能**: 4个接口 (签到签退、文件传输)
- **电子票据**: 4个接口 (电子结算凭证管理)
- **政策管理**: 1个接口 (政策查询)

### 🏗️ **系统架构与设计**
- **RESTful API设计**: 统一的接口规范和响应格式
- **多语言SDK支持**: Python、Java、C#、Delphi、JavaScript、PHP
- **双模式集成**: 侵入式和无侵入式集成方案
- **容器化部署**: Docker/Kubernetes完整部署方案
- **微服务架构**: 高可用、可扩展的系统架构

### 🔒 **安全与认证**
- **多层次认证**: API Key + JWT + 医保局AK/SK签名
- **权限控制**: 基于角色的权限管理(RBAC)
- **数据安全**: 加密存储、数据脱敏、安全传输
- **审计跟踪**: 完整的操作审计和日志记录

### 📊 **监控与运维**
- **全方位监控**: 206个接口的完整监控体系
- **智能告警**: 多级告警规则和自动化处理
- **性能优化**: 缓存策略、连接池、负载均衡
- **故障排除**: 完整的故障诊断和解决方案

### 📚 **文档与支持**
- **完整示例**: 多语言SDK的完整使用示例
- **集成指南**: 详细的集成步骤和最佳实践
- **故障排除**: 常见问题的解决方案和诊断工具
- **API文档**: 自动生成的完整API文档

### 🎯 **商业价值**
- **标准化产品**: 可作为标准产品销售给多家医院
- **分级适配**: 支持药店、诊所、医院等不同等级机构
- **易于维护**: 统一的核心服务，降低维护成本
- **快速部署**: 容器化部署，支持快速上线

这份完善的API规范文档为医保接口SDK系统提供了全面的技术指导，确保系统能够满足各种医疗机构的需求，同时具备良好的扩展性和维护性。
            