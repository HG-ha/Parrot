import os
import mlog
class PathManager:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 创建必要的目录
        self.config_dir = os.path.join(self.base_path, 'config')
        self.history_dir = os.path.join(self.base_path, 'history')
        self.output_dir = os.path.join(self.base_path, 'output')
        self.input_dir = os.path.join(self.base_path, 'input')
        
        self._ensure_directories()
        
        # 配置文件路径
        self.history_file = os.path.join(self.config_dir, 'history.json')
        self.settings_file = os.path.join(self.config_dir, 'settings.json')
        self.roles_file = os.path.join(self.config_dir, 'roles.json')

    def _ensure_directories(self):
        """确保所有必要的目录都存在"""
        for directory in [self.config_dir, self.history_dir, self.output_dir, self.input_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def clear_cache(self):
        """清除输入输出缓存目录"""
        import shutil
        for directory in [self.output_dir, self.input_dir]:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        mlog.error(f"清除缓存失败: {str(e)}")
