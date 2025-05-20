from app.core.utils import run_async
from app.ui import SettingsPage
import app.core.mlog as mlog
import os
import subprocess

class SettingsCallbacks:
    def __init__(self, app, page, settings_manager, api_manager, model_manager, path_manager):
        self.app = app
        self.page = page
        self.settings_manager = settings_manager
        self.api_manager = api_manager
        self.model_manager = model_manager
        self.path_manager = path_manager
        
        # 初始化日志状态
        self._apply_logging_settings()

    async def settings_on_test_connection(self, api_url):
        """测试API连接"""
        # 确保当前显示的是设置页面
        settings_page = self.app.content_container.content
        if not isinstance(settings_page, SettingsPage):
            return
            
        # 测试连接
        success, message = await self.api_manager.check_connection(api_url)
        settings_page.update_api_status(success, message)
        
        return success, message

    def settings_on_save_api_settings(self, api_settings):
        """保存API设置"""
        # 更新设置
        self.settings_manager.update(api_settings)
        self.settings_manager.save_settings()
        
        # 重新测试连接
        run_async(self.settings_on_test_connection(api_settings['api_url']))

    def settings_on_toggle_model(self):
        """切换模型运行状态"""
        # 确保当前显示的是设置页面
        settings_page = self.app.content_container.content
        if not isinstance(settings_page, SettingsPage):
            return
        # 检查模型当前运行状态
        if self.model_manager.is_starting():
            # 停止模型
            self.model_manager.stop_model()
            settings_page.update_model_status(False)
        elif self.model_manager.is_running():
            # 停止模型
            self.model_manager.stop_model()
            settings_page.update_model_status(False)
        else:
            # 获取模型设置
            host = self.settings_manager.get('model_host', '127.0.0.1')
            port = self.settings_manager.get('model_port', '8000')
            
            # 定义更新输出的回调
            def update_output(output_text):
                settings_page.update_model_output(output_text)
            
            # 运行模型，传入 path_manager
            success, error = self.model_manager.run_model(
                host, port, 
                update_output, 
                settings_page.update_model_status,
                path_manager=self.path_manager
            )
            
            # 处理模型缺失的情况
            if not success:
                if error == "MODEL_NOT_FOUND" or error == "PYTHON_NOT_FOUND":
                    # 显示模型下载提示
                    settings_page.show_model_download_dialog()
                    return
                else:
                    # 其他错误则显示在输出区域
                    settings_page.update_model_output(f"启动模型失败: {error}")
            
            # 启动进程成功后更新为正在启动状态
            settings_page.update_model_status(False, success)

    async def settings_on_download_model(self):
        """处理模型下载"""
        # 确保当前显示的是设置页面
        settings_page = self.app.content_container.content
        if not isinstance(settings_page, SettingsPage):
            return
            
        try:
            # 开始下载模型
            success, error = await self.model_manager.download_model(
                progress_callback=settings_page.update_download_progress
            )
            
            if success:
                # 确保更新UI显示成功消息
                settings_page.update_download_progress(-1, -1, "模型准备完成！")
                # 下载成功后关闭对话框
                settings_page.close_model_download_dialog()
                # 尝试启动模型
                self.settings_on_toggle_model()
            else:
                # 显示错误信息
                settings_page.update_download_progress(-1, -1, f"下载失败: {error}")
                
        except Exception as e:
            # 确保异常也能显示给用户
            settings_page.update_download_progress(-1, -1, f"发生错误: {str(e)}")
            mlog.error(f"下载模型时发生错误: {str(e)}")

    def settings_on_theme_change(self, theme_mode):
        """更改主题设置"""
        self.settings_manager.set('theme_mode', theme_mode)
        self.settings_manager.save_settings()
        self.app.set_theme_mode(theme_mode)
    
    def settings_on_auto_load_change(self, auto_load):
        """更改自动加载模型设置"""
        self.settings_manager.set('auto_load_model', auto_load)
        self.settings_manager.save_settings()
    
    def settings_on_clear_cache(self):
        """清除缓存目录"""
        return self.path_manager.clear_cache()
        
    def settings_on_logging_change(self, logging_enabled):
        """更改日志启用状态"""
        try:
            # 更新设置
            self.settings_manager.set('logging_enabled', logging_enabled)
            
            # 立即保存设置到配置文件
            self.settings_manager.save_settings()
            
            # 应用新的日志状态
            actual_status = mlog.enable_logging(logging_enabled)
                
            return actual_status
        except Exception as e:
            # 如果发生错误，返回当前实际状态
            return mlog.get_logging_status()
        
    def _apply_logging_settings(self):
        """应用日志设置"""
        logging_enabled = self.settings_manager.get('logging_enabled', True)
        mlog.enable_logging(logging_enabled)

    def settings_on_open_model_folder(self):
        """打开模型文件夹"""
        # 使用path_manager中的模型路径
        model_dir = self.path_manager.model_path
        
        try:
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
                mlog.info(f"创建模型目录: {model_dir}")
                
            mlog.info(f"打开模型目录: {model_dir}")
            if os.name == 'nt':  # Windows
                os.startfile(model_dir)
            elif os.name == 'posix':  # macOS 和 Linux
                subprocess.run(['xdg-open' if os.sys.platform == 'linux' else 'open', model_dir])
        except Exception as e:
            mlog.error(f"打开模型文件夹失败: {str(e)}")

    def settings_on_save_paths(self, paths):
        """保存路径设置"""
        try:
            # 验证路径
            for key, path in paths.items():
                if path and not self.path_manager.is_valid_path(path):
                    mlog.error(f"无效的路径: {path}")
                    return False

            # 保存路径设置
            if self.path_manager.save_custom_paths(paths):
                # 保存到设置文件
                self.settings_manager.set('paths', paths)
                self.settings_manager.save_settings()
                
                # 更新模型管理器的路径
                self.model_manager.update_model_path(self.path_manager)
                
                return True
            return False
        except Exception as e:
            mlog.error(f"保存路径设置失败: {str(e)}")
            return False

    def settings_on_reset_paths(self):
        """恢复默认路径设置"""
        try:
            # 移除paths设置
            self.settings_manager.settings.pop('paths', None)
            self.settings_manager.save_settings()

            # 重新初始化路径管理器
            self.path_manager._load_custom_paths()
            self.path_manager._init_dirs()
            
            # 更新模型管理器的路径
            self.model_manager.update_model_path(self.path_manager)
            
            return True
        except Exception as e:
            mlog.error(f"恢复默认路径设置失败: {str(e)}")
            return False
