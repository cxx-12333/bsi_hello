# -*- coding: utf-8 -*-
"""
gRPC服务端依赖注入容器
"""

import logging
from dependency_injector import containers, providers
from app.grpc_api.server import UserServiceGrpc, OrderServiceGrpc, ProductServiceGrpc
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
    
    # OrderServiceGrpc工厂
    order_service_grpc = providers.Factory(
        OrderServiceGrpc,
        order_service=service_container.order_service
    )
    
    # ProductServiceGrpc工厂
    product_service_grpc = providers.Factory(
        ProductServiceGrpc,
        product_service=service_container.product_service
    )
    
    # 服务发现支持 - 返回所有可用的gRPC服务工厂
    def get_all_grpc_services(self):
        """
        获取所有可用的gRPC服务实例
        用于自动服务发现
        """
        services = {}
        logger = logging.getLogger(__name__)
        
        # 定义服务映射
        service_mappings = {
            'user_service_grpc': 'user_service_grpc',
            'order_service_grpc': 'order_service_grpc',
            'product_service_grpc': 'product_service_grpc'
        }
        
        # 统一处理服务初始化
        for service_key, attr_name in service_mappings.items():
            if hasattr(self, attr_name):
                try:
                    services[service_key] = getattr(self, attr_name)()
                except Exception as e:
                    logger.warning(f"Failed to initialize {service_key}: {e}")
        
        return services
    
    # 注册方法以便在DynamicContainer中使用
    get_all_grpc_services = providers.Callable(get_all_grpc_services)