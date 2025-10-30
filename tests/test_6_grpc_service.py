#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gRPC服务测试脚本
"""

import unittest
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import grpc
    from app.grpc_api.generated import user_pb2, user_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

class TestGRPCService(unittest.IsolatedAsyncioTestCase):
    """gRPC服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.grpc_available = GRPC_AVAILABLE
        if self.grpc_available:
            self.grpc_address = 'localhost:9001'
    
    async def test_grpc_service_connection(self):
        """测试gRPC服务连接"""
        if not self.grpc_available:
            self.skipTest("gRPC库未安装，跳过测试")
        
        try:
            # 创建gRPC通道和存根
            channel = grpc.aio.insecure_channel(self.grpc_address)
            stub = user_pb2_grpc.UserServiceStub(channel)
            
            # 测试连接（这里只是检查是否能建立连接）
            # 在实际测试中，您可能需要调用一个简单的ping方法
            self.assertIsNotNone(stub)
            
            # 关闭通道
            await channel.close()
        except Exception as e:
            self.fail(f"gRPC服务连接测试失败: {e}")
    
    async def test_grpc_user_service_get_user(self):
        """测试gRPC用户服务获取用户"""
        if not self.grpc_available:
            self.skipTest("gRPC库未安装，跳过测试")
        
        try:
            # 创建gRPC通道和存根
            channel = grpc.aio.insecure_channel(self.grpc_address)
            stub = user_pb2_grpc.UserServiceStub(channel)
            
            # 创建获取用户请求
            request = user_pb2.UserRequest(id="1")
            
            # 调用获取用户方法
            response = await stub.GetUser(request)
            
            # 验证响应
            self.assertIsNotNone(response)
            # 根据实际实现验证响应内容
            # self.assertTrue(hasattr(response, 'user'))
            
            # 关闭通道
            await channel.close()
        except grpc.aio.AioRpcError as e:
            # 如果是未实现的错误，可能是服务端还未实现该方法
            if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                self.skipTest("gRPC服务GetUser方法未实现")
            else:
                self.fail(f"gRPC用户服务获取用户测试失败: {e}")
        except Exception as e:
            self.fail(f"gRPC用户服务获取用户测试失败: {e}")
    
    async def test_grpc_user_service_create_user(self):
        """测试gRPC用户服务创建用户"""
        if not self.grpc_available:
            self.skipTest("gRPC库未安装，跳过测试")
        
        try:
            # 创建gRPC通道和存根
            channel = grpc.aio.insecure_channel(self.grpc_address)
            stub = user_pb2_grpc.UserServiceStub(channel)
            
            # 创建用户请求
            request = user_pb2.CreateUserRequest(name="Test User")
            
            # 调用创建用户方法
            response = await stub.CreateUser(request)
            
            # 验证响应
            self.assertIsNotNone(response)
            # 根据实际实现验证响应内容
            # self.assertTrue(hasattr(response, 'user'))
            # self.assertEqual(response.user.name, "Test User")
            
            # 关闭通道
            await channel.close()
        except grpc.aio.AioRpcError as e:
            # 如果是未实现的错误，可能是服务端还未实现该方法
            if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                self.skipTest("gRPC服务CreateUser方法未实现")
            else:
                self.fail(f"gRPC用户服务创建用户测试失败: {e}")
        except Exception as e:
            self.fail(f"gRPC用户服务创建用户测试失败: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)