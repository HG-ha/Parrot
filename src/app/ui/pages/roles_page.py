import flet as ft
import app.core.mlog as mlog
from app.ui.components.pagination import Pagination

class RolesPage(ft.Card):
    """
    角色管理页面
    """
    def __init__(self, page: ft.Page, callbacks=None):
        """
        初始化角色管理页面
        
        Args:
            page: Flet页面对象
            callbacks: 回调函数字典，包含添加、编辑、删除等操作
        """
        self.page = page
        self.callbacks = callbacks or {}
        self.roles = []  # 角色数据引用
        self.current_edit_role = {"role": None}  # 当前正在编辑的角色
        self.current_page = 1
        self.page_size = 5  # 修改默认每页显示为5条
        self.total_roles = 0
        self.current_keyword = ""

        self.is_mobile = self.page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
        
        # 创建搜索框，添加后缀清除按钮，设置高度使其更矮
        self.search_field = ft.TextField(
            label="搜索角色",
            hint_text="输入角色名称过滤",
            width=300,
            height=55,  # 设置较小的高度
            border=ft.InputBorder.OUTLINE,
            border_radius=6,  # 稍微减小圆角以适应矮一点的外观
            on_change=self._filter_roles,
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
        
        # 角色列表
        self.roles_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            controls=[]
        )
        
        # 分页控件
        self.pagination = Pagination(
            total_items=0,  # 初始为0，稍后更新
            page_size=self.page_size,
            current_page=self.current_page,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_page_size_change,  # 添加页面大小变更回调
            is_mobile=self.is_mobile
        )
        
        if self.is_mobile:
            self.add_role_button = ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                on_click=self._show_add_dialog,
                tooltip="添加角色",
            )
            # 将FAB添加到页面
            self.page.floating_action_button = self.add_role_button
            self.page.floating_action_button_location = ft.FloatingActionButtonLocation.END_FLOAT
        else:
            self.add_role_button = ft.ElevatedButton(
                text="添加角色",
                on_click=self._show_add_dialog,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            )
        
        # 创建添加对话框的控件
        self.role_name_input = ft.TextField(label="角色名称")
        self.role_description_input = ft.TextField(label="角色描述")
        self.role_file_input = ft.TextField(
            label="音频角色文件或URL",
            value=""
        )
        self.role_speaker_text_input = ft.TextField(
            label="精准模式提示文本",
            value="",
            hint_text="角色说的文字内容，用于精准模式的speaker参数"
        )
        
        self.pick_file_button = ft.ElevatedButton(
            text="选择文件",
            on_click=lambda _: self._pick_audio_file(False),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        # 添加角色对话框
        self.add_role_dialog = ft.AlertDialog(
            title=ft.Text("添加角色"),
            content=self._create_role_dialog_content(
                self.role_name_input,
                self.role_description_input,
                self.role_file_input,
                self.pick_file_button,
                self.role_speaker_text_input
            ),
            actions=[
                ft.TextButton(
                    "取消", 
                    on_click=self._close_add_dialog,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.TextButton(
                    "添加", 
                    on_click=self._add_role,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ]
        )
        
        # 创建编辑对话框的控件
        self.edit_role_name_input = ft.TextField(label="角色名称")
        self.edit_role_description_input = ft.TextField(label="角色描述")
        self.edit_role_file_input = ft.TextField(
            label="音频角色文件或URL",
            value=""
        )
        self.edit_role_speaker_text_input = ft.TextField(
            label="精准模式提示文本",
            value="",
            hint_text="角色说的文字内容，用于精准模式的speaker参数"
        )
        
        self.pick_edit_file_button = ft.ElevatedButton(
            text="选择文件",
            on_click=lambda _: self._pick_audio_file(True),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        # 编辑角色对话框
        self.edit_role_dialog = ft.AlertDialog(
            title=ft.Text("编辑角色"),
            content=self._create_role_dialog_content(
                self.edit_role_name_input,
                self.edit_role_description_input,
                self.edit_role_file_input,
                self.pick_edit_file_button,
                self.edit_role_speaker_text_input
            ),
            actions=[
                ft.TextButton(
                    "取消", 
                    on_click=lambda e: (setattr(self.edit_role_dialog, "open", False), self.page.update()),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.TextButton(
                    "保存", 
                    on_click=self._save_edit_role,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ]
        )
        
        # 添加对话框到页面overlay
        self.page.overlay.append(self.add_role_dialog)
        self.page.overlay.append(self.edit_role_dialog)
        
        # 创建页面布局
        bottom_row_controls = []
        if not self.is_mobile:
            bottom_row_controls.append(self.add_role_button)
            bottom_row_controls.append(self.pagination)
            bottom_row_alignment = ft.MainAxisAlignment.SPACE_BETWEEN
        else:
            bottom_row_controls.append(self.pagination)
            bottom_row_alignment = ft.MainAxisAlignment.CENTER
            
        content = ft.Container(
            content=ft.Column([
                self.search_row,
                ft.Divider(),
                self.roles_list,
                ft.Container(
                    content=ft.Row(
                        bottom_row_controls,
                        alignment=bottom_row_alignment
                    ),
                    padding=ft.padding.symmetric(vertical=10)  # 添加垂直内边距
                )
            ]),
            padding=20
        )
        
        # 调用父类初始化
        super().__init__(
            content=content
        )
    
    def _create_role_dialog_content(self, name_input, description_input, file_input, file_button, speaker_text_input):
        """创建角色对话框内容"""
        return ft.Container(
            content=ft.Column([
                name_input,
                description_input,
                speaker_text_input,
                ft.Container(
                    content=ft.Column([
                        file_input,
                        file_button
                    ]),
                    padding=ft.padding.only(top=10)
                )
            ], height=min(self.page.height * 0.6, 350)),  # 增加高度以容纳新的输入框
            width=400,
        )
    
    def _show_add_dialog(self, e):
        """显示添加角色对话框"""
        self.role_name_input.value = ""
        self.role_description_input.value = ""
        self.role_file_input.value = ""
        self.role_speaker_text_input.value = ""
        self.add_role_dialog.open = True
        self.page.update()
    
    def _close_add_dialog(self, e):
        """关闭添加角色对话框"""
        self.add_role_dialog.open = False
        self.page.update()
    
    def _add_role(self, e):
        """添加角色"""
        role_name = self.role_name_input.value
        role_description = self.role_description_input.value
        role_file = self.role_file_input.value
        role_speaker_text = self.role_speaker_text_input.value
        
        if role_name and role_file:
            role = {
                "name": role_name, 
                "description": role_description, 
                "file": role_file,
                "speaker_text": role_speaker_text
            }
            if "on_add_role" in self.callbacks:
                self.callbacks["on_add_role"](role)
            
            # 关闭对话框
            self._close_add_dialog(e)
    
    def _pick_audio_file(self, is_edit_mode=False):
        """选择音频文件"""
        if "on_pick_file" in self.callbacks:
            self.callbacks["on_pick_file"](is_edit_mode)
    
    def update_file_path(self, file_path, is_edit_mode=False):
        """更新文件路径
        
        Args:
            file_path: 文件路径
            is_edit_mode: 是否是编辑模式
        """
        if is_edit_mode:
            self.edit_role_file_input.value = file_path
            self.edit_role_file_input.update()
        else:
            self.role_file_input.value = file_path
            self.role_file_input.update()
    
    def create_role_item(self, role):
        """创建单个角色项
        
        Args:
            role: 角色数据字典
        
        Returns:
            ft.Container: 角色项控件
        """
        def delete_role_click(e):
            def handle_delete(e, dialog, role_to_delete):
                try:
                    if "on_delete_role" in self.callbacks:
                        self.callbacks["on_delete_role"](role_to_delete)
                    self.page.close(dialog)
                except Exception as ex:
                    mlog.error(f"删除角色失败: {str(ex)}")

            def close_dialog(e, dialog):
                try:
                    self.page.close(dialog)
                except Exception as ex:
                    mlog.error(f"关闭对话框失败: {str(ex)}")

            dialog = ft.AlertDialog(
                title=ft.Text("确认删除"),
                content=ft.Text(f"确定要删除角色 '{role['name']}' 吗？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: close_dialog(e, dialog), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                    ft.TextButton("删除", on_click=lambda e: handle_delete(e, dialog, role), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                ],
            )
            self.page.open(dialog)

        def edit_role_click(e):
            self.current_edit_role["role"] = role
            self.edit_role_name_input.value = role["name"]
            self.edit_role_description_input.value = role["description"]
            self.edit_role_file_input.value = role["file"]
            self.edit_role_speaker_text_input.value = role.get("speaker_text", "")
            self.edit_role_dialog.open = True
            self.page.update()

        # 创建要显示在列表中的控件
        column_controls = [
            ft.Text(role['name'], size=16, weight=ft.FontWeight.BOLD),
            ft.Text(role['description'], size=14),
            ft.Text(role['file'], size=12, color=ft.Colors.GREY_400),
        ]
        
        # 只有当speaker_text存在且非空时才添加
        speaker_text = role.get('speaker_text', '')
        if speaker_text:
            column_controls.append(
                ft.Text(f"精准模式文本: {speaker_text}", size=12, color=ft.Colors.GREY_400)
            )

        # 创建角色项UI
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        column_controls, 
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip="编辑角色",
                        on_click=edit_role_click
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip="删除角色",
                        on_click=delete_role_click
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=10,
            border_radius=8,
            margin=ft.margin.only(bottom=10),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),  # 添加浅色边框
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE)  # 添加浅色背景
        )
    
    def _save_edit_role(self, e):
        """保存编辑后的角色"""
        role = self.current_edit_role["role"]
        if role is None:
            return
        
        # 保留原有的ID和其他字段
        updated_role = {
            'id': role.get('id'),  # 确保ID被保留
            'name': self.edit_role_name_input.value,
            'description': self.edit_role_description_input.value,
            'file': self.edit_role_file_input.value,
            'speaker_text': self.edit_role_speaker_text_input.value
        }
        
        if "on_edit_role" in self.callbacks:
            self.callbacks["on_edit_role"](updated_role)
        
        self.edit_role_dialog.open = False
        self.page.update()
    
    def _on_page_change(self, page):
        """
        页码变更回调
        
        Args:
            page: 新的页码
        """
        # 先更新本地状态
        self.current_page = page
        
        # 然后调用回调函数获取当前页的数据
        if "on_page_change" in self.callbacks:
            self.callbacks["on_page_change"](page, self.page_size, self.current_keyword)
        self.roles_list.scroll_to(offset=0, duration=300)
    
    def _on_page_size_change(self, new_size, new_page):
        """
        每页显示数量变更回调
        
        Args:
            new_size: 新的每页显示数量
            new_page: 新的当前页码
        """
        # 先更新本地状态
        mlog.debug(f"修改每页显示数量: {new_size}, 页码: {new_page}")
        self.page_size = new_size
        self.current_page = new_page
        
        # 然后调用回调函数重新获取数据
        if "on_page_size_change" in self.callbacks:
            self.callbacks["on_page_size_change"](new_size, new_page, self.current_keyword)
        elif "on_page_change" in self.callbacks:
            # 如果没有专门的页面大小变更回调，则使用页码变更回调
            self.callbacks["on_page_change"](new_page, new_size, self.current_keyword)
        
        self.roles_list.scroll_to(offset=0, duration=300)
    
    def _filter_roles(self, e):
        """根据名称过滤角色"""
        self.current_keyword = self.search_field.value.strip().lower()
        self.current_page = 1  # 重置到第一页
        
        if "on_filter_roles" in self.callbacks:
            self.callbacks["on_filter_roles"](self.current_keyword, self.current_page, self.page_size)
    
    def _clear_search(self, e):
        """清除搜索框"""
        self.search_field.value = ""
        self.current_keyword = ""
        self.current_page = 1  # 重置到第一页
        
        if "on_clear_filter" in self.callbacks:
            self.callbacks["on_clear_filter"]()
        
        self.page.update()
    
    def update_roles_list(self, roles, total_count=None):
        """
        更新角色列表
        
        Args:
            roles: 角色数据列表
            total_count: 过滤后的总记录数(可选)
        """
        self.roles = roles
        
        # 更新总记录数
        if total_count is not None:
            self.total_roles = total_count
            self.pagination.update_total(total_count)
        
        # 先创建角色项控件列表
        role_items = [self.create_role_item(role) for role in roles]
        
        # 检查 roles_list 是否有 page 属性，确保它已添加到页面
        if hasattr(self.roles_list, "_Control__page") and self.roles_list._Control__page:
            # 已添加到页面，可以直接更新
            self.roles_list.controls = role_items
            self.roles_list.update()
        else:
            # 尚未添加到页面，只替换控件列表但不调用 update()
            self.roles_list.controls = role_items