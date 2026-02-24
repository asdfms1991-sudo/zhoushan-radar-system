"""
日志管理模块
支持日志轮转、分类存储
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path


class LogManager:
    """日志管理器"""

    def __init__(self, log_dir='logs', max_bytes=10*1024*1024, backup_count=5):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def get_logger(self, name, level=logging.INFO):
        """获取日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 避免重复添加handler
        if logger.handlers:
            return logger

        # 文件handler - 轮转
        log_file = self.log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def get_error_logger(self, name='error'):
        """获取错误日志记录器"""
        log_file = self.log_dir / f"{name}.log"
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)

        if not logger.handlers:
            handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)

        return logger


class SystemLogger:
    """系统日志"""

    def __init__(self):
        self.log_manager = LogManager()

    def log_startup(self, info):
        """记录启动"""
        logger = self.log_manager.get_logger('system')
        logger.info(f"系统启动: {info}")

    def log_shutdown(self, info):
        """记录关闭"""
        logger = self.log_manager.get_logger('system')
        logger.info(f"系统关闭: {info}")

    def log_error(self, module, error, stack=None):
        """记录错误"""
        logger = self.log_manager.get_error_logger()
        logger.error(f"[{module}] {error}")
        if stack:
            logger.error(f"堆栈: {stack}")

    def log_warning(self, module, warning):
        """记录警告"""
        logger = self.log_manager.get_logger('system')
        logger.warning(f"[{module}] {warning}")

    def log_info(self, module, info):
        """记录信息"""
        logger = self.log_manager.get_logger('system')
        logger.info(f"[{module}] {info}")


# 全局实例
system_logger = SystemLogger()
