# -*- coding: utf-8 -*-
"""
订单服务接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class OrderServiceInterface(ABC):
    """订单服务接口"""
    
    @abstractmethod
    def create_order(self, user_id: str, product_name: str, quantity: int) -> Dict[str, Any]:
        """创建订单"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """获取订单"""
        pass