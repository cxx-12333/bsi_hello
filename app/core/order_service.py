# -*- coding: utf-8 -*-
"""
订单服务实现
"""

import uuid
from typing import Dict, Any
from app.core.interfaces.order_service_interface import OrderServiceInterface


class OrderService(OrderServiceInterface):
    """订单服务实现"""
    
    def __init__(self, db_session_factory=None):
        # 在实际应用中，这里会注入数据库会话工厂
        # 为了简化示例，我们使用内存存储
        self.db_session_factory = db_session_factory
        self.orders = {}
    
    def create_order(self, user_id: str, product_name: str, quantity: int) -> Dict[str, Any]:
        """创建订单"""
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "user_id": user_id,
            "product_name": product_name,
            "quantity": quantity
        }
        self.orders[order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """获取订单"""
        return self.orders.get(order_id, {})