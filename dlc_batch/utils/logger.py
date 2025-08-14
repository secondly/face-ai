"""
日志管理模块

提供统一的日志配置和管理功能。
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(name="dlc_batch", level="INFO", log_file=None, 
                format_str=None, max_size="10MB", backup_count=5):
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，None表示不写入文件
        format_str: 日志格式字符串
        max_size: 日志文件最大大小
        backup_count: 备份文件数量
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 默认格式
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_str)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (可选)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 解析文件大小
        if isinstance(max_size, str):
            if max_size.endswith("MB"):
                max_bytes = int(max_size[:-2]) * 1024 * 1024
            elif max_size.endswith("KB"):
                max_bytes = int(max_size[:-2]) * 1024
            else:
                max_bytes = int(max_size)
        else:
            max_bytes = max_size
        
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name="dlc_batch"):
    """获取已配置的日志记录器"""
    return logging.getLogger(name)

class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self):
        """获取类专用的日志记录器"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger
