import os
import json
import app.core.mlog as mlog

class RoleManager:
    """
    角色管理类，负责角色数据的读取和保存
    """
    def __init__(self, pathmanager,dbmanager):
        """初始化角色管理器"""
        self.path_manager = pathmanager
        self.db_manager = dbmanager
        self.roles_file = self.path_manager.roles_file
        self._migrate_from_json_if_needed()
        self._ensure_speaker_text_column()
    
    def _migrate_from_json_if_needed(self):
        """
        如果存在旧的JSON文件，则迁移数据到SQLite
        """
        if os.path.exists(self.roles_file):
            try:
                with open(self.roles_file, 'r') as f:
                    roles = json.load(f)
                
                if roles:
                    conn = self.db_manager.get_connection()
                    cursor = conn.cursor()
                    
                    # 检查数据库中是否已有角色数据
                    cursor.execute("SELECT COUNT(*) FROM roles")
                    count = cursor.fetchone()[0]
                    
                    # 如果数据库是空的，才进行迁移
                    if count == 0:
                        for role in roles:
                            cursor.execute(
                                "INSERT INTO roles (name, description, file) VALUES (?, ?, ?)",
                                (role.get('name', ''), role.get('description', ''), role.get('file', ''))
                            )
                        
                        conn.commit()
                        mlog.info(f"成功从JSON迁移{len(roles)}个角色到数据库")
                        
                        # 备份旧文件
                        backup_file = self.roles_file + ".bak"
                        os.rename(self.roles_file, backup_file)
                        mlog.info(f"旧的JSON文件已备份为: {backup_file}")
                    
                    conn.close()
            except Exception as e:
                mlog.error(f"从JSON迁移角色数据失败: {str(e)}")
    
    def _ensure_speaker_text_column(self):
        """
        确保数据库表中有speaker_text字段
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 检查是否存在speaker_text列
            cursor.execute("PRAGMA table_info(roles)")
            columns = [col["name"] for col in cursor.fetchall()]
            
            # 如果不存在，则添加
            if "speaker_text" not in columns:
                cursor.execute("ALTER TABLE roles ADD COLUMN speaker_text TEXT")
                conn.commit()
                mlog.info("已添加speaker_text列到roles表")
                
            conn.close()
        except Exception as e:
            mlog.error(f"确保speaker_text列存在失败: {str(e)}")
    
    def add_role(self, role):
        """
        添加角色
        
        Args:
            role: 角色数据字典
        
        Returns:
            bool: 添加是否成功
        """
        try:
            # 验证必要字段
            if not role.get('name') or not role.get('file'):
                mlog.error("添加角色失败: 名称和文件路径为必填项")
                return False
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO roles (name, description, file, speaker_text) VALUES (?, ?, ?, ?)",
                (role.get('name', ''), role.get('description', ''), 
                 role.get('file', ''), role.get('speaker_text', ''))
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            mlog.error(f"添加角色失败: {str(e)}")
            return False
    
    def update_role(self, index_or_role, new_data=None):
        """
        更新角色数据
        
        Args:
            index_or_role: 角色索引或角色对象
            new_data: 新的角色数据（如果提供索引）
        
        Returns:
            bool: 更新是否成功
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if isinstance(index_or_role, int):
                # 通过索引更新
                if new_data:
                    cursor.execute(
                        "UPDATE roles SET name=?, description=?, file=?, speaker_text=? WHERE id=?",
                        (new_data.get('name', ''), new_data.get('description', ''), 
                         new_data.get('file', ''), new_data.get('speaker_text', ''), index_or_role)
                    )
            else:
                # 直接通过角色对象更新
                role_id = index_or_role.get('id')
                if role_id:
                    cursor.execute(
                        "UPDATE roles SET name=?, description=?, file=?, speaker_text=? WHERE id=?",
                        (index_or_role.get('name', ''), index_or_role.get('description', ''), 
                         index_or_role.get('file', ''), index_or_role.get('speaker_text', ''), role_id)
                    )
                else:
                    # 如果没有ID，尝试通过名称匹配
                    cursor.execute(
                        "UPDATE roles SET description=?, file=?, speaker_text=? WHERE name=?",
                        (index_or_role.get('description', ''), index_or_role.get('file', ''),
                         index_or_role.get('speaker_text', ''), index_or_role.get('name', ''))
                    )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            mlog.error(f"更新角色失败: {str(e)}")
            return False
    
    def delete_role(self, index_or_role):
        """
        删除角色
        
        Args:
            index_or_role: 角色索引或角色对象
        
        Returns:
            bool: 删除是否成功
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if isinstance(index_or_role, int):
                # 通过ID删除
                cursor.execute("DELETE FROM roles WHERE id=?", (index_or_role,))
            else:
                # 通过角色对象删除
                role_id = index_or_role.get('id')
                if role_id:
                    cursor.execute("DELETE FROM roles WHERE id=?", (role_id,))
                else:
                    # 如果没有ID，尝试通过名称匹配
                    cursor.execute("DELETE FROM roles WHERE name=?", (index_or_role.get('name', ''),))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            mlog.error(f"删除角色失败: {str(e)}")
            return False
    
    def get_roles(self):
        """
        获取所有角色
        
        Returns:
            list: 角色列表
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, description, file, speaker_text FROM roles ORDER BY name")
            
            roles = []
            for row in cursor.fetchall():
                roles.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'file': row['file'],
                    'speaker_text': row['speaker_text'] if 'speaker_text' in row.keys() else ''
                })
            
            conn.close()
            return roles
        except Exception as e:
            mlog.error(f"获取角色列表失败: {str(e)}")
            return []
    
    def get_role_by_name(self, name):
        """
        通过名称获取角色
        
        Args:
            name: 角色名称
        
        Returns:
            dict: 角色数据字典，如果找不到则返回None
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, description, file, speaker_text FROM roles WHERE name=?", (name,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'file': row['file'],
                    'speaker_text': row['speaker_text'] if 'speaker_text' in row.keys() else ''
                }
            return None
        except Exception as e:
            mlog.error(f"通过名称获取角色失败: {str(e)}")
            return None
    
    def filter_roles(self, keyword):
        """
        按关键词筛选角色
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            list: 过滤后的角色列表
        """
        try:
            if not keyword or keyword.strip() == "":
                return self.get_roles()
            
            keyword = f"%{keyword.lower().strip()}%"
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, name, description, file, speaker_text FROM roles "
                "WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? "
                "ORDER BY name",
                (keyword, keyword)
            )
            
            roles = []
            for row in cursor.fetchall():
                roles.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'file': row['file'],
                    'speaker_text': row['speaker_text'] if 'speaker_text' in row.keys() else ''
                })
            
            conn.close()
            return roles
        except Exception as e:
            mlog.error(f"筛选角色失败: {str(e)}")
            return []
    
    def get_roles_paged(self, page=1, page_size=10):
        """
        分页获取角色列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页记录数
            
        Returns:
            list: 当前页的角色列表
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            offset = (page - 1) * page_size
            
            # 添加日志
            mlog.debug(f"分页获取角色: 页码={page}, 每页={page_size}, 偏移={offset}")
            
            cursor.execute(
                "SELECT id, name, description, file, speaker_text FROM roles ORDER BY name LIMIT ? OFFSET ?",
                (page_size, offset)
            )
            
            roles = []
            for row in cursor.fetchall():
                roles.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'file': row['file'],
                    'speaker_text': row['speaker_text'] if 'speaker_text' in row.keys() else ''
                })
            
            conn.close()
            mlog.debug(f"获取到 {len(roles)} 条角色记录")
            return roles
        except Exception as e:
            mlog.error(f"分页获取角色列表失败: {str(e)}")
            return []
    
    def get_total_roles(self):
        """
        获取角色总数
        
        Returns:
            int: 角色总数
        """
        return self.db_manager.get_table_count('roles')
    
    def filter_roles_paged(self, keyword, page=1, page_size=10):
        """
        按关键词分页筛选角色
        
        Args:
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页记录数
            
        Returns:
            list: 过滤后的当前页角色列表
        """
        try:
            if not keyword or keyword.strip() == "":
                return self.get_roles_paged(page, page_size)
            
            keyword = f"%{keyword.lower().strip()}%"
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            offset = (page - 1) * page_size
            
            cursor.execute(
                "SELECT id, name, description, file, speaker_text FROM roles "
                "WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? "
                "ORDER BY name LIMIT ? OFFSET ?",
                (keyword, keyword, page_size, offset)
            )
            
            roles = []
            for row in cursor.fetchall():
                roles.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'file': row['file'],
                    'speaker_text': row['speaker_text'] if 'speaker_text' in row.keys() else ''
                })
            
            conn.close()
            return roles
        except Exception as e:
            mlog.error(f"分页筛选角色失败: {str(e)}")
            return []
    
    def get_filtered_count(self, keyword):
        """
        获取过滤后的角色总数
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            int: 过滤后的角色总数
        """
        if not keyword or keyword.strip() == "":
            return self.get_total_roles()
            
        keyword = f"%{keyword.lower().strip()}%"
        return self.db_manager.get_table_count(
            'roles', 
            'LOWER(name) LIKE ? OR LOWER(description) LIKE ?', 
            (keyword, keyword)
        )
