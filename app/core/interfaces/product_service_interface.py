# -*- coding: utf-8 -*-
"""
产品服务接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ProductServiceInterface(ABC):
    """产品服务接口"""
    
    @abstractmethod
    def create_product(self, name: str, price: float) -> Dict[str, Any]:
        """创建产品"""
        pass
    
    @abstractmethod
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """获取产品"""
        pass