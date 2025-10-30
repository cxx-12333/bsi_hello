# -*- coding: utf-8 -*-
"""
数据访问容器 - 管理数据访问层的依赖
"""

from dependency_injector import containers, providers
from app.db.session import get_db_session_factory


class DataAccessContainer(containers.DeclarativeContainer):
    """数据访问容器，管理数据访问层的依赖"""
    
    # 配置
    config = providers.Configuration()
    
    # 数据库会话提供者
    db_session = providers.Factory(
        get_db_session_factory
    )