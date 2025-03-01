import flet as ft

class ClonePage(ft.Card):
    """
    语音克隆页面
    """
    def __init__(self, page: ft.Page, callbacks=None):
        """
        初始化语音克隆页面
        
        Args:
            page: Flet页面对象
            callbacks: 回调函数字典，包含生成、清除等操作
        """
        self.page = page
        # 设置回调函数
        self.callbacks = callbacks or {}
        self.on_generate = self.callbacks.get("on_generate", lambda e: None)
        self.on_clear = self.callbacks.get("on_clear", lambda e: None)
        self.on_select_role = self.callbacks.get("on_select_role", lambda e: None)
        self.on_select_file = self.callbacks.get("on_select_file", lambda e: None)
        self.on_play_audio = self.callbacks.get("on_play_audio", lambda e: None)
        
        # 创建控件
        self.text_input = ft.TextField(
            label="文本内容",
            multiline=True,
            min_lines=1,
            max_lines=8,
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        self.speaker_input = ft.TextField(
            label="说话人", 
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        self.prompt_input = ft.TextField(
            label="提示音频路径或URL",
            border=ft.InputBorder.OUTLINE, 
            border_radius=8
        )
        
        self.instruction_input = ft.TextField(
            label="提示词 (instruction)",
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        self.zero_shot_speaker_input = ft.TextField(
            label="参考音频文本内容 (speaker)",
            border=ft.InputBorder.OUTLINE,
            border_radius=8
        )
        
        # 速度滑块
        self.speed_input = ft.Slider(
            value=1.0,
            min=0.1,
            max=3.0,
            divisions=29,  # 步进为0.1
            label="1.0",
            thumb_color=ft.Colors.BLUE
        )
        
        self.speed_value_text = ft.Text(f"当前速度: 1.0")
        self.speed_input.on_change = self._update_speed_text
        
        # 输出文本区域
        self.output_text = ft.Text()
        
        # 按钮
        self.generate_button = ft.ElevatedButton(
            text="生成",
            on_click=self.on_generate,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        self.clear_button = ft.ElevatedButton(
            text="清除",
            on_click=self.on_clear,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=10)
        )
        
        self.select_role_button = ft.ElevatedButton(
            text="选择角色",
            on_click=self.on_select_role,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        self.select_file_button = ft.ElevatedButton(
            text="选择文件",
            on_click=self.on_select_file,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        # 创建容器
        self.instruction_container = ft.Container(
            content=self.instruction_input,
            visible=False  # 默认隐藏
        )

        self.zero_shot_container = ft.Container(
            content=self.zero_shot_speaker_input,
            visible=False  # 默认隐藏
        )
        
        # 文件选择行
        self.clone_row = ft.Row(
            [
                ft.Container(expand=True, content=self.prompt_input),
                self.select_role_button,
                self.select_file_button
            ], 
            spacing=10
        )
        
        # 创建模式选择单选按钮组
        self.mode_radio_group = self._create_mode_radio_group()
        self.mode_container = ft.Container(
            content=self.mode_radio_group,
            margin=ft.margin.only(top=10, bottom=10)
        )
        
        # 音频播放区域
        self.audio_file_path = None
        self.audio_info_text = ft.Text("", expand=True)  # 添加expand=True使其能自适应宽度
        
        self.play_button = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED,
            icon_color=ft.Colors.BLUE,
            icon_size=30,
            tooltip="播放/暂停",
            selected=False,
            selected_icon=ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED,
            on_click=self.on_play_audio,
        )
        
        # 将音频播放组件包装成一个Row，以便在底部显示
        self.audio_player_row = ft.Row(
            [
                self.play_button,
                self.audio_info_text
            ],
            visible=False  # 默认隐藏
        )
        
        # 调用父类初始化
        super().__init__(
            content=self._create_content(),
            expand=True
        )
    
    def _create_content(self):
        """创建页面内容"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                # 基础参数部分
                                self.text_input,
                                self.speaker_input,
                                # 额外参数容器
                                self.instruction_container,
                                self.zero_shot_container,
                                # 其他参数
                                self.clone_row,
                                self.speed_input,
                                self.speed_value_text,
                                # 添加模式选择
                                self.mode_container,
                                # 输出文本
                                self.output_text,
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=20,
                        ),
                        expand=True,  # 让内容区域占满剩余空间
                    ),
                    # 底部按钮行 - 修改为包含音频播放器
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=self.audio_player_row,
                                    expand=True,  # 让它占据左侧空间
                                    alignment=ft.alignment.center_left  # 左对齐内容
                                ),
                                # 右侧按钮 - 使用单独容器确保右对齐
                                ft.Container(
                                    content=ft.Row(
                                        [self.generate_button, self.clear_button],
                                        spacing=10,
                                    ),
                                    alignment=ft.alignment.center_right  # 右对齐内容
                                ),
                            ],
                        ),
                        margin=ft.margin.only(top=20),
                    )
                ],
                spacing=0,  # 移除列间距以防止按钮移动
                expand=True  # 确保整个列占满高度
            ),
            padding=20,
            expand=True  # 确保容器占满卡片高度
        )
    
    def _create_mode_radio_group(self):
        """创建模式选择单选按钮组"""
        radio_group = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="quick", label="快速推理"),
                    ft.Radio(value="language_control", label="语言控制"),
                    ft.Radio(value="zero_shot", label="精准模式"),
                ]
            ),
            value="quick",  # 默认选择快速推理
        )
        
        def on_mode_change(e):
            # 根据选择的模式显示或隐藏相应的参数输入区域
            selected_mode = e.control.value
            self.instruction_container.visible = (selected_mode == "language_control")
            self.zero_shot_container.visible = (selected_mode == "zero_shot")
            self.page.update()
        
        radio_group.on_change = on_mode_change
        return radio_group
    
    def _update_speed_text(self, e):
        """更新速度显示文本"""
        self.speed_value_text.value = f"当前速度: {self.speed_input.value:.1f}"
        self.speed_input.label = f"{self.speed_input.value:.1f}"
        self.speed_input.update()
        self.speed_value_text.update()
    
    def get_current_mode(self):
        """获取当前选择的模式"""
        return self.mode_radio_group.value
    
    def set_mode(self, mode):
        """设置模式
        
        Args:
            mode: 模式名称 ("quick", "language_control", "zero_shot")
        """
        self.mode_radio_group.value = mode
        self.instruction_container.visible = (mode == "language_control")
        self.zero_shot_container.visible = (mode == "zero_shot")
    
    def clear_inputs(self):
        """清除所有输入"""
        self.text_input.value = ""
        self.speaker_input.value = ""
        self.prompt_input.value = ""
        self.instruction_input.value = ""
        self.zero_shot_speaker_input.value = ""
        self.speed_input.value = 1.0
        self.speed_value_text.value = "当前速度: 1.0"
        self.output_text.value = ""
        # 隐藏音频播放器
        self.audio_player_row.visible = False
        
    def get_parameters(self):
        """获取所有参数值
        
        Returns:
            dict: 参数字典
        """
        return {
            'text': self.text_input.value,
            'speaker': self.speaker_input.value,
            'prompt': self.prompt_input.value,
            'speed': self.speed_input.value,
            'mode': self.get_current_mode(),
            'instruction': self.instruction_input.value,
            'speaker_text': self.zero_shot_speaker_input.value
        }
        
    def set_parameters(self, params):
        """设置参数值
        
        Args:
            params (dict): 参数字典
        """
        # 优先切换模式
        if 'mode' in params:
            self.set_mode(params['mode'])
        if 'text' in params:
            self.text_input.value = params['text']
        if 'speaker' in params:
            self.speaker_input.value = params['speaker']
        if 'prompt' in params:
            self.prompt_input.value = params['prompt']
        if 'speed' in params:
            self.speed_input.value = params['speed']
            self.speed_input.label = f"{params['speed']:.1f}"
            self.speed_value_text.value = f"当前速度: {params['speed']:.1f}"
        if 'instruction' in params:
            self.instruction_input.value = params['instruction']
        if 'speaker_text' in params:
            self.zero_shot_speaker_input.value = params['speaker_text']
        
        # 需要更新界面
        self.page.update()
    
    def set_output_text(self, text):
        """设置输出文本
        
        Args:
            text: 输出文本
        """
        self.output_text.value = text
        self.output_text.update()
    
    def show_audio_player(self, audio_file, info_text=""):
        """显示音频播放器
        
        Args:
            audio_file: 音频文件路径
            info_text: 显示的信息文本
        """
        self.audio_file_path = audio_file
        self.audio_info_text.value = info_text
        self.audio_player_row.visible = True  # 修改为audio_player_row
        self.page.update()
    
    def get_current_audio_file(self):
        """获取当前音频文件路径
        
        Returns:
            str: 音频文件路径
        """
        return self.audio_file_path
