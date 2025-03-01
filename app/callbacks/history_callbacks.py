import app.core.mlog as mlog

class HistoryCallbacks:
    def __init__(self, app, page, history_manager, audio_manager, global_audio_state):
        self.app = app
        self.page = page
        self.history_manager = history_manager
        self.audio_manager = audio_manager
        self.global_audio_state = global_audio_state

    def history_on_play(self, item, play_button):
        """播放历史记录音频"""
        self.audio_manager.play_audio(
            item['file_path'],
            play_button,
            page=self.page
        )

    def history_on_delete(self, item, container):
        """删除历史记录项"""
        self.history_manager.delete_record(item)
        
        # 重新计算总页数并加载当前页
        total = self.history_manager.get_filtered_count(self.app.history_page.current_keyword)
        
        # 如果当前页已经没有数据，则回到上一页
        page = self.app.history_page.current_page
        pages_count = (total + self.app.history_page.page_size - 1) // self.app.history_page.page_size
        if page > pages_count and page > 1:
            page = pages_count
        
        self.history_on_page_change(
            page, 
            self.app.history_page.page_size,
            self.app.history_page.current_keyword
        )

    def history_on_reuse(self, item):
        """重用历史记录参数"""
        # 先切换到克隆页面
        self.app.show_page("clone")
        
        # 设置参数
        self.app.clone_page.set_parameters({
            'text': item['text'],
            'speaker': item['speaker'],
            'prompt': item['reference'],
            'speed': item['speed'],
            'mode': item.get('mode', 'quick')
        })
        
        # 设置特定模式的参数
        if item.get('mode') == 'language_control' and 'instruction' in item:
            self.app.clone_page.set_parameters({'instruction': item['instruction']})
        elif item.get('mode') == 'zero_shot' and 'speaker_text' in item:
            self.app.clone_page.set_parameters({'speaker_text': item['speaker_text']})

    def history_on_filter(self, keyword, page=1, page_size=None):
        """根据关键词过滤历史记录"""
        # 确保使用提供的页面大小，或者默认使用当前页面设置
        page_size = page_size if page_size is not None else self.app.history_page.page_size
        
        filtered = self.history_manager.filter_history_paged(keyword, page, page_size)
        total = self.history_manager.get_filtered_count(keyword)
        self.app.history_page.update_history_list(filtered, self.global_audio_state, total)

    def history_on_clear_filter(self):
        """清除历史记录过滤器"""
        self.app.history_page.current_keyword = ""
        self.history_on_page_change(1, self.app.history_page.page_size, "")

    def history_get_global_audio_state(self):
        """获取全局音频状态"""
        return self.global_audio_state

    def history_on_page_change(self, page, page_size=None, keyword=""):
        """
        页面变化回调
        
        Args:
            page: 页码
            page_size: 每页显示数量
            keyword: 搜索关键词
        """
        # 确保使用提供的页面大小，或者默认使用当前页面设置
        page_size = page_size if page_size is not None else self.app.history_page.page_size
        
        # 强制记录参数
        mlog.debug(f"历史页面回调 - 加载页码: {page}, 每页显示: {page_size}, 关键词: '{keyword}'")
        
        try:
            # 强制更新当前页面的设置
            self.app.history_page.current_page = page
            self.app.history_page.page_size = page_size
            
            # 获取筛选或全部数据
            if keyword:
                history = self.history_manager.filter_history_paged(keyword, page, page_size)
                total = self.history_manager.get_filtered_count(keyword)
            else:
                history = self.history_manager.get_history_paged(page, page_size)
                total = self.history_manager.get_total_history()
            
            mlog.debug(f"历史页面回调 - 获取到 {len(history)} 条记录, 共 {total} 条")
            
            def update_ui():
                # 更新历史列表
                self.app.history_page.update_history_list(history, self.global_audio_state, total)
                # 触发页面整体更新
                self.page.update()
                
            # 在主线程中安全更新UI
            update_ui()
            
        except Exception as e:
            mlog.error(f"历史页面更新失败: {str(e)}")
    
    def history_on_page_size_change(self, new_size, new_page, keyword=""):
        """
        页面大小变更回调
        
        Args:
            new_size: 新的每页显示数量
            new_page: 新的当前页码
            keyword: 搜索关键词
        """
        # 记录变更详情
        mlog.debug(f"历史页面回调 - 修改每页显示数量: {new_size}, 页码: {new_page}")
        
        # 明确更新当前页面的页码和每页显示数量
        self.app.history_page.current_page = new_page
        self.app.history_page.page_size = new_size
        
        # 调用页面变更回调来重新加载数据
        self.history_on_page_change(new_page, new_size, keyword)
