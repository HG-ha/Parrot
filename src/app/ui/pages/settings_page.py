import flet as ft
import asyncio
import webbrowser
from app.core.utils import run_async

class SettingsPage(ft.Card):
    """
    设置页面
    """
    def __init__(self, page: ft.Page, settings=None, callbacks=None):
        """
        初始化设置页面
        
        Args:
            page: Flet页面对象
            settings: 当前设置
            callbacks: 回调函数字典
        """
        super().__init__()
        self.page = page
        self.settings = settings or {}  # 默认为空字典
        self.callbacks = callbacks or {}
        
        # 模型下载对话框
        self.download_progress = ft.Container(
            content=ft.ProgressBar(
                width=300,
                visible=False
            ),
            margin=ft.margin.only(top=20)  # 设置顶部边距为20
        )
        
        self.download_progress_text = ft.Text(
            visible=False
        )
        
        self.model_download_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("模型未下载"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("请先下载模型。", size=16),
                    ft.Text("1. 点击下方按钮自动下载，建议挑选最适合的下载方式", size=14),
                    ft.Text("2. 如选择自动下载，下载完成前请不要关闭此窗口", size=14),
                    ft.Text("3. 不要重复点击", size=14),
                    self.download_progress,
                    self.download_progress_text
                ], 
                spacing=10),
                padding=10,
                width=350,
                height=250
            ),
            actions=[
                ft.TextButton(
                    "自动下载",
                    on_click=self._start_download,
                    tooltip="可能不稳定，但很方便"
                ),
                ft.TextButton(
                    "手动下载",
                    on_click=self._open_download_page,
                ),
                ft.TextButton(
                    "关闭",
                    on_click=lambda e: self.close_model_download_dialog()
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # API设置控件
        self.api_url_input = ft.TextField(
            label="API地址",
            value=self.settings.get('api_url', 'http://127.0.0.1:8000'),
            width=300,
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        self.api_status_text = ft.Text(
            value="API状态: 未检测",
            color=ft.Colors.GREY
        )
        
        self.test_connection_button = ft.ElevatedButton(
            text="测试连接",
            on_click=self._test_connection,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        # 模型设置控件
        self.model_host_input = ft.TextField(
            label="模型Host",
            value=self.settings.get('model_host', '127.0.0.1'),
            width=300,
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        self.model_port_input = ft.TextField(
            label="模型端口",
            value=self.settings.get('model_port', '8000'),
            width=300,
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        self.model_status_text = ft.Text(
            value="模型状态: 未运行",
            color=ft.Colors.RED
        )
        
        self.run_model_button = ft.ElevatedButton(
            text="运行模型",
            on_click=self._toggle_run_model,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )

        self.open_folder_button = ft.ElevatedButton(
            icon=ft.Icons.FOLDER_OPEN,
            text="模型目录",
            tooltip="打开模型目录",
            on_click=self._open_model_folder,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        # 模型输出区
        self.model_output_text = ft.Text(
            value="",
            size=12,
            selectable=True,
            expand=True,  # 让文本控件填满可用空间
            color=ft.Colors.GREEN_400 # 经典黑底绿字
        )
        
        self.model_output_scroll = ft.Column(
            [self.model_output_text],
            scroll=ft.ScrollMode.ALWAYS,
            auto_scroll=True,
            expand=True,  # 让滚动区域填满可用空间
        )
        
        self.model_output_container = ft.Container(
            content=ft.Column([
                ft.Text("模型输出:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.model_output_scroll,
                    height=200,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=5,
                    padding=10,
                    bgcolor=ft.Colors.BLACK, # 经典黑底绿字
                )
            ]),
            visible=False,  # 初始不可见
        )
        
        # 界面设置控件
        self.theme_mode_dropdown = ft.Dropdown(
            label="主题模式",
            value=self.settings.get('theme_mode', 'system'),
            options=[
                ft.dropdown.Option("system", "跟随系统"),
                ft.dropdown.Option("light", "浅色模式"),
                ft.dropdown.Option("dark", "深色模式"),
            ],
            width=200,
            on_change=self._on_theme_change
        )
        
        self.auto_load_model_checkbox = ft.Checkbox(
            label="启动时自动加载模型", 
            value=self.settings.get('auto_load_model', False),
            on_change=self._on_auto_load_change
        )
        
        # 日志设置控件
        self.logging_enabled_checkbox = ft.Checkbox(
            label="启用日志", 
            value=self.settings.get('logging_enabled', True),
            on_change=self._on_logging_change
        )
        
        # 缓存管理
        self.clear_cache_button = ft.ElevatedButton(
            text="清除缓存",
            on_click=self._clear_cache,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        # 输出信息
        self.settings_output_text = ft.Text()
        
        # 设置提交事件 - 改为自动保存
        self.api_url_input.on_change = self._save_api_settings
        self.model_host_input.on_change = self._save_api_settings
        self.model_port_input.on_change = self._save_api_settings
        
        # 本地模型标题
        self.local_model_title = ft.Text("本地模型设置", size=20, weight=ft.FontWeight.BOLD)

        # 本地模型相关按钮
        self.open_folder_button = ft.Row([
                    self.open_folder_button,
                    self.run_model_button,
                    self.model_status_text
                ], spacing=10)

        # 路径设置控件
        self.model_path_input = ft.TextField(
            label="模型路径",
            value=self.settings.get('paths', {}).get('model_path', ''),
            width=300,
            border=ft.InputBorder.OUTLINE,
            border_radius=8,
            suffix=ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: self._pick_directory('model_path')
            )
        )
        
        self.history_path_input = ft.TextField(
            label="历史记录路径",
            value=self.settings.get('paths', {}).get('history_dir', ''),
            width=300,
            border=ft.InputBorder.OUTLINE,
            border_radius=8,
            suffix=ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: self._pick_directory('history_dir')
            )
        )

        # 路径选择器
        self.path_picker = ft.FilePicker(
            on_result=self._on_path_picked
        )
        self.page.overlay.append(self.path_picker)
        self._current_path_field = None

        # 保存路径按钮
        self.save_paths_button = ft.ElevatedButton(
            text="保存路径设置",
            on_click=self._save_paths,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )

        # 在保存路径按钮旁边添加恢复默认按钮
        self.reset_paths_button = ft.ElevatedButton(
            text="恢复默认路径",
            on_click=self._reset_paths,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )

        # 组合页面内容
        content = ft.Container(
            content=ft.Column([
                ft.Text("API设置", size=20, weight=ft.FontWeight.BOLD),
                self.api_url_input,
                ft.Row([
                    self.test_connection_button,
                    self.api_status_text
                ], spacing=10),
                ft.Divider(),
                self.local_model_title,
                self.model_host_input,
                self.model_port_input,
                self.auto_load_model_checkbox,
                self.open_folder_button,
                self.model_output_container,
                ft.Divider(),
                ft.Text("界面设置", size=20, weight=ft.FontWeight.BOLD),
                self.theme_mode_dropdown,
                ft.Divider(),
                ft.Text("系统设置", size=20, weight=ft.FontWeight.BOLD),
                self.logging_enabled_checkbox,
                ft.Divider(),
                ft.Text("缓存管理", size=20, weight=ft.FontWeight.BOLD),
                self.clear_cache_button,
                ft.Divider(),
                ft.Text("路径设置", size=20, weight=ft.FontWeight.BOLD),
                self.model_path_input,
                self.history_path_input,
                ft.Row([
                    self.save_paths_button,
                    # self.reset_paths_button,
                ], spacing=10),
                ft.Divider(),
                self.settings_output_text
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True
        )

        # 当存在于Android、iOS平台时，隐藏本地模型相关
        if self.page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS, ft.PagePlatform.ANDROID_TV]:
            self.model_host_input.visible = False
            self.model_port_input.visible = False
            self.auto_load_model_checkbox.visible = False
            self.local_model_title.visible = False
            self.model_output_container.visible = False
            self.open_folder_button.visible = False
            content.content.controls[3].visible = False

        # 调用父类初始化
        super().__init__(
            content=content,
            expand=True
        )
    
    def _test_connection(self, e):
        """测试API连接"""
        self.api_status_text.color = ft.Colors.GREY
        self.api_status_text.value = "API状态: 正在检测..."
        self.page.update()

        if "on_test_connection" in self.callbacks:
            asyncio.run(self.callbacks["on_test_connection"](self.api_url_input.value))
    
    def update_api_status(self, is_connected, message=None):
        """更新API状态显示
        
        Args:
            is_connected: 是否连接成功
            message: 状态消息
        """
        if is_connected:
            self.api_status_text.value = "API状态: 已连接"
            self.api_status_text.color = ft.Colors.GREEN
        else:
            self.api_status_text.value = f"API状态: {message or '连接失败'}"
            self.api_status_text.color = ft.Colors.RED
        
        self.api_status_text.update()
    
    def _save_api_settings(self, e=None):
        """保存API设置"""
        if "on_save_api_settings" in self.callbacks:
            self.callbacks["on_save_api_settings"]({
                'api_url': self.api_url_input.value,
                'model_host': self.model_host_input.value,
                'model_port': self.model_port_input.value
            })
            self.settings_output_text.value = "API设置已保存"
            self.page.update()
    
    def _toggle_run_model(self, e):
        """运行或停止模型"""
        if "on_toggle_model" in self.callbacks:
            self.callbacks["on_toggle_model"]()
        self.page.update()
    
    def update_model_status(self, is_running: bool, is_starting: bool = False):
        """更新模型状态显示"""
        if is_starting:
            self.model_status_text.value = "模型状态: 正在启动"
            self.model_status_text.color = ft.Colors.ORANGE
            self.run_model_button.text = "停止模型"
            self.model_output_container.visible = True
        elif is_running:
            self.model_status_text.value = "模型状态: 正在运行"
            self.model_status_text.color = ft.Colors.GREEN
            self.run_model_button.text = "停止模型"
            self.model_output_container.visible = True
        else:
            self.model_status_text.value = "模型状态: 已停止"
            self.model_status_text.color = ft.Colors.RED
            self.run_model_button.text = "运行模型"
            self.model_output_container.visible = False
        self.page.update()
    
    def update_model_output(self, text: str):
        """更新模型输出显示"""
        if self.model_output_text:
            self.model_output_text.value = text
            # 强制滚动到底部
            if self.model_output_scroll:
                self.model_output_scroll.scroll_to(offset=float('inf'), duration=0)
            self.page.update()
    
    def _on_theme_change(self, e):
        """主题改变回调"""
        if "on_theme_change" in self.callbacks:
            self.callbacks["on_theme_change"](self.theme_mode_dropdown.value)
            self.settings_output_text.value = "已更改主题设置"
            self.settings_output_text.update()
    
    def _on_auto_load_change(self, e):
        """自动加载模型设置改变"""
        if "on_auto_load_change" in self.callbacks:
            self.callbacks["on_auto_load_change"](self.auto_load_model_checkbox.value)
            self.settings_output_text.value = "自动加载模型设置已更新"
            self.settings_output_text.update()
    
    def _on_logging_change(self, e):
        """日志设置改变回调"""
        if "on_logging_change" in self.callbacks:
            # 显示加载指示器
            self.settings_output_text.value = "正在更新日志设置..."
            self.settings_output_text.update()
            
            # 调用回调函数并获取结果
            result = self.callbacks["on_logging_change"](self.logging_enabled_checkbox.value)
            
            # 确保复选框状态与实际设置一致
            self.logging_enabled_checkbox.value = result
            
            # 更新状态显示
            status = "启用" if result else "禁用"
            self.settings_output_text.value = f"日志已{status}并保存到设置"
            self.settings_output_text.color = ft.Colors.GREEN if result == self.logging_enabled_checkbox.value else ft.Colors.RED
            self.settings_output_text.update()
    
    def _clear_cache(self, e):
        """清除缓存"""
        if "on_clear_cache" in self.callbacks:
            success = self.callbacks["on_clear_cache"]()
            if success:
                self.settings_output_text.value = "缓存清除成功"
            else:
                self.settings_output_text.value = "缓存清除失败"
            self.settings_output_text.update()
    
    def update_settings(self, settings):
        """更新设置值
        
        Args:
            settings: 设置字典
        """
        self.settings = settings
        
        # 更新控件值
        self.api_url_input.value = settings.get('api_url', self.api_url_input.value)
        self.model_host_input.value = settings.get('model_host', self.model_host_input.value)
        self.model_port_input.value = settings.get('model_port', self.model_port_input.value)
        self.theme_mode_dropdown.value = settings.get('theme_mode', self.theme_mode_dropdown.value)
        self.auto_load_model_checkbox.value = settings.get('auto_load_model', self.auto_load_model_checkbox.value)
        self.logging_enabled_checkbox.value = settings.get('logging_enabled', self.logging_enabled_checkbox.value)
        self.model_path_input.value = settings.get('paths', {}).get('model_path', self.model_path_input.value)
        self.history_path_input.value = settings.get('paths', {}).get('history_dir', self.history_path_input.value)
        
        # 更新控件
        self.page.update()
    
    def _open_download_page(self, e):
        """打开模型下载页面"""
        # 打开GitHub仓库页面
        webbrowser.open("https://github.com/HG-ha/Parrot")
        
    def show_model_download_dialog(self):
        """显示模型下载提示对话框"""
        self.page.open(self.model_download_dialog)
       
        
    def close_model_download_dialog(self):
        """关闭模型下载提示对话框"""
        self.page.close(self.model_download_dialog)
    
    def _start_download(self, e):
        """开始下载模型"""
        if "on_download_model" in self.callbacks:
            # 显示进度条
            self.download_progress.content.visible = True
            self.download_progress_text.visible = True
            self.page.update()
            
            # 调用下载回调
            run_async(self.callbacks["on_download_model"]())
    
    def update_download_progress(self, current, total, status_text=None):
        """更新下载进度"""
        if current == -1 or total == -1:
            # 显示状态文本，隐藏进度条
            self.download_progress.content.visible = False
            self.download_progress_text.value = status_text
        else:
            # 显示进度条和百分比
            self.download_progress.content.visible = True
            
            if total > 0:
                progress = current / total
                self.download_progress.content.value = progress
                
                # 计算百分比
                percentage = (current / total) * 100
                
                # 只显示状态文本和百分比
                if "下载" in status_text:
                    self.download_progress_text.value = f"{status_text} ({percentage:.1f}%)"
                elif "解压" in status_text:
                    self.download_progress_text.value = status_text
        
        self.download_progress_text.visible = True
        self.page.update()
    
    def _open_model_folder(self, e):
        """打开模型文件夹"""
        if "on_open_model_folder" in self.callbacks:
            self.callbacks["on_open_model_folder"]()

    def _pick_directory(self, path_field):
        """打开目录选择器"""
        self._current_path_field = path_field
        self.path_picker.get_directory_path()

    def _on_path_picked(self, e):
        """处理目录选择结果"""
        if e.path and self._current_path_field:
            if self._current_path_field == 'model_path':
                self.model_path_input.value = e.path
            elif self._current_path_field == 'history_dir':
                self.history_path_input.value = e.path
            self.page.update()

    def _save_paths(self, e):
        """保存路径设置"""
        paths = {
            'model_path': self.model_path_input.value,
            'history_dir': self.history_path_input.value
        }
        
        if "on_save_paths" in self.callbacks:
            success = self.callbacks["on_save_paths"](paths)
            if success:
                self.settings_output_text.value = "路径设置已保存"
            else:
                self.settings_output_text.value = "保存路径设置失败"
            self.settings_output_text.update()

    def _reset_paths(self, e):
        """恢复默认路径设置"""
        if "on_reset_paths" in self.callbacks:
            success = self.callbacks["on_reset_paths"]()
            if success:
                self.settings_output_text.value = "已恢复默认路径设置"
                # 清空输入框值以使用默认值
                self.model_path_input.value = ""
                self.history_path_input.value = ""
            else:
                self.settings_output_text.value = "恢复默认路径设置失败"
            self.settings_output_text.update()
            self.page.update()
