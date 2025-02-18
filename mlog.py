import logging
import socket
import os
from datetime import datetime

hostname = socket.gethostname()

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

# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 创建日志文件名（使用当前日期）
log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

# 配置日志记录器
logger = logging.getLogger("CosyVoice")
logger.setLevel(logging.DEBUG)

# 配置文件处理器
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 配置控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(HostnameColoredFormatter(
    '%(asctime)s - %(hostname)s - %(levelname)s - %(filename)s:%(lineno)d - Func: %(funcName)s - PID: %(process)d - %(message)s'
))

# 添加处理器到日志记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 导出便捷函数
def debug(msg): logger.debug(msg)
def info(msg): logger.info(msg)
def warning(msg): logger.warning(msg)
def error(msg): logger.error(msg)
def critical(msg): logger.critical(msg)