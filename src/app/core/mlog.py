import logging
import socket
import os
from datetime import datetime

hostname = socket.gethostname()
# 日志开关状态
_logging_enabled = False
class HostnameColoredFormatter(logging.Formatter):
    COLOR_CODES = {
        logging.DEBUG: "\033[0;37m",
        logging.INFO: "\033[0;36m",
        logging.WARNING: "\033[0;33m",
        logging.ERROR: "\033[0;31m",
        logging.CRITICAL: "\033[1;31m"
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        record.hostname = hostname
        color_code = self.COLOR_CODES.get(record.levelno, self.RESET_CODE)
        message = super().format(record)
        return f"{color_code}{message}{self.RESET_CODE}"


log_dir = "logs"

# 创建日志文件名（使用当前日期）
log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

# 配置日志记录器
logger = logging.getLogger("CosyVoice")
logger.setLevel(logging.DEBUG)
if _logging_enabled:
    # 配置文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)

# 配置控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(HostnameColoredFormatter(
    '%(asctime)s - %(hostname)s - %(levelname)s - %(filename)s:%(lineno)d - Func: %(funcName)s - PID: %(process)d - %(message)s'
))

    
logger.addHandler(console_handler)


if not os.path.exists(log_dir) and _logging_enabled:
    os.makedirs(log_dir)

# 导出便捷函数
def debug(msg): 
    if _logging_enabled:
        logger.debug(msg)
        
def info(msg): 
    if _logging_enabled:
        logger.info(msg)
        
def warning(msg): 
    if _logging_enabled:
        logger.warning(msg)
        
def error(msg): 
    if _logging_enabled:
        logger.error(msg)
        
def critical(msg): 
    if _logging_enabled:
        logger.critical(msg)

# 控制日志开关的函数
def enable_logging(enabled=True):
    """
    启用或禁用日志
    
    Args:
        enabled: 是否启用日志
        
    Returns:
        bool: 当前日志状态
    """
    global _logging_enabled  # 确保在函数开始处声明
    try:
        _logging_enabled = bool(enabled)  # 确保转换为布尔值
        if _logging_enabled:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.CRITICAL)  # 设置为仅显示关键错误
        return _logging_enabled
    except Exception:
        # 如果发生异常，恢复到之前状态并返回
        if _logging_enabled:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.CRITICAL)
        return _logging_enabled

# 获取当前日志状态
def get_logging_status():
    return _logging_enabled