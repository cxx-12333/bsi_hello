# -*- coding: utf-8 -*-
"""
gRPC服务端依赖注入容器
"""

from dependency_injector import containers, providers
from app.grpc_api.server import UserServiceGrpc
from app.containers.data_access_container import DataAccessContainer
from app.containers.root_container import RootContainer
from app.containers.service_container import ServiceContainer


class GrpcContainer(containers.DeclarativeContainer):
    """gRPC服务端依赖注入容器"""
    
    # 配置
    config = providers.Configuration()
    
    # 声明依赖的容器
    root_container = providers.Container(RootContainer)
    data_access_container = providers.Container(DataAccessContainer)
    service_container = providers.Container(ServiceContainer)
    
    # UserServiceGrpc工厂
    user_service_grpc = providers.Factory(
        UserServiceGrpc,
        user_service=service_container.user_service
    )