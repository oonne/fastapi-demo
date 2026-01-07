"""
日志配置模块
使用 Python 标准库 logging 实现日志记录到文件
支持每日时间轮换
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


def setup_logging(
    log_dir: str = "logs",
    app_log_level: str = "INFO",
    access_log_level: str = "INFO",
    backup_count: int = 30,
) -> None:
    """
    配置应用日志和 Uvicorn 访问日志
    
    Args:
        log_dir: 日志文件目录
        app_log_level: 应用日志级别
        access_log_level: 访问日志级别
        backup_count: 保留的日志文件数量（天数）
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 日志格式
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ========== 配置应用日志 ==========
    app_logger = logging.getLogger("app")
    app_logger.setLevel(getattr(logging, app_log_level.upper()))
    
    # 清除已有的处理器
    app_logger.handlers.clear()
    
    # 应用日志文件处理器（每日轮换）
    app_file_handler = TimedRotatingFileHandler(
        filename=str(log_path / "app.log"),
        when="midnight",  # 每天午夜轮换
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    app_file_handler.setLevel(getattr(logging, app_log_level.upper()))
    app_file_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(app_file_handler)
    
    # 应用错误日志文件处理器（单独记录 ERROR 及以上级别）
    error_file_handler = TimedRotatingFileHandler(
        filename=str(log_path / "error.log"),
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(error_file_handler)
    
    # 控制台输出（可选，用于开发环境）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, app_log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    app_logger.addHandler(console_handler)
    
    # ========== 配置 Uvicorn 访问日志 ==========
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(getattr(logging, access_log_level.upper()))
    
    # 清除已有的处理器
    uvicorn_access_logger.handlers.clear()
    
    # 访问日志文件处理器（每日轮换）
    access_file_handler = TimedRotatingFileHandler(
        filename=str(log_path / "access.log"),
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    access_file_handler.setLevel(getattr(logging, access_log_level.upper()))
    # 访问日志使用简化格式
    access_formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    access_file_handler.setFormatter(access_formatter)
    uvicorn_access_logger.addHandler(access_file_handler)
    
    # ========== 配置 Uvicorn 错误日志 ==========
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(logging.INFO)
    
    # Uvicorn 错误日志文件处理器
    uvicorn_error_file_handler = TimedRotatingFileHandler(
        filename=str(log_path / "uvicorn.log"),
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    uvicorn_error_file_handler.setLevel(logging.INFO)
    uvicorn_error_file_handler.setFormatter(detailed_formatter)
    uvicorn_error_logger.addHandler(uvicorn_error_file_handler)
    
    # ========== 配置根日志记录器（防止其他库的日志丢失）==========
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # 只记录 WARNING 及以上级别
    
    # 根日志文件处理器
    root_file_handler = TimedRotatingFileHandler(
        filename=str(log_path / "root.log"),
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    root_file_handler.setLevel(logging.WARNING)
    root_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(root_file_handler)


def get_logger(name: str = "app") -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为 "app"
    
    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)

