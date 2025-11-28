"""
日志系统配置
使用 loguru 进行日志管理
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: str = "logs", log_level: str = "INFO"):
    """
    配置 loguru 日志系统
    
    Args:
        log_dir: 日志文件目录
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # 移除默认的 handler
    logger.remove()
    
    # 添加控制台输出（彩色）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 添加文件输出（按日期轮转）
    logger.add(
        log_path / "seo_workbench_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留 30 天
        compression="zip",  # 压缩旧日志
        encoding="utf-8"
    )
    
    # 添加错误日志文件（仅记录 ERROR 及以上级别）
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更久
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成 - 日志目录: {log_path.absolute()}, 级别: {log_level}")


def get_logger(name: str = None):
    """
    获取 logger 实例
    
    Args:
        name: logger 名称（可选）
        
    Returns:
        logger 实例
    """
    if name:
        return logger.bind(name=name)
    return logger


class LogCapture:
    """日志捕获器，用于在 UI 中显示日志"""
    
    def __init__(self):
        self.logs = []
        self.max_logs = 1000  # 最多保留 1000 条日志
        
    def write(self, message):
        """
        写入日志消息
        
        Args:
            message: 日志消息
        """
        self.logs.append(message)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
    
    def get_logs(self, level: str = None) -> list:
        """
        获取日志列表
        
        Args:
            level: 过滤日志级别（可选）
            
        Returns:
            日志消息列表
        """
        if level:
            return [log for log in self.logs if level in log]
        return self.logs
    
    def clear(self):
        """清空日志"""
        self.logs.clear()


# 全局日志捕获器实例
_log_capture = LogCapture()


def setup_ui_logger():
    """
    为 UI 添加日志捕获器
    
    Returns:
        LogCapture 实例
    """
    logger.add(
        _log_capture.write,
        format="{time:HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )
    return _log_capture


def get_log_capture() -> LogCapture:
    """
    获取日志捕获器实例
    
    Returns:
        LogCapture 实例
    """
    return _log_capture


if __name__ == "__main__":
    # 测试代码
    setup_logger(log_level="DEBUG")
    
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")
    
    # 测试 UI 日志捕获
    capture = setup_ui_logger()
    logger.info("这条日志会被捕获")
    print("\n捕获的日志:")
    for log in capture.get_logs():
        print(log)

