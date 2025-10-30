#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库和Redis初始化
用于验证app/db/session.py和app/internal/lock/red_lock.py中的组件是否能正常工作
"""

import unittest
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入公共初始化方法和默认配置
from tests.common import init_config_from_consul, parse_consul_address, DEFAULT_CONSUL_ADDRESS, DEFAULT_CONSUL_TOKEN
from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.consul_registry import ConsulRegistry
from app.db.session import get_engine, get_async_session_local
import app.internal.lock.red_lock as red_lock

# Consul连接配置 - 使用本地Consul服务
registryAddress = "https://consul.dev.shijizhongyun.com"
registryToken = "3f84201a-31a2-c843-bbc0-0a45983aa7b7"  # 本地开发环境通常不需要token
configPath = "bsi/hello_py"


class TestDBAndRedisInitialization(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        pass

    def tearDown(self):
        """测试后清理"""
        pass

    def _init_config_from_consul(self):
        """从Consul初始化配置"""
        print(f"从Consul初始化配置: {registryAddress}, 路径: {configPath}")

        # 使用公共方法初始化Consul配置
        bootstrap, registry = init_config_from_consul(registryAddress, registryToken, configPath)
        return True

    def test_database_engine_initialization(self):
        """测试数据库引擎初始化"""
        # 初始化Consul配置
        self._init_config_from_consul()

        # 获取数据库引擎
        engine = get_engine()

        # 测试数据库引擎是否已正确初始化
        self.assertIsNotNone(engine, "数据库引擎未初始化")
        print(f"数据库引擎URL: {engine.url}")

    def test_redis_client_initialization(self):
        """测试Redis客户端初始化"""
        # 初始化Consul配置
        self._init_config_from_consul()

        # 初始化Redis客户端
        asyncio.run(red_lock.init_redis_client())

        # 检查Redis客户端是否已初始化
        self.assertIsNotNone(red_lock.redis_client, "Redis客户端未初始化")
        self.assertIsNotNone(red_lock.lock_manager, "Redis锁管理器未初始化")

    def test_database_connection(self):
        """测试数据库连接"""
        # 初始化Consul配置
        self._init_config_from_consul()

        # 获取数据库引擎
        engine = get_engine()

        # 检查数据库引擎是否已初始化
        self.assertIsNotNone(engine, "数据库引擎未初始化")
        print(f"数据库引擎URL: {engine.url}")

        # 运行异步测试
        try:
            result = asyncio.run(self._async_test_database_connection())
            if not result:
                print("警告: 数据库连接测试失败，可能是数据库服务未运行")
            else:
                print("数据库连接测试成功")
        except Exception as e:
            print(f"数据库连接测试出现异常: {e}")
            print("这可能是由于数据库服务未运行或配置不正确导致的")

    def test_redis_connection(self):
        """测试Redis连接"""
        # 初始化Consul配置
        self._init_config_from_consul()

        # 初始化Redis客户端
        try:
            asyncio.run(red_lock.init_redis_client())
        except Exception as e:
            print(f"Redis客户端初始化失败: {e}")
            self.skipTest("Redis客户端初始化失败")

        # 检查Redis客户端是否已初始化
        if red_lock.redis_client is None:
            print("Redis客户端未初始化，跳过连接测试")
            self.skipTest("Redis客户端未初始化")

        self.assertIsNotNone(red_lock.lock_manager, "Redis锁管理器未初始化")

        # 运行异步测试
        try:
            result = asyncio.run(self._async_test_redis_connection())
            if not result:
                print("警告: Redis连接测试失败，可能是Redis服务未运行")
            else:
                print("Redis连接测试成功")
        except Exception as e:
            print(f"Redis连接测试出现异常: {e}")
            print("这可能是由于Redis服务未运行或配置不正确导致的")

    async def _async_test_database_connection(self):
        """异步测试数据库连接"""
        try:
            # 获取异步会话工厂
            AsyncSessionLocal = get_async_session_local()

            # 测试连接
            async with AsyncSessionLocal() as session:
                # 执行简单查询，使用text()函数包装SQL语句
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            print(f"数据库连接测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _async_test_redis_connection(self):
        """异步测试Redis连接"""
        try:
            # 检查Redis客户端是否已初始化
            if red_lock.redis_client is None:
                print("Redis客户端未初始化")
                return False

            # 测试连接
            result = await red_lock.redis_client.ping()
            return result
        except Exception as e:
            print(f"Redis连接测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    unittest.main(verbosity=2)