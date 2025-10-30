# -*- coding: utf-8 -*-
"""
API依赖注入容器
"""

from dependency_injector import containers, providers
from app.containers.service_container import ServiceContainer
from app.api.router_user import create_router


class ApiContainer(containers.DeclarativeContainer):
    """API依赖注入容器"""
    
    # 配置
    config = providers.Configuration()
    
    # 声明依赖的容器
    service_container = providers.Container(ServiceContainer)
    
    # 用户路由工厂
    user_router = providers.Factory(
        create_router,
        user_service=service_container.user_service
    )