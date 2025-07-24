"""配置管理CLI工具"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .factory import config_factory
from .env_manager import env_manager
from .validator import ConfigValidator
from ..exceptions import ConfigurationException


class ConfigCLI:
    """配置管理命令行工具"""
    
    def __init__(self):
        """初始化CLI工具"""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(
            description="医保接口SDK配置管理工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  # 验证当前环境配置
  python -m medical_insurance_sdk.config.cli validate
  
  # 创建开发环境配置模板
  python -m medical_insurance_sdk.config.cli create-template development
  
  # 生成环境变量模板
  python -m medical_insurance_sdk.config.cli generate-env
  
  # 显示配置信息
  python -m medical_insurance_sdk.config.cli info
  
  # 备份配置文件
  python -m medical_insurance_sdk.config.cli backup ./backup
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # validate 命令
        validate_parser = subparsers.add_parser('validate', help='验证配置')
        validate_parser.add_argument('--environment', '-e', help='环境名称')
        validate_parser.add_argument('--config-file', '-f', help='配置文件路径')
        validate_parser.add_argument('--config-dir', '-d', help='配置目录')
        validate_parser.add_argument('--env-file', help='环境变量文件路径')
        
        # create-template 命令
        template_parser = subparsers.add_parser('create-template', help='创建配置模板')
        template_parser.add_argument('environment', help='环境名称')
        template_parser.add_argument('--output-dir', '-o', default='.', help='输出目录')
        template_parser.add_argument('--include-sensitive', action='store_true', help='包含敏感信息')
        
        # generate-env 命令
        env_parser = subparsers.add_parser('generate-env', help='生成环境变量模板')
        env_parser.add_argument('--output', '-o', default='.env.template', help='输出文件')
        env_parser.add_argument('--include-sensitive', action='store_true', help='包含敏感信息')
        
        # info 命令
        info_parser = subparsers.add_parser('info', help='显示配置信息')
        info_parser.add_argument('--format', choices=['json', 'table'], default='table', help='输出格式')
        
        # backup 命令
        backup_parser = subparsers.add_parser('backup', help='备份配置文件')
        backup_parser.add_argument('backup_dir', help='备份目录')
        
        # restore 命令
        restore_parser = subparsers.add_parser('restore', help='恢复配置文件')
        restore_parser.add_argument('backup_dir', help='备份目录')
        
        # test-connection 命令
        test_parser = subparsers.add_parser('test-connection', help='测试连接')
        test_parser.add_argument('--environment', '-e', help='环境名称')
        test_parser.add_argument('--config-file', '-f', help='配置文件路径')
        
        return parser
    
    def run(self, args: Optional[list] = None):
        """运行CLI工具"""
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return
        
        try:
            if parsed_args.command == 'validate':
                self._validate_command(parsed_args)
            elif parsed_args.command == 'create-template':
                self._create_template_command(parsed_args)
            elif parsed_args.command == 'generate-env':
                self._generate_env_command(parsed_args)
            elif parsed_args.command == 'info':
                self._info_command(parsed_args)
            elif parsed_args.command == 'backup':
                self._backup_command(parsed_args)
            elif parsed_args.command == 'restore':
                self._restore_command(parsed_args)
            elif parsed_args.command == 'test-connection':
                self._test_connection_command(parsed_args)
        except Exception as e:
            print(f"错误: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _validate_command(self, args):
        """验证配置命令"""
        print("正在验证配置...")
        
        try:
            # 创建配置
            config = config_factory.create_configuration(
                environment=args.environment,
                config_file=args.config_file,
                config_dir=args.config_dir,
                load_env_file=args.env_file,
                validate=False  # 我们手动验证以获取详细报告
            )
            
            # 验证配置
            validator = ConfigValidator()
            is_valid = validator.validate_settings(config)
            report = validator.get_validation_report()
            
            # 验证环境变量
            env_report = env_manager.validate_environment()
            
            # 输出结果
            print(f"\n配置验证结果:")
            print(f"环境: {config.environment}")
            print(f"配置有效: {'是' if is_valid else '否'}")
            
            if report['errors']:
                print(f"\n错误 ({len(report['errors'])}):")
                for error in report['errors']:
                    print(f"  - {error}")
            
            if report['warnings']:
                print(f"\n警告 ({len(report['warnings'])}):")
                for warning in report['warnings']:
                    print(f"  - {warning}")
            
            print(f"\n环境变量:")
            print(f"  已定义: {env_report['total_count']}")
            print(f"  已加载: {env_report['loaded_count']}")
            print(f"  缺少必需: {len(env_report['missing_required'])}")
            
            if env_report['missing_required']:
                print(f"  缺少的必需环境变量:")
                for var in env_report['missing_required']:
                    print(f"    - {var}")
            
            if not is_valid or not env_report['valid']:
                sys.exit(1)
            else:
                print("\n✓ 配置验证通过")
                
        except Exception as e:
            print(f"配置验证失败: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _create_template_command(self, args):
        """创建配置模板命令"""
        print(f"正在创建 {args.environment} 环境配置模板...")
        
        try:
            templates = config_factory.generate_configuration_template(
                environment=args.environment,
                include_env_file=True,
                include_sensitive=args.include_sensitive
            )
            
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, content in templates.items():
                output_file = output_dir / filename
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"已创建: {output_file}")
            
            print(f"\n✓ 配置模板创建完成，输出目录: {output_dir}")
            
        except Exception as e:
            print(f"创建配置模板失败: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _generate_env_command(self, args):
        """生成环境变量模板命令"""
        print("正在生成环境变量模板...")
        
        try:
            template_content = env_manager.generate_env_template(
                include_sensitive=args.include_sensitive
            )
            
            output_file = Path(args.output)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            print(f"✓ 环境变量模板已生成: {output_file}")
            
        except Exception as e:
            print(f"生成环境变量模板失败: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _info_command(self, args):
        """显示配置信息命令"""
        try:
            info = config_factory.get_configuration_info()
            
            if args.format == 'json':
                print(json.dumps(info, indent=2, ensure_ascii=False))
            else:
                self._print_info_table(info)
                
        except Exception as e:
            print(f"获取配置信息失败: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _print_info_table(self, info):
        """以表格形式打印配置信息"""
        print("配置信息:")
        print("=" * 50)
        
        # 环境变量信息
        env_info = info.get('environment_variables', {})
        print(f"环境变量:")
        print(f"  总定义数量: {env_info.get('total_defined', 0)}")
        print(f"  已加载数量: {env_info.get('loaded_count', 0)}")
        
        validation = env_info.get('validation', {})
        print(f"  验证状态: {'通过' if validation.get('valid', False) else '失败'}")
        if validation.get('errors'):
            print(f"  错误数量: {len(validation['errors'])}")
        if validation.get('missing_required'):
            print(f"  缺少必需: {len(validation['missing_required'])}")
        
        # 配置文件信息
        config_info = info.get('config_files', {})
        print(f"\n配置文件:")
        print(f"  配置目录: {config_info.get('config_directory', 'N/A')}")
        
        available_envs = config_info.get('available_environments', [])
        if available_envs:
            print(f"  可用环境: {', '.join(available_envs)}")
        else:
            print(f"  可用环境: 无")
    
    def _backup_command(self, args):
        """备份配置文件命令"""
        print(f"正在备份配置文件到: {args.backup_dir}")
        
        try:
            backup_path = config_factory.backup_configuration(args.backup_dir)
            print(f"✓ 配置文件备份完成: {backup_path}")
            
        except Exception as e:
            print(f"备份配置文件失败: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _restore_command(self, args):
        """恢复配置文件命令"""
        print(f"正在从备份恢复配置文件: {args.backup_dir}")
        
        try:
            config_factory.restore_configuration(args.backup_dir)
            print("✓ 配置文件恢复完成")
            
        except Exception as e:
            print(f"恢复配置文件失败: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _test_connection_command(self, args):
        """测试连接命令"""
        print("正在测试连接...")
        
        try:
            # 创建配置
            config = config_factory.create_configuration(
                environment=args.environment,
                config_file=args.config_file,
                validate=False
            )
            
            # 测试连接
            validator = ConfigValidator()
            results = validator.test_connections(config)
            
            print(f"\n连接测试结果:")
            for service, success in results.items():
                status = "✓ 成功" if success else "✗ 失败"
                print(f"  {service}: {status}")
            
            if not all(results.values()):
                sys.exit(1)
            else:
                print("\n✓ 所有连接测试通过")
                
        except Exception as e:
            print(f"连接测试失败: {str(e)}", file=sys.stderr)
            sys.exit(1)


def main():
    """CLI入口点"""
    cli = ConfigCLI()
    cli.run()


if __name__ == '__main__':
    main()