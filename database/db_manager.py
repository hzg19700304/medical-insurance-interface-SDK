#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保接口SDK数据库管理工具
创建时间: 2024-01-15
版本: 1.0.0
"""

import os
import sys
import logging
import argparse
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    print("请安装pymysql: pip install pymysql")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, host: str = 'localhost', port: int = 3306, 
                 user: str = 'root', password: str = '', 
                 database: str = 'medical_insurance_sdk'):
        """
        初始化数据库管理器
        
        Args:
            host: 数据库主机
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
        # 获取脚本目录
        self.script_dir = Path(__file__).parent
        self.schema_dir = self.script_dir / 'schema'
    
    def connect(self, create_db: bool = False) -> bool:
        """
        连接数据库
        
        Args:
            create_db: 是否创建数据库（如果不存在）
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 如果需要创建数据库，先连接到mysql系统数据库
            if create_db:
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                
                # 创建数据库
                with self.connection.cursor() as cursor:
                    cursor.execute(f"""
                        CREATE DATABASE IF NOT EXISTS `{self.database}` 
                        DEFAULT CHARACTER SET utf8mb4 
                        DEFAULT COLLATE utf8mb4_unicode_ci
                    """)
                    logger.info(f"数据库 {self.database} 创建成功或已存在")
                
                self.connection.close()
            
            # 连接到目标数据库
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            logger.info(f"成功连接到数据库 {self.database}")
            return True
            
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("数据库连接已断开")
    
    def execute_sql_file(self, file_path: Path) -> bool:
        """
        执行SQL文件
        
        Args:
            file_path: SQL文件路径
            
        Returns:
            bool: 执行是否成功
        """
        if not file_path.exists():
            logger.error(f"SQL文件不存在: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句（简单处理，按分号分割）
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.connection.cursor() as cursor:
                for sql in sql_statements:
                    # 跳过注释和空行
                    if sql.startswith('--') or sql.startswith('/*') or not sql:
                        continue
                    
                    try:
                        cursor.execute(sql)
                        self.connection.commit()
                    except Exception as e:
                        logger.warning(f"执行SQL语句失败: {sql[:100]}... 错误: {e}")
                        continue
            
            logger.info(f"成功执行SQL文件: {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"执行SQL文件失败: {e}")
            return False
    
    def create_tables(self) -> bool:
        """创建数据库表"""
        logger.info("开始创建数据库表...")
        return self.execute_sql_file(self.schema_dir / '01_create_tables.sql')
    
    def create_indexes(self) -> bool:
        """创建索引"""
        logger.info("开始创建索引...")
        return self.execute_sql_file(self.schema_dir / '02_create_indexes.sql')
    
    def create_constraints(self) -> bool:
        """创建约束"""
        logger.info("开始创建约束...")
        return self.execute_sql_file(self.schema_dir / '03_create_constraints.sql')
    
    def insert_initial_data(self) -> bool:
        """插入初始数据"""
        logger.info("开始插入初始数据...")
        return self.execute_sql_file(self.schema_dir / '04_initial_data.sql')
    
    def setup_database(self) -> bool:
        """完整的数据库设置"""
        logger.info("开始完整的数据库设置...")
        
        steps = [
            ("创建表结构", self.create_tables),
            ("创建索引", self.create_indexes),
            ("创建约束", self.create_constraints),
            ("插入初始数据", self.insert_initial_data)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"执行步骤: {step_name}")
            if not step_func():
                logger.error(f"步骤失败: {step_name}")
                return False
        
        logger.info("数据库设置完成!")
        return True
    
    def check_database_status(self) -> Dict[str, Any]:
        """检查数据库状态"""
        status = {}
        
        try:
            with self.connection.cursor() as cursor:
                # 检查表数量
                cursor.execute("""
                    SELECT COUNT(*) as table_count 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = %s
                """, (self.database,))
                status['table_count'] = cursor.fetchone()['table_count']
                
                # 检查索引数量
                cursor.execute("""
                    SELECT COUNT(DISTINCT INDEX_NAME) as index_count 
                    FROM INFORMATION_SCHEMA.STATISTICS 
                    WHERE TABLE_SCHEMA = %s AND INDEX_NAME != 'PRIMARY'
                """, (self.database,))
                status['index_count'] = cursor.fetchone()['index_count']
                
                # 检查约束数量
                cursor.execute("""
                    SELECT COUNT(*) as constraint_count 
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                    WHERE TABLE_SCHEMA = %s
                """, (self.database,))
                status['constraint_count'] = cursor.fetchone()['constraint_count']
                
                # 检查触发器数量
                cursor.execute("""
                    SELECT COUNT(*) as trigger_count 
                    FROM INFORMATION_SCHEMA.TRIGGERS 
                    WHERE TRIGGER_SCHEMA = %s
                """, (self.database,))
                status['trigger_count'] = cursor.fetchone()['trigger_count']
                
                # 检查存储过程数量
                cursor.execute("""
                    SELECT COUNT(*) as procedure_count 
                    FROM INFORMATION_SCHEMA.ROUTINES 
                    WHERE ROUTINE_SCHEMA = %s
                """, (self.database,))
                status['procedure_count'] = cursor.fetchone()['procedure_count']
                
                # 检查数据记录数量
                tables = ['medical_interface_config', 'medical_organization_config', 
                         'medical_institution_info', 'business_operation_logs']
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                        status[f'{table}_count'] = cursor.fetchone()['count']
                    except:
                        status[f'{table}_count'] = 0
                
        except Exception as e:
            logger.error(f"检查数据库状态失败: {e}")
            status['error'] = str(e)
        
        return status
    
    def create_monthly_partition(self, year: int, month: int) -> bool:
        """
        创建月度分区
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            bool: 创建是否成功
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("CALL CreateMonthlyPartition(%s)", (f"{year}-{month:02d}-01",))
                self.connection.commit()
                logger.info(f"成功创建 {year}-{month:02d} 月度分区")
                return True
        except Exception as e:
            logger.error(f"创建月度分区失败: {e}")
            return False
    
    def cleanup_old_partitions(self, months_to_keep: int = 12) -> bool:
        """
        清理旧分区
        
        Args:
            months_to_keep: 保留的月份数
            
        Returns:
            bool: 清理是否成功
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("CALL DropOldPartitions(%s)", (months_to_keep,))
                self.connection.commit()
                logger.info(f"成功清理超过 {months_to_keep} 个月的旧分区")
                return True
        except Exception as e:
            logger.error(f"清理旧分区失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='医保接口SDK数据库管理工具')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', type=int, default=3306, help='数据库端口')
    parser.add_argument('--user', default='root', help='数据库用户名')
    parser.add_argument('--password', default='', help='数据库密码')
    parser.add_argument('--database', default='medical_insurance_sdk', help='数据库名称')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 初始化命令
    init_parser = subparsers.add_parser('init', help='初始化数据库')
    init_parser.add_argument('--create-db', action='store_true', help='创建数据库（如果不存在）')
    
    # 状态检查命令
    subparsers.add_parser('status', help='检查数据库状态')
    
    # 分区管理命令
    partition_parser = subparsers.add_parser('partition', help='分区管理')
    partition_parser.add_argument('--create', help='创建月度分区 (格式: YYYY-MM)')
    partition_parser.add_argument('--cleanup', type=int, help='清理旧分区，保留指定月份数')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建数据库管理器
    db_manager = DatabaseManager(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    try:
        if args.command == 'init':
            # 连接数据库
            if not db_manager.connect(create_db=args.create_db):
                return
            
            # 初始化数据库
            if db_manager.setup_database():
                logger.info("数据库初始化成功!")
            else:
                logger.error("数据库初始化失败!")
        
        elif args.command == 'status':
            # 连接数据库
            if not db_manager.connect():
                return
            
            # 检查状态
            status = db_manager.check_database_status()
            
            print("\n=== 数据库状态 ===")
            print(f"表数量: {status.get('table_count', 0)}")
            print(f"索引数量: {status.get('index_count', 0)}")
            print(f"约束数量: {status.get('constraint_count', 0)}")
            print(f"触发器数量: {status.get('trigger_count', 0)}")
            print(f"存储过程数量: {status.get('procedure_count', 0)}")
            print("\n=== 数据记录数量 ===")
            print(f"接口配置: {status.get('medical_interface_config_count', 0)}")
            print(f"机构配置: {status.get('medical_organization_config_count', 0)}")
            print(f"机构信息: {status.get('medical_institution_info_count', 0)}")
            print(f"操作日志: {status.get('business_operation_logs_count', 0)}")
        
        elif args.command == 'partition':
            # 连接数据库
            if not db_manager.connect():
                return
            
            if args.create:
                try:
                    year, month = map(int, args.create.split('-'))
                    db_manager.create_monthly_partition(year, month)
                except ValueError:
                    logger.error("日期格式错误，请使用 YYYY-MM 格式")
            
            if args.cleanup:
                db_manager.cleanup_old_partitions(args.cleanup)
    
    finally:
        db_manager.disconnect()


if __name__ == '__main__':
    main()