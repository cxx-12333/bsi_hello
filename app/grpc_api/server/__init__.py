# -*- coding: utf-8 -*-
"""
gRPC服务端实现模块
"""

from .user_service_grpc import UserServiceGrpc
from .order_service_grpc import OrderServiceGrpc
from .product_service_grpc import ProductServiceGrpc

__all__ = ['UserServiceGrpc', 'OrderServiceGrpc', 'ProductServiceGrpc']