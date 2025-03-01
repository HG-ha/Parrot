import os
import shutil
import app.core.mlog as mlog

class PathManager:
    """
    路径管理类，负责应用中各种路径的管理
    """
    def __init__(self):
        """初始化路径管理器，创建必要的目录"""
        # 应用根目录
        self.root_dir = os.getcwd()

        # 数据目录
        self.data_dir = os.path.join(self.root_dir, "config")
        
        # 历史记录目录和文件
        self.history_dir = os.path.join(self.root_dir, "history")
        self.history_file = os.path.join(self.data_dir, "history.json")
        
        # 设置文件
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        
        # 角色文件
        self.roles_file = os.path.join(self.data_dir, "roles.json")
        
        # 数据库文件
        self.database_file = os.path.join(self.data_dir, "cosyvoice.db")
        
        # 临时目录
        self.temp_dir = os.path.join(self.root_dir, "input")
        
        # 输出目录
        self.output_dir = os.path.join(self.root_dir, "output")
        
        # 模型路径
        self.model_path = os.path.join(self.root_dir, "cosyvoice_api")
        
        # 调用初始化
        self._init_dirs()
    
    def _init_dirs(self):
        """创建必要的目录"""
        try:
            # 创建目录（如果不存在）
            dirs = [
                self.data_dir, 
                self.history_dir,
                self.temp_dir,
                self.output_dir,
            ]
            
            for dir_path in dirs:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    mlog.info(f"创建目录: {dir_path}")
        except Exception as e:
            mlog.error(f"创建目录失败: {str(e)}")
    
    def get_file_path(self, filename, directory=None):
        """
        获取指定目录下的文件路径
        
        Args:
            filename: 文件名
            directory: 目录名，如果为None，则使用根目录
        
        Returns:
            str: 文件完整路径
        """
        if directory is None:
            return os.path.join(self.root_dir, filename)
        
        if directory == "data":
            return os.path.join(self.data_dir, filename)
        elif directory == "history":
            return os.path.join(self.history_dir, filename)
        elif directory == "input":
            return os.path.join(self.temp_dir, filename)
        elif directory == "output":
            return os.path.join(self.output_dir, filename)
        # elif directory == "fonts":
        #     return os.path.join(self.fonts_dir, filename)
        # elif directory == "assets":
        #     return os.path.join(self.assets_dir, filename)
        else:
            # 如果是其他目录，直接拼接
            return os.path.join(directory, filename)
    
    def clear_cache(self):
        """
        清除临时文件和缓存
        
        Returns:
            bool: 是否成功清除
        """
        try:
            # 清空临时目录
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir)
                mlog.info(f"清空临时目录: {self.temp_dir}")
            return True
        except Exception as e:
            mlog.error(f"清除缓存失败: {str(e)}")
            return False
    
    def ensure_dir_exists(self, dir_path):
        """
        确保目录存在，如果不存在则创建
        
        Args:
            dir_path: 目录路径
        
        Returns:
            bool: 是否成功确保目录存在
        """
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                mlog.info(f"创建目录: {dir_path}")
            return True
        except Exception as e:
            mlog.error(f"确保目录存在失败: {str(e)}")
            return False
    
    def is_valid_path(self, path):
        """
        检查路径是否有效
        
        Args:
            path: 要检查的路径
        
        Returns:
            bool: 路径是否有效
        """
        try:
            # 检查路径是否存在或是否可以创建
            if os.path.exists(os.path.dirname(path)):
                return True
            
            # 尝试创建路径的父目录
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
                return True
                
            return False
        except Exception:
            return False
