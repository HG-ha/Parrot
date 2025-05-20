import sqlite3
import os
import app.core.mlog as mlog

class DBManager:
    """
    数据库管理类，负责SQLite数据库的连接和初始化
    """
    def __init__(self, pathmanager):
        """初始化数据库管理器"""
        self.path_manager = pathmanager
        self.db_file = self.path_manager.database_file
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """
        初始化数据库，创建必要的表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建角色表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                file TEXT NOT NULL,
                speaker_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建历史记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                speaker TEXT NOT NULL,
                reference TEXT NOT NULL,
                file_path TEXT NOT NULL,
                speed REAL DEFAULT 1.0,
                mode TEXT DEFAULT 'quick',
                instruction TEXT,
                speaker_text TEXT,
                timestamp TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            conn.close()
            mlog.info("数据库初始化成功")
        except Exception as e:
            mlog.error(f"数据库初始化失败: {str(e)}")
    
    def get_connection(self):
        """
        获取数据库连接
        
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        try:
            # 启用外键约束
            conn = sqlite3.connect(self.db_file)
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 使结果以字典形式返回
            conn.row_factory = sqlite3.Row
            
            return conn
        except Exception as e:
            mlog.error(f"获取数据库连接失败: {str(e)}")
            raise e

    def get_table_count(self, table_name, where_clause=None, params=()):
        """
        获取表中的记录总数
        
        Args:
            table_name: 表名
            where_clause: WHERE条件子句(可选)
            params: WHERE条件参数(可选)
            
        Returns:
            int: 记录总数
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = f"SELECT COUNT(*) FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except Exception as e:
            mlog.error(f"获取表记录数失败: {str(e)}")
            return 0

    def debug_query_params(self, query, params):
        """
        调试查询参数，记录到日志
        
        Args:
            query: SQL查询语句
            params: 查询参数
        """
        mlog.debug(f"执行SQL查询: {query}")
        mlog.debug(f"参数: {params}")
