import flet as ft
import os
import json
import asyncio
import datetime
import pygame
import shutil
from train import CosyVoiceWrapper
from modelscope import snapshot_download
import mlog
from path_manager import PathManager

# 初始化CosyVoiceWrapper
cosyvoice_wrapper = None

# 初始化路径管理器
path_manager = PathManager()

# 历史记录文件路径
history_file = path_manager.history_file
settings_file = path_manager.settings_file
roles_file = path_manager.roles_file

# 在文件开头，其他全局变量附近添加
global_audio_state = {
    "current_player": None,  # 当前播放的按钮
    "pygame_initialized": False
}

# 加载历史记录
def load_history():
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

# 保存历史记录
def save_history(history):
    with open(history_file, 'w') as f:
        json.dump(history, f)

# 加载设置
def load_settings():
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    return {
        'auto_load_model': False, 
        'theme_mode': 'system',  # system, light, dark
        'device': 'cpu'  # cpu, cuda
    }

# 保存设置
def save_settings(settings):
    with open(settings_file, 'w') as f:
        json.dump(settings, f)

# 加载音频角色
def load_roles():
    if os.path.exists(roles_file):
        with open(roles_file, 'r') as f:
            return json.load(f)
    return []

# 保存音频角色
def save_roles(roles):
    mlog.debug(f"保存角色数据: {roles}")  # 替换 print(roles)
    with open(roles_file, 'w') as f:
        json.dump(roles, f)

# 异步加载模型
async def load_model():
    global cosyvoice_wrapper
    cosyvoice_wrapper = CosyVoiceWrapper('pretrained_models/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=False)

# 下载模型
def download_model():
    snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')

# 检查模型是否已下载
def is_model_downloaded():
    return os.path.exists('pretrained_models/CosyVoice2-0.5B')

# 应用名
app_name = "CosyVoice2.0 - 0.5B"

# Flet应用程序
def main(page: ft.Page):
    # 设置窗口属性
    page.window.title_bar_hidden = True
    page.window.frameless = True
    page.window.title_bar_buttons_hidden = True

    page.title = app_name
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START

    # 创建自定义标题栏
    def close_window(e):
        page.window.close()

    def minimize_window(e):
        page.window.minimized = True
        page.update()

    title_bar = ft.Container(
        content=ft.Row(
            [
                ft.WindowDragArea(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AUTO_AWESOME, size=20),  # 修改：使用 Icons
                            ft.Text(app_name, size=16, weight=ft.FontWeight.BOLD),
                        ],
                    ),
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.REMOVE,  # 修改：使用 Icons
                    tooltip="最小化",
                    icon_color=ft.Colors.GREY_700,  # 修改：使用 Colors
                    on_click=minimize_window
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,  # 修改：使用 Icons
                    tooltip="关闭",
                    icon_color=ft.Colors.GREY_700,  # 修改：使用 Colors
                    on_click=close_window
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.padding.only(left=15, right=10, top=5, bottom=5),
        bgcolor=ft.Colors.SURFACE,  # 修改：使用 Colors
    )

    # 修改 set_theme_mode 函数，增加按钮更新
    def set_theme_mode(mode):
        page.theme_mode = mode
        
        # 确定当前应该使用的主题（light或dark）
        is_light = (mode == "light" or 
                   (mode == "system" and page.platform_brightness == ft.Brightness.LIGHT))
        
        # 设置菜单容器背景色
        menu_container.bgcolor = ft.colors.GREY_50 if is_light else ft.colors.GREY_900

        # 更新所有菜单按钮
        for button in menu_items.controls + [settings_button]:
            button.content.style.bgcolor = ft.colors.GREY_100 if is_light else ft.colors.GREY_800
            button.content.style.color = ft.colors.BLACK if is_light else ft.colors.WHITE
        
        # 更新内容区域的颜色
        if content_container.content:
            card_color = ft.colors.GREY_50 if is_light else ft.colors.GREY_900
            item_color = ft.colors.GREY_100 if is_light else ft.colors.GREY_800
            
            # 更新历史记录项的颜色
            if isinstance(history_list, ft.ListView):
                for item in history_list.controls:
                    if isinstance(item, ft.Container):
                        item.bgcolor = item_color
            
            # 更新角色列表项的颜色
            if isinstance(roles_list, ft.ListView):
                for item in roles_list.controls:
                    if isinstance(item, ft.Container):
                        item.bgcolor = item_color
            
            update_container_colors(content_container.content, card_color, item_color)
        
        page.update()

    def update_container_colors(control, card_color, item_color):
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
            update_container_colors(control.content, card_color, item_color)
        elif isinstance(control, (ft.Column, ft.Row)):
            for child in control.controls:
                update_container_colors(child, card_color, item_color)

    # 根据设置初始化主题
    settings = load_settings()
    page.theme_mode = settings.get('theme_mode', 'system')

    # 添加标题栏模型状态
    def update_title():
        page.title = f"{app_name} - {'模型已加载' if cosyvoice_wrapper else '模型未加载'}"
        page.update()

    # 加载历史记录、设置和音频角色
    history = load_history()
    roles = load_roles()

    # 修改 create_menu_button 函数
    def create_menu_button(text, on_click):
        # 获取当前是否是亮色主题
        is_light = (page.theme_mode == "light" or 
                   (page.theme_mode == "system" and page.platform_brightness == ft.Brightness.LIGHT))
        return ft.Container(
            content=ft.TextButton(
                text=text,
                on_click=on_click,
                style=ft.ButtonStyle(
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=10),
                    # 根据主题设置按钮颜色
                    bgcolor=ft.Colors.GREY_100 if is_light else ft.Colors.GREY_800,  # 修改：使用 Colors
                    # bgcolor=ft.colors.BLACK if is_light else ft.colors.WHITE,
                    color=ft.Colors.BLACK if is_light else ft.Colors.WHITE,  # 修改：使用 Colors
                ),
            ),
            margin=ft.margin.only(bottom=5),
            border_radius=10,
            width=180,
        )

    # 添加打开Github页面的函数
    def open_github(e):
        import webbrowser
        webbrowser.open('https://github.com/HG-ha/CosyVoice_Role_management')

    menu_items = ft.Column(
        controls=[
            create_menu_button("语音克隆", lambda e: show_page("clone")),
            create_menu_button("生成记录", lambda e: show_page("history")),
            create_menu_button("角色管理", lambda e: show_page("roles")),
            create_menu_button("Github", open_github),  # 添加 Github 按钮
        ],
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 设置按钮
    settings_button = create_menu_button("设置", lambda e: show_page("settings"))

    # 语音克隆界面
    text_input = ft.TextField(
        label="文本内容",
        multiline=True,
        min_lines=1,  # 最小显示3行
        max_lines=8,  # 最大显示8行
        border=ft.InputBorder.OUTLINE,
        border_radius=8
    )
    speaker_input = ft.TextField(label="说话人", border=ft.InputBorder.OUTLINE, border_radius=8)
    prompt_input = ft.TextField(label="提示音频路径或URL", border=ft.InputBorder.OUTLINE, border_radius=8)
    
    # 新增：选择角色按钮及对话框相关逻辑
    select_role_dialog = ft.AlertDialog(
        title=ft.Text("选择角色"),
        content=ft.Column([]),
        actions=[
            ft.TextButton("取消", on_click=lambda e: (setattr(select_role_dialog, "open", False), page.update()),
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ]
    )
    page.overlay.append(select_role_dialog)
    
    def select_role(role):
        speaker_input.value = role["name"]
        prompt_input.value = role["file"]
        page.update()
    
    def show_select_role_dialog(e):
        # 构建角色列表按钮
        role_buttons = [ft.TextButton(
            text=r["name"],
            on_click=lambda e, r=r: (select_role(r),
                                       setattr(select_role_dialog, "open", False),
                                       page.update())
        ) for r in roles]
        # 新增：分块函数，每行3个按钮
        def chunk_list(lst, n):
            return [lst[i:i+n] for i in range(0, len(lst), n)]
        rows = [ft.Row(controls=chunk, spacing=10) for chunk in chunk_list(role_buttons, 3)]
        # 将所有行组合成一个 Column
        select_role_dialog.content = ft.Column(controls=rows, spacing=10)
        select_role_dialog.open = True
        page.update()
    
    select_role_button = ft.ElevatedButton(
        text="选择角色",
        on_click=show_select_role_dialog,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    
    # 新增：在语音克隆中保存选中文件信息
    clone_selected_details = {"filename": None}
    
    speed_input = ft.Slider(
        value=1.0,
        min=0.1,
        max=3.0,
        divisions=29,  # 步进为0.1
        label="1.0",
        thumb_color=ft.Colors.BLUE  # 新增：设置滑块颜色
    )
    speed_value_text = ft.Text(f"当前速度: {speed_input.value:.1f}")
    speed_input.on_change = lambda e: (
        setattr(speed_value_text, "value", f"当前速度: {speed_input.value:.1f}"),
        setattr(speed_input, "label", f"{speed_input.value:.1f}"),
        speed_input.update(),
        speed_value_text.update()
    )
    output_text = ft.Text()

    def update_history(new_record):
        history.append(new_record)
        save_history(history)
        # 直接更新控件列表
        history_list.controls = [create_history_item(item) for item in history]
        if content_container.content == history_page:
            page.update()

    def generate_audio(e):
        if cosyvoice_wrapper is None:
            output_text.value = "模型尚未加载，请先加载模型。"
            page.update()
            return

        text = text_input.value
        speaker = speaker_input.value
        prompt = prompt_input.value
        speed = speed_input.value

        success, file_path = cosyvoice_wrapper.inference_cross_lingual(text, prompt, speed=speed)
        if success:
            # 移动文件到history目录
            new_file_path = os.path.join(path_manager.history_dir, os.path.basename(file_path))
            shutil.move(file_path, new_file_path)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_record = {
                'text': text,
                'speaker': speaker,
                'speed': speed,
                'reference': prompt,
                'file_path': new_file_path,  # 使用新的文件路径
                'timestamp': timestamp
            }
            output_text.value = f"生成成功: {new_file_path}"
            update_history(history_record)
        else:
            output_text.value = f"生成失败: {file_path}"
        page.update()

    # 新增：清除按钮及回调
    def clear_parameters(e):
        text_input.value = ""
        speaker_input.value = ""
        prompt_input.value = ""
        speed_input.value = 1.0
        speed_value_text.value = "当前速度: 1.0"
        output_text.value = ""
        page.update()
        
    clear_button = ft.ElevatedButton(
        text="清除",
        on_click=clear_parameters,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=10
        )
    )
    
    generate_button = ft.ElevatedButton(
        text="生成",
        on_click=generate_audio,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # 新增：为语音克隆界面添加文件选择控件及回调
    def clone_on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            prompt_input.value = file_path
            clone_selected_details["filename"] = os.path.basename(file_path)
            prompt_input.update()
    
    clone_file_picker = ft.FilePicker(on_result=clone_on_file_picked)
    page.overlay.append(clone_file_picker)
    
    clone_file_button = ft.ElevatedButton(
        text="选择文件",
        on_click=lambda _: clone_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=['wav', 'mp3']
        ),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    
    # 修改：将语音克隆界面中 prompt_input 行替换为包含“选择角色”和“选择文件”两个按钮
    clone_row = ft.Row([
        ft.Container(expand=True, content=prompt_input),
        select_role_button,
        clone_file_button
    ], spacing=10)
    
    # 修改 clone_page 布局
    clone_page = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                text_input,
                                speaker_input,
                                clone_row,
                                speed_input,
                                speed_value_text,
                                output_text,
                                ft.Row(
                                    [generate_button, clear_button],
                                    alignment=ft.MainAxisAlignment.END,
                                    spacing=10
                                )
                            ],
                            scroll=ft.ScrollMode.AUTO,  # 添加滚动功能
                            spacing=20,  # 增加组件间距
                        ),
                        expand=True,  # 允许容器扩展
                    )
                ],
                expand=True,  # 允许列扩展
            ),
            padding=20,
            expand=True,  # 允许容器扩展
        ),
        expand=True,  # 允许卡片扩展
    )

    # 生成记录界面
    def create_history_item(item):
        def play_pause_audio(e):
            import pygame
            try:
                # 如果有其他音频正在播放，先停止它
                if (global_audio_state["current_player"] is not None and 
                    global_audio_state["current_player"] != play_button):
                    global_audio_state["current_player"].selected = False
                    pygame.mixer.music.stop()
                    global_audio_state["current_player"].update()
                    
                # 初始化 pygame（如果还没初始化）
                if not global_audio_state["pygame_initialized"]:
                    pygame.init()
                    pygame.mixer.init()
                    global_audio_state["pygame_initialized"] = True

                if not play_button.selected:
                    # 开始播放
                    pygame.mixer.music.load(item['file_path'])
                    pygame.mixer.music.play()
                    play_button.selected = True
                    global_audio_state["current_player"] = play_button
                    # 启动定时器检查播放状态
                    page.timer_interval = 0.1
                    page.on_timer = check_playback_status
                else:
                    # 暂停播放
                    pygame.mixer.music.pause()
                    play_button.selected = False
                    # 停止定时器
                    page.timer_interval = None
                    page.on_timer = None
                page.update()
            except Exception as ex:
                mlog.error(f"播放失败: {str(ex)}") 
                play_button.selected = False
                global_audio_state["current_player"] = None
                page.update()

        def check_playback_status(e):
            if not pygame.mixer.music.get_busy():
                # 音频播放完毕，重置状态
                play_button.selected = False
                global_audio_state["current_player"] = None
                page.timer_interval = None
                page.on_timer = None
                page.update()
                return False  # 停止定时器
            return True  # 继续定时器

        def open_file_location(e):
            import subprocess
            import os
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
                mlog.error(f"打开文件位置失败: {str(ex)}")  # 替换 print(f"打开文件位置失败: {str(ex)}")

        play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            selected_icon=ft.Icons.PAUSE,
            tooltip="播放",
            selected=False,
            on_click=play_pause_audio
        )

        audio_state = {
            "pygame_loaded": False
        }

        def reuse_parameters(e):
            text_input.value = item['text']
            speaker_input.value = item['speaker']
            prompt_input.value = item['reference']
            speed_input.value = item['speed']
            speed_value_text.value = f"当前速度: {item['speed']:.1f}"
            show_page("clone")
            page.update()

        def delete_history(e):
            def handle_delete(e, dialog):
                dialog.open = False
                page.update()
                history.remove(item)
                save_history(history)
                history_list.controls.remove(container)
                history_list.update()
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("确认删除"),
                content=ft.Text("确定要删除这条记录吗？"),
                actions=[
                    ft.TextButton("取消", 
                                on_click=lambda e: (setattr(dialog, "open", False), page.update()),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                    ft.TextButton("删除", 
                                on_click=lambda e: handle_delete(e, dialog),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ]
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.colors.GREY_400),
                    ft.Text(item['timestamp'], size=12, color=ft.colors.GREY_400)
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
            # 移除固定的背景色，改为动态获取
            border_radius=10,
            padding=10,
            margin=5
        )
        return container

    # 搜索历史记录
    history_search = ft.TextField(
        label="搜索记录",
        hint_text="输入关键词搜索",
        width=300,
        border=ft.InputBorder.OUTLINE,
        border_radius=8
    )

    def filter_history(e):
        keyword = history_search.value.strip().lower()
        filtered = [
            create_history_item(item) 
            for item in history 
            if (keyword in item['text'].lower() or 
                keyword in item['speaker'].lower() or 
                keyword in os.path.basename(item['reference']).lower())
        ]
        history_list.controls = filtered
        history_list.update()

    history_search.on_change = filter_history

    def clear_history_search(e):
        history_search.value = ""
        history_list.controls = [create_history_item(item) for item in history]
        history_list.update()
        page.update()

    # 修改历史记录页面布局，将搜索框和清除按钮放在一行
    history_search_row = ft.Row(
        [
            history_search,
            ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="清除搜索",
                on_click=clear_history_search
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    # 历史记录列表
    history_list = ft.ListView(
        expand=True,
        spacing=10,
        controls=[create_history_item(item) for item in history]
    )

    # 修改历史记录页面布局
    history_page = ft.Card(
        content=ft.Container(
            content=ft.Column([
                history_search_row,  # 使用新的搜索行
                ft.Divider(),
                history_list,
            ]),
            padding=20
        )
    )

    # 设置界面
    auto_load_model_checkbox = ft.Checkbox(label="启动时自动加载模型", value=settings['auto_load_model'])
    theme_mode_dropdown = ft.Dropdown(
        label="主题模式",
        value=settings.get('theme_mode', 'system'),
        options=[
            ft.dropdown.Option("system", "跟随系统"),
            ft.dropdown.Option("light", "浅色模式"),
            ft.dropdown.Option("dark", "深色模式"),
        ],
        width=200,
    )

    # 功能保留
    device_dropdown = ft.Dropdown(
        label="设备选择",
        value=settings.get('device', 'cpu'),
        options=[
            ft.dropdown.Option("cpu", "CPU"),
            ft.dropdown.Option("cuda", "CUDA (GPU)"),
        ],
        width=200,
    )

    model_status = ft.Text(
        value="模型状态：" + ("已下载" if is_model_downloaded() else "未下载"),
        color=ft.Colors.GREEN if is_model_downloaded() else ft.Colors.RED  # 修改：使用 Colors
    )

    settings_output_text = ft.Text()  # 设置界面专用的输出文本

    

    # 修改加载模型按钮的回调函数
    async def load_model_button_click(e):
        # 创建加载中对话框
        loading_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("加载模型"),
            content=ft.Column([
                ft.ProgressRing(),
                ft.Text("正在加载模型，请稍候...", text_align=ft.TextAlign.CENTER),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            height = page.height * 0.2
            ),
            
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        update_title()
        try:
            await load_model()
            # 显示成功提示
            success_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("成功"),
                content=ft.Text("模型加载完成！"),
                actions=[
                    ft.TextButton("确定", on_click=lambda _: page.close(success_dialog))
                ],
            )
            page.close(loading_dialog)
            page.dialog = success_dialog
            page.open(success_dialog)
            update_title()
        except Exception as ex:
            # 显示错误提示
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("错误"),
                content=ft.Text(f"加载失败：{str(ex)}"),
                actions=[
                    ft.TextButton("确定", on_click=lambda _: page.close(error_dialog))
                ],
            )
            page.close(loading_dialog)
            page.dialog = error_dialog
            page.open(error_dialog)
    
    # 定义加载模型按钮
    load_model_button = ft.ElevatedButton(
        text="加载模型",
        on_click=load_model_button_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    def save_settings_button_click(e):
        settings['auto_load_model'] = auto_load_model_checkbox.value
        is_light = (theme_mode_dropdown.value == "light" or 
                   (theme_mode_dropdown.value == "system" and page.platform_brightness == ft.Brightness.LIGHT))
        settings['theme_mode'] = theme_mode_dropdown.value
        settings['device'] = device_dropdown.value
        save_settings(settings)
        set_theme_mode("light" if is_light else "dark")
        settings_output_text.value = "设置已保存。"
        page.update()

    save_settings_button = ft.ElevatedButton(
        text="保存设置",
        on_click=save_settings_button_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # 修改下载模型按钮点击逻辑
    def download_model_button_click(e):
        # 创建下载中对话框
        downloading_dialog = ft.AlertDialog(
            modal=True,
            adaptive=True,  # 自适应高度
            title=ft.Text("下载模型"),
            content=ft.Container(
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text("正在下载模型，请稍候...", text_align=ft.TextAlign.CENTER)
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True  # 内容自适应高度
                ),
                alignment=ft.alignment.center  # 内容居中
            ),
        )
        page.dialog = downloading_dialog
        page.open(downloading_dialog)
        page.update()

        try:
            if is_model_downloaded():
                page.close(downloading_dialog)
                settings_output_text.value = "模型已下载"
            else:
                download_model()
                page.close(downloading_dialog)
                # 显示下载成功提示
                success_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("下载完成"),
                    content=ft.Text("模型下载成功！"),
                    actions=[
                        ft.TextButton("确定", on_click=lambda _: page.close(success_dialog))
                    ],
                )
                page.dialog = success_dialog
                page.open(success_dialog)
                settings_output_text.value = "模型下载成功。"
        except Exception as ex:
            page.close(downloading_dialog)
            # 显示错误提示
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("下载失败"),
                content=ft.Text(f"下载失败：{str(ex)}"),
                actions=[
                    ft.TextButton("确定", on_click=lambda _: page.close(error_dialog))
                ],
            )
            page.dialog = error_dialog
            page.open(error_dialog)
        page.update()

    download_model_button = ft.ElevatedButton(
        text="下载模型",
        on_click=download_model_button_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    def clear_cache(e):
        try:
            path_manager.clear_cache()
            settings_output_text.value = "缓存清除成功"
            mlog.info("缓存清除成功")
        except Exception as ex:
            settings_output_text.value = f"清除缓存失败: {str(ex)}"
            mlog.error(f"清除缓存失败: {str(ex)}")
        page.update()

    clear_cache_button = ft.ElevatedButton(
        text="清除缓存",
        on_click=clear_cache,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # 修改设置页面布局
    settings_page = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("模型设置", size=20, weight=ft.FontWeight.BOLD),
                auto_load_model_checkbox,
                ft.Row(
                    controls=[load_model_button, download_model_button],
                    alignment=ft.MainAxisAlignment.END
                ),
                model_status,
                ft.Divider(),
                ft.Text("界面设置", size=20, weight=ft.FontWeight.BOLD),
                theme_mode_dropdown,
                ft.Divider(),
                ft.Text("缓存管理", size=20, weight=ft.FontWeight.BOLD),
                clear_cache_button,
                ft.Divider(),
                ft.Row(
                    controls=[save_settings_button],
                    alignment=ft.MainAxisAlignment.END
                ),
                settings_output_text
            ]),
            padding=20
        ),
        expand=True
    )

    # 音频角色管理界面 - 修复删除逻辑
    def create_role_item(role):
        def delete_role_click(e):
            def handle_delete(e, dialog, role_to_delete):
                try:
                    dialog.open = False
                    page.update()

                    roles.remove(role_to_delete)
                    save_roles(roles)

                    temp_controls = [create_role_item(r) for r in roles]
                    roles_list.controls = temp_controls
                    roles_list.update()
                    page.update()
                except Exception as ex:
                    mlog.error(f"删除角色失败: {str(ex)}")  # 替换 print(f"Error in handle_delete: {str(ex)}")

            def close_dialog(e, dialog):
                try:
                    dialog.open = False
                    page.update()
                except Exception as ex:
                    mlog.error(f"关闭对话框失败: {str(ex)}")  # 替换 print(f"Error in close_dialog: {str(ex)}")

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("确认删除"),
                content=ft.Text(f"确定要删除角色 '{role['name']}' 吗？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: close_dialog(e, dialog), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                    ft.TextButton("删除", on_click=lambda e: handle_delete(e, dialog, role), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
                ],
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        # 新增编辑按钮回调
        def edit_role_click(e):
            current_edit_role["role"] = role
            edit_role_name_input.value = role["name"]
            edit_role_description_input.value = role["description"]
            edit_role_file_input.value = role["file"]
            edit_role_dialog.open = True
            page.update()

        # 创建角色项UI
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column([
                        ft.Text(role['name'], size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(role['description'], size=14),
                        ft.Text(role['file'], size=12, color=ft.colors.GREY_400),
                    ], 
                    expand=True
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,  # 修改：使用 Icons 代替 icons
                        tooltip="编辑角色",
                        on_click=edit_role_click
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,  # 修改：使用 Icons 代替 icons
                        tooltip="删除角色",
                        on_click=delete_role_click
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=10,
            # 移除固定的背景色
            border_radius=8,
            margin=ft.margin.only(bottom=10)
        )

    # 修改角色列表的初始化方式
    roles_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        controls=[create_role_item(role) for role in roles] if roles else []
    )

    def show_add_role_dialog(e):
        add_role_dialog.open = True
        page.update()

    def close_add_role_dialog(e):
        add_role_dialog.open = False
        page.update()

    role_name_input = ft.TextField(label="角色名称")
    role_description_input = ft.TextField(label="角色描述")

    # 修改文件选择相关代码
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            role_file_input.value = e.files[0].path
            role_file_input.update()

    role_file_picker = ft.FilePicker(
        on_result=on_file_picked
    )
    role_file_input = ft.TextField(
        label="音频角色文件或URL",
        value=""
    )
    
    pick_file_button = ft.ElevatedButton(
        text="选择文件",
        on_click=lambda _: role_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=['wav', 'mp3']
        ),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10)  # 添加圆角
        )
    )

    def add_role(e):
        role_name = role_name_input.value
        role_description = role_description_input.value
        role_file = role_file_input.value
        if role_name and role_file:
            role = {"name": role_name, "description": role_description, "file": role_file}
            roles.append(role)
            save_roles(roles)
            roles_list.controls.append(create_role_item(role))
            roles_list.update()
            role_name_input.value = ""
            role_description_input.value = ""
            role_file_input.value = ""
            close_add_role_dialog(e)

    add_role_button = ft.ElevatedButton(
        text="添加角色",
        on_click=show_add_role_dialog,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    add_role_dialog = ft.AlertDialog(
        title=ft.Text("添加角色"),
        content=ft.Container(
            content=ft.Column([
                role_name_input,
                role_description_input,
                ft.Container(
                    content=ft.Column([
                        role_file_input,
                        pick_file_button
                    ]),
                    padding=ft.padding.only(top=10)
                )
            ]),
            width=400,
        ),
        actions=[
            ft.TextButton("取消", on_click=close_add_role_dialog, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
            ft.TextButton("添加", on_click=add_role, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ]
    )

    # 新增：编辑角色相关控件与对话框
    edit_role_name_input = ft.TextField(label="角色名称")
    edit_role_description_input = ft.TextField(label="角色描述")
    edit_role_file_input = ft.TextField(label="音频角色文件或URL", value="")
    
    # 添加编辑角色的文件选择按钮定义
    pick_edit_file_button = ft.ElevatedButton(
        text="选择文件",
        on_click=lambda _: role_file_picker.pick_files(allow_multiple=False, allowed_extensions=['wav', 'mp3']),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # 修改：文件选择回调，同时处理编辑和添加角色的情况
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            # 根据当前打开的对话框更新对应的输入框
            if edit_role_dialog.open:
                edit_role_file_input.value = file_path
                edit_role_file_input.update()
            else:
                role_file_input.value = file_path
                role_file_input.update()

    # 当前正在编辑的角色（引用role对象）
    current_edit_role = {"role": None}

    def save_edit_role(e):
        role = current_edit_role["role"]
        if role is None:
            return
        role["name"] = edit_role_name_input.value
        role["description"] = edit_role_description_input.value
        role["file"] = edit_role_file_input.value
        save_roles(roles)
        # 刷新列表
        roles_list.controls = [create_role_item(r) for r in roles]
        roles_list.update()
        edit_role_dialog.open = False
        page.update()

    edit_role_dialog = ft.AlertDialog(
        title=ft.Text("编辑角色"),
        content=ft.Container(
            content=ft.Column([
                edit_role_name_input,
                edit_role_description_input,
                ft.Container(
                    content=ft.Column([
                        edit_role_file_input,
                        pick_edit_file_button
                    ]),
                    padding=ft.padding.only(top=10)
                )
            ]),
            width=400,
        ),
        actions=[
            ft.TextButton("取消", on_click=lambda e: (setattr(edit_role_dialog, "open", False), page.update()),
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
            ft.TextButton("保存", on_click=save_edit_role,
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
        ]
    )

    # 搜索角色
    search_field = ft.TextField(
        label="搜索角色",
        hint_text="输入角色名称过滤",
        width=300,
        border=ft.InputBorder.OUTLINE,
        border_radius=8
    )
    def filter_roles(e):
        keyword = search_field.value.strip().lower()
        filtered = [create_role_item(r) for r in roles if keyword in r['name'].lower()]
        roles_list.controls = filtered
        roles_list.update()
    search_field.on_change = filter_roles

    def clear_role_search(e):
        search_field.value = ""
        roles_list.controls = [create_role_item(r) for r in roles]
        roles_list.update()
        page.update()

    # 修改角色搜索行布局
    role_search_row = ft.Row(
        [
            search_field,
            ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="清除搜索",
                on_click=clear_role_search
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    # 修改角色管理页面布局
    roles_page = ft.Card(
        content=ft.Container(
            content=ft.Column([
                role_search_row,  # 使用新的搜索行
                roles_list,
                ft.Row([add_role_button], alignment=ft.MainAxisAlignment.END)
            ]),
            padding=20
        )
    )

    # 页面切换逻辑
    content_container = ft.Container(
        expand=True,
        alignment=ft.alignment.top_left,
        height=page.height * 0.95
    )

    def show_page(page_name):
        if page_name == "clone":
            content_container.content = clone_page
        elif page_name == "history":
            content_container.content = history_page
        elif page_name == "roles":
            content_container.content = roles_page
        elif page_name == "settings":
            content_container.content = settings_page
        
        # 更新颜色
        if page.theme_mode == "light" or (page.theme_mode == "system" and page.platform_brightness == ft.Brightness.LIGHT):
            update_container_colors(content_container.content, ft.colors.GREY_50, ft.colors.GREY_100)
        else:
            update_container_colors(content_container.content, ft.colors.GREY_900, ft.colors.GREY_800)
        
        page.update()

    # 默认显示语音克隆界面
    show_page("clone")

    # 修改 menu_container 布局
    menu_container = ft.Container(
        content=ft.Column([
            menu_items,
            settings_button
        ]),
        width=200,
        height=page.height* 0.95,
        padding=20,  # 增加内边距使布局更加宽松
        bgcolor=ft.colors.GREY_100,
        border_radius=20,  # 添加圆角效果
        margin=15,  # 添加外边距,与边缘保持一定距离
    )

    # 相应的主布局也需要调整
    page.add(
        ft.Container(
            ft.Column(
                [
                    title_bar,
                    ft.Row(
                        [
                            menu_container,
                            ft.VerticalDivider(opacity=0.8),  # 降低分割线透明度
                            ft.Container(
                                content=ft.Column([content_container]),
                                expand=True,
                                padding=10
                            )
                        ],
                        expand=True,
                        spacing=0,
                    )
                ],
                spacing=0,
                expand=True,
            ),
            border_radius=20,
        )
    )

    # 添加 FilePicker 控件到页面
    page.overlay.append(role_file_picker)
    page.overlay.append(add_role_dialog)
    # 添加编辑对话框到页面 overlay
    page.overlay.append(edit_role_dialog)

    # 修改自动加载模型的实现
    if settings['auto_load_model']:
        asyncio.run(load_model_button_click(page))

    # 在page初始化后添加平台亮度变化的处理
    def on_platform_brightness_change(e):
        if page.theme_mode == "system":
            set_theme_mode("system")

    page.on_platform_brightness_change = on_platform_brightness_change

    # 在应用初始化时设置当前主题
    set_theme_mode(settings.get('theme_mode', 'system'))

ft.app(target=main)