#!/usr/bin/env python3
"""
医保接口SDK开发环境快速搭建脚本
自动化设置开发环境，包括依赖安装、数据库初始化、配置文件生成等
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional


class DevEnvironmentSetup:
    """开发环境设置器"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def check_system_requirements(self) -> bool:
        """检查系统要求"""
        self.logger.info("检查系统要求...")
        
        requirements = {
            'python3': 'Python 3.8+',
            'pip': 'pip包管理器',
            'git': 'Git版本控制'
        }
        
        missing = []
        for cmd, desc in requirements.items():
            if not shutil.which(cmd):
                missing.append(f"{cmd} ({desc})")
        
        if missing:
            self.logger.error(f"缺少必要的系统组件: {', '.join(missing)}")
            return False
        
        # 检查Python版本
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            version_str = result.stdout.strip()
            self.logger.info(f"Python版本: {version_str}")
            
            # 简单的版本检查
            if 'Python 3.' not in version_str:
                self.logger.error("需要Python 3.8或更高版本")
                return False
                
        except Exception as e:
            self.logger.error(f"检查Python版本失败: {e}")
            return False
        
        self.logger.info("系统要求检查通过")
        return True
    
    def create_virtual_environment(self) -> bool:
        """创建虚拟环境"""
        venv_path = self.project_root / 'venv'
        
        if venv_path.exists():
            self.logger.info("虚拟环境已存在，跳过创建")
            return True
        
        self.logger.info("创建Python虚拟环境...")
        
        try:
            subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], 
                          check=True)
            self.logger.info("虚拟环境创建成功")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"创建虚拟环境失败: {e}")
            return False
    
    def get_venv_python(self) -> str:
        """获取虚拟环境Python路径"""
        venv_path = self.project_root / 'venv'
        
        if os.name == 'nt':  # Windows
            return str(venv_path / 'Scripts' / 'python.exe')
        else:  # Unix/Linux/macOS
            return str(venv_path / 'bin' / 'python')
    
    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        self.logger.info("安装项目依赖...")
        
        python_path = self.get_venv_python()
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            self.logger.error("requirements.txt文件不存在")
            return False
        
        try:
            # 升级pip
            subprocess.run([python_path, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                          check=True)
            
            # 安装依赖
            subprocess.run([python_path, '-m', 'pip', 'install', '-r', str(requirements_file)], 
                          check=True)
            
            self.logger.info("依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"安装依赖失败: {e}")
            return False
    
    def create_directories(self) -> bool:
        """创建必要的目录"""
        self.logger.info("创建项目目录...")
        
        directories = [
            'logs',
            'data',
            'secrets',
            'docker/mysql',
            'docker/redis',
            'docker/nginx/ssl',
            'tests/fixtures',
            'medical_insurance_sdk/api',
            'medical_insurance_sdk/config',
            'medical_insurance_sdk/core',
            'medical_insurance_sdk/utils',
            'medical_insurance_sdk/models',
            'medical_insurance_sdk/async_processing',
            'medical_insurance_sdk/integration'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("目录创建完成")
        return True
    
    def create_config_files(self) -> bool:
        """创建配置文件"""
        self.logger.info("创建配置文件...")
        
        # 创建.env文件
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'
        
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
            self.logger.info("已创建.env配置文件")
        
        # 创建开发环境配置
        dev_config = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "username": "medical_user",
                "password": "wodemima",
                "database": "medical_insurance_sdk",
                "charset": "utf8mb4"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": "wodemima",
                "db": 0
            },
            "logging": {
                "level": "DEBUG",
                "file": "logs/medical_insurance_sdk.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "sdk": {
                "version": "1.0.0",
                "timeout": 30,
                "max_retry": 3,
                "environment": "development"
            }
        }
        
        config_file = self.project_root / 'config' / 'development.json'
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(dev_config, f, ensure_ascii=False, indent=2)
        
        self.logger.info("开发配置文件创建完成")
        return True
    
    def setup_git_hooks(self) -> bool:
        """设置Git钩子"""
        self.logger.info("设置Git钩子...")
        
        git_dir = self.project_root / '.git'
        if not git_dir.exists():
            self.logger.warning("不是Git仓库，跳过Git钩子设置")
            return True
        
        hooks_dir = git_dir / 'hooks'
        
        # 创建pre-commit钩子
        pre_commit_hook = hooks_dir / 'pre-commit'
        pre_commit_content = '''#!/bin/bash
# 医保SDK pre-commit钩子

echo "运行代码质量检查..."

# 运行flake8检查
python -m flake8 medical_insurance_sdk/ tests/ --max-line-length=88 --extend-ignore=E203,W503

if [ $? -ne 0 ]; then
    echo "代码质量检查失败，请修复后再提交"
    exit 1
fi

# 运行单元测试
python -m pytest tests/ -v --tb=short

if [ $? -ne 0 ]; then
    echo "单元测试失败，请修复后再提交"
    exit 1
fi

echo "代码质量检查通过"
'''
        
        with open(pre_commit_hook, 'w', encoding='utf-8') as f:
            f.write(pre_commit_content)
        
        # 设置执行权限（Unix系统）
        if os.name != 'nt':
            os.chmod(pre_commit_hook, 0o755)
        
        self.logger.info("Git钩子设置完成")
        return True
    
    def create_test_files(self) -> bool:
        """创建测试文件"""
        self.logger.info("创建测试文件...")
        
        # 创建pytest配置
        pytest_ini = self.project_root / 'pytest.ini'
        if not pytest_ini.exists():
            pytest_content = '''[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
'''
            with open(pytest_ini, 'w', encoding='utf-8') as f:
                f.write(pytest_content)
        
        # 创建基础测试文件
        test_basic = self.project_root / 'tests' / 'test_basic.py'
        if not test_basic.exists():
            test_content = '''"""
基础测试用例
"""

import pytest
from medical_insurance_sdk import __version__


def test_version():
    """测试版本信息"""
    assert __version__ is not None


def test_import():
    """测试模块导入"""
    from medical_insurance_sdk.sdk import MedicalInsuranceSDK
    assert MedicalInsuranceSDK is not None


@pytest.mark.unit
def test_basic_functionality():
    """测试基本功能"""
    # 这里添加基本功能测试
    pass
'''
            with open(test_basic, 'w', encoding='utf-8') as f:
                f.write(test_content)
        
        self.logger.info("测试文件创建完成")
        return True
    
    def create_development_scripts(self) -> bool:
        """创建开发脚本"""
        self.logger.info("创建开发脚本...")
        
        scripts_dir = self.project_root / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        
        # 创建运行测试脚本
        run_tests_script = scripts_dir / 'run_tests.py'
        if not run_tests_script.exists():
            script_content = '''#!/usr/bin/env python3
"""
运行测试脚本
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """运行所有测试"""
    project_root = Path(__file__).parent.parent
    
    # 运行单元测试
    print("运行单元测试...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/', '-v', '--cov=medical_insurance_sdk',
        '--cov-report=html', '--cov-report=term'
    ], cwd=project_root)
    
    if result.returncode != 0:
        print("测试失败")
        sys.exit(1)
    
    print("所有测试通过")

if __name__ == '__main__':
    run_tests()
'''
            with open(run_tests_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
        
        self.logger.info("开发脚本创建完成")
        return True
    
    def setup_ide_config(self) -> bool:
        """设置IDE配置"""
        self.logger.info("设置IDE配置...")
        
        # VSCode配置
        vscode_dir = self.project_root / '.vscode'
        vscode_dir.mkdir(exist_ok=True)
        
        # 创建VSCode设置
        vscode_settings = {
            "python.defaultInterpreterPath": "./venv/bin/python",
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "python.linting.mypyEnabled": True,
            "python.formatting.provider": "black",
            "python.testing.pytestEnabled": True,
            "python.testing.pytestArgs": ["tests"],
            "files.exclude": {
                "**/__pycache__": True,
                "**/*.pyc": True,
                ".pytest_cache": True,
                "htmlcov": True
            }
        }
        
        settings_file = vscode_dir / 'settings.json'
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(vscode_settings, f, indent=2)
        
        # 创建启动配置
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: 当前文件",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal"
                },
                {
                    "name": "Python: 运行测试",
                    "type": "python",
                    "request": "launch",
                    "module": "pytest",
                    "args": ["tests/", "-v"],
                    "console": "integratedTerminal"
                }
            ]
        }
        
        launch_file = vscode_dir / 'launch.json'
        with open(launch_file, 'w', encoding='utf-8') as f:
            json.dump(launch_config, f, indent=2)
        
        self.logger.info("IDE配置完成")
        return True
    
    def print_next_steps(self):
        """打印后续步骤"""
        print("\n" + "="*60)
        print("开发环境设置完成！")
        print("="*60)
        print()
        print("后续步骤:")
        print("1. 激活虚拟环境:")
        if os.name == 'nt':
            print("   .\\venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print()
        print("2. 配置数据库连接:")
        print("   编辑 .env 文件，设置数据库连接参数")
        print()
        print("3. 初始化数据库:")
        print("   python scripts/migrate_database.py init --password=your_password")
        print()
        print("4. 运行测试:")
        print("   python -m pytest tests/ -v")
        print()
        print("5. 启动开发服务器:")
        print("   python -m uvicorn medical_insurance_sdk.api.main:app --reload")
        print()
        print("6. 使用Docker (可选):")
        print("   ./scripts/docker-setup.sh dev")
        print()
        print("有用的命令:")
        print("  - 代码格式化: python -m black medical_insurance_sdk/")
        print("  - 代码检查: python -m flake8 medical_insurance_sdk/")
        print("  - 类型检查: python -m mypy medical_insurance_sdk/")
        print("  - 测试覆盖率: python -m pytest --cov=medical_insurance_sdk")
        print()
    
    def setup_all(self) -> bool:
        """执行完整设置"""
        self.logger.info("开始设置开发环境...")
        
        steps = [
            ("检查系统要求", self.check_system_requirements),
            ("创建虚拟环境", self.create_virtual_environment),
            ("安装项目依赖", self.install_dependencies),
            ("创建项目目录", self.create_directories),
            ("创建配置文件", self.create_config_files),
            ("设置Git钩子", self.setup_git_hooks),
            ("创建测试文件", self.create_test_files),
            ("创建开发脚本", self.create_development_scripts),
            ("设置IDE配置", self.setup_ide_config)
        ]
        
        for step_name, step_func in steps:
            self.logger.info(f"执行步骤: {step_name}")
            
            try:
                if not step_func():
                    self.logger.error(f"步骤失败: {step_name}")
                    return False
            except Exception as e:
                self.logger.error(f"步骤异常: {step_name} - {e}")
                return False
        
        self.print_next_steps()
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='医保接口SDK开发环境设置')
    parser.add_argument('--skip-venv', action='store_true', help='跳过虚拟环境创建')
    parser.add_argument('--skip-deps', action='store_true', help='跳过依赖安装')
    
    args = parser.parse_args()
    
    try:
        setup = DevEnvironmentSetup()
        
        if args.skip_venv:
            setup.logger.info("跳过虚拟环境创建")
        if args.skip_deps:
            setup.logger.info("跳过依赖安装")
        
        success = setup.setup_all()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n设置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"设置失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()