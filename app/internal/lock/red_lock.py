import asyncio
import redis.asyncio as redis
from ..log.logger import logger
from ..config.bootstrap import Bootstrap

# -------------------- Redis配置 --------------------
# 使用全局配置对象
bootstrap = Bootstrap.get_instance()

# 全局Redis客户端和锁管理器
redis_client = None
lock_manager = None

def get_redis_config():
    """获取Redis配置"""
    return bootstrap.get_redis_config_dict()

async def init_redis_client():
    """初始化Redis客户端"""
    global redis_client, lock_manager
    try:
        # 使用全局配置对象获取Redis配置
        redis_config = get_redis_config()
        
        # 构建Redis连接URL，如果提供了密码则包含在URL中
        if redis_config.get('password'):
            redis_url = f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        else:
            redis_url = f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        
        redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        # 初始化锁管理器
        lock_manager = redis.Redis(  
            host=redis_config['host'],
            port=redis_config['port'],
            db=redis_config['db'],
            password=redis_config.get('password'),  # 添加密码参数
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis client initialized successfully")
        logger.info(f"Redis配置: host={redis_config['host']}, port={redis_config['port']}, db={redis_config['db']}")
        # 如果设置了密码，记录密码已设置（但不显示具体值）
        if redis_config.get('password'):
            logger.info("Redis密码认证已启用")
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}")
        raise

def get_redis_client():
    """获取Redis客户端"""
    global redis_client
    if redis_client is None:
        raise RuntimeError("Redis客户端尚未初始化，请先调用init_redis_client()")
    return redis_client

def get_lock_manager():
    """获取锁管理器"""
    global lock_manager
    if lock_manager is None:
        raise RuntimeError("Redis锁管理器尚未初始化，请先调用init_redis_client()")
    return lock_manager
