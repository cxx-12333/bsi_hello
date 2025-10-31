# -*- coding: utf-8 -*-
"""
gRPC服务端实现
"""

import sys
import grpc
from typing import AsyncGenerator

from app.grpc_api.generated import user_pb2, user_pb2_grpc
from app.core.interfaces.user_service_interface import UserServiceInterface


class UserServiceGrpc(user_pb2_grpc.UserServiceServicer):
    """gRPC用户服务实现"""
    
    def __init__(self, user_service: UserServiceInterface):
        """
        初始化UserServiceGrpc
        
        Args:
            user_service: 用户服务实例（通过依赖注入提供）
        """
        self.user_service = user_service

    async def GetUser(self, request, context):
        """
        获取用户信息
        
        Args:
            request: 用户请求对象
            context: gRPC上下文
            
        Returns:
            UserReply: 用户信息响应
        """
        result = await self.user_service.get_user(int(request.id))
        if "error" in result:
            # 设置错误状态
            await context.abort(grpc.StatusCode.NOT_FOUND, result["error"])
            return user_pb2.UserReply()
        return user_pb2.UserReply(id=str(result["id"]), name=result["name"])

    async def CreateUser(self, request, context):
        """
        创建用户
        
        Args:
            request: 创建用户请求对象
            context: gRPC上下文
            
        Returns:
            UserReply: 用户信息响应
        """
        result = await self.user_service.create_user(request.name)
        if "error" in result:
            # 设置错误状态
            await context.abort(grpc.StatusCode.INTERNAL, result["error"])
            return user_pb2.UserReply()
        return user_pb2.UserReply(id=str(result["id"]), name=result["name"])
