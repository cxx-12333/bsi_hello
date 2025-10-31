# -*- coding: utf-8 -*-
"""
订单gRPC服务实现
"""

import grpc
from app.grpc_api.generated import order_pb2, order_pb2_grpc
from app.core.interfaces.order_service_interface import OrderServiceInterface


class OrderServiceGrpc(order_pb2_grpc.OrderServiceServicer):
    """gRPC订单服务实现"""
    
    def __init__(self, order_service: OrderServiceInterface):
        self.order_service = order_service
    
    def GetOrder(self, request, context):
        """获取订单的gRPC方法"""
        try:
            order_data = self.order_service.get_order(request.id)
            if not order_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Order {request.id} not found")
                raise
            
            return order_pb2.OrderReply(
                id=order_data["id"],
                user_id=order_data["user_id"],
                product_name=order_data["product_name"],
                quantity=order_data["quantity"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get order: {str(e)}")
            raise
    
    def CreateOrder(self, request, context):
        """创建订单的gRPC方法"""
        try:
            order_data = self.order_service.create_order(
                request.user_id,
                request.product_name,
                request.quantity
            )
            return order_pb2.OrderReply(
                id=order_data["id"],
                user_id=order_data["user_id"],
                product_name=order_data["product_name"],
                quantity=order_data["quantity"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create order: {str(e)}")
            raise