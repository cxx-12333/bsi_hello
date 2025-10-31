#!/usr/bin/env python3
"""
测试多服务gRPC客户端的脚本
"""

import unittest
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入公共初始化方法
from tests.common import init_config_from_consul

# 导入项目日志系统
from app.internal.log.logger import init_logger, logger

from app.containers.application_container import ApplicationContainer
from app.internal.client.user_service_client import UserServiceClient
from app.internal.client.notification_service_client import NotificationServiceClient
from app.internal.client.multi_service_grpc_client import MultiServiceGrpcClient

# 初始化日志系统
init_logger()


class TestMultiServiceGrpcClient(unittest.IsolatedAsyncioTestCase):
    """多服务gRPC客户端测试类"""

    def setUp(self):
        """测试前准备"""
        logger.info("=== 多服务gRPC客户端测试 ===")

    async def test_user_service(self):
        """测试用户服务"""
        logger.info("1. 测试用户服务客户端...")

        # 使用公共方法初始化Consul配置
        logger.info("   初始化Consul配置...")
        init_config_from_consul()

        # 手动创建多服务客户端和用户服务客户端
        logger.info("   创建应用容器和客户端...")
        container = ApplicationContainer()
        # 获取已初始化的bootstrap和registry实例
        bootstrap = container.root_container.bootstrap()
        registry = container.root_container.consul_registry()
        multi_client = MultiServiceGrpcClient(bootstrap, registry)
        user_client = UserServiceClient(multi_client)

        # 连接到用户服务
        logger.info("   连接到用户服务...")
        connected = await user_client.connect("bsi.hello_py.grpc")
        self.assertTrue(connected, "连接用户服务失败")
        logger.info("   连接用户服务成功")

        # 测试创建用户
        logger.info("   测试创建用户...")
        user = await user_client.create_user("Test User")
        self.assertIsNotNone(user, "创建用户失败")
        logger.info(f"   创建用户成功: ID={user['id']}, Name={user['name']}")
        user_id = user['id']

        # 测试获取用户
        logger.info("   测试获取用户...")
        user = await user_client.get_user(user_id)
        self.assertIsNotNone(user, "获取用户失败")
        logger.info(f"   获取用户成功: ID={user['id']}, Name={user['name']}")

        # 关闭用户服务连接
        logger.info("   关闭用户服务连接...")
        await user_client.close()
        logger.info("   用户服务连接已关闭")

    async def test_notification_service(self):
        """测试通知服务"""
        logger.info("\n2. 测试通知服务客户端...")

        # 使用公共方法初始化Consul配置
        logger.info("   初始化Consul配置...")
        init_config_from_consul()

        # 手动创建多服务客户端和通知服务客户端
        logger.info("   创建应用容器和客户端...")
        container = ApplicationContainer()
        # 获取已初始化的bootstrap和registry实例
        bootstrap = container.root_container.bootstrap()
        registry = container.root_container.consul_registry()
        multi_client = MultiServiceGrpcClient(bootstrap, registry)
        notification_client = NotificationServiceClient(multi_client)

        # 连接到通知服务
        logger.info("   连接到通知服务...")
        connected = await notification_client.connect("bsi.hello_py.grpc")
        self.assertTrue(connected, "连接通知服务失败")
        logger.info("   连接通知服务成功")

        # 测试获取通知列表
        logger.info("   测试获取通知列表...")
        # 注意：由于通知服务客户端尚未完全实现，我们只验证连接成功
        # 在实际项目中，这里应该测试真实的业务逻辑
        logger.info("   通知服务客户端连接成功（通知服务功能尚未完全实现）")

        # 关闭通知服务连接
        logger.info("   关闭通知服务连接...")
        await notification_client.close()
        logger.info("   通知服务连接已关闭")

if __name__ == "__main__":
    unittest.main(verbosity=2)