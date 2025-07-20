"""日志管理工具类"""

import logging
import logging.handlers
import os
from typing import Dict, Any, Optional


class LogManager:
    """日志管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化日志管理器

        Args:
            config: 日志配置
        """
        self.config = config or {}
        self.level = self.config.get("level", "INFO")
        self.log_file = self.config.get("file", "logs/medical_insurance_sdk.log")
        self.max_size = self.config.get("max_size", "10MB")
        self.backup_count = self.config.get("backup_count", 5)

        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("medical_insurance_sdk")
        logger.setLevel(getattr(logging, self.level.upper()))

        # 避免重复添加处理器
        if logger.handlers:
            return logger

        # 创建日志目录
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self._parse_size(self.max_size),
            backupCount=self.backup_count,
            encoding="utf-8",
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()

        # 格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)

    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)

    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)

    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)

    def log_api_call(
        self, api_code: str, request_data: dict, response_data: dict, kwargs: dict
    ):
        """记录API调用日志

        Args:
            api_code: 接口编码
            request_data: 请求数据
            response_data: 响应数据
            kwargs: 其他参数
        """
        # TODO: 实现详细的API调用日志记录
        self.info(f"API调用: {api_code}, 机构: {kwargs.get('org_code', 'unknown')}")
        self.debug(f"请求数据: {request_data}")
        self.debug(f"响应数据: {response_data}")
