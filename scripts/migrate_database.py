#!/usr/bin/env python3
"""
医保接口SDK数据库迁移脚本
支持数据库初始化、升级和数据迁移
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

import pymysql
from pymysql.cursors import DictCursor


class DatabaseMigrator:
    """数据库迁移器"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=False
            )
            self.logger.info(f"成功连接到数据库 {self.host}:{self.port}/{self.database}")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.logger.info("数据库连接已关闭")
    
    def execute_sql_file(self, file_path: str) -> bool:
        """执行SQL文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.connection.cursor() as cursor:
                for statement in statements:
                    if statement and not statement.startswith('--'):
                        cursor.execute(statement)
                
                self.connection.commit()
            
            self.logger.info(f"成功执行SQL文件: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"执行SQL文件失败 {file_path}: {e}")
            self.connection.rollback()
            return False
    
    def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        try:
            # 连接到MySQL服务器（不指定数据库）
            temp_connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            
            with temp_connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES LIKE %s", (self.database,))
                result = cursor.fetchone()
            
            temp_connection.close()
            return result is not None
            
        except Exception as e:
            self.logger.error(f"检查数据库存在性失败: {e}")
            return False
    
    def create_database(self) -> bool:
        """创建数据库"""
        try:
            # 连接到MySQL服务器（不指定数据库）
            temp_connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            
            with temp_connection.cursor() as cursor:
                cursor.execute(f"""
                    CREATE DATABASE IF NOT EXISTS `{self.database}` 
                    DEFAULT CHARACTER SET utf8mb4 
                    DEFAULT COLLATE utf8mb4_unicode_ci
                """)
            
            temp_connection.close()
            self.logger.info(f"数据库 {self.database} 创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建数据库失败: {e}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (self.database, table_name))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            self.logger.error(f"检查表存在性失败: {e}")
            return False
    
    def get_migration_version(self) -> Optional[str]:
        """获取当前迁移版本"""
        try:
            if not self.check_table_exists('migration_history'):
                return None
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT version FROM migration_history 
                    ORDER BY applied_at DESC LIMIT 1
                """)
                result = cursor.fetchone()
                return result['version'] if result else None
        except Exception as e:
            self.logger.error(f"获取迁移版本失败: {e}")
            return None
    
    def record_migration(self, version: str, description: str) -> bool:
        """记录迁移历史"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO migration_history (version, description, applied_at)
                    VALUES (%s, %s, %s)
                """, (version, description, datetime.now()))
                self.connection.commit()
            
            self.logger.info(f"迁移记录已保存: {version}")
            return True
        except Exception as e:
            self.logger.error(f"记录迁移历史失败: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """初始化数据库"""
        self.logger.info("开始初始化数据库...")
        
        # 检查并创建数据库
        if not self.check_database_exists():
            if not self.create_database():
                return False
        
        # 连接到数据库
        self.connect()
        
        try:
            # 创建迁移历史表
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        version VARCHAR(50) NOT NULL,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_version (version),
                        INDEX idx_applied_at (applied_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                self.connection.commit()
            
            # 执行数据库初始化脚本
            schema_files = [
                'database/schema/01_create_tables.sql',
                'database/schema/02_create_indexes.sql',
                'database/schema/03_create_constraints.sql',
                'database/schema/04_initial_data.sql'
            ]
            
            for schema_file in schema_files:
                if os.path.exists(schema_file):
                    if not self.execute_sql_file(schema_file):
                        return False
                else:
                    self.logger.warning(f"Schema文件不存在: {schema_file}")
            
            # 记录初始化版本
            self.record_migration('1.0.0', '数据库初始化')
            
            self.logger.info("数据库初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            return False
        finally:
            self.disconnect()
    
    def backup_database(self, backup_file: str) -> bool:
        """备份数据库"""
        self.logger.info(f"开始备份数据库到: {backup_file}")
        
        try:
            import subprocess
            
            # 使用mysqldump备份
            cmd = [
                'mysqldump',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--user={self.user}',
                f'--password={self.password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                self.database
            ]
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"数据库备份成功: {backup_file}")
                return True
            else:
                self.logger.error(f"数据库备份失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            return False
    
    def restore_database(self, backup_file: str) -> bool:
        """恢复数据库"""
        self.logger.info(f"开始从备份恢复数据库: {backup_file}")
        
        try:
            import subprocess
            
            # 使用mysql恢复
            cmd = [
                'mysql',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--user={self.user}',
                f'--password={self.password}',
                self.database
            ]
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                self.logger.info("数据库恢复成功")
                return True
            else:
                self.logger.error(f"数据库恢复失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"数据库恢复失败: {e}")
            return False
    
    def validate_database(self) -> bool:
        """验证数据库结构"""
        self.logger.info("开始验证数据库结构...")
        
        self.connect()
        
        try:
            # 检查必要的表
            required_tables = [
                'medical_interface_config',
                'medical_organization_config',
                'business_operation_logs',
                'medical_institution_info',
                'medical_interface_stats'
            ]
            
            missing_tables = []
            for table in required_tables:
                if not self.check_table_exists(table):
                    missing_tables.append(table)
            
            if missing_tables:
                self.logger.error(f"缺少必要的表: {', '.join(missing_tables)}")
                return False
            
            # 检查配置数据
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM medical_interface_config")
                config_count = cursor.fetchone()['count']
                
                if config_count == 0:
                    self.logger.warning("接口配置表为空")
            
            self.logger.info("数据库结构验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库验证失败: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='医保接口SDK数据库迁移工具')
    parser.add_argument('action', choices=['init', 'backup', 'restore', 'validate'], 
                       help='操作类型')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', type=int, default=3306, help='数据库端口')
    parser.add_argument('--user', default='root', help='数据库用户')
    parser.add_argument('--password', required=True, help='数据库密码')
    parser.add_argument('--database', default='medical_insurance_sdk', help='数据库名')
    parser.add_argument('--backup-file', help='备份文件路径')
    
    args = parser.parse_args()
    
    # 创建迁移器
    migrator = DatabaseMigrator(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    success = False
    
    try:
        if args.action == 'init':
            success = migrator.initialize_database()
        elif args.action == 'backup':
            if not args.backup_file:
                backup_file = f"backup_{args.database}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            else:
                backup_file = args.backup_file
            success = migrator.backup_database(backup_file)
        elif args.action == 'restore':
            if not args.backup_file:
                print("错误: 恢复操作需要指定备份文件")
                sys.exit(1)
            success = migrator.restore_database(args.backup_file)
        elif args.action == 'validate':
            success = migrator.validate_database()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"操作失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()