import flet as ft
import os
import app.core.mlog as mlog
from app.ui.components.pagination import Pagination

class HistoryPage(ft.Card):
    """
    生成记录页面
    """
    def __init__(self, page: ft.Page, callbacks=None):
        """
        初始化历史记录页面
        
        Args:
            page: Flet页面对象
            callbacks: 回调函数字典，包含播放、删除、重用等操作的回调
        """
        self.page = page
        self.callbacks = callbacks or {}
        self.history_items = []  # 历史记录项的引用
        self.current_page = 1
        self.page_size = 5  # 修改默认每页显示为5条
        self.total_history = 0
        self.current_keyword = ""
        
        # 创建搜索框
        self.search_field = ft.TextField(
            label="搜索记录",
            hint_text="输入关键词搜索",
            width=300,
            height=55,
            border=ft.InputBorder.OUTLINE,
            border_radius=6,
            on_change=self._filter_history,
            suffix=ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="清除搜索",
                on_click=self._clear_search,
                icon_size=18,  # 减小图标尺寸以适应较矮的搜索框
                height=35,
                width=35
            )
        )

        self.search_row = ft.Row(
            [self.search_field],
            alignment=ft.MainAxisAlignment.CENTER
        )

        # 创建历史记录列表
        self.history_list = ft.ListView(
            expand=True,
            spacing=10,
            controls=[]  # 初始化为空
        )
        
        # 分页控件
        self.pagination = Pagination(
            total_items=0,  # 初始为0，稍后更新
            page_size=self.page_size,
            current_page=self.current_page,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_page_size_change  # 添加页面大小变更回调
        )
        
        # 布局构建
        content = ft.Container(
            content=ft.Column([
                self.search_row,
                ft.Divider(),
                self.history_list,
                ft.Row(
                    [self.pagination],
                    alignment=ft.MainAxisAlignment.END  # 设置为左对齐
                ),  # 将分页控件放在行容器中并左对齐
            ]),
            padding=20
        )
        
        # 调用父类初始化
        super().__init__(
            content=content
        )
        
        # 设置初始回调
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置初始回调函数"""
        # 确保所有必需的回调都存在，没有提供时使用空函数
        if "on_page_change" not in self.callbacks:
            mlog.warning("历史页面 - 未提供页面变更回调函数，使用空函数")
            self.callbacks["on_page_change"] = lambda page, page_size, keyword: None
            
        if "on_page_size_change" not in self.callbacks:
            self.callbacks["on_page_size_change"] = lambda new_size, new_page, keyword: None
            
        if "on_filter" not in self.callbacks:
            self.callbacks["on_filter"] = lambda keyword, page, page_size: None
            
        if "on_clear_filter" not in self.callbacks:
            self.callbacks["on_clear_filter"] = lambda: None
    
    def create_history_item(self, item, global_audio_state):
        """
        创建单个历史记录项
        
        Args:
            item: 历史记录数据
            global_audio_state: 全局音频状态
        
        Returns:
            ft.Container: 历史记录项控件
        """
        def play_pause_audio(e):
            try:
                # 不在此处先切换按钮状态，让音频管理器来控制
                # 调用播放回调
                if "on_play" in self.callbacks:
                    self.callbacks["on_play"](item, play_button)
            except Exception as ex:
                mlog.error(f"播放失败: {str(ex)}") 
                play_button.selected = False
                if "current_player" in global_audio_state:
                    global_audio_state["current_player"] = None
                self.page.update()

        def open_file_location(e):
            import subprocess
            try:
                file_path = os.path.abspath(item['file_path'])
                # Windows
                if os.name == 'nt':
                    subprocess.run(['explorer', '/select,', file_path])
                # macOS
                elif os.name == 'posix' and os.uname().sysname == 'Darwin':
                    subprocess.run(['open', '-R', file_path])
                # Linux
                elif os.name == 'posix':
                    subprocess.run(['xdg-open', os.path.dirname(file_path)])
            except Exception as ex:
                mlog.error(f"打开文件位置失败: {str(ex)}")

        def reuse_parameters(e):
            if "on_reuse" in self.callbacks:
                self.callbacks["on_reuse"](item)

        def delete_history(e):
            def handle_delete(e, dialog):
                dialog.open = False
                self.page.update()
                
                if "on_delete" in self.callbacks:
                    self.callbacks["on_delete"](item, container)
                
            dialog = ft.AlertDialog(
                title=ft.Text("确认删除"),
                content=ft.Text("确定要删除这条记录吗？"),
                actions=[
                    ft.TextButton("取消", 
                                on_click=lambda e: (setattr(dialog, "open", False), self.page.update()),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                    ft.TextButton("删除", 
                                on_click=lambda e: handle_delete(e, dialog),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ]
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            selected_icon=ft.Icons.PAUSE,
            tooltip="播放",
            selected=False,
            on_click=play_pause_audio
        )

        container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.GREY_400),
                    ft.Text(item['timestamp'], size=12, color=ft.Colors.GREY_400)
                ]),
                ft.Row([
                    ft.Text("文本: ", weight=ft.FontWeight.BOLD),
                    ft.Text(item['text'])
                ]),
                ft.Row([
                    ft.Text("说话人: ", weight=ft.FontWeight.BOLD),
                    ft.Text(item['speaker']),
                    ft.Text("  语速: ", weight=ft.FontWeight.BOLD),
                    ft.Text(f"{item['speed']:.1f}"),
                ]),
                ft.Row([
                    ft.Text("参考音频: ", weight=ft.FontWeight.BOLD),
                    ft.Text(os.path.basename(item['reference']))
                ]),
                ft.Row([
                    ft.Container(expand=True),  # 这会把后面的按钮推到右边
                    play_button,
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        tooltip="打开文件位置",
                        on_click=open_file_location
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REPLAY,
                        tooltip="使用相同参数重新生成",
                        on_click=reuse_parameters
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="删除",
                        on_click=delete_history
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ]),
            border_radius=10,
            padding=10,
            margin=5,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),  # 添加浅色边框
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE)  # 添加浅色背景
        )
        return container

    def update_history_list(self, history, global_audio_state, total_count=None):
        """更新历史记录列表
        
        Args:
            history: 历史记录数据列表
            global_audio_state: 全局音频状态
            total_count: 过滤后的总记录数(可选)
        """
        mlog.debug(f"更新历史记录列表: 获取到 {len(history)} 条记录")
        self.history_items = history
        
        # 更新总记录数
        if total_count is not None:
            self.total_history = total_count
            self.pagination.update_total(total_count)
            mlog.debug(f"更新分页器总数: {total_count}")
        
        # 先创建历史记录项控件列表
        history_items = [self.create_history_item(item, global_audio_state) for item in history]
        
        # 更新列表控件，但先检查是否已添加到页面
        self.history_list.controls = history_items
        
        try:
            # 安全地更新UI
            if hasattr(self.history_list, "_Control__page") and self.history_list._Control__page:
                self.history_list.update()
                mlog.debug("历史记录列表更新完成(直接更新)")
            else:
                # 如果列表尚未添加到页面，不要调用update()
                mlog.debug("历史记录列表已设置，但不直接更新(等待父控件更新)")
        except Exception as e:
            mlog.error(f"更新历史列表失败: {str(e)}")
    
    def _filter_history(self, e):
        """根据关键词过滤历史记录"""
        self.current_keyword = self.search_field.value.strip().lower()
        self.current_page = 1  # 重置到第一页
        
        if "on_filter" in self.callbacks:
            self.callbacks["on_filter"](self.current_keyword, self.current_page, self.page_size)
    
    def _clear_search(self, e):
        """清除搜索框内容"""
        self.search_field.value = ""
        self.current_keyword = ""
        self.current_page = 1  # 重置到第一页
        
        if "on_clear_filter" in self.callbacks:
            self.callbacks["on_clear_filter"]()
        
        self.page.update()
    
    def _on_page_change(self, page):
        """
        页码变更回调
        
        Args:
            page: 新的页码
        """
        # 先更新本地状态
        mlog.debug(f"历史页面 - 页码变化: 从 {self.current_page} 到 {page}")
        self.current_page = page
        
        # 然后调用回调函数获取当前页的数据
        if "on_page_change" in self.callbacks:
            mlog.debug(f"历史页面 - 调用页面变更回调: {self.callbacks['on_page_change']}")
            self.callbacks["on_page_change"](page, self.page_size, self.current_keyword)
        else:
            mlog.warning("历史页面 - 没有找到页面变更回调函数")
    
    def _on_page_size_change(self, new_size, new_page):
        """
        每页显示数量变更回调
        
        Args:
            new_size: 新的每页显示数量
            new_page: 新的当前页码
        """
        # 先更新本地状态
        mlog.debug(f"历史页面 - 修改每页显示数量: {new_size}, 页码: {new_page}")
        self.page_size = new_size
        self.current_page = new_page
        
        # 然后调用回调函数重新获取数据
        if "on_page_size_change" in self.callbacks:
            self.callbacks["on_page_size_change"](new_size, new_page, self.current_keyword)
        elif "on_page_change" in self.callbacks:
            # 如果没有专门的页面大小变更回调，则使用页码变更回调
            self.callbacks["on_page_change"](new_page, new_size, self.current_keyword)
