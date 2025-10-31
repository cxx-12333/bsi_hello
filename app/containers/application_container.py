# -*- coding: utf-8 -*-
"""
应用容器 - 管理应用层的依赖
"""

from dependency_injector import containers, providers
from app.containers.root_container import RootContainer
from app.containers.data_access_container import DataAccessContainer
from app.containers.service_container import ServiceContainer
from app.containers.api_container import ApiContainer
from app.containers.grpc_container import GrpcContainer
from app.internal.client.multi_service_grpc_client import MultiServiceGrpcClient
from app.internal.client.user_service_client import UserServiceClient
from app.internal.client.notification_service_client import NotificationServiceClient


class ClientContainer(containers.DeclarativeContainer):
    """客户端容器，管理gRPC客户端依赖"""
    multi_grpc_client = providers.Factory(MultiServiceGrpcClient)
    user_service_client = providers.Factory(UserServiceClient)
    notification_service_client = providers.Factory(NotificationServiceClient)


class ApplicationContainer(containers.DeclarativeContainer):
    """应用容器，管理应用层的依赖"""
    
    # 配置
    config = providers.Configuration()

    # 根容器
    root_container = providers.Container(
        RootContainer,
        config=config
    )
    
    # 数据访问容器
    data_access_container = providers.Container(
        DataAccessContainer,
        config=config
    )
    
    # 服务容器
    service_container = providers.Container(
        ServiceContainer,
        config=config,
        root_container=root_container,
        data_access_container=data_access_container
    )
    
    # API容器
    api_container = providers.Container(
        ApiContainer,
        config=config,
        service_container=service_container
    )
    
    # gRPC容器 - 使用providers.Factory确保正确类型和方法
    grpc_container = providers.Factory(GrpcContainer,
        config=config,
        root_container=root_container,
        data_access_container=data_access_container,
        service_container=service_container
    )
    
    # 客户端容器
    client_container = providers.Container(ClientContainer)