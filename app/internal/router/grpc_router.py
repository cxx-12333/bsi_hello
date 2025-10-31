#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from grpc_reflection.v1alpha import reflection
from grpc_health.v1 import health_pb2

# 导入服务管理器
from app.internal.server.service_manager import get_registered_service_names, clear_registered_service_names, get_collected_add_function

logger = logging.getLogger(__name__)

def setup_grpc_services(server, user_service_grpc=None, health_servicer=None):
    """设置gRPC服务（兼容旧版本）"""
    try:
        # 清空之前的服务名称列表
        clear_registered_service_names()
        
        # 注册服务（使用装饰器包装的函数，会自动收集服务名称）
        from app.grpc_api.generated import user_pb2_grpc
        from grpc_health.v1 import health_pb2_grpc
        
        if user_service_grpc:
            get_collected_add_function(user_pb2_grpc.add_UserServiceServicer_to_server)(user_service_grpc, server)
        if health_servicer:
            get_collected_add_function(health_pb2_grpc.add_HealthServicer_to_server)(health_servicer, server)
        
        # 获取自动收集的服务名称
        registered_names = get_registered_service_names()
        
        # 启用反射
        SERVICE_NAMES = tuple(
            registered_names + 
            [health_pb2.DESCRIPTOR.services_by_name['Health'].full_name, reflection.SERVICE_NAME]
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)
        
        logger.info(f"Registered services for reflection: {SERVICE_NAMES}")
        
    except Exception as e:
        logger.error(f"Failed to setup gRPC services: {e}")
        raise

def setup_grpc_services_with_mapping(server, service_mapping: dict):
    """使用服务映射字典设置gRPC服务"""
    try:
        # 清空之前的服务名称列表
        clear_registered_service_names()
        
        # 动态导入gRPC服务模块
        from app.grpc_api.generated import user_pb2_grpc, order_pb2_grpc, product_pb2_grpc
        from grpc_health.v1 import health_pb2_grpc
        
        # 服务处理器映射
        service_handlers = {
            'user_service_grpc': {
                'adder': user_pb2_grpc.add_UserServiceServicer_to_server,
                'instance': service_mapping.get('user_service_grpc')
            },
            'order_service_grpc': {
                'adder': order_pb2_grpc.add_OrderServiceServicer_to_server,
                'instance': service_mapping.get('order_service_grpc')
            },
            'product_service_grpc': {
                'adder': product_pb2_grpc.add_ProductServiceServicer_to_server,
                'instance': service_mapping.get('product_service_grpc')
            },
            'health_servicer': {
                'adder': health_pb2_grpc.add_HealthServicer_to_server,
                'instance': service_mapping.get('health_servicer')
            }
        }
        
        # 遍历所有服务并注册
        for service_key, service_info in service_handlers.items():
            service_instance = service_info['instance']
            service_adder = service_info['adder']
            
            # 只注册存在的服务实例
            if service_instance:
                try:
                    get_collected_add_function(service_adder)(service_instance, server)
                    logger.debug(f"Registered service: {service_key}")
                except Exception as e:
                    logger.error(f"Failed to register service {service_key}: {e}")
        
        # 获取已注册的服务名称列表
        service_names = get_registered_service_names()
        
        # 启用反射功能
        reflection.enable_server_reflection(service_names, server)
        
        logger.info(f"All gRPC services registered: {service_names}")
        
    except Exception as e:
        logger.error(f"Failed to setup gRPC services with mapping: {e}")
        raise

def setup_grpc_services_auto_discovery(server, app_container):
    """自动发现并注册gRPC服务"""
    try:
        # 清空之前的服务名称列表
        clear_registered_service_names()
        
        # 直接创建GrpcContainer实例并获取所有服务
        from app.containers.grpc_container import GrpcContainer
        grpc_container = GrpcContainer(
            config=app_container.config,
            root_container=app_container.root_container,
            data_access_container=app_container.data_access_container,
            service_container=app_container.service_container
        )
        service_mapping = grpc_container.get_all_grpc_services(grpc_container)
        
        # 特殊处理健康检查服务
        try:
            from grpc_health.v1.health import HealthServicer
            service_mapping['health_servicer'] = HealthServicer()
            logger.debug("Health servicer created successfully")
        except Exception as e:
            logger.warning(f"Failed to create health servicer: {e}")
        
        # 使用服务映射注册所有发现的服务
        setup_grpc_services_with_mapping(server, service_mapping)
        
        # 记录发现的服务
        discovered_services = list(service_mapping.keys())
        logger.info(f"Auto-discovered gRPC services: {discovered_services}")
        
    except Exception as e:
        logger.error(f"Failed to auto-discover gRPC services: {e}")
        raise