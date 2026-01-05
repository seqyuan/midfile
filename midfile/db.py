"""数据库操作模块"""
import sqlite3
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class db_sql:
    """数据库操作类"""
    
    # 允许更新的列名白名单
    ALLOWED_UPDATE_COLUMNS = {'pmid', 'product', 'sample', 'ftype', 'fileformat', 'cloudpath', 'downpath'}
    
    # 允许查询的列名白名单
    ALLOWED_QUERY_COLUMNS = {'pmid', 'product', 'sample', 'ftype', 'fileformat', 'filepath', 'cloudpath', 'downpath'}
    
    def __init__(self, dbpath):
        self.dbpath = dbpath
        self.conn = None
        self.cur = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.conn = sqlite3.connect(self.dbpath)
        self.cur = self.conn.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        return False

    def _check_column_exists(self, table_name, column_name):
        """检查表中是否存在指定列"""
        try:
            self.cur.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.cur.fetchall()]
            return column_name in columns
        except sqlite3.Error as e:
            logger.error(f'检查列是否存在失败: {e}')
            return False
    
    def _upgrade_database(self):
        """升级数据库结构，添加新列"""
        try:
            # 检查并添加 product 列
            if not self._check_column_exists('files', 'product'):
                self.cur.execute("ALTER TABLE files ADD COLUMN product TEXT")
                logger.info('已添加 product 列')
            
            # 检查 pmid 列是否存在空值，如果有则警告
            self.cur.execute("SELECT COUNT(*) FROM files WHERE pmid IS NULL OR pmid = ''")
            null_count = self.cur.fetchone()[0]
            if null_count > 0:
                logger.warning(f'发现 {null_count} 条记录的 pmid 为空，请手动更新')
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f'升级数据库失败: {e}')
            self.conn.rollback()
            raise

    def crt_tb_sql(self):
        """创建数据库表
        files表:
        - pmid: subproject id, 不能为空
        - product: 产品或分析流程类型
        - sample: sample name, 如果是过滤的数据, 比如raw/clean data, 这个名字就是过滤的样本名称, 如果是分析报告里的中间数据则应该是信息搜集表中填写的结题报告中的样本名称, 或用all 等标示整合rds的关键字, 需要每个产品流程单独设定命名规则
        - ftype: file type, 可以配合fileformat使用对文件做区分, 例如 raw/clean; 也可以配合sample使用对文件做区分, 例如merge/integrate, 需要每个产品流程单独设定命名规则
        - fileformat: rds, fastq, gef, count, barcode, genes等
        - filepath: 最好和cloudpath一样精确到文件, 而不是目录; 如果是fastq, 可以写两行:R1和R2各一行, unique not null
        - cloudpath: 统一存储在middlefile bucket
        
        ref表:
        - pmid: subproject id
        - alignref: 分析时信息搜集表中填写的比对参考基因组版本
        - annoref: 分析时信息搜集表中填写的注释参考基因组版本
        """
        crt_tb_sql_c = """
        CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        pmid TEXT NOT NULL,
        product TEXT,
        sample TEXT,
        ftype TEXT,
        fileformat TEXT,
        filepath UNIQUE NOT NULL,
        cloudpath TEXT,
        downpath TEXT
        );"""

        crt_tb_sql_ref = """
        CREATE TABLE IF NOT EXISTS ref(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        pmid TEXT,
        alignref TEXT,
        annoref TEXT
        );"""
        
        try:
            self.cur.execute(crt_tb_sql_c)
            self.cur.execute(crt_tb_sql_ref)
            # 升级现有数据库（如果表已存在，添加新列）
            self._upgrade_database()
            self.conn.commit()
            logger.info('数据库表创建/升级成功')
        except sqlite3.Error as e:
            logger.error(f'创建数据库表失败: {e}')
            self.conn.rollback()
            raise

    def insert_tb_sql(self, pmid, product, sample, ftype, fileformat, filepath):
        """插入文件记录"""
        # 验证 pmid 不能为空
        if not pmid or pmid.strip() == '':
            raise ValueError('pmid 不能为空')
        
        insert_sql = "INSERT INTO files (pmid, product, sample, ftype, fileformat, filepath) VALUES (?,?,?,?,?,?)"
        try:
            self.cur.execute(insert_sql, (pmid, product, sample, ftype, fileformat, filepath))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            logger.warning(f'文件已存在: {filepath}')
            raise
        except sqlite3.Error as e:
            logger.error(f'插入记录失败: {e}')
            self.conn.rollback()
            raise

    def insert_tb_sql_ref(self, pmid, alignref, annoref):
        """插入参考基因组版本记录"""
        insert_sql = "INSERT INTO ref (pmid, alignref, annoref) VALUES (?,?,?)"
        try:
            self.cur.execute(insert_sql, (pmid, alignref, annoref))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f'插入参考基因组记录失败: {e}')
            self.conn.rollback()
            raise

    def update_tb_value_sql(self, filepath, name, value):
        """更新文件记录
        注意: name 必须是允许的列名之一，防止SQL注入
        """
        if name not in self.ALLOWED_UPDATE_COLUMNS:
            raise ValueError(f'不允许更新列: {name}，允许的列: {self.ALLOWED_UPDATE_COLUMNS}')
        
        update_sql = f"UPDATE files SET {name} = ? WHERE filepath = ?"
        try:
            self.cur.execute(update_sql, (value, filepath))
            if self.cur.rowcount == 0:
                logger.warning(f'未找到要更新的文件: {filepath}')
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f'更新记录失败: {e}')
            self.conn.rollback()
            raise

    def check_file_sql(self, filepath):
        """检查文件是否存在"""
        query_sql = "SELECT * FROM files WHERE filepath = ?"
        try:
            filesdf = pd.read_sql(query_sql, con=self.conn, params=(filepath,))
            return filesdf
        except Exception as e:
            logger.error(f'查询文件失败: {e}')
            raise
    
    def query_recored(self, conditions):
        """根据条件查询记录
        conditions: dict, 例如 {'pmid': 'xxx', 'sample': 'yyy'}
        """
        if not conditions:
            raise ValueError('查询条件不能为空')
        
        where_clauses = []
        params = []
        for key, value in conditions.items():
            if key not in self.ALLOWED_QUERY_COLUMNS:
                raise ValueError(f'不允许查询的列: {key}，允许的列: {self.ALLOWED_QUERY_COLUMNS}')
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        query_sql = f"SELECT * FROM files WHERE {' AND '.join(where_clauses)}"
        try:
            filesdf = pd.read_sql(query_sql, con=self.conn, params=params)
            return filesdf
        except Exception as e:
            logger.error(f'查询记录失败: {e}')
            raise

    def get_unique_values(self):
        """获取 product, ftype, fileformat 的唯一组合"""
        try:
            # 获取 product, ftype, fileformat 的唯一组合
            sql = """
            SELECT DISTINCT product, ftype, fileformat 
            FROM files 
            ORDER BY product, ftype, fileformat
            """
            df = pd.read_sql(sql, con=self.conn)
            return df
        except Exception as e:
            logger.error(f'获取唯一值失败: {e}')
            raise

