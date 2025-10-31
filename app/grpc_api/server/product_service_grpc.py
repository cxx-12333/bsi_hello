# -*- coding: utf-8 -*-
"""
产品gRPC服务实现
"""

import grpc
from app.grpc_api.generated import product_pb2, product_pb2_grpc
from app.core.interfaces.product_service_interface import ProductServiceInterface


class ProductServiceGrpc(product_pb2_grpc.ProductServiceServicer):
    """gRPC产品服务实现"""
    
    def __init__(self, product_service: ProductServiceInterface):
        self.product_service = product_service
    
    def GetProduct(self, request, context):
        """获取产品的gRPC方法"""
        try:
            product_data = self.product_service.get_product(request.id)
            if not product_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Product {request.id} not found")
                raise
            
            return product_pb2.ProductReply(
                id=product_data["id"],
                name=product_data["name"],
                price=product_data["price"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get product: {str(e)}")
            raise
    
    def CreateProduct(self, request, context):
        """创建产品的gRPC方法"""
        try:
            product_data = self.product_service.create_product(
                request.name,
                request.price
            )
            return product_pb2.ProductReply(
                id=product_data["id"],
                name=product_data["name"],
                price=product_data["price"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create product: {str(e)}")
            raise