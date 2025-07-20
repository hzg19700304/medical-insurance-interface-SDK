# 医保接口SDK

通用医保接口SDK，支持多医院部署，兼容C/S和B/S架构。

## 项目概述

本SDK提供统一的医保接口调用能力，支持：
- 174个医保接口的统一调用
- 多医院配置管理
- 配置驱动的接口处理
- 完整的日志记录和监控
- 数据库存储和管理

## 项目结构

```
medical_insurance_sdk/
├── __init__.py              # SDK主入口
├── client.py                # 客户端接口
├── sdk.py                   # SDK核心类
├── exceptions.py            # 异常定义
├── config/                  # 配置管理
│   ├── __init__.py
│   ├── database.py          # 数据库配置
│   ├── manager.py           # 配置管理器
│   └── models.py            # 配置模型
├── core/                    # 核心组件
│   ├── __init__.py
│   ├── processor.py         # 通用接口处理器
│   ├── validator.py         # 数据验证器
│   └── protocol.py          # 协议处理器
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── request.py           # 请求模型
│   ├── response.py          # 响应模型
│   └── log.py               # 日志模型
└── utils/                   # 工具类
    ├── __init__.py
    ├── crypto.py            # 加密工具
    ├── http.py              # HTTP客户端
    └── logger.py            # 日志管理
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置相关参数：

```bash
cp .env.example .env
```

### 3. 基本使用

```python
from medical_insurance_sdk import MedicalInsuranceClient

# 创建客户端
client = MedicalInsuranceClient()

# 调用接口
result = client.call(
    api_code='1101',  # 人员信息获取
    data={'psn_no': '430123199001011234'},
    org_code='H43010000001'
)

print(result)
```

## 开发环境设置

### 快速设置

可以使用提供的设置脚本：

```bash
python scripts/setup_dev.py
```

### 手动设置

#### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

#### 2. 安装开发依赖

```bash
pip install -r requirements.txt
pip install -e .
```

#### 3. 代码格式化

```bash
black medical_insurance_sdk/
flake8 medical_insurance_sdk/
```

#### 4. 运行测试

```bash
pytest tests/
```

### 详细命令记录

完整的项目设置命令和验证过程记录在 [docs/setup-commands.md](docs/setup-commands.md) 中，包含：
- 所有执行的终端命令
- 命令执行结果
- 验证步骤
- 环境信息

这个文档可用于：
- 问题排查
- 环境重建
- 团队成员参考

## 数据库配置

### MySQL数据库设置

1. 创建数据库：
```sql
CREATE DATABASE medical_insurance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 配置环境变量：
```bash
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=your_password
DB_DATABASE=medical_insurance
```

## 配置说明

### 数据库配置
- `DB_HOST`: 数据库主机地址
- `DB_PORT`: 数据库端口
- `DB_USERNAME`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `DB_DATABASE`: 数据库名称

### SDK配置
- `SDK_TIMEOUT`: 接口调用超时时间（秒）
- `SDK_MAX_RETRY`: 最大重试次数
- `LOG_LEVEL`: 日志级别

## 开发规范

### 代码风格
- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用 MyPy 进行类型检查

### 提交规范
- 提交前运行代码格式化和检查
- 编写单元测试
- 更新相关文档

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 联系方式

- 项目地址: https://github.com/medical-insurance-sdk/medical-insurance-sdk
- 问题反馈: https://github.com/medical-insurance-sdk/medical-insurance-sdk/issues

## 更新日志

### v1.0.0 (开发中)
- 项目基础架构搭建
- 数据库连接和配置管理
- 基础SDK框架实现