import flet as ft
import app.core.mlog as mlog

class Pagination(ft.Row):
    """
    分页组件
    """
    def __init__(
        self,
        total_items=0,
        page_size=10,
        current_page=1,
        on_page_change=None,
        on_page_size_change=None
    ):
        """
        初始化分页组件
        
        Args:
            total_items: 总记录数
            page_size: 每页记录数
            current_page: 当前页码
            on_page_change: 页码变更回调函数
            on_page_size_change: 每页记录数变更回调函数
        """
        self.total_items = total_items
        self.page_size = page_size
        self.current_page = current_page
        self.on_page_change = on_page_change or (lambda page: None)
        self.on_page_size_change = on_page_size_change or (lambda size, page: None)
        
        # 计算总页数
        self.total_pages = self._calculate_total_pages()
        
        # 创建页码选择器
        self.page_dropdown = ft.Dropdown(
            options=self._get_page_options(),
            value=str(current_page),
            on_change=self._on_page_selected,
        )
        
        # 创建每页记录数选择器
        self.per_page_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(text="5条/页", key="5"),
                ft.dropdown.Option(text="10条/页", key="10"),
                ft.dropdown.Option(text="20条/页", key="20"),
                ft.dropdown.Option(text="50条/页", key="50")
            ],
            value=str(page_size),
            on_change=self._on_page_size_selected
        )
        
        # 上一页按钮
        self.prev_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self._prev_page,
            disabled=current_page <= 1
        )
        
        # 下一页按钮
        self.next_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._next_page,
            disabled=current_page >= self.total_pages
        )
        
        # 页码信息文本
        self.page_info = ft.Text(
            self._get_page_info_text(),
            size=12,
            width=100
        )
        
        # 初始化Row
        super().__init__(
            controls=[
                self.prev_button,
                self.page_dropdown,
                self.next_button,
                self.page_info,
                self.per_page_dropdown
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    def _calculate_total_pages(self):
        """计算总页数"""
        if self.page_size == 0:
            return 1
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)
    
    def _get_page_options(self):
        """获取页码选项"""
        options = []
        for i in range(1, self.total_pages + 1):
            options.append(ft.dropdown.Option(text=str(i), key=str(i)))
        return options
    
    def _get_page_info_text(self):
        """获取页码信息文本"""
        return f"{self.current_page}/{self.total_pages}页 共{self.total_items}条"
    
    def _on_page_selected(self, e):
        """页码选择回调"""
        try:
            page = int(e.control.value)
            if page != self.current_page:
                self.current_page = page
                self._update_controls()
                self.on_page_change(page)
        except Exception as ex:
            mlog.error(f"页码选择异常: {str(ex)}")
    
    def _on_page_size_selected(self, e):
        """每页记录数选择回调"""
        try:
            new_size = int(e.control.value)
            if new_size != self.page_size:
                old_page = self.current_page
                self.page_size = new_size
                
                # 重新计算总页数和当前页码
                self.total_pages = self._calculate_total_pages()
                
                # 确保当前页码不超过总页数
                new_page = min(old_page, self.total_pages)
                self.current_page = new_page
                
                # 更新控件
                self._update_controls()
                
                # 调用回调
                self.on_page_size_change(new_size, new_page)
        except Exception as ex:
            mlog.error(f"每页记录数选择异常: {str(ex)}")
    
    def _prev_page(self, e):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_controls()
            self.on_page_change(self.current_page)
    
    def _next_page(self, e):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_controls()
            self.on_page_change(self.current_page)
    
    def _update_controls(self):
        """更新控件状态"""
        # 更新页码选择器
        self.page_dropdown.options = self._get_page_options()
        self.page_dropdown.value = str(self.current_page)
        
        # 更新按钮状态
        self.prev_button.disabled = self.current_page <= 1
        self.next_button.disabled = self.current_page >= self.total_pages
        
        # 更新页码信息
        self.page_info.value = self._get_page_info_text()
        
        # 更新每页记录数选择器
        self.per_page_dropdown.value = str(self.page_size)
        
        # 更新控件
        self.update()
    
    def update_total(self, total_items):
        """
        更新总记录数
        
        Args:
            total_items: 新的总记录数
        """
        try:
            self.total_items = total_items
            old_total_pages = self.total_pages
            
            # 重新计算总页数
            self.total_pages = self._calculate_total_pages()
            
            # 如果总页数变化或当前页超过总页数，更新当前页
            if old_total_pages != self.total_pages or self.current_page > self.total_pages:
                self.current_page = min(self.current_page, self.total_pages)
            
            # 更新控件状态
            self._update_controls()
        except Exception as ex:
            mlog.error(f"更新分页数据异常: {str(ex)}")
