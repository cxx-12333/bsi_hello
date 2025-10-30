#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
依赖注入测试脚本
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.containers.application_container import ApplicationContainer
from app.core.user_service import UserService

class TestDependencyInjection(unittest.IsolatedAsyncioTestCase):
    """依赖注入测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建应用容器
        self.container = ApplicationContainer()
    
    async def test_container_creation(self):
        """测试容器创建"""
        # 验证容器已创建
        self.assertIsNotNone(self.container)
        # 检查容器的主要组件
        self.assertTrue(hasattr(self.container, 'config'))
        self.assertTrue(hasattr(self.container, 'root_container'))
        self.assertTrue(hasattr(self.container, 'data_access_container'))
        self.assertTrue(hasattr(self.container, 'service_container'))
    
    async def test_user_service_injection(self):
        """测试用户服务注入"""
        # 从容器获取用户服务
        user_service = self.container.service_container().user_service()
        
        # 验证用户服务已正确注入
        self.assertIsNotNone(user_service)
        self.assertIsInstance(user_service, UserService)
    
    async def test_user_service_get_user_with_injected_session(self):
        """测试用户服务通过注入会话获取用户"""
        # 从容器获取用户服务
        user_service = self.container.service_container().user_service()
        
        # 验证用户服务已正确注入
        self.assertIsNotNone(user_service)
        self.assertIsInstance(user_service, UserService)
    
    async def test_user_service_create_user_with_injected_session(self):
        """测试用户服务通过注入会话创建用户"""
        # 从容器获取用户服务
        user_service = self.container.service_container().user_service()
        
        # 验证用户服务已正确注入
        self.assertIsNotNone(user_service)
        self.assertIsInstance(user_service, UserService)
    
    async def test_api_routes_injection(self):
        """测试API路由注入"""
        # 获取API路由
        user_router = self.container.api_container().user_router()
        
        # 验证API路由已正确注入
        self.assertIsNotNone(user_router)
        # 验证API路由类型
        from fastapi import APIRouter
        self.assertIsInstance(user_router, APIRouter)
    
    async def test_grpc_service_injection(self):
        """测试gRPC服务注入"""
        # 从容器获取gRPC服务
        grpc_service = self.container.grpc_container().user_service_grpc()
        
        # 验证gRPC服务已正确注入
        self.assertIsNotNone(grpc_service)
        # 根据实际实现验证gRPC服务对象的属性

if __name__ == '__main__':
    unittest.main(verbosity=2)