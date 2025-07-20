#!/usr/bin/env python3
"""开发环境设置脚本"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"执行: {description}")
    print(f"命令: {command}")
    print(f"{'='*50}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} 成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
    else:
        print(f"❌ {description} 失败")
        if result.stderr:
            print(f"错误: {result.stderr}")
        return False
    
    return True


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本需要3.8或更高")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def setup_virtual_environment():
    """设置虚拟环境"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ 虚拟环境已存在")
        return True
    
    return run_command("python -m venv venv", "创建虚拟环境")


def install_dependencies():
    """安装依赖"""
    # 检查是否在虚拟环境中
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  建议在虚拟环境中运行")
    
    commands = [
        ("pip install --upgrade pip", "升级pip"),
        ("pip install -r requirements.txt", "安装项目依赖"),
        ("pip install -e .", "安装项目包（开发模式）")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True


def setup_environment_file():
    """设置环境变量文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env文件已存在")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ 已从.env.example创建.env文件")
        print("⚠️  请根据实际情况修改.env文件中的配置")
        return True
    else:
        print("❌ .env.example文件不存在")
        return False


def create_directories():
    """创建必要的目录"""
    directories = ["logs", "data", "config"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {directory}")
        else:
            print(f"✅ 目录已存在: {directory}")
    
    return True


def run_tests():
    """运行测试"""
    return run_command("python -m pytest tests/ -v", "运行测试")


def main():
    """主函数"""
    print("🚀 开始设置医保SDK开发环境")
    
    steps = [
        ("检查Python版本", check_python_version),
        ("设置虚拟环境", setup_virtual_environment),
        ("安装依赖", install_dependencies),
        ("设置环境文件", setup_environment_file),
        ("创建目录", create_directories),
        ("运行测试", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 步骤: {step_name}")
        if not step_func():
            print(f"❌ 步骤失败: {step_name}")
            sys.exit(1)
    
    print("\n🎉 开发环境设置完成！")
    print("\n📝 下一步:")
    print("1. 激活虚拟环境: source venv/bin/activate (Linux/Mac) 或 venv\\Scripts\\activate (Windows)")
    print("2. 修改.env文件中的数据库配置")
    print("3. 运行测试: pytest tests/")
    print("4. 开始开发!")


if __name__ == "__main__":
    main()