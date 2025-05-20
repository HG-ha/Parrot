import os
import shutil
import app.core.mlog as mlog
import platform
import flet as ft
import json

class PathManager:
    """
    路径管理类，负责应用中各种路径的管理
    """
    def __init__(self, page: ft.Page = None, package_name: str = "com.parrot.parrot"):
        """初始化路径管理器，创建必要的目录"""
        # 应用包名
        self.package_name = package_name
        self.page = page
        # 检测平台类型
        self.is_mobile = self.page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS,ft.PagePlatform.ANDROID_TV]
        self.platform = page.platform if page else None

        # 确定应用根目录
        self.root_dir = self._determine_root_dir()
        
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
        self.temp_dir = os.path.join(self.root_dir, "temp")
        
        # 输出目录
        self.output_dir = os.path.join(self.root_dir, "output")
        
        # 模型路径 - 默认在安装目录，但可以被自定义配置覆盖
        self.app_install_dir = os.getcwd()
        self.model_path = os.path.join(self.app_install_dir, "cosyvoice_api")
        
        # 从设置文件读取自定义路径 - 确保在初始化其他路径之后调用
        self._load_custom_paths()
        
        # 调用初始化
        self._init_dirs()
        
        mlog.info(f"应用数据根目录: {self.root_dir}")
        mlog.info(f"模型目录: {self.model_path}")
    
    def _determine_root_dir(self):
        """根据平台确定应用数据根目录"""
        if self.platform in [ft.PagePlatform.ANDROID,ft.PagePlatform.ANDROID_TV]:
            # Android 平台使用标准的应用私有数据目录
            base_dir = f"/storage/emulated/0/Android/data/{self.package_name}/files"
            try:
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir, exist_ok=True)
                if os.access(base_dir, os.W_OK):
                    return base_dir
            except Exception as e:
                mlog.warning(f"无法访问Android私有目录: {str(e)}")
                errdialog = ft.AlertDialog(
                    title=ft.Text("目录创建错误"),
                    content=ft.Text(f"应用无法创建必要的目录:\n{e}\n\n请确保应用有足够的权限访问存储。\n\n{base_dir}"),
                    actions=[
                        ft.TextButton("确定", on_click=lambda: self.page.close(errdialog)),
                    ],
                )
                self.page.open(errdialog)
                self.page.update()

        elif self.platform == ft.PagePlatform.IOS:
            # iOS 平台使用Documents目录
            try:
                home_dir = os.path.expanduser("~")
                base_dir = os.path.join(home_dir, "Documents", "Parrot")
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir, exist_ok=True)
                return base_dir
            except Exception as e:
                mlog.warning(f"无法创建iOS数据目录: {str(e)}")
        
        # 其他平台或回退选项 - 使用标准用户数据目录
        try:
            if platform.system() == "Windows":
                # Windows: %APPDATA%\Parrot
                base_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser("~")), "Parrot")
            elif platform.system() == "Darwin":
                # macOS: ~/Library/Application Support/Parrot
                base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Parrot")
            else:
                # Linux/其他: ~/.local/share/Parrot
                base_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "Parrot")
            
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            return base_dir
        except Exception as e:
            mlog.error(f"创建标准数据目录失败: {str(e)}")
            
            # 最后的回退选项: 当前工作目录下的data文件夹
            fallback_dir = os.path.join(os.getcwd(), "data")
            if not os.path.exists(fallback_dir):
                os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
    
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
            error_msg = f"创建目录失败: {str(e)}"
            mlog.error(error_msg)
                
            errdialog = ft.AlertDialog(
                title=ft.Text("目录创建错误"),
                content=ft.Text(f"应用无法创建必要的目录:\n{error_msg}\n\n请确保应用有足够的权限访问存储。"),
                actions=[
                    ft.TextButton("确定", on_click=lambda: self.page.close(errdialog)),
                ],
            )
            self.page.open(errdialog)
    
    def _load_custom_paths(self):
        """从设置文件加载自定义路径"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                paths = settings.get('paths', {})
                
                # 仅更新允许自定义的路径
                if paths.get('model_path') and os.path.exists(paths['model_path']):
                    mlog.info(f"使用自定义模型路径: {paths['model_path']}")
                    self.model_path = paths['model_path']
                else:
                    mlog.info(f"使用默认模型路径: {self.model_path}")
                    
                if paths.get('history_dir'):
                    self.history_dir = paths['history_dir']
                
        except Exception as e:
            mlog.error(f"加载自定义路径配置失败: {str(e)}")
    
    def save_custom_paths(self, paths):
        """保存自定义路径配置"""
        try:
            self.ensure_dir_exists(self.data_dir)
            
            # 验证路径
            for key, path in paths.items():
                if path and not self.is_valid_path(path):
                    mlog.error(f"无效的路径: {path}")
                    return False
            
            # 处理模型路径
            if paths.get('model_path'):
                model_path = os.path.abspath(paths['model_path'])
                if not os.path.exists(model_path):
                    os.makedirs(model_path, exist_ok=True)
                    mlog.info(f"创建模型路径: {model_path}")
                paths['model_path'] = model_path
            
            # 读取现有设置
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # 保存设置
            settings['paths'] = paths
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            # 重新加载路径
            self._load_custom_paths()
            
            # 确保所有必要的目录都存在
            self._init_dirs()
            
            return True
        except Exception as e:
            mlog.error(f"保存自定义路径配置失败: {str(e)}")
            return False
    
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
            if not path:  # 如果路径为空，允许使用默认路径
                return True
                
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
