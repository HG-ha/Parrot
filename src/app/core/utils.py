import os
import shutil
import datetime
import app.core.mlog as mlog
import json
import uuid
import asyncio
from urllib.parse import urlparse

def is_url(string):
    """
    判断字符串是否为有效URL
    
    Args:
        string: 要检查的字符串
    
    Returns:
        bool: 是否为有效URL
    """
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_file_path(path):
    """
    判断路径是否为有效的文件路径
    
    Args:
        path: 要检查的路径
    
    Returns:
        bool: 是否为有效文件路径
    """
    try:
        # 检查路径是否存在
        if os.path.isfile(path):
            return True
            
        # 检查路径中的目录是否存在
        dir_path = os.path.dirname(path)
        if dir_path and os.path.isdir(dir_path):
            return True
            
        return False
    except:
        return False

def generate_unique_filename(prefix="", extension=".wav"):
    """
    生成唯一的文件名
    
    Args:
        prefix: 文件名前缀
        extension: 文件扩展名
    
    Returns:
        str: 唯一文件名
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}{extension}"

def ensure_dir_exists(path):
    """
    确保目录存在
    
    Args:
        path: 目录路径
    
    Returns:
        bool: 是否成功
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as e:
        mlog.error(f"创建目录失败: {str(e)}")
        return False

def move_file(src, dst):
    """
    移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
    
    Returns:
        bool: 是否成功
    """
    try:
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
            
        # 移动文件
        shutil.move(src, dst)
        return True
    except Exception as e:
        mlog.error(f"移动文件失败: {str(e)}")
        return False

def copy_file(src, dst):
    """
    复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
    
    Returns:
        bool: 是否成功
    """
    try:
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
            
        # 复制文件
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        mlog.error(f"复制文件失败: {str(e)}")
        return False

def delete_file(path):
    """
    删除文件
    
    Args:
        path: 文件路径
    
    Returns:
        bool: 是否成功
    """
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    except Exception as e:
        mlog.error(f"删除文件失败: {str(e)}")
        return False

def format_file_size(size_bytes):
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        str: 格式化后的文件大小
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_file_info(path):
    """
    获取文件信息
    
    Args:
        path: 文件路径
    
    Returns:
        dict: 文件信息字典，包含名称、大小、修改时间等
    """
    try:
        if not os.path.exists(path):
            return None
            
        stat_info = os.stat(path)
        return {
            'name': os.path.basename(path),
            'path': path,
            'size': stat_info.st_size,
            'size_formatted': format_file_size(stat_info.st_size),
            'modified': datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            'created': datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        mlog.error(f"获取文件信息失败: {str(e)}")
        return None

def run_async(coroutine):
    """
    运行异步代码
    
    Args:
        coroutine: 要运行的协程
    
    Returns:
        任何协程的返回值
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(coroutine)

def load_json(file_path, default=None):
    """
    从文件加载JSON数据
    
    Args:
        file_path: JSON文件路径
        default: 如果文件不存在或加载失败时的默认值
    
    Returns:
        加载的数据或默认值
    """
    if default is None:
        default = {}
        
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        mlog.error(f"加载JSON文件失败 {file_path}: {str(e)}")
        return default

def save_json(file_path, data):
    """
    保存数据到JSON文件
    
    Args:
        file_path: JSON文件路径
        data: 要保存的数据
    
    Returns:
        bool: 是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        mlog.error(f"保存JSON文件失败 {file_path}: {str(e)}")
        return False
