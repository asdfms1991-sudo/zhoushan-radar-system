"""
日志系统 V2.0
支持分级日志、文件轮转、多输出
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """日志管理器"""
    
    # 日志级别映射
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, name: str = 'radar', config: Optional[dict] = None):
        """初始化日志系统"""
        self.name = name
        self.config = config or {}
        self.log_level = self.config.get('log_level', 'INFO')
        self.log_dir = self.config.get('log_dir', 'logs')
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        # 创建logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.LEVELS.get(self.log_level, logging.INFO))
        
        # 清除已有handlers
        self.logger.handlers.clear()
        
        # 创建日志目录
        log_path = Path(self.log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.LEVELS.get(self.log_level, logging.INFO))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（带轮转）
        log_file = log_path / f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log'
        max_bytes = self.config.get('log_rotation', {}).get('max_size_mb', 100) * 1024 * 1024
        backup_count = self.config.get('log_rotation', {}).get('backup_count', 5)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 错误日志单独文件
        error_file = log_path / f'{self.name}_error.log'
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=max_bytes,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def critical(self, msg: str):
        self.logger.critical(msg)
    
    def exception(self, msg: str):
        self.logger.exception(msg)
    
    def get_logger(self) -> logging.Logger:
        """获取logger对象"""
        return self.logger


def setup_logger(name: str = 'radar', config: Optional[dict] = None) -> logging.Logger:
    """便捷函数：创建日志器"""
    return Logger(name, config).get_logger()


class LoggerManager:
    """日志管理器（支持多模块）"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, config: Optional[dict] = None) -> logging.Logger:
        """获取指定名称的logger"""
        if name not in cls._loggers:
            cls._loggers[name] = Logger(name, config).get_logger()
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, level: str):
        """设置全局日志级别"""
        for logger in cls._loggers.values():
            logger.setLevel(Logger.LEVELS.get(level, logging.INFO))


if __name__ == '__main__':
    # 测试日志
    logger = setup_logger('test')
    logger.info("测试信息")
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    print("日志测试完成")
