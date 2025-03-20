import os
import json
import datetime
import shutil
import app.core.mlog as mlog

class HistoryManager:
    """
    历史记录管理类，负责历史生成记录的读取和保存
    """
    def __init__(self, pathmanager,dbmanager):
        """初始化历史记录管理器"""
        self.path_manager = pathmanager
        self.db_manager = dbmanager
        self.history_file = self.path_manager.history_file
        self.history_dir = self.path_manager.history_dir
        self._migrate_from_json_if_needed()
    
    def _migrate_from_json_if_needed(self):
        """
        如果存在旧的JSON文件，则迁移数据到SQLite
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                
                if history:
                    conn = self.db_manager.get_connection()
                    cursor = conn.cursor()
                    
                    # 检查数据库中是否已有历史数据
                    cursor.execute("SELECT COUNT(*) FROM history")
                    count = cursor.fetchone()[0]
                    
                    # 如果数据库是空的，才进行迁移
                    if count == 0:
                        for item in history:
                            cursor.execute(
                                "INSERT INTO history (text, speaker, reference, file_path, speed, mode, instruction, speaker_text, timestamp) "
                                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (item.get('text', ''), item.get('speaker', ''), item.get('reference', ''),
                                 item.get('file_path', ''), item.get('speed', 1.0), item.get('mode', 'quick'),
                                 item.get('instruction', ''), item.get('speaker_text', ''), item.get('timestamp', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            )
                        
                        conn.commit()
                        mlog.info(f"成功从JSON迁移{len(history)}条历史记录到数据库")
                        
                        # 备份旧文件
                        backup_file = self.history_file + ".bak"
                        os.rename(self.history_file, backup_file)
                        mlog.info(f"旧的JSON文件已备份为: {backup_file}")
                    
                    conn.close()
            except Exception as e:
                mlog.error(f"从JSON迁移历史记录失败: {str(e)}")
    
    def add_record(self, record, source_file=None):
        """
        添加历史记录
        
        Args:
            record: 记录数据字典
            source_file: 源文件路径（如果需要移动文件）
        
        Returns:
            bool: 添加是否成功
        """
        try:
            # 添加时间戳（如果没有）
            if 'timestamp' not in record:
                record['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 如果提供源文件，则移动到历史目录
            if source_file and os.path.exists(source_file):
                # 确保历史目录存在
                os.makedirs(self.history_dir, exist_ok=True)
                
                # 构建目标文件路径
                target_file = os.path.join(self.history_dir, os.path.basename(source_file))
                
                # 移动文件
                shutil.move(source_file, target_file)
                
                # 更新记录中的文件路径
                record['file_path'] = target_file
            
            # 添加记录到数据库
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO history (text, speaker, reference, file_path, speed, mode, instruction, speaker_text, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (record.get('text', ''), record.get('speaker', ''), record.get('reference', ''),
                 record.get('file_path', ''), record.get('speed', 1.0), record.get('mode', 'quick'),
                 record.get('instruction', ''), record.get('speaker_text', ''), record['timestamp'])
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            mlog.error(f"添加历史记录失败: {str(e)}")
            return False
    
    def delete_record(self, index_or_record, delete_file=True):
        """
        删除历史记录
        
        Args:
            index_or_record: 记录索引或记录对象
            delete_file: 是否同时删除音频文件
        
        Returns:
            bool: 删除是否成功
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            file_path = None
            
            if isinstance(index_or_record, int):
                # 先获取文件路径
                cursor.execute("SELECT file_path FROM history WHERE id=?", (index_or_record,))
                row = cursor.fetchone()
                if row:
                    file_path = row['file_path']
                
                # 删除记录
                cursor.execute("DELETE FROM history WHERE id=?", (index_or_record,))
            else:
                # 通过对象删除
                record_id = index_or_record.get('id')
                file_path = index_or_record.get('file_path')
                
                if record_id:
                    cursor.execute("DELETE FROM history WHERE id=?", (record_id,))
                else:
                    # 如果没有ID，尝试通过文件路径匹配
                    cursor.execute("DELETE FROM history WHERE file_path=?", (file_path,))
            
            conn.commit()
            conn.close()
            
            # 删除对应的音频文件
            if delete_file and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    mlog.info(f"成功删除音频文件: {file_path}")
                except Exception as e:
                    mlog.error(f"删除音频文件失败: {file_path}, 错误: {str(e)}")
            
            return True
        except Exception as e:
            mlog.error(f"删除历史记录失败: {str(e)}")
            return False
    
    def get_history(self):
        """
        获取所有历史记录
        
        Returns:
            list: 历史记录列表
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, text, speaker, reference, file_path, speed, mode, instruction, speaker_text, timestamp "
                "FROM history ORDER BY timestamp DESC"
            )
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row['id'],
                    'text': row['text'],
                    'speaker': row['speaker'],
                    'reference': row['reference'],
                    'file_path': row['file_path'],
                    'speed': row['speed'],
                    'mode': row['mode'],
                    'instruction': row['instruction'],
                    'speaker_text': row['speaker_text'],
                    'timestamp': row['timestamp']
                })
            
            conn.close()
            return history
        except Exception as e:
            mlog.error(f"获取历史记录失败: {str(e)}")
            return []
    
    def filter_history(self, keyword):
        """
        按关键词筛选历史记录
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            list: 过滤后的历史记录列表
        """
        try:
            if not keyword or keyword.strip() == "":
                return self.get_history()
            
            keyword = f"%{keyword.lower().strip()}%"
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, text, speaker, reference, file_path, speed, mode, instruction, speaker_text, timestamp "
                "FROM history "
                "WHERE LOWER(text) LIKE ? OR LOWER(speaker) LIKE ? OR LOWER(reference) LIKE ? "
                "ORDER BY timestamp DESC",
                (keyword, keyword, keyword)
            )
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row['id'],
                    'text': row['text'],
                    'speaker': row['speaker'],
                    'reference': row['reference'],
                    'file_path': row['file_path'],
                    'speed': row['speed'],
                    'mode': row['mode'],
                    'instruction': row['instruction'],
                    'speaker_text': row['speaker_text'],
                    'timestamp': row['timestamp']
                })
            
            conn.close()
            return history
        except Exception as e:
            mlog.error(f"筛选历史记录失败: {str(e)}")
            return []
    
    def clear_all(self, delete_files=False):
        """
        清除所有历史记录
        
        Args:
            delete_files: 是否同时删除所有音频文件
        
        Returns:
            bool: 清除是否成功
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 如果需要删除文件，先获取所有文件路径
            file_paths = []
            if delete_files:
                cursor.execute("SELECT file_path FROM history")
                for row in cursor.fetchall():
                    file_paths.append(row['file_path'])
            
            # 清空历史记录表
            cursor.execute("DELETE FROM history")
            
            conn.commit()
            conn.close()
            
            # 删除文件
            if delete_files:
                for file_path in file_paths:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            mlog.error(f"删除音频文件失败: {file_path}, 错误: {str(e)}")
            
            return True
        except Exception as e:
            mlog.error(f"清除所有历史记录失败: {str(e)}")
            return False
    
    def get_history_paged(self, page=1, page_size=10):
        """
        分页获取历史记录
        
        Args:
            page: 页码，从1开始
            page_size: 每页记录数
            
        Returns:
            list: 当前页的历史记录列表
        """
        try:
            mlog.debug(f"历史管理器 - 分页获取历史: 页码={page}, 每页={page_size}")
            
            # 验证输入参数
            if page < 1:
                page = 1
                mlog.warning(f"页码必须大于0，已自动调整为1")
            
            if page_size < 1:
                page_size = 10
                mlog.warning(f"每页显示数量必须大于0，已自动调整为10")
                
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            offset = (page - 1) * page_size
            
            # SQL调试信息
            sql = "SELECT id, text, speaker, reference, file_path, speed, mode, instruction, speaker_text, timestamp FROM history ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            mlog.debug(f"执行SQL: {sql} [params: {page_size}, {offset}]")
            
            cursor.execute(sql, (page_size, offset))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row['id'],
                    'text': row['text'],
                    'speaker': row['speaker'],
                    'reference': row['reference'],
                    'file_path': row['file_path'],
                    'speed': row['speed'],
                    'mode': row['mode'],
                    'instruction': row['instruction'],
                    'speaker_text': row['speaker_text'],
                    'timestamp': row['timestamp']
                })
            
            conn.close()
            mlog.debug(f"历史管理器 - 查询返回 {len(history)} 条记录")
            return history
        except Exception as e:
            mlog.error(f"分页获取历史记录失败: {str(e)}")
            return []
    
    def get_total_history(self):
        """
        获取历史记录总数
        
        Returns:
            int: 历史记录总数
        """
        return self.db_manager.get_table_count('history')
    
    def filter_history_paged(self, keyword, page=1, page_size=10):
        """
        按关键词分页筛选历史记录
        
        Args:
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页记录数
            
        Returns:
            list: 过滤后的当前页历史记录列表
        """
        try:
            mlog.debug(f"历史管理器 - 分页筛选历史: 关键词='{keyword}', 页码={page}, 每页={page_size}")
            if not keyword or keyword.strip() == "":
                return self.get_history_paged(page, page_size)
            
            keyword = f"%{keyword.lower().strip()}%"
            
            # 验证输入参数
            if page < 1:
                page = 1
                mlog.warning(f"页码必须大于0，已自动调整为1")
            
            if page_size < 1:
                page_size = 10
                mlog.warning(f"每页显示数量必须大于0，已自动调整为10")
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            offset = (page - 1) * page_size
            
            # SQL调试信息
            sql = """SELECT id, text, speaker, reference, file_path, speed, mode, instruction, speaker_text, timestamp
                   FROM history WHERE LOWER(text) LIKE ? OR LOWER(speaker) LIKE ? OR LOWER(reference) LIKE ?
                   ORDER BY timestamp DESC LIMIT ? OFFSET ?"""
            mlog.debug(f"执行SQL: {sql} [关键词: {keyword}, 每页: {page_size}, 偏移: {offset}]")
            
            cursor.execute(sql, (keyword, keyword, keyword, page_size, offset))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row['id'],
                    'text': row['text'],
                    'speaker': row['speaker'],
                    'reference': row['reference'],
                    'file_path': row['file_path'],
                    'speed': row['speed'],
                    'mode': row['mode'],
                    'instruction': row['instruction'],
                    'speaker_text': row['speaker_text'],
                    'timestamp': row['timestamp']
                })
            
            conn.close()
            mlog.debug(f"历史管理器 - 筛选查询返回 {len(history)} 条记录")
            return history
        except Exception as e:
            mlog.error(f"分页筛选历史记录失败: {str(e)}")
            return []

    def get_filtered_count(self, keyword):
        """
        获取过滤后的历史记录总数
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            int: 过滤后的历史记录总数
        """
        if not keyword or keyword.strip() == "":
            return self.get_total_history()
            
        keyword = f"%{keyword.lower().strip()}%"
        return self.db_manager.get_table_count(
            'history', 
            'LOWER(text) LIKE ? OR LOWER(speaker) LIKE ? OR LOWER(reference) LIKE ?', 
            (keyword, keyword, keyword)
        )

