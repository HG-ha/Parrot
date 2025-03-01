import flet as ft
import webbrowser

class SideMenu(ft.Container):
    """
    应用程序的侧边菜单组件
    """
    def __init__(self, page: ft.Page, on_page_change=None, on_toggle_menu=None):
        """
        初始化侧边菜单
        
        Args:
            page: Flet页面对象
            on_page_change: 页面切换回调函数，接收页面名称作为参数
            on_toggle_menu: 菜单展开/折叠回调函数
        """
        self.page = page
        self.on_page_change = on_page_change or (lambda _: None)
        self.on_toggle_menu = on_toggle_menu or (lambda _: None)
        
        # 当前选中的页面
        self.current_page = "clone"  # 默认选中语音克隆页面
        
        # 菜单是否折叠标志
        self.is_collapsed = False
        
        # 创建菜单项
        self.menu_items = self._create_menu_items()
        
        # 创建设置按钮
        self.settings_button = self._create_menu_button("设置", lambda e: self.on_page_change("settings"), "settings")
        
        # 创建折叠/展开按钮
        self.toggle_button = ft.IconButton(
            icon=ft.Icons.MENU_OPEN,
            tooltip="折叠导航",
            on_click=self._toggle_menu,
            icon_size=20,
        )
        
        # 创建菜单顶部控制区 - 调整为和菜单按钮相同的宽度和对齐方式
        menu_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("导航", size=16, weight=ft.FontWeight.BOLD),
                    self.toggle_button
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=150,  # 与按钮文本宽度保持一致
            ),
            margin=ft.margin.only(bottom=5),
            border_radius=10,
            alignment=ft.alignment.center,  # 容器内部居中对齐
            width=180,  # 与菜单按钮保持相同的宽度
            visible=not self.is_collapsed
        )
        
        # 创建菜单容器
        menu_content = ft.Column(
            [
                menu_header,
                self.menu_items,
                self.settings_button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # 在顶部和底部之间均匀分布
            expand=True,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # 确保水平居中
        )
        
        # 创建折叠状态下的小按钮
        self.collapsed_toggle_button = ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="展开导航",
            on_click=self._toggle_menu,
            icon_size=20,
        )
        
        self.collapsed_menu = ft.Column(
            [
                self.collapsed_toggle_button,
                self._create_collapsed_menu_items(),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=15,
            visible=False,  # 初始不可见
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # 确保水平居中
        )
        
        # 创建堆叠布局，用于切换显示
        self.menu_stack = ft.Stack([
            menu_content,
            self.collapsed_menu
        ])
        
        # 调用父类初始化
        super().__init__(
            content=self.menu_stack,
            width=min(page.width * 0.2, 190),  # 设置为窗口宽度的20%，最大270px
            padding=20,
            bgcolor=ft.Colors.GREY_100,  # 初始背景色，会被update_theme覆盖
            border_radius=20,
            margin=15,
            alignment=ft.alignment.center
        )
    
    def _create_menu_items(self):
        """创建菜单项列表"""
        return ft.Column(
            controls=[
                self._create_menu_button("语音克隆", lambda e: self.on_page_change("clone"), "clone"),
                self._create_menu_button("生成记录", lambda e: self.on_page_change("history"), "history"),
                self._create_menu_button("角色管理", lambda e: self.on_page_change("roles"), "roles"),
                self._create_menu_button("Github", self._open_github, None),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.START,  # 垂直方向顶部对齐
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # 水平居中
        )
    
    def _create_collapsed_menu_items(self):
        """创建折叠状态下的菜单项"""
        return ft.Column(
            controls=[
                self._create_collapsed_button(ft.Icons.RECORD_VOICE_OVER, "语音克隆", "clone"),
                self._create_collapsed_button(ft.Icons.HISTORY, "生成记录", "history"),
                self._create_collapsed_button(ft.Icons.PERSON, "角色管理", "roles"),
                self._create_collapsed_button(ft.Icons.LINK, "Github", None),
                self._create_collapsed_button(ft.Icons.SETTINGS, "设置", "settings"),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    
    def _create_collapsed_button(self, icon, tooltip, page_id=None):
        """创建折叠状态下的图标按钮"""
        # 获取当前是否是亮色主题
        is_light = (self.page.theme_mode == "light" or 
                   (self.page.theme_mode == "system" and self.page.platform_brightness == ft.Brightness.LIGHT))
        
        # 判断是否为当前选中页面
        is_selected = page_id and self.current_page == page_id
        
        # 根据选中状态设置不同的图标颜色
        if is_selected:
            icon_color = ft.Colors.BLUE_800 if is_light else ft.Colors.BLUE_200
        else:
            icon_color = ft.Colors.BLACK if is_light else ft.Colors.WHITE
            
        # 处理Github特殊按钮
        on_click = lambda e: self._open_github(e) if page_id is None else self.on_page_change(page_id)
        
        return ft.IconButton(
            icon=icon,
            tooltip=tooltip,
            on_click=on_click,
            icon_color=icon_color,
            icon_size=24,
            data=page_id,  # 存储页面ID，方便后续更新
        )
    
    def _create_menu_button(self, text, on_click, page_id=None):
        """
        创建菜单按钮
        
        Args:
            text: 按钮文本
            on_click: 点击回调函数
            page_id: 页面标识符，用于高亮显示当前页面
        """
        # 获取当前是否是亮色主题
        is_light = (self.page.theme_mode == "light" or 
                   (self.page.theme_mode == "system" and self.page.platform_brightness == ft.Brightness.LIGHT))
        
        # 判断是否为当前选中页面
        is_selected = page_id and self.current_page == page_id
        
        # 根据选中状态设置不同的背景色和文本颜色
        if is_selected:
            bg_color = ft.Colors.BLUE_100 if is_light else ft.Colors.BLUE_900
            text_color = ft.Colors.BLUE_800 if is_light else ft.Colors.BLUE_200
        else:
            bg_color = ft.Colors.GREY_100 if is_light else ft.Colors.GREY_800
            text_color = ft.Colors.BLACK if is_light else ft.Colors.WHITE
            
        return ft.Container(
            content=ft.TextButton(
                text=text,
                on_click=on_click,
                style=ft.ButtonStyle(
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=10),
                    bgcolor=bg_color,
                    color=text_color,
                ),
                width=150,  # 设置固定宽度
            ),
            margin=ft.margin.only(bottom=5),
            border_radius=10,
            alignment=ft.alignment.center,  # 容器内部居中对齐
            width=180,  # 保持容器宽度
            data=page_id,  # 存储页面ID，方便后续更新
        )
    
    def _open_github(self, e):
        """打开GitHub页面"""
        webbrowser.open('https://github.com/HG-ha/Parrot')
    
    def _toggle_menu(self, e=None):
        """切换菜单展开/折叠状态"""
        self.is_collapsed = not self.is_collapsed
        self._update_menu_state()
        # 调用外部回调
        if self.on_toggle_menu:
            self.on_toggle_menu(self.is_collapsed)
    
    def toggle_menu(self):
        self._toggle_menu()
    
    def _update_menu_state(self):
        """根据折叠状态更新菜单显示"""
        if self.is_collapsed:
            self.width = 70  # 折叠状态宽度
            self.padding = 10
            self.collapsed_menu.visible = True
            self.menu_stack.controls[0].visible = False  # 隐藏展开菜单
        else:
            self.width = min(self.page.width * 0.2, 190)  # 恢复原宽度
            self.padding = 20
            self.collapsed_menu.visible = False
            self.menu_stack.controls[0].visible = True  # 显示展开菜单
        self.update()
    
    def update_theme(self, theme_mode):
        """
        更新菜单主题
        
        Args:
            theme_mode: 主题模式（system, light, dark）
        """
        # 确定当前应该使用的主题（light或dark）
        is_light = (theme_mode == "light" or 
                  (theme_mode == "system" and self.page.platform_brightness == ft.Brightness.LIGHT))
        
        # 更新菜单背景色
        self.bgcolor = ft.Colors.GREY_50 if is_light else ft.Colors.GREY_900
        
        # 更新所有按钮颜色
        self.update_selected_page(self.current_page)
    
    def update_selected_page(self, page_id):
        """
        更新选中的页面，高亮显示对应的菜单按钮
        
        Args:
            page_id: 页面标识符
        """
        # 更新当前页面
        self.current_page = page_id
        
        # 获取当前是否是亮色主题
        is_light = (self.page.theme_mode == "light" or 
                  (self.page.theme_mode == "system" and self.page.platform_brightness == ft.Brightness.LIGHT))
        
        # 更新所有菜单按钮的样式
        for button in self.menu_items.controls:
            button_page_id = button.data
            if button_page_id and button_page_id == page_id:
                # 当前选中页面的按钮样式
                button.content.style.bgcolor = ft.Colors.BLUE_GREY_100 if is_light else ft.Colors.BLUE_GREY_800
                button.content.style.color = ft.Colors.BLUE_800 if is_light else ft.Colors.BLUE_200
            else:
                # 其他页面的按钮样式
                button.content.style.bgcolor = ft.Colors.GREY_100 if is_light else ft.Colors.GREY_800
                button.content.style.color = ft.Colors.BLACK if is_light else ft.Colors.WHITE
        
        # 单独处理设置按钮
        if self.settings_button.data == page_id:
            self.settings_button.content.style.bgcolor = ft.Colors.BLUE_GREY_100 if is_light else ft.Colors.BLUE_GREY_800
            self.settings_button.content.style.color = ft.Colors.BLUE_800 if is_light else ft.Colors.BLUE_200
        else:
            self.settings_button.content.style.bgcolor = ft.Colors.GREY_100 if is_light else ft.Colors.GREY_800
            self.settings_button.content.style.color = ft.Colors.BLACK if is_light else ft.Colors.WHITE
            
        # 更新折叠菜单的图标按钮颜色
        for button in self.collapsed_menu.controls[1].controls:
            button_page_id = button.data
            if button_page_id and button_page_id == page_id:
                button.icon_color = ft.Colors.BLUE_800 if is_light else ft.Colors.BLUE_200
            else:
                button.icon_color = ft.Colors.BLACK if is_light else ft.Colors.WHITE
    
    def resize(self, page_width):
        """
        调整菜单大小
        
        Args:
            page_width: 页面宽度
        """
        if not self.is_collapsed:
            self.width = min(page_width * 0.2, 270)  # 设置为窗口宽度的20%，最大270px
            if self.width < 180:  # 保证菜单最小宽度
                self.width = 180
