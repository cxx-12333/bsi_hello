# -*- coding: utf-8 -*-
"""
产品服务实现
"""

import uuid
from typing import Dict, Any
from app.core.interfaces.product_service_interface import ProductServiceInterface


class ProductService(ProductServiceInterface):
    """产品服务实现"""
    
    def __init__(self, db_session_factory=None):
        # 在实际应用中，这里会注入数据库会话工厂
        # 为了简化示例，我们使用内存存储
        self.db_session_factory = db_session_factory
        self.products = {}
    
    def create_product(self, name: str, price: float) -> Dict[str, Any]:
        """创建产品"""
        product_id = str(uuid.uuid4())
        product = {
            "id": product_id,
            "name": name,
            "price": price
        }
        self.products[product_id] = product
        return product
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """获取产品"""
        return self.products.get(product_id, {})