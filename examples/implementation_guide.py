#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK实施指南

本指南提供了医保接口SDK的详细实施步骤和最佳实践，包括：
- 环境准备和安装
- 配置管理
- 接口集成
- 测试验证
- 部署上线
- 运维监控

作者: 医保SDK开发团队
版本: 1.0.0
更新时间: 2024-01-15
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ImplementationStep:
    """实施步骤"""
    step_id: str
    title: str
    description: str
    commands: List[str]
    files: List[str]
    validation: str
    notes: List[str]


class MedicalInsuranceSDKImplementationGuide:
    """医保接口SDK实施指南"""
    
    def __init__(self):
        """初始化实施指南"""
        self.project_root = Path.cwd()
        self.config_dir = self.project_root / "config"
        self.examples_dir = self.project_root / "examples"
        self.docs_dir = self.project_root / "docs"
        
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "="*80)
        print(f" {title} ")
        print("="*80)
    
    def print_step(self, step: ImplementationStep):
        """打印实施步骤"""
        print(f"\n📋 步骤 {step.step_id}: {step.title}")
        print("-" * 60)
        print(f"描述: {step.description}")
        
        if step.commands:
            print("\n🔧 执行命令:")
            for cmd in step.commands:
                print(f"  $ {cmd}")
        
        if step.files:
            print("\n📁 相关文件:")
            for file in step.files:
                print(f"  - {file}")
        
        if step.validation:
            print(f"\n✅ 验证方法: {step.validation}")
        
        if step.notes:
            print("\n📝 注意事项:")
            for note in step.notes:
                print(f"  • {note}")
    
    def step_01_environment_preparation(self):
        """步骤1: 环境准备"""
        step = ImplementationStep(
            step_id="01",
            title="环境准备",
            description="准备开发和运行环境，安装必要的软件和依赖",
            commands=[
                "python --version  # 检查Python版本 (需要3.8+)",
                "pip install --upgrade pip",
                "pip install -r requirements.txt",
                "mysql --version  # 检查MySQL版本 (需要5.7+)",
                "redis-server --version  # 检查Redis版本 (需要6.0+)"
            ],
            files=[
                "requirements.txt",
                "pyproject.toml",
                ".env.example"
            ],
            validation="运行 python -c \"import medical_insurance_sdk; print('SDK导入成功')\"",
            notes=[
                "确保Python版本为3.8或更高",
                "MySQL需要支持JSON数据类型",
                "Redis用于缓存，建议配置持久化",
                "开发环境可以使用Docker快速搭建"
            ]
        )
        
        self.print_step(step)
        
        # 创建环境检查脚本
        self._create_environment_check_script()
    
    def step_02_database_setup(self):
        """步骤2: 数据库设置"""
        step = ImplementationStep(
            step_id="02",
            title="数据库设置",
            description="创建数据库、表结构，并初始化基础数据",
            commands=[
                "mysql -u root -p < database/setup_database.sql",
                "python scripts/initialize_config_data.py",
                "python scripts/validate_config_data.py"
            ],
            files=[
                "database/setup_database.sql",
                "database/schema/",
                "scripts/initialize_config_data.py"
            ],
            validation="运行数据库连接测试脚本",
            notes=[
                "建议为应用创建专用数据库用户",
                "生产环境需要配置数据库备份",
                "注意设置合适的字符集(utf8mb4)",
                "索引策略需要根据实际使用情况调整"
            ]
        )
        
        self.print_step(step)
        
        # 创建数据库初始化脚本
        self._create_database_init_script()
    
    def step_03_configuration_setup(self):
        """步骤3: 配置设置"""
        step = ImplementationStep(
            step_id="03",
            title="配置设置",
            description="配置应用参数、数据库连接、Redis缓存等",
            commands=[
                "cp .env.example .env",
                "# 编辑 .env 文件，填入实际配置",
                "python scripts/validate_config.py config/development.json"
            ],
            files=[
                ".env",
                "config/development.json",
                "config/production.json",
                "config/organization_config.json"
            ],
            validation="运行配置验证脚本",
            notes=[
                "敏感信息使用环境变量",
                "不同环境使用不同配置文件",
                "定期更新机构配置信息",
                "配置文件需要版本控制"
            ]
        )
        
        self.print_step(step)
        
        # 创建配置模板
        self._create_config_templates()
    
    def step_04_interface_configuration(self):
        """步骤4: 接口配置"""
        step = ImplementationStep(
            step_id="04",
            title="接口配置",
            description="配置医保接口参数、验证规则、响应映射等",
            commands=[
                "python scripts/import_interface_config.py",
                "python scripts/test_interface_config.py 1101",
                "python scripts/test_interface_config.py 2201"
            ],
            files=[
                "config/interface_config_template.json",
                "scripts/import_interface_config.py",
                "scripts/test_interface_config.py"
            ],
            validation="测试主要接口配置是否正确",
            notes=[
                "接口配置支持热更新",
                "验证规则需要根据实际需求调整",
                "响应映射要与前端需求匹配",
                "支持地区差异化配置"
            ]
        )
        
        self.print_step(step)
        
        # 创建接口配置脚本
        self._create_interface_config_script()
    
    def step_05_basic_testing(self):
        """步骤5: 基础测试"""
        step = ImplementationStep(
            step_id="05",
            title="基础测试",
            description="执行基础功能测试，验证SDK核心功能",
            commands=[
                "python -m pytest tests/test_basic.py -v",
                "python examples/basic_usage_example.py",
                "python test_connection_pool.py"
            ],
            files=[
                "tests/test_basic.py",
                "examples/basic_usage_example.py",
                "test_connection_pool.py"
            ],
            validation="所有基础测试用例通过",
            notes=[
                "测试前确保数据库和Redis正常运行",
                "测试数据不要使用真实患者信息",
                "记录测试结果和性能指标",
                "发现问题及时修复和重测"
            ]
        )
        
        self.print_step(step)
    
    def step_06_integration_testing(self):
        """步骤6: 集成测试"""
        step = ImplementationStep(
            step_id="06",
            title="集成测试",
            description="执行完整业务流程测试，验证端到端功能",
            commands=[
                "python -m pytest tests/test_integration.py -v",
                "python examples/common_scenarios_guide.py",
                "python test_his_integration_comprehensive.py"
            ],
            files=[
                "tests/test_integration.py",
                "examples/common_scenarios_guide.py",
                "test_his_integration_comprehensive.py"
            ],
            validation="完整业务流程测试通过",
            notes=[
                "测试覆盖主要业务场景",
                "验证异常处理机制",
                "检查日志记录完整性",
                "确认性能指标符合要求"
            ]
        )
        
        self.print_step(step)
    
    def step_07_performance_testing(self):
        """步骤7: 性能测试"""
        step = ImplementationStep(
            step_id="07",
            title="性能测试",
            description="执行性能和压力测试，验证系统承载能力",
            commands=[
                "python run_stress_tests.py",
                "python -m pytest tests/test_performance_stress.py -v",
                "python simple_stress_test.py"
            ],
            files=[
                "run_stress_tests.py",
                "tests/test_performance_stress.py",
                "simple_stress_test.py"
            ],
            validation="性能指标满足要求",
            notes=[
                "测试并发处理能力",
                "监控内存和CPU使用",
                "验证数据库连接池效果",
                "记录性能基线数据"
            ]
        )
        
        self.print_step(step)
    
    def step_08_security_configuration(self):
        """步骤8: 安全配置"""
        step = ImplementationStep(
            step_id="08",
            title="安全配置",
            description="配置安全参数，加强系统安全防护",
            commands=[
                "# 配置SSL/TLS证书",
                "# 设置访问控制规则",
                "# 配置日志审计",
                "python scripts/security_check.py"
            ],
            files=[
                "config/security_config.json",
                "scripts/security_check.py",
                "ssl/certificates/"
            ],
            validation="安全检查脚本通过",
            notes=[
                "敏感数据必须加密存储",
                "配置强密码策略",
                "启用访问日志记录",
                "定期更新安全配置"
            ]
        )
        
        self.print_step(step)
    
    def step_09_deployment_preparation(self):
        """步骤9: 部署准备"""
        step = ImplementationStep(
            step_id="09",
            title="部署准备",
            description="准备生产环境部署文件和脚本",
            commands=[
                "docker build -t medical-insurance-sdk .",
                "docker-compose -f docker-compose.prod.yml config",
                "python scripts/deploy_production.sh --dry-run"
            ],
            files=[
                "Dockerfile",
                "docker-compose.prod.yml",
                "scripts/deploy_production.sh"
            ],
            validation="部署脚本验证通过",
            notes=[
                "生产配置与开发配置分离",
                "容器化部署提高可移植性",
                "准备回滚方案",
                "配置健康检查"
            ]
        )
        
        self.print_step(step)
    
    def step_10_production_deployment(self):
        """步骤10: 生产部署"""
        step = ImplementationStep(
            step_id="10",
            title="生产部署",
            description="部署到生产环境并进行验证",
            commands=[
                "# 备份现有系统",
                "docker-compose -f docker-compose.prod.yml up -d",
                "python scripts/health_check.py",
                "python scripts/smoke_test.py"
            ],
            files=[
                "docker-compose.prod.yml",
                "scripts/health_check.py",
                "scripts/smoke_test.py"
            ],
            validation="生产环境健康检查通过",
            notes=[
                "分阶段部署降低风险",
                "监控系统状态",
                "准备应急预案",
                "及时处理告警"
            ]
        )
        
        self.print_step(step)
    
    def step_11_monitoring_setup(self):
        """步骤11: 监控设置"""
        step = ImplementationStep(
            step_id="11",
            title="监控设置",
            description="配置系统监控、日志收集和告警机制",
            commands=[
                "# 配置Prometheus监控",
                "# 设置Grafana仪表板",
                "# 配置日志收集",
                "python scripts/setup_monitoring.py"
            ],
            files=[
                "monitoring/prometheus.yml",
                "monitoring/grafana-dashboard.json",
                "scripts/setup_monitoring.py"
            ],
            validation="监控系统正常工作",
            notes=[
                "监控关键业务指标",
                "设置合理的告警阈值",
                "定期检查监控系统",
                "保留足够的历史数据"
            ]
        )
        
        self.print_step(step)
    
    def step_12_documentation_and_training(self):
        """步骤12: 文档和培训"""
        step = ImplementationStep(
            step_id="12",
            title="文档和培训",
            description="完善文档，培训相关人员",
            commands=[
                "# 生成API文档",
                "# 编写操作手册",
                "# 准备培训材料",
                "python scripts/generate_docs.py"
            ],
            files=[
                "docs/api-documentation.md",
                "docs/user-manual.md",
                "docs/troubleshooting-guide.md"
            ],
            validation="文档完整且准确",
            notes=[
                "文档要及时更新",
                "提供实际使用示例",
                "建立问题反馈机制",
                "定期组织培训"
            ]
        )
        
        self.print_step(step)
    
    def _create_environment_check_script(self):
        """创建环境检查脚本"""
        script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境检查脚本"""

import sys
import subprocess
import importlib

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要3.8+)")
        return False

def check_package(package_name):
    """检查Python包"""
    try:
        importlib.import_module(package_name)
        print(f"✓ {package_name} 已安装")
        return True
    except ImportError:
        print(f"✗ {package_name} 未安装")
        return False

def check_command(command):
    """检查命令是否可用"""
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {command} 可用")
            return True
        else:
            print(f"✗ {command} 不可用")
            return False
    except FileNotFoundError:
        print(f"✗ {command} 未找到")
        return False

def main():
    """主函数"""
    print("医保接口SDK环境检查")
    print("=" * 40)
    
    checks = []
    
    # 检查Python版本
    checks.append(check_python_version())
    
    # 检查必要的包
    packages = ['mysql.connector', 'redis', 'requests', 'pydantic']
    for package in packages:
        checks.append(check_package(package))
    
    # 检查外部命令
    commands = ['mysql', 'redis-server']
    for command in commands:
        checks.append(check_command(command))
    
    # 总结
    print("\\n" + "=" * 40)
    passed = sum(checks)
    total = len(checks)
    print(f"检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 环境检查通过，可以继续安装")
        return 0
    else:
        print("✗ 环境检查失败，请解决上述问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        script_path = self.project_root / "scripts" / "environment_check.py"
        script_path.parent.mkdir(exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✓ 创建环境检查脚本: {script_path}")
    
    def _create_database_init_script(self):
        """创建数据库初始化脚本"""
        script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库初始化脚本"""

import os
import json
import mysql.connector
from pathlib import Path

def create_database_connection():
    """创建数据库连接"""
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'charset': 'utf8mb4'
    }
    
    return mysql.connector.connect(**config)

def create_database_and_tables():
    """创建数据库和表"""
    conn = create_database_connection()
    cursor = conn.cursor()
    
    try:
        # 创建数据库
        db_name = os.getenv('DB_NAME', 'medical_insurance')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {db_name}")
        
        # 读取SQL文件
        sql_file = Path(__file__).parent.parent / "database" / "setup_database.sql"
        if sql_file.exists():
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 执行SQL语句
            for statement in sql_content.split(';'):
                if statement.strip():
                    cursor.execute(statement)
        
        conn.commit()
        print("✓ 数据库和表创建成功")
        
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    print("数据库初始化")
    print("=" * 30)
    
    try:
        create_database_and_tables()
        print("✓ 数据库初始化完成")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''
        
        script_path = self.project_root / "scripts" / "database_init.py"
        script_path.parent.mkdir(exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✓ 创建数据库初始化脚本: {script_path}")
    
    def _create_config_templates(self):
        """创建配置模板"""
        # 开发环境配置
        dev_config = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "database": "medical_insurance_dev",
                "username": "dev_user",
                "password": "${DB_PASSWORD}",
                "pool_size": 10
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "database": 0,
                "password": "${REDIS_PASSWORD}"
            },
            "logging": {
                "level": "DEBUG",
                "file": "logs/medical_insurance_sdk.log"
            },
            "security": {
                "secret_key": "${SECRET_KEY}",
                "token_expire_hours": 24
            }
        }
        
        # 生产环境配置
        prod_config = {
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT}",
                "database": "${DB_NAME}",
                "username": "${DB_USER}",
                "password": "${DB_PASSWORD}",
                "pool_size": 20
            },
            "redis": {
                "host": "${REDIS_HOST}",
                "port": "${REDIS_PORT}",
                "database": 0,
                "password": "${REDIS_PASSWORD}"
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/medical_insurance_sdk.log"
            },
            "security": {
                "secret_key": "${SECRET_KEY}",
                "token_expire_hours": 8
            }
        }
        
        # 保存配置文件
        self.config_dir.mkdir(exist_ok=True)
        
        with open(self.config_dir / "development.json", 'w', encoding='utf-8') as f:
            json.dump(dev_config, f, indent=2, ensure_ascii=False)
        
        with open(self.config_dir / "production.json", 'w', encoding='utf-8') as f:
            json.dump(prod_config, f, indent=2, ensure_ascii=False)
        
        print("✓ 创建配置模板文件")
    
    def _create_interface_config_script(self):
        """创建接口配置脚本"""
        script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接口配置导入脚本"""

import json
import mysql.connector
from pathlib import Path

def import_interface_config():
    """导入接口配置"""
    # 这里应该连接数据库并导入配置
    print("导入接口配置...")
    
    # 示例配置数据
    configs = {
        "1101": {
            "api_name": "人员信息获取",
            "required_params": ["mdtrt_cert_type", "mdtrt_cert_no", "psn_name"],
            "validation_rules": {
                "mdtrt_cert_type": {"enum": ["01", "02", "03"]},
                "certno": {"pattern": "^[0-9]{17}[0-9Xx]$"}
            }
        },
        "2201": {
            "api_name": "门诊结算",
            "required_params": ["mdtrt_id", "psn_no", "chrg_bchno"],
            "validation_rules": {
                "mdtrt_id": {"max_length": 30},
                "psn_no": {"max_length": 30}
            }
        }
    }
    
    for api_code, config in configs.items():
        print(f"  导入接口 {api_code}: {config['api_name']}")
    
    print("✓ 接口配置导入完成")

if __name__ == "__main__":
    import_interface_config()
'''
        
        script_path = self.project_root / "scripts" / "import_interface_config.py"
        script_path.parent.mkdir(exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✓ 创建接口配置脚本: {script_path}")
    
    def run_implementation_guide(self):
        """运行完整实施指南"""
        self.print_header("医保接口SDK实施指南")
        
        print("本指南将引导您完成医保接口SDK的完整实施过程。")
        print("请按照以下步骤逐步执行，确保每个步骤都成功完成后再进行下一步。")
        
        # 执行所有步骤
        steps = [
            self.step_01_environment_preparation,
            self.step_02_database_setup,
            self.step_03_configuration_setup,
            self.step_04_interface_configuration,
            self.step_05_basic_testing,
            self.step_06_integration_testing,
            self.step_07_performance_testing,
            self.step_08_security_configuration,
            self.step_09_deployment_preparation,
            self.step_10_production_deployment,
            self.step_11_monitoring_setup,
            self.step_12_documentation_and_training
        ]
        
        for step_func in steps:
            step_func()
        
        self.print_header("实施指南完成")
        print("🎉 恭喜！您已完成医保接口SDK的完整实施过程。")
        print("\n📋 后续工作:")
        print("  • 定期检查系统运行状态")
        print("  • 及时更新配置和文档")
        print("  • 收集用户反馈并持续改进")
        print("  • 关注SDK版本更新")
        
        print("\n📞 技术支持:")
        print("  • 文档: docs/")
        print("  • 示例: examples/")
        print("  • 问题反馈: GitHub Issues")


def main():
    """主函数"""
    guide = MedicalInsuranceSDKImplementationGuide()
    guide.run_implementation_guide()


if __name__ == "__main__":
    main()