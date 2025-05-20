import flet as ft
import app.core.mlog as mlog

class RoleCallbacks:
    def __init__(self, app, page, role_manager):
        self.app = app
        self.page = page
        self.role_manager = role_manager

    def roles_on_add_role(self, role):
        """添加新角色"""
        self.role_manager.add_role(role)
        # 重新加载当前页数据
        self.roles_on_page_change(
            self.app.roles_page.current_page, 
            self.app.roles_page.page_size,
            self.app.roles_page.current_keyword
        )

    def roles_on_edit_role(self, role):
        """编辑角色信息"""
        self.role_manager.update_role(role)
        # 重新加载当前页数据
        self.roles_on_page_change(
            self.app.roles_page.current_page, 
            self.app.roles_page.page_size,
            self.app.roles_page.current_keyword
        )

    def roles_on_delete_role(self, role):
        """删除角色"""
        self.role_manager.delete_role(role)
        # 重新计算总页数并加载当前页
        total = self.role_manager.get_filtered_count(self.app.roles_page.current_keyword)
        
        # 如果当前页已经没有数据，则回到上一页
        page = self.app.roles_page.current_page
        pages_count = (total + self.app.roles_page.page_size - 1) // self.app.roles_page.page_size
        if page > pages_count and page > 1:
            page = pages_count
        
        self.roles_on_page_change(
            page, 
            self.app.roles_page.page_size,
            self.app.roles_page.current_keyword
        )

    def roles_on_filter(self, keyword, page=1, page_size=None):
        """根据关键词过滤角色"""
        # 如果没有提供page_size，则使用当前页面设置的大小
        page_size = page_size if page_size is not None else self.app.roles_page.page_size
        
        filtered = self.role_manager.filter_roles_paged(keyword, page, page_size)
        total = self.role_manager.get_filtered_count(keyword)
        self.app.roles_page.update_roles_list(filtered, total)

    def roles_on_clear_filter(self):
        """清除角色过滤器"""
        self.app.roles_page.current_keyword = ""
        self.roles_on_page_change(1, self.app.roles_page.page_size, "")

    def roles_on_page_change(self, page, page_size=None, keyword=""):
        """页面变化回调"""
        # 确保使用提供的页面大小，或者默认使用当前页面设置
        page_size = page_size if page_size is not None else self.app.roles_page.page_size
        
        # 强制记录参数
        mlog.debug(f"角色页面回调 - 加载页码: {page}, 每页显示: {page_size}, 关键词: '{keyword}'")
        
        try:
            # 强制更新当前页面的设置
            self.app.roles_page.current_page = page
            self.app.roles_page.page_size = page_size
            
            # 获取筛选或全部数据
            if keyword:
                roles = self.role_manager.filter_roles_paged(keyword, page, page_size)
                total = self.role_manager.get_filtered_count(keyword)
            else:
                roles = self.role_manager.get_roles_paged(page, page_size)
                total = self.role_manager.get_total_roles()
            
            mlog.debug(f"角色页面回调 - 获取到 {len(roles)} 条记录, 共 {total} 条")
            self.app.roles_page.update_roles_list(roles, total)
            
        except Exception as e:
            mlog.error(f"角色页面回调异常: {str(e)}")
            # 确保至少显示一个空列表，防止UI崩溃
            self.app.roles_page.update_roles_list([], 0)

    def roles_on_page_size_change(self, new_size, new_page, keyword=""):
        """
        页面大小变更回调
        
        Args:
            new_size: 新的每页显示数量
            new_page: 新的当前页码
            keyword: 搜索关键词
        """
        # 记录变更详情
        mlog.debug(f"角色页面回调 - 修改每页显示数量: {new_size}, 页码: {new_page}")
        
        # 明确更新当前页面的页码和每页显示数量
        self.app.roles_page.current_page = new_page
        self.app.roles_page.page_size = new_size
        
        # 调用页面变更回调来重新加载数据
        self.roles_on_page_change(new_page, new_size, keyword)

    def roles_on_pick_file(self, is_edit_mode):
        """打开文件选择器"""
        self.app.role_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=['wav', 'mp3']
        )
        # 记录当前是否处于编辑模式
        self.app.role_file_picker.data = is_edit_mode

    def role_file_picked(self, e: ft.FilePickerResultEvent):
        """文件选择完成后的回调"""
        if e.files:
            file_path = e.files[0].path
            # 根据之前设置的标志决定更新哪个输入框
            is_edit_mode = self.app.role_file_picker.data
            self.app.roles_page.update_file_path(file_path, is_edit_mode)
