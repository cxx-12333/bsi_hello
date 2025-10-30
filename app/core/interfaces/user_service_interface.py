# -*- coding: utf-8 -*-
"""
UserService接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class UserServiceInterface(ABC):
    """UserService接口定义"""
    
    @abstractmethod
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """根据ID获取用户信息"""
        pass
    
    @abstractmethod
    async def create_user(self, name: str) -> Dict[str, Any]:
        """创建新用户"""
        pass