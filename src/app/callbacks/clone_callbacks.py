import flet as ft
import os
import datetime
import aiohttp
import json
import shutil  # 添加shutil导入
from app.core.utils import run_async
import app.core.mlog as mlog

class CloneCallbacks:
    def __init__(self, app, page, settings_manager, api_manager, history_manager):
        self.app = app
        self.page = page
        self.settings_manager = settings_manager
        self.api_manager = api_manager
        self.history_manager = history_manager
        
        # 存储当前生成的音频文件路径
        self.current_audio_path = None

        # 添加移动端特定属性
        self.is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
        
        # 使用path_manager中的历史目录
        self.mobile_audio_dir = self.app.path_manager.history_dir
        mlog.info(f"音频将保存到: {self.mobile_audio_dir}")

    def on_generate(self, e):
        """处理生成按钮点击事件"""
        run_async(self._check_and_generate())

    async def _check_and_generate(self):
        """检查API连接并生成音频"""
        # 获取当前API地址
        api_url = self.settings_manager.get('api_url', 'http://127.0.0.1:8000')
        
        # 检查API连接
        success, message = await self.api_manager.check_connection(api_url)
        if not success:
            self._show_error_dialog(f"API连接失败: {message}")
            return
        
        # 显示进度对话框
        progress_dialog = self._create_progress_dialog()
        self.page.open(progress_dialog)
        
        # 获取参数
        params = self.app.clone_page.get_parameters()
        
        # 生成音频
        success, result = await self.api_manager.generate_audio(
            api_url, 
            params, 
            lambda progress_info: self._update_progress(progress_dialog, progress_info)
        )
        
        if success:
            await self._handle_generation_success(params, result)
        else:
            self.app.clone_page.set_output_text(f"生成失败: {result}")
        
        # 关闭进度对话框
        self.page.close(progress_dialog)

    def _show_error_dialog(self, message):
        """显示错误对话框"""
        error_dialog = ft.AlertDialog(
            title=ft.Text("错误"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("确定", 
                             on_click=lambda _: (setattr(error_dialog, "open", False), self.page.update()),
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ],
        )
        self.page.open(error_dialog)

    def _create_progress_dialog(self):
        """创建进度对话框"""
        return ft.AlertDialog(
            modal=True,  # 添加模态窗口属性
            title=ft.Text("生成音频"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressBar(
                            value=0
                        ),
                        ft.Text(
                            "生成进度: 0%",
                            text_align=ft.TextAlign.CENTER,
                            size=14,
                            weight=ft.FontWeight.W_500
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,  # 垂直居中
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # 水平居中
                    spacing=20,  # 增加组件间距
                ),
                padding=ft.padding.all(20),  # 添加内边距
                width=min(200, self.page.width * 0.8),  # 自适应宽度，但不超过屏幕80%
                height=150,  # 固定高度
            ),
            actions=[],  # 移除所有操作按钮
            actions_alignment=ft.MainAxisAlignment.END,  # 操作按钮右对齐
        )

    def _update_progress(self, dialog, progress_info):
        """更新进度对话框"""
        if isinstance(progress_info, dict):
            progress = progress_info.get("progress", 0)
            dialog.content.content.controls[0].value = progress / 100
            dialog.content.content.controls[1].value = progress_info.get(
                "text_progress", f"生成进度: {progress:.1f}%"
            )
        else:
            progress = float(progress_info)
            dialog.content.content.controls[0].value = progress / 100
            dialog.content.content.controls[1].value = f"生成进度: {progress:.1f}%"
        self.page.update()

    async def _download_audio_file(self, api_url, file_path):
        """在移动端下载并保存音频文件"""
        try:
            # 提取文件名，忽略路径中的分隔符
            filename = os.path.basename(file_path.replace('\\', '/'))
            download_url = f"{api_url}/download/{filename}"
            
            # 使用时间戳作为文件名前缀，避免重复
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = os.path.join(
                self.mobile_audio_dir, 
                f"{timestamp}_{filename}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        with open(local_filename, 'wb') as f:
                            while True:
                                chunk = await response.content.read(8192)
                                if not chunk:
                                    break
                                f.write(chunk)
                        return True, local_filename
                    else:
                        error_msg = f"下载失败，HTTP状态码: {response.status}"
                        mlog.error(error_msg)
                        return False, error_msg

        except Exception as e:
            error_msg = f"下载音频文件失败: {str(e)}"
            mlog.error(error_msg)
            return False, error_msg

    async def _handle_generation_success(self, params, result):
        """处理生成成功的情况"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 处理路径分隔符
        normalized_result = result.replace('\\', '/')
        
        if self.is_mobile:
            # 移动端：下载音频文件
            api_url = self.settings_manager.get('api_url', 'http://127.0.0.1:8000')
            success, local_file = await self._download_audio_file(api_url, normalized_result)
            
            if not success:
                self.app.clone_page.set_output_text(f"下载音频失败: {local_file}")
                return
                
            target_file = local_file
        else:
            # 桌面端处理逻辑
            target_file = os.path.join(
                self.app.path_manager.history_dir, 
                os.path.basename(normalized_result)
            )
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            if os.path.exists(result):
                try:
                    # 使用shutil.move替代os.rename
                    shutil.move(result, target_file)
                except Exception as e:
                    error_msg = f"移动音频文件失败: {str(e)}"
                    mlog.error(error_msg)
                    self.app.clone_page.set_output_text(error_msg)
                    return

        # 创建并添加历史记录
        record = {
            'text': params['text'],
            'speaker': params['speaker'],
            'speed': params['speed'],
            'reference': params['prompt'],
            'file_path': target_file,
            'timestamp': timestamp,
            'mode': params['mode']
        }
        
        if params['mode'] == "language_control":
            record['instruction'] = params['instruction']
        elif params['mode'] == "zero_shot":
            record['speaker_text'] = params['speaker_text']
        
        # 更新历史记录和UI
        self.history_manager.add_record(record)
        self._update_ui_after_generation(target_file)

    def _update_ui_after_generation(self, target_file):
        """更新生成后的UI元素"""
        if self.app.history_page:
            self.app.history_page.update_history_list(
                self.history_manager.get_history(), 
                self.app.global_audio_state
            )
        
        self.current_audio_path = target_file
        self.app.clone_page.show_audio_player(
            target_file, 
            os.path.basename(target_file)
        )
        self.app.clone_page.set_output_text(f"生成成功: {target_file}")

    def on_clear(self, e):
        """清除输入框内容"""
        self.app.clone_page.clear_inputs()
        self.current_audio_path = None
        self.page.update()

    async def _upload_file_to_api(self, file_path):
        """将文件上传到API服务器"""
        try:
            # 获取API地址
            api_url = self.settings_manager.get('api_url', 'http://127.0.0.1:8000')
            upload_url = f"{api_url}/upload_file"
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()
                
            # 准备表单数据
            form_data = aiohttp.FormData()
            form_data.add_field('file',
                                file_content,
                                filename=os.path.basename(file_path),
                                content_type='audio/wav')
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            return True, result.get("relative_path")
                        else:
                            return False, result.get("error", "上传失败")
                    else:
                        return False, f"上传失败，HTTP状态码: {response.status}"
                        
        except Exception as e:
            error_msg = f"上传文件失败: {str(e)}"
            mlog.error(error_msg)
            return False, error_msg

    def on_select_role(self, e):
        """打开角色选择对话框"""
        # 构建角色列表按钮
        roles = self.app.role_manager.get_roles()
        role_buttons = [
            ft.TextButton(
                text=r["name"],
                on_click=lambda e, r=r: (
                    self.select_role(r),
                    setattr(self.app.select_role_dialog, "open", False),
                    self.page.update()
                )
            ) for r in roles
        ]
        
        # 分块函数，每行3个按钮
        def chunk_list(lst, n):
            return [lst[i:i+n] for i in range(0, len(lst), n)]
        
        rows = [ft.Row(controls=chunk, spacing=10) for chunk in chunk_list(role_buttons, 3)]
        
        # 将所有行组合成一个 Column
        self.app.select_role_dialog.content = ft.Column(
            controls=rows, 
            spacing=10, 
            height=min(self.page.height * 0.6, len(rows) * 50)
        )
        self.app.select_role_dialog.open = True
        self.page.update()

    async def select_role_with_upload(self, role):
        """选择角色并处理文件上传（如果在移动端）"""
        # 获取当前选择的模式
        mode = self.app.clone_page.get_current_mode()
        
        # 初始化参数
        params = {
            'speaker': role["name"]
        }
        
        # 处理音频文件路径
        file_path = role["file"]
        if self.is_mobile:
            # 如果是移动端，上传文件到API服务器
            success, server_path = await self._upload_file_to_api(file_path)
            if success:
                params['prompt'] = server_path  # 使用服务器相对路径
            else:
                self._show_error_dialog(f"文件上传失败: {server_path}")
                return
        else:
            # 桌面端直接使用文件路径
            params['prompt'] = file_path
        
        # 根据不同模式设置额外参数
        if mode == "language_control":
            params['instruction'] = role["description"]
        elif mode == "zero_shot" and role.get("speaker_text"):
            params['speaker_text'] = role.get("speaker_text")
        
        # 更新UI
        self.app.clone_page.set_parameters(params)

    def select_role(self, role):
        """选择角色后更新参数"""
        run_async(self.select_role_with_upload(role))

    def on_select_file(self, e):
        """打开文件选择器"""
        self.app.clone_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=['wav', 'mp3']
        )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """文件选择完成后的回调"""
        if e.files:
            file_path = e.files[0].path
            run_async(self.handle_file_selection(file_path))
    
    async def handle_file_selection(self, file_path):
        """处理文件选择，根据平台决定是否上传"""
        if self.is_mobile:
            # 移动端上传文件
            success, server_path = await self._upload_file_to_api(file_path)
            if success:
                self.app.clone_page.set_parameters({'prompt': server_path})
            else:
                self._show_error_dialog(f"文件上传失败: {server_path}")
        else:
            # 桌面端直接使用本地路径
            self.app.clone_page.set_parameters({'prompt': file_path})

    def on_play_audio(self, e):
        """处理音频播放按钮点击"""
        audio_file = self.app.clone_page.get_current_audio_file()
        if not audio_file or not os.path.exists(audio_file):
            self._show_error_dialog("无法播放音频：文件不存在")
            return
        
        # 使用音频管理器播放/停止音频
        self.app.audio_manager.play_audio(
            audio_file,
            self.app.clone_page.play_button,
            page=self.page
        )
