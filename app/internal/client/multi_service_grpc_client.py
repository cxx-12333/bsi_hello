#!/usr/bin/env python3
"""
多服务gRPC客户端实现，支持Consul服务发现
"""

import asyncio
import grpc
import logging
from typing import Optional, List, Dict, Any, TypeVar, Type
from dependency_injector.wiring import Provide, inject

from app.internal.registry.consul_registry import ConsulRegistry
from app.internal.config.bootstrap import Bootstrap
from urllib.parse import urlparse

# 配置日志
logger = logging.getLogger(__name__)

T = TypeVar('T')  # 用于泛型类型提示


class MultiServiceGrpcClient:
    """多服务gRPC客户端基类"""

    @inject
    def __init__(
            self,
            bootstrap: Bootstrap = Provide["root_container.bootstrap"],
            registry: ConsulRegistry = Provide["root_container.consul_registry"]
    ):
        """
        初始化多服务gRPC客户端

        Args:
            bootstrap: Bootstrap配置实例（通过依赖注入提供）
            registry: Consul注册中心实例（通过依赖注入提供）
        """
        self.bootstrap = bootstrap
        self.registry = registry
        self.channels: Dict[str, grpc.aio.Channel] = {}
        self.stubs: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    async def connect_via_discovery(self, service_name: str, stub_class: Type[T]) -> Optional[T]:
        """
        通过服务发现连接到指定的gRPC服务

        Args:
            service_name: 服务名称
            stub_class: gRPC stub类

        Returns:
            Optional[T]: 服务stub实例，连接失败时返回None
        """
        try:
            # 发现服务
            self.logger.info(f"正在发现服务: {service_name}")
            nodes = self.registry.discover_service(service_name)

            if not nodes:
                self.logger.error(f"未找到服务: {service_name}")
                return None

            # 使用第一个可用节点
            node = nodes[0]
            address = node["Address"]
            port = node["Port"]

            self.logger.info(f"发现服务节点: {address}:{port}")

            # 建立gRPC连接
            target = f"{address}:{port}"
            self.logger.info(f"正在连接到gRPC服务: {target}")

            # 创建通道和stub
            channel = grpc.aio.insecure_channel(target)
            stub = stub_class(channel)

            # 等待通道就绪
            await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
            self.logger.info("gRPC连接成功建立")

            # 保存通道和stub以便后续使用和清理
            self.channels[service_name] = channel
            self.stubs[service_name] = stub

            return stub

        except asyncio.TimeoutError:
            self.logger.error("连接gRPC服务超时")
            return None
        except Exception as e:
            self.logger.error(f"连接gRPC服务失败: {e}")
            return None

    async def connect_direct(self, service_name: str, stub_class: Type[T],
                             host: str = "localhost", port: int = 9001) -> Optional[T]:
        """
        直接连接到指定的gRPC服务

        Args:
            service_name: 服务名称（用于标识连接）
            stub_class: gRPC stub类
            host: 服务主机地址
            port: 服务端口号

        Returns:
            Optional[T]: 服务stub实例，连接失败时返回None
        """
        try:
            target = f"{host}:{port}"
            self.logger.info(f"正在直接连接到gRPC服务: {target}")

            # 创建通道和stub
            channel = grpc.aio.insecure_channel(target)
            stub = stub_class(channel)

            # 等待通道就绪
            await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
            self.logger.info("gRPC连接成功建立")

            # 保存通道和stub以便后续使用和清理
            self.channels[service_name] = channel
            self.stubs[service_name] = stub

            return stub

        except asyncio.TimeoutError:
            self.logger.error("连接gRPC服务超时")
            return None
        except Exception as e:
            self.logger.error(f"连接gRPC服务失败: {e}")
            return None

    async def get_service_stub(self, service_name: str, stub_class: Type[T],
                               use_discovery: bool = True) -> Optional[T]:
        """
        获取指定服务的gRPC stub实例

        Args:
            service_name: 服务名称
            stub_class: gRPC stub类
            use_discovery: 是否使用服务发现，默认True

        Returns:
            Optional[T]: 服务stub实例，获取失败时返回None
        """
        # 如果已经存在stub且通道仍然活跃，直接返回
        if service_name in self.stubs:
            try:
                # 检查通道是否仍然就绪
                await asyncio.wait_for(self.channels[service_name].channel_ready(), timeout=1.0)
                return self.stubs[service_name]
            except:
                # 通道不可用，移除旧的连接
                await self.close_service(service_name)

        # 建立新的连接
        if use_discovery:
            return await self.connect_via_discovery(service_name, stub_class)
        else:
            # 从配置中获取服务端口（如果有的话）
            port = getattr(self.bootstrap.service, f"{service_name.replace('.', '_')}_port", 9001)
            return await self.connect_direct(service_name, stub_class, "localhost", port)

    async def close_service(self, service_name: str):
        """
        关闭指定服务的连接

        Args:
            service_name: 服务名称
        """
        if service_name in self.channels:
            try:
                await self.channels[service_name].close()
                self.logger.info(f"已关闭服务 {service_name} 的连接")
            except Exception as e:
                self.logger.error(f"关闭服务 {service_name} 的连接时发生错误: {e}")
            finally:
                # 从字典中移除
                del self.channels[service_name]
                if service_name in self.stubs:
                    del self.stubs[service_name]

    async def close(self):
        """关闭所有gRPC连接"""
        service_names = list(self.channels.keys())
        for service_name in service_names:
            await self.close_service(service_name)
        self.logger.info("所有gRPC连接已关闭")