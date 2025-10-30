#!/usr/bin/env python3
"""
用户服务gRPC客户端实现
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dependency_injector.wiring import Provide, inject

from app.internal.client.multi_service_grpc_client import MultiServiceGrpcClient
from app.grpc_api.generated import user_pb2, user_pb2_grpc

# 配置日志
logger = logging.getLogger(__name__)

class UserServiceClient:
    """用户服务gRPC客户端"""
    
    @inject
    def __init__(
        self,
        multi_client: MultiServiceGrpcClient = Provide["client_container.multi_grpc_client"]
    ):
        """
        初始化用户服务gRPC客户端
        
        Args:
            multi_client: 多服务gRPC客户端实例（通过依赖注入提供）
        """
        self.multi_client = multi_client
        self.stub = None
        self.service_name = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, service_name: str = None, use_discovery: bool = True) -> bool:
        """
        连接到用户服务
        
        Args:
            service_name: 服务名称，默认为"user.grpc"
            use_discovery: 是否使用服务发现，默认True
            
        Returns:
            bool: 连接是否成功
        """
        if service_name is None:
            # 默认使用"user.grpc"作为服务名
            service_name = "user.grpc"
        
        self.service_name = service_name
        self.stub = await self.multi_client.get_service_stub(
            service_name, user_pb2_grpc.UserServiceStub, use_discovery
        )
        
        return self.stub is not None
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户信息，用户不存在时返回None
        """
        if not self.stub:
            self.logger.error("gRPC客户端未连接")
            return None
            
        try:
            request = user_pb2.UserRequest(id=str(user_id))
            response = await self.stub.GetUser(request)
            return {
                "id": int(response.id),
                "name": response.name
            }
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None
    
    async def create_user(self, name: str) -> Optional[Dict[str, Any]]:
        """
        创建用户
        
        Args:
            name: 用户名
            
        Returns:
            Optional[Dict[str, Any]]: 创建的用户信息，创建失败时返回None
        """
        if not self.stub:
            self.logger.error("gRPC客户端未连接")
            return None
            
        try:
            request = user_pb2.CreateUserRequest(name=name)
            response = await self.stub.CreateUser(request)
            return {
                "id": int(response.id),
                "name": response.name
            }
        except Exception as e:
            self.logger.error(f"创建用户失败: {e}")
            return None
    
    async def close(self):
        """关闭用户服务连接"""
        if self.service_name:
            await self.multi_client.close_service(self.service_name)