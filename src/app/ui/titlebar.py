import flet as ft
import app.core.mlog as mlog

class TitleBar(ft.Container):
    """
    自定义应用标题栏组件
    """
    def __init__(self, page: ft.Page, app_name: str = "Parrot", on_close=None, on_maximize=None, main_container=None):
        """
        初始化标题栏
        
        Args:
            page: Flet页面对象
            app_name: 应用名称
            on_close: 关闭窗口的回调函数
            on_maximize: 最大化/还原窗口的回调函数
            main_container: 主容器引用，用于控制圆角
        """
        self.page = page
        self.app_name = app_name
        self.on_close = on_close or self._default_close
        self.on_maximize = on_maximize or self._default_maximize
        self.main_container = main_container
        
        # 创建标题区域（可拖动且支持双击最大化）
        self.title_area = ft.WindowDragArea(
            ft.GestureDetector(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=20),
                        ft.Text(self.app_name, size=16, weight=ft.FontWeight.BOLD),
                    ],
                ),
                on_double_tap=self._toggle_maximize
            ),
            expand=True,
        )
        
        # 创建最大化/还原按钮
        self.maximize_button = ft.IconButton(
            icon=ft.Icons.CROP_SQUARE_SHARP,
            tooltip="最大化",
            icon_color=ft.Colors.GREY_700,
            on_click=self._toggle_maximize
        )
        
        # 创建标题栏控件
        title_content = ft.Row(
            [
                self.title_area,
                ft.IconButton(
                    icon=ft.Icons.REMOVE,
                    tooltip="最小化",
                    icon_color=ft.Colors.GREY_700,
                    on_click=self._minimize_window
                ),
                self.maximize_button,
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="关闭",
                    icon_color=ft.Colors.GREY_700,
                    on_click=self._close_window
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # 调用父类初始化
        super().__init__(
            content=title_content,
            padding=ft.padding.only(left=15, right=10, top=5, bottom=5),
            bgcolor=ft.Colors.SURFACE,
        )
        
        # 更新最大化/还原按钮的图标
        self._update_maximize_button()
    
    def _minimize_window(self, e):
        """最小化窗口"""
        self.page.window.minimized = True
        self.page.update()
    
    def _toggle_maximize(self, e=None):
        """切换窗口最大化/还原状态"""
        try:
            mlog.info("切换窗口最大化状态")
            if self.on_maximize:
                self.on_maximize(e)
            self._update_maximize_button()
        except Exception as ex:
            mlog.error(f"切换窗口最大化状态失败: {str(ex)}")
    
    def _update_maximize_button(self):
        """根据窗口当前状态更新最大化/还原按钮图标"""
        try:
            if self.page.window.maximized:
                self.maximize_button.icon = ft.Icons.FILTER_NONE
                self.maximize_button.tooltip = "还原"
                if self.main_container:
                    self.main_container.border_radius = 0
            else:
                self.maximize_button.icon = ft.Icons.CROP_SQUARE_SHARP
                self.maximize_button.tooltip = "最大化"
                if self.main_container:
                    self.main_container.border_radius = 20
            self.maximize_button.update()
            self.page.update()
        except Exception as ex:
            pass
            # mlog.error(f"更新最大化按钮失败: {str(ex)}")
    
    def _close_window(self, e):
        """关闭窗口"""
        if self.on_close:
            self.on_close(e)
    
    def _default_close(self, e):
        """默认关闭行为"""
        self.page.window.close()
    
    def _default_maximize(self, e):
        """默认最大化/还原行为"""
        self.page.window.maximized = not self.page.window.maximized
        self.page.update()
        # 更新按钮图标
        self._update_maximize_button()
