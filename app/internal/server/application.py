#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import signal
import sys
import uuid
from loguru import logger

from app.internal.config.bootstrap import Bootstrap
from app.internal.server.grpc_srv.server import start_grpc, stop_grpc
from app.internal.server.http_srv.server import start_http
from app.internal.log.logger import init_logger
from app.internal.utils import get_local_ip


class Application:
    def __init__(self, bootstrap: Bootstrap):
        self.bootstrap = bootstrap
        self.http_server = None
        self.grpc_task = None
        self.registered_service_ids = []
        self.registry = None
        self._is_shutting_down = False

    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            # 在事件循环中创建任务
            loop = asyncio.get_running_loop()
            loop.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def register_services(self):
        """注册服务"""
        # 获取本地IP地址
        local_ip = self.bootstrap.registry.local_ip if self.bootstrap.registry.local_ip else get_local_ip()
        
        # 注册HTTP服务
        http_service_name = f"{self.bootstrap.service.name}.http"
        unique_id = str(uuid.uuid4())
        http_service_id = f"{http_service_name}-{unique_id}"
        self.registry.register_service(
            service_name=http_service_name,
            service_id=http_service_id,
            address=local_ip,
            port=self.bootstrap.service.http_port,
            protocol="http",
            deregister_critical_service_after="90s"
        )
        self.registered_service_ids.append(http_service_id)
        logger.info(f"HTTP service registered with ID: {http_service_id}")
        
        # 注册gRPC服务
        grpc_service_name = f"{self.bootstrap.service.name}.grpc"
        unique_id = str(uuid.uuid4())
        grpc_service_id = f"{grpc_service_name}-{unique_id}"
        self.registry.register_service(
            service_name=grpc_service_name,
            service_id=grpc_service_id,
            address=local_ip,
            port=self.bootstrap.service.grpc_port,
            protocol="grpc",
            deregister_critical_service_after="90s"
        )
        self.registered_service_ids.append(grpc_service_id)
        logger.info(f"gRPC service registered with ID: {grpc_service_id}")
        
        logger.info("服务注册完成")

    def deregister_services(self):
        """注销服务"""
        if self.registry:
            for service_id in self.registered_service_ids:
                try:
                    result = self.registry.deregister_service(service_id)
                    if result:
                        logger.info(f"已注销服务: {service_id}")
                    else:
                        # 注销失败的日志已经在registry.deregister_service中记录，这里不再重复记录
                        pass
                except Exception as e:
                    logger.exception(f"注销服务 {service_id} 时发生异常")  # 使用exception级别自动包含堆栈跟踪

    async def run(self, container, registry=None):
        """运行应用"""
        try:
            # 初始化日志系统
            init_logger()
            
            # 设置注册中心
            self.registry = registry
            
            # 设置信号处理器
            self.setup_signal_handlers()
            
            # 注册服务
            if self.registry:
                await self.register_services()
            
            # 启动HTTP服务器
            self.http_server = start_http(container, self.bootstrap)
            
            # 使用自动发现启动gRPC服务器
            from app.internal.server.grpc_srv.server import start_grpc_auto_discovery
            self.grpc_task = start_grpc_auto_discovery(self.bootstrap, container.grpc_container())
            
            # 等待服务器完成
            await asyncio.gather(self.http_server, self.grpc_task)
            
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """关闭应用"""
        # 防止重复关闭
        if self._is_shutting_down:
            logger.info("关闭流程已在进行中.")
            return
        self._is_shutting_down = True
        
        logger.info("开始关闭应用...")
        
        # 注销服务
        self.deregister_services()
        
        # 停止HTTP服务器
        logger.info("停止HTTP服务器...")
        if self.http_server:
            if not self.http_server.done():
                logger.info("取消HTTP服务器任务...")
                self.http_server.cancel()
                try:
                    await self.http_server
                except asyncio.CancelledError:
                    logger.info("HTTP服务器任务已取消")
                except Exception as e:
                    logger.error(f"Error cancelling HTTP server task: {e}")
            else:
                logger.info("HTTP服务器任务已完成，无需取消")
        else:
            logger.info("HTTP服务器任务未初始化")
        
        # 停止gRPC服务器
        logger.info("停止gRPC服务器...")
        if self.grpc_task:
            if not self.grpc_task.done():
                logger.info("取消gRPC服务器任务...")
                self.grpc_task.cancel()
                try:
                    await self.grpc_task
                except asyncio.CancelledError:
                    logger.info("gRPC服务器任务已取消")
                except Exception as e:
                    logger.error(f"Error cancelling gRPC server task: {e}")
            else:
                logger.info("gRPC服务器任务已完成，无需取消")
        else:
            logger.info("gRPC服务器任务未初始化")
        
        logger.info("应用已关闭")