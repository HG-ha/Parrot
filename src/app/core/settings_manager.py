import os
import json
import app.core.mlog as mlog
from app.core.path_manager import PathManager

class SettingsManager:
    """
    设置管理类，负责读取和保存应用设置
    """
    def __init__(self):
        """初始化设置管理器"""
        self.path_manager = PathManager()
        self.settings_file = self.path_manager.settings_file
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """
        加载设置
        
        Returns:
            dict: 设置字典
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # 确保有默认值
                    return self._apply_default_settings(settings)
            except Exception as e:
                mlog.error(f"加载设置失败: {str(e)}")
                return self._get_default_settings()
        return self._get_default_settings()
    
    def _get_default_settings(self):
        """
        获取默认设置
        
        Returns:
            dict: 默认设置字典
        """
        return {
            'theme_mode': 'system',  # system, light, dark
            'api_url': 'http://127.0.0.1:8000',  # 默认API地址
            'model_host': '127.0.0.1',  # 默认模型运行host
            'model_port': '8000',  # 默认模型运行端口
            'auto_load_model': False,  # 默认不自动加载
            'output_dir': os.path.join(os.getcwd(), "output"),  # 默认输出目录
            'logging_enabled': False    # 默认不启用日志
        }
    
    def _apply_default_settings(self, settings):
        """
        应用默认设置到已有设置
        
        Args:
            settings: 已有设置字典
        
        Returns:
            dict: 合并后的设置字典
        """
        defaults = self._get_default_settings()
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value
        return settings
    
    def save_settings(self):
        """
        保存设置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            # 打印更多调试信息
            mlog.info(f"正在保存设置到: {self.settings_file}")
            mlog.debug(f"设置内容: {self.settings}")
            
            # 写入文件
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            
            # 验证文件是否正确写入
            if os.path.exists(self.settings_file):
                file_size = os.path.getsize(self.settings_file)
                mlog.info(f"设置已保存，文件大小: {file_size} 字节")
                return True
            else:
                mlog.error(f"无法验证设置文件是否已写入: {self.settings_file}")
                return False
                
        except Exception as e:
            mlog.error(f"保存设置失败: {str(e)}")
            # 尝试使用备选方法保存
            try:
                temp_file = f"{self.settings_file}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                # 如果写入成功，重命名文件
                if os.path.exists(temp_file):
                    os.replace(temp_file, self.settings_file)
                    mlog.info(f"使用备选方法保存设置成功")
                    return True
            except Exception as e2:
                mlog.error(f"备选保存方法也失败: {str(e2)}")
            return False
    
    def get(self, key, default=None):
        """
        获取设置值
        
        Args:
            key: 设置键
            default: 默认值
        
        Returns:
            设置值
        """
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """
        设置值
        
        Args:
            key: 设置键
            value: 设置值
        
        Returns:
            bool: 设置是否成功
        """
        try:
            self.settings[key] = value
            return True
        except Exception as e:
            mlog.error(f"设置值失败: {str(e)}")
            return False
    
    def update(self, settings_dict):
        """
        批量更新设置
        
        Args:
            settings_dict: 设置字典
        
        Returns:
            bool: 更新是否成功
        """
        try:
            for key, value in settings_dict.items():
                self.settings[key] = value
            return True
        except Exception as e:
            mlog.error(f"批量更新设置失败: {str(e)}")
            return False
