import flet as ft
import threading
import app.core.mlog as mlog
import traceback
from concurrent.futures import ThreadPoolExecutor

# 导入功能管理器
from app.core.path_manager import PathManager
from app.core.settings_manager import SettingsManager
from app.core.role_manager import RoleManager
from app.core.history_manager import HistoryManager
from app.core.audio_manager import AudioManager
from app.core.model_manager import ModelManager
from app.core.api_manager import ApiManager
from app.core.utils import run_async

# 导入自定义UI组件
from app.ui import TitleBar, SideMenu, ClonePage, HistoryPage, RolesPage, SettingsPage

# 导入回调处理器
from app.callbacks.clone_callbacks import CloneCallbacks
from app.callbacks.history_callbacks import HistoryCallbacks
from app.callbacks.role_callbacks import RoleCallbacks
from app.callbacks.settings_callbacks import SettingsCallbacks

class CosyVoiceApp:
    """主应用控制器类"""
    
    def __init__(self, page: ft.Page, app_name: str):
        self.page = page
        self.app_name = app_name
        
        # 初始化各种管理器
        self.path_manager = PathManager()
        self.settings_manager = SettingsManager()
        self.role_manager = RoleManager()
        self.history_manager = HistoryManager()
        self.audio_manager = AudioManager()
        self.model_manager = ModelManager()
        self.api_manager = ApiManager()

        # 全局状态
        self.global_audio_state = self.audio_manager.state
        
        # UI组件
        self.title_bar = None
        self.menu_container = None
        self.content_container = None
        self.main_container = None
        self.clone_page = None
        self.history_page = None
        self.roles_page = None
        self.settings_page = None
        self.vertical_divider = None
        
        # 菜单状态
        self.menu_collapsed = False
        
        # 文件选择器
        self.clone_file_picker = None
        self.role_file_picker = None
        
        # 对话框
        self.select_role_dialog = None
        self.loading_dialog = None
        self.model_thread = None
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
        
        # 初始化回调处理器
        self._init_callbacks()

    def _init_callbacks(self):
        """初始化回调处理器类"""
        self.clone_callbacks = CloneCallbacks(
            self, self.page, self.settings_manager, 
            self.api_manager, self.history_manager
        )
        
        self.history_callbacks = HistoryCallbacks(
            self, self.page, self.history_manager, 
            self.audio_manager, self.global_audio_state
        )
        
        self.role_callbacks = RoleCallbacks(
            self, self.page, self.role_manager
        )
        
        self.settings_callbacks = SettingsCallbacks(
            self, self.page, self.settings_manager, 
            self.api_manager, self.model_manager, 
            self.path_manager
        )

    def build(self):
        """构建应用UI"""
        self._configure_page()
        self._create_pickers()
        self._create_dialogs()
        self._create_pages()
        self._create_layout()
        self._setup_event_handlers()

    def _configure_page(self):
        """配置页面基本属性"""
        # 设置窗口属性
        self.page.window.title_bar_hidden = True
        self.page.window.frameless = True
        self.page.window.title_bar_buttons_hidden = True
        self.page.window.bgcolor = ft.Colors.TRANSPARENT
        self.page.window.shadow = True
        self.page.window.center()
        
        # 修改页面基础属性
        self.page.title = self.app_name
        self.page.padding = 0
        self.page.bgcolor = ft.Colors.TRANSPARENT
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START

        # 设置字体
        self.page.theme = ft.Theme(font_family="Microsoft YaHei")

        # 设置主题模式
        self.page.theme_mode = self.settings_manager.get('theme_mode', 'system')

    def _create_pickers(self):
        """创建文件选择器"""
        # 克隆页面文件选择器
        self.clone_file_picker = ft.FilePicker(on_result=self.clone_callbacks.on_file_picked)
        self.page.overlay.append(self.clone_file_picker)
        
        # 角色页面文件选择器
        self.role_file_picker = ft.FilePicker(on_result=self.role_callbacks.role_file_picked)
        self.page.overlay.append(self.role_file_picker)

    def _create_dialogs(self):
        """创建对话框"""
        # 角色选择对话框
        self.select_role_dialog = ft.AlertDialog(
            title=ft.Text("选择角色"),
            content=ft.Column([]),
            actions=[
                ft.TextButton("取消", 
                             on_click=lambda e: (setattr(self.select_role_dialog, "open", False), self.page.update()),
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ]
        )
        self.page.overlay.append(self.select_role_dialog)

    def _create_pages(self):
        """创建各个功能页面"""
        # 创建主容器（为了能在标题栏中引用）
        self.main_container = ft.Container(
            content=None,  # 暂时为空，稍后会填充
            expand=True,
            border_radius=20,
            bgcolor=self._get_theme_color(ft.Colors.GREY_50, ft.Colors.GREY_900),
        )
        
        # 创建标题栏
        self.title_bar = TitleBar(
            self.page, 
            self.app_name, 
            on_close=self._on_window_close,
            main_container=self.main_container  # 传递主容器引用
        )
        
        # 创建垂直分隔线
        self.vertical_divider = ft.VerticalDivider(opacity=0.3)
        
        # 克隆页面
        self.clone_page = ClonePage(
            self.page,
            callbacks={
                "on_generate": self.clone_callbacks.on_generate,
                "on_clear": self.clone_callbacks.on_clear,
                "on_select_role": self.clone_callbacks.on_select_role,
                "on_select_file": self.clone_callbacks.on_select_file,
                "on_play_audio": self.clone_callbacks.on_play_audio  # 添加音频播放回调
            }
        )
        
        # 历史记录页面 - 确保所有回调都正确注册
        self.history_page = HistoryPage(
            self.page,
            callbacks={
                "on_play": self.history_callbacks.history_on_play,
                "on_delete": self.history_callbacks.history_on_delete,
                "on_reuse": self.history_callbacks.history_on_reuse,
                "on_filter": self.history_callbacks.history_on_filter,
                "on_clear_filter": self.history_callbacks.history_on_clear_filter,
                "on_page_change": self.history_callbacks.history_on_page_change,  # 确保注册页面变更回调
                "on_page_size_change": self.history_callbacks.history_on_page_size_change,  # 确保注册页面大小变更回调
                "get_global_audio_state": self.history_callbacks.history_get_global_audio_state
            }
        )
        
        # 角色管理页面
        self.roles_page = RolesPage(
            self.page,
            callbacks={
                "on_add_role": self.role_callbacks.roles_on_add_role,
                "on_edit_role": self.role_callbacks.roles_on_edit_role,
                "on_delete_role": self.role_callbacks.roles_on_delete_role,
                "on_filter_roles": self.role_callbacks.roles_on_filter,
                "on_clear_filter": self.role_callbacks.roles_on_clear_filter,
                "on_pick_file": self.role_callbacks.roles_on_pick_file
            }
        )
        
        # 设置页面
        self.settings_page = SettingsPage(
            self.page,
            settings=self.settings_manager.settings,
            callbacks={
                "on_test_connection": self.settings_callbacks.settings_on_test_connection,
                "on_save_api_settings": self.settings_callbacks.settings_on_save_api_settings,
                "on_toggle_model": self.settings_callbacks.settings_on_toggle_model,
                "on_theme_change": self.settings_callbacks.settings_on_theme_change,
                "on_auto_load_change": self.settings_callbacks.settings_on_auto_load_change,
                "on_clear_cache": self.settings_callbacks.settings_on_clear_cache,
                "on_logging_change": self.settings_callbacks.settings_on_logging_change,
                "on_download_model": self.settings_callbacks.settings_on_download_model,
                "on_open_model_folder": self.settings_callbacks.settings_on_open_model_folder,
            }
        )

    def _create_layout(self):
        """创建主布局"""
        # 内容区域容器
        self.content_container = ft.Container(
            expand=True,
            border_radius=20,
            margin=ft.Margin(12, 12, 12, 12),
        )
        
        # 菜单
        self.menu_container = SideMenu(
            self.page, 
            on_page_change=self.show_page,
            on_toggle_menu=self._handle_toggle_menu,
        )
        
        # 更新主容器内容
        self.main_container.content = ft.Container(
            content=ft.Column(
                [
                    self.title_bar, 
                    ft.Container(  
                        content=ft.Row(
                            [
                                self.menu_container,
                                self.vertical_divider,
                                self.content_container,
                            ],
                            expand=True,
                            spacing=0,
                        ),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True
            ),
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLUE_GREY_400),
                offset=ft.Offset(0, 2)
            )
        )
        
        # 将主容器添加到页面
        self.page.add(self.main_container)

    def _handle_toggle_menu(self, is_collapsed):
        """处理菜单折叠/展开状态变化"""
        self.menu_collapsed = is_collapsed
        self.vertical_divider.visible = not is_collapsed
        self.page.update()

    def _setup_event_handlers(self):
        """设置事件处理函数"""
        # 添加窗口大小改变事件处理
        self.page.on_resize = self._on_page_resize
        
        # 添加平台亮度变化的处理
        self.page.on_platform_brightness_change = self._on_platform_brightness_change

    def _on_window_close(self, e):
        """窗口关闭前清理资源"""
        # 停止可能运行的模型进程
        self.model_manager.stop_model()
        # 清理音频资源
        self.audio_manager.cleanup()
        # 关闭窗口
        self.page.window.close()

    def _on_page_resize(self, e):
        """页面大小改变处理"""
        if self.menu_container:
            self.menu_container.resize(self.page.width)
            self.page.update()

    def _on_platform_brightness_change(self, e):
        """平台亮度变化处理"""
        if self.page.theme_mode == "system":
            self.set_theme_mode("system")

    def _get_theme_color(self, light_color, dark_color):
        """根据当前主题返回相应颜色"""
        is_light = (self.page.theme_mode == "light" or 
                   (self.page.theme_mode == "system" and 
                    self.page.platform_brightness == ft.Brightness.LIGHT))
        return light_color if is_light else dark_color

    def set_theme_mode(self, mode):
        """设置主题模式"""
        self.page.theme_mode = mode
        
        # 确定当前应该使用的主题（light或dark）
        is_light = (mode == "light" or 
                   (mode == "system" and self.page.platform_brightness == ft.Brightness.LIGHT))
        
        # 自定义主题色
        # 更新主容器背景色
        self.main_container.bgcolor = ft.Colors.GREY_50 if is_light else ft.Colors.GREY_900
        
        # 更新菜单样式
        self.menu_container.update_theme(mode)
        
        # 更新内容区域的颜色
        if self.content_container.content:
            card_color = ft.Colors.GREY_50 if is_light else ft.Colors.GREY_900
            item_color = ft.Colors.GREY_100 if is_light else ft.Colors.GREY_800
            
            self._update_container_colors(self.content_container.content, card_color, item_color)
        
        self.page.update()

    def _update_container_colors(self, control, card_color, item_color):
        """递归更新所有容器和卡片的颜色"""
        if isinstance(control, ft.Card):
            control.color = card_color
        elif isinstance(control, ft.Container):
            if isinstance(control.content, (ft.Column, ft.Row)):
                # 如果是历史记录或角色项的容器，使用item_color
                if control.padding == 10 and control.margin == 5:  # 历史记录项
                    control.bgcolor = item_color
                elif control.padding == 10 and isinstance(control.margin, ft.margin.Margin):  # 角色项
                    control.bgcolor = item_color
        
        # 递归处理子控件
        if isinstance(control, ft.Container) and control.content:
            self._update_container_colors(control.content, card_color, item_color)
        elif isinstance(control, (ft.Column, ft.Row)):
            for child in control.controls:
                self._update_container_colors(child, card_color, item_color)

    def show_page(self, page_name):
        """切换显示页面"""
        try:
            if page_name == "clone":
                self.content_container.content = self.clone_page
            elif page_name == "history":
                self.content_container.content = self.history_page
            elif page_name == "roles":
                self.content_container.content = self.roles_page
            elif page_name == "settings":
                self.content_container.content = self.settings_page
            
            # 更新菜单选中状态
            self.menu_container.update_selected_page(page_name)
            
            # 更新颜色
            card_color = self._get_theme_color(ft.Colors.GREY_50, ft.Colors.GREY_900)
            item_color = self._get_theme_color(ft.Colors.GREY_100, ft.Colors.GREY_800)
            
            self._update_container_colors(self.content_container.content, card_color, item_color)
            
            self.content_container.update()
            self.page.update()
        except Exception as e:
            error_details = traceback.format_exc()
            mlog.error(f"切换页面 '{page_name}' 失败: {str(e)}\n{error_details}")
            
            # 显示错误对话框
            error_dialog = ft.AlertDialog(
                title=ft.Text("错误"),
                content=ft.Text(f"切换到{page_name}页面失败，请重试。"),
                actions=[
                    ft.TextButton("确定", 
                                  on_click=lambda _: (setattr(error_dialog, "open", False), self.page.update()),
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ],
            )
            self.page.open(error_dialog)

    def initialize(self):
        """初始化应用"""
        try:
            # 首先设置主题并显示界面
            self.set_theme_mode(self.settings_manager.get('theme_mode', 'system'))
            self.show_page("clone")
            self.page.update()

            # 同步加载初始数据
            roles_data = self.role_manager.get_roles_paged(1, self.roles_page.page_size)
            history_data = self.history_manager.get_history_paged(1, self.history_page.page_size)
            
            mlog.debug(f"初始化加载: 角色数据={len(roles_data)}条, 历史数据={len(history_data)}条")
            
            # 更新UI数据
            self.role_callbacks.roles_on_page_change(1, self.roles_page.page_size, "")
            self.history_callbacks.history_on_page_change(1, self.history_page.page_size, "")
            
            # 处理特殊平台显示
            if self.page.web or self.page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS, ft.PagePlatform.ANDROID_TV]:
                self.title_bar.visible = False
                self.main_container.border_radius = 0

            # 默认折叠导航并更新界面
            self.menu_container.toggle_menu()
            self.page.update()
            
            # 检查API连接
            run_async(self.settings_callbacks.settings_on_test_connection(
                self.settings_manager.get('api_url', 'http://127.0.0.1:8000')
            ))
            
            # 自动加载模型
            if self.settings_manager.get('auto_load_model', False):
                self.show_page("settings")
                self.settings_callbacks.settings_on_toggle_model()
                self.show_page("clone")
                
        except Exception as e:
            mlog.error(f"应用初始化失败: {str(e)}")
            # 显示错误对话框
            error_dialog = ft.AlertDialog(
                title=ft.Text("初始化错误"),
                content=ft.Text(f"应用初始化失败: {str(e)}"),
                actions=[
                    ft.TextButton("确定", 
                        on_click=lambda _: (setattr(error_dialog, "open", False), self.page.update()),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ]
            )
            self.page.dialog = error_dialog
            error_dialog.open = True
            self.page.update()


