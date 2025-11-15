# persist-1<persist1@126.com>
# 原因：将 db.py 改造为模块，移除直接执行入口，修复相对导入问题。
# 副作用：无
# 回滚策略：还原此文件。
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from tools import utils
from database.db_session import create_tables

async def init_table_schema(db_type: str):
    """
    Initializes the database table schema. 
    This will create tables based on the ORM models.
    Args:
        db_type: The type of database, 'sqlite' or 'mysql'.
    """
    utils.logger.info(f"[init_table_schema] begin init {db_type} table schema ...")
    await create_tables(db_type)
    utils.logger.info(f"[init_table_schema] {db_type} table schema init successful")

async def init_db(db_type: str = None):
    await init_table_schema(db_type)

async def close():
    """
    Placeholder for closing database connections if needed in the future.
    """
    pass
# In db.py
def get_db_engine():
    """
    创建并返回一个同步数据库引擎，用于Streamlit dashboard等需要同步访问的场景
    支持SQLite和MySQL数据库
    """
    from sqlalchemy import create_engine
    import config
    from config.db_config import mysql_db_config, sqlite_db_config
    
    # 根据配置决定使用哪种数据库
    db_type = config.SAVE_DATA_OPTION
    
    if db_type == "sqlite":
        # SQLite使用同步引擎
        db_url = f"sqlite:///{sqlite_db_config['db_path']}"
        engine = create_engine(db_url, echo=False)
        return engine
    elif db_type in ["mysql", "db"]:
        # MySQL使用pymysql驱动（同步）
        try:
            import pymysql
        except ImportError:
            raise ImportError(
                "使用MySQL数据库需要安装pymysql，请运行: pip install pymysql"
            )
        db_url = f"mysql+pymysql://{mysql_db_config['user']}:{mysql_db_config['password']}@{mysql_db_config['host']}:{mysql_db_config['port']}/{mysql_db_config['db_name']}"
        engine = create_engine(db_url, echo=False)
        return engine
    else:
        raise ValueError(f"Unsupported database type for sync engine: {db_type}. Please use 'sqlite' or 'db'/'mysql'")
