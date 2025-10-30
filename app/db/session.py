from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..internal.config.bootstrap import Bootstrap
from ..internal.log.logger import logger

# -------------------- 数据库配置 --------------------
# 使用全局配置对象
bootstrap = Bootstrap.get_instance()

# -------------------- 异步引擎 --------------------
# 延迟初始化引擎，确保配置已加载
_engine = None

def get_engine():
    """获取数据库引擎，如果尚未创建则创建它"""
    global _engine
    if _engine is None:
        DATABASE_URL = bootstrap.get_database_url()
        _engine = create_async_engine(DATABASE_URL, echo=True)
        logger.info(f"数据库引擎已初始化，URL: {DATABASE_URL}")
    return _engine

# -------------------- 异步 Session --------------------
def get_async_session_local():
    """获取异步会话工厂"""
    return sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False
    )

# -------------------- 简单工具函数 --------------------
async def get_db_session():
    """获取数据库会话"""
    async with get_async_session_local()() as session:
        yield session

# 提供一个可以直接用于依赖注入的函数
def get_db_session_factory():
    """获取数据库会话工厂"""
    return get_async_session_local()()
