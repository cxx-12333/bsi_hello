# -*- coding: utf-8 -*-
"""
服务容器 - 管理服务层的依赖
"""

from dependency_injector import containers, providers
from app.core.user_service import UserService
from app.core.order_service import OrderService
from app.core.product_service import ProductService


class ServiceContainer(containers.DeclarativeContainer):
    """服务容器，管理服务层的依赖"""
    
    # 配置
    config = providers.Configuration()
    
    # 声明依赖的容器
    root_container = providers.DependenciesContainer()
    data_access_container = providers.DependenciesContainer()

    
    # UserService工厂
    user_service = providers.Factory(
        UserService,
        db_session_factory=data_access_container.db_session.provider
    )
    
    # OrderService工厂
    order_service = providers.Factory(
        OrderService,
        db_session_factory=data_access_container.db_session.provider
    )
    
    # ProductService工厂
    product_service = providers.Factory(
        ProductService,
        db_session_factory=data_access_container.db_session.provider
    )