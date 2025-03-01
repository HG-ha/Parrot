import app.core.mlog as mlog

class LoggingManager:
    """日志管理器类，负责控制日志的启用/禁用状态"""
    
    def __init__(self, settings_manager=None):
        """
        初始化日志管理器
        
        Args:
            settings_manager: 设置管理器实例，如果提供，将从中读取日志配置
        """
        self.settings_manager = settings_manager
        self._initialize()
    
    def _initialize(self):
        """初始化日志状态"""
        if self.settings_manager:
            enabled = self.settings_manager.get('logging_enabled', True)
            self.enable_logging(enabled)
    
    def enable_logging(self, enabled=True):
        """
        启用或禁用日志
        
        Args:
            enabled: 是否启用日志
        
        Returns:
            bool: 当前日志状态
        """
        try:
            # 应用日志状态
            actual_status = mlog.enable_logging(enabled)
            
            # 如果设置管理器可用，同步设置
            if self.settings_manager and actual_status != self.settings_manager.get('logging_enabled'):
                self.settings_manager.set('logging_enabled', actual_status)
                self.settings_manager.save_settings()
                
            return actual_status
        except Exception as e:
            # 发生异常时，返回当前状态
            return mlog.get_logging_status()
    
    def get_logging_status(self):
        """
        获取当前日志状态
        
        Returns:
            bool: 当前日志是否启用
        """
        return mlog.get_logging_status()
    
    def toggle_logging(self):
        """
        切换日志状态
        
        Returns:
            bool: 切换后的日志状态
        """
        current_status = self.get_logging_status()
        return self.enable_logging(not current_status)
    
    def update_from_settings(self):
        """从设置管理器更新日志状态"""
        if self.settings_manager:
            enabled = self.settings_manager.get('logging_enabled', True)
            self.enable_logging(enabled)
