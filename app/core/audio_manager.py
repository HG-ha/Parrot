import flet_audio as fat
import app.core.mlog as mlog
import time

class AudioManager:
    """
    音频管理类，处理音频播放相关功能
    """
    def __init__(self):
        """初始化音频管理器"""
        self.state = {
            "current_player": None,  # 当前播放的按钮
            "current_audio": None,   # 当前的Audio组件
            "page": None,            # flet页面引用
            "audio_added": False,    # 标记音频组件是否已添加到页面
        }

    def initialize(self, page):
        """
        初始化音频管理器
        
        Args:
            page: Flet页面对象，用于添加Audio组件
        """
        self.state["page"] = page
        return True

    def play_audio(self, file_path, play_button, on_complete=None, page=None):
        """
        播放音频文件
        
        Args:
            file_path: 音频文件路径
            play_button: 播放按钮控件
            on_complete: 播放完成后的回调函数
            page: Flet页面对象，用于更新UI
        """
        try:
            # 使用提供的页面，或者使用初始化时保存的页面
            current_page = page or self.state["page"]
            if not current_page:
                mlog.error("无法播放音频：页面对象未提供")
                return False
            
            # 确保当前没有音频播放中，或者是同一个按钮的切换操作
            if play_button.selected:
                # 如果当前按钮已处于选中状态，表示要暂停
                mlog.info(f"暂停音频: {file_path}")
                if self.state["current_audio"] and self.state["audio_added"]:
                    self.state["current_audio"].pause()
                    
                play_button.selected = False
                self.state["current_player"] = None
                play_button.update()
                current_page.update()
                return True
                
            # 停止任何正在播放的音频
            self._stop_current_audio()
                
            # 创建并播放新音频
            mlog.info(f"开始播放新音频: {file_path}")
            
            # 创建新的Audio组件
            audio = fat.Audio(
                src=file_path,
                autoplay=False,  # 先不要自动播放
                volume=1,
                on_state_changed=lambda e: self._handle_state_change(
                    e, play_button, on_complete, current_page
                )
            )
            
            # 先添加到页面，再播放
            current_page.overlay.append(audio)
            current_page.update()
            
            # 确保组件已添加到页面
            time.sleep(0.1)  # 给一点时间让组件添加到页面
            
            # 更新状态
            self.state["current_player"] = play_button
            self.state["current_audio"] = audio
            self.state["audio_added"] = True
            
            # 标记按钮为选中状态
            play_button.selected = True
            play_button.update()
            
            # 开始播放
            audio.play()
            current_page.update()
            
            return True
            
        except Exception as ex:
            mlog.error(f"播放失败: {str(ex)}")
            play_button.selected = False
            self.state["current_player"] = None
            if page:
                page.update()
            return False
    
    def _stop_current_audio(self):
        """停止当前正在播放的音频"""
        try:
            if self.state["current_audio"] and self.state["audio_added"]:
                mlog.info("停止当前音频播放")
                # 停止播放
                self.state["current_audio"].pause()
                self.state["current_audio"].release()
                
                # 从页面移除
                if self.state["page"] and self.state["current_audio"] in self.state["page"].overlay:
                    self.state["page"].overlay.remove(self.state["current_audio"])
                    self.state["page"].update()
                
                self.state["audio_added"] = False
                
            if self.state["current_player"]:
                self.state["current_player"].selected = False
                self.state["current_player"].update()
                self.state["current_player"] = None
                
        except Exception as ex:
            mlog.error(f"停止当前音频失败: {str(ex)}")
    
    def _handle_state_change(self, e, play_button, on_complete=None, page=None):
        """
        处理音频状态变化
        
        Args:
            e: 状态变化事件
            play_button: 播放按钮控件
            on_complete: 播放完成回调
            page: Flet页面对象
        """
        try:
            mlog.info(f"音频状态变化: {e.data}")
            
            # 处理播放状态变化
            if e.data == "playing":
                play_button.selected = True
                play_button.update()
                if page:
                    page.update()
            
            # 处理暂停状态
            elif e.data == "paused":
                # 不必做任何事，按钮状态应该已经处理过了
                pass
            
            # 检查状态是否为completed
            elif e.data == "completed" or e.data == "stopped":
                # 音频播放完毕，重置状态
                play_button.selected = False
                self.state["current_player"] = None
                
                # 清理Audio控件
                if self.state["current_audio"] and self.state["audio_added"]:
                    try:
                        # 从页面移除
                        if page and self.state["current_audio"] in page.overlay:
                            page.overlay.remove(self.state["current_audio"])
                    except Exception as ex:
                        mlog.error(f"移除Audio控件失败: {str(ex)}")
                        
                    self.state["audio_added"] = False
                    self.state["current_audio"] = None
                
                # 调用完成回调
                if on_complete:
                    on_complete()
                
                # 强制更新按钮状态
                play_button.update()
                if page:
                    page.update()
                    
        except Exception as ex:
            mlog.error(f"处理音频状态变化失败: {str(ex)}")
            try:
                if play_button:
                    play_button.selected = False
                    play_button.update()
                self.state["current_player"] = None
                if page:
                    page.update()
            except Exception as ex2:
                mlog.error(f"重置按钮状态失败: {str(ex2)}")
    
    def stop_all(self):
        """停止所有音频播放"""
        try:
            self._stop_current_audio()
        except Exception as ex:
            mlog.error(f"停止所有音频失败: {str(ex)}")
    
    def cleanup(self):
        """清理音频资源"""
        self.stop_all()
        self.state["page"] = None
