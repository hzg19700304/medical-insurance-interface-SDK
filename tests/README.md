# 医保接口SDK测试指南

本目录包含医保接口SDK的所有测试用例，采用分层测试架构。

## 测试结构

```
tests/
├── __init__.py
├── README.md                    # 本文件
├── test_runner.py              # 统一测试运行器
├── test_basic.py               # 基础功能测试
├── test_core_components.py     # 核心组件测试
├── test_helpers.py             # 辅助工具测试
├── test_integration.py         # 基础集成测试
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── test_config_manager.py      # 配置管理器测试
│   ├── test_data_validator.py      # 数据验证器测试
│   ├── test_universal_processor.py # 通用处理器测试
│   ├── test_client_implementation.py # 客户端实现测试
│   ├── test_config_system.py       # 配置系统测试
│   ├── test_validation.py          # 验证组件测试
│   └── test_protocol_components.py # 协议组件测试
├── integration/                # 集成测试
│   ├── __init__.py
│   ├── test_1101_interface.py      # 1101接口测试
│   ├── test_2201_interface.py      # 2201接口测试
│   ├── test_interface_1101_person_info.py  # 1101详细测试
│   ├── test_interface_2201_settlement.py   # 2201详细测试
│   ├── test_apifox_integration.py  # Apifox集成测试
│   ├── test_his_integration*.py    # HIS系统集成测试
│   └── test_sdk_*.py              # SDK集成测试
├── performance/                # 性能测试
│   ├── __init__.py
│   ├── test_performance_stress.py  # 压力测试
│   ├── test_metrics_collector.py   # 指标收集测试
│   ├── run_stress_tests.py        # 压力测试运行器
│   └── simple_stress_test.py      # 简单压力测试
└── fixtures/                   # 测试数据和工具
    ├── __init__.py
    ├── insert_test_*.py           # 测试数据插入脚本
    ├── check_*.py                 # 数据检查脚本
    └── verify_*.py                # 验证脚本
```

## 运行测试

### 使用统一测试运行器

```bash
# 运行所有测试
python tests/test_runner.py

# 运行单元测试
python tests/test_runner.py --unit

# 运行集成测试
python tests/test_runner.py --integration

# 运行性能测试
python tests/test_runner.py --performance

# 运行快速测试
python tests/test_runner.py --quick

# 列出所有测试文件
python tests/test_runner.py --list
```

### 使用pytest直接运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定类型的测试
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/performance/ -v

# 运行特定测试文件
pytest tests/integration/test_1101_interface.py -v
```

## 测试分类

### 单元测试 (tests/unit/)
测试单个组件的功能，不依赖外部服务：
- 配置管理器
- 数据验证器
- 通用接口处理器
- 协议组件

### 集成测试 (tests/integration/)
测试组件间的协作和完整流程：
- 医保接口调用
- 数据库集成
- 外部服务集成
- HIS系统集成

### 性能测试 (tests/performance/)
测试系统性能和并发能力：
- 压力测试
- 并发测试
- 缓存性能测试
- 指标收集

### 测试数据 (tests/fixtures/)
测试相关的数据和工具：
- 测试数据插入脚本
- 数据验证脚本
- 配置检查工具

## 测试覆盖范围

### 核心功能
- ✅ 接口调用流程
- ✅ 数据验证和转换
- ✅ 配置管理
- ✅ 错误处理
- ✅ 缓存机制

### 医保接口
- ✅ 1101 人员信息查询
- ✅ 2201 门诊挂号
- ⏳ 其他接口（待扩展）

### 系统集成
- ✅ 数据库操作
- ✅ Redis缓存
- ✅ 异步任务处理
- ✅ HIS系统集成

## 测试最佳实践

### 1. 测试命名规范
- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 2. 测试组织
- 按功能模块组织测试
- 使用setup/teardown管理测试环境
- 使用fixtures提供测试数据

### 3. 断言和验证
- 使用明确的断言消息
- 验证预期结果和异常情况
- 测试边界条件

### 4. 测试隔离
- 每个测试独立运行
- 不依赖测试执行顺序
- 清理测试产生的数据

## 持续集成

测试可以集成到CI/CD流程中：

```yaml
# GitHub Actions示例
- name: Run Tests
  run: |
    python tests/test_runner.py --all
    pytest tests/ --cov=medical_insurance_sdk
```

## 故障排除

### 常见问题
1. **导入错误**：确保项目根目录在Python路径中
2. **数据库连接**：检查数据库配置和连接
3. **依赖缺失**：安装所有测试依赖

### 调试技巧
- 使用`-v`参数获取详细输出
- 使用`--tb=short`获取简洁的错误信息
- 单独运行失败的测试进行调试

## 贡献指南

添加新测试时请：
1. 选择合适的测试类别（unit/integration/performance）
2. 遵循现有的命名和组织规范
3. 添加适当的文档和注释
4. 确保测试可以独立运行