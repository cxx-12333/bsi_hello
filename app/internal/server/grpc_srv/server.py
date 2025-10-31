#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from concurrent import futures
import uuid

import grpc
from grpc_reflection.v1alpha import reflection
from grpc_health.v1 import health_pb2, health_pb2_grpc

from app.grpc_api.generated import user_pb2_grpc
from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.base import RegistryClient

# 导入服务管理器
from app.internal.server.service_manager import get_registered_service_names, clear_registered_service_names, get_collected_add_function
from app.internal.router.grpc_router import setup_grpc_services, setup_grpc_services_with_mapping, setup_grpc_services_auto_discovery

# 全局gRPC服务器实例，用于在程序退出时正确关闭
grpc_server_instance = None

logger = logging.getLogger(__name__)

def start_grpc(bootstrap: Bootstrap, user_service_grpc=None, health_servicer=None):
    """启动gRPC服务器（兼容旧版本）"""
    global grpc_server_instance
    
    try:
        # 创建gRPC服务器
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        
        # 保存全局实例
        grpc_server_instance = server
        
        # 注册服务（使用router目录中的配置）
        setup_grpc_services(server, user_service_grpc, health_servicer)
        
        # 绑定端口
        server_address = f"[::]:{bootstrap.service.grpc_port}"
        server.add_insecure_port(server_address)
        logger.info(f"gRPC server starting on {server_address}")
        
        # 启动服务器
        async def serve():
            await server.start()
            logger.info("gRPC server started successfully")
            try:
                await server.wait_for_termination()
            except asyncio.CancelledError:
                logger.info("gRPC server is being cancelled")
                # 正确关闭服务器
                try:
                    await server.stop(None)
                    logger.info("gRPC server stopped successfully")
                except asyncio.CancelledError:
                    # 忽略在关闭过程中可能出现的CancelledError
                    logger.info("gRPC server stop was cancelled, ignoring")
                except Exception as e:
                    logger.error(f"Error stopping gRPC server: {e}")
        
        return asyncio.create_task(serve())
        
    except Exception as e:
        logger.error(f"Failed to start gRPC server: {e}")
        raise

def start_grpc_with_mapping(bootstrap: Bootstrap, service_mapping: dict = None):
    """使用服务映射启动gRPC服务器（推荐新版本）"""
    global grpc_server_instance
    
    try:
        # 创建gRPC服务器
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        
        # 保存全局实例
        grpc_server_instance = server
        
        # 如果没有提供服务映射，创建空字典
        if service_mapping is None:
            service_mapping = {}
        
        # 注册服务（使用router目录中的配置）
        setup_grpc_services_with_mapping(server, service_mapping)
        
        # 绑定端口
        server_address = f"[::]:{bootstrap.service.grpc_port}"
        server.add_insecure_port(server_address)
        logger.info(f"gRPC server starting on {server_address}")
        
        # 启动服务器
        async def serve():
            await server.start()
            logger.info("gRPC server started successfully")
            try:
                await server.wait_for_termination()
            except asyncio.CancelledError:
                logger.info("gRPC server is being cancelled")
                # 正确关闭服务器
                try:
                    await server.stop(None)
                    logger.info("gRPC server stopped successfully")
                except asyncio.CancelledError:
                    # 忽略在关闭过程中可能出现的CancelledError
                    logger.info("gRPC server stop was cancelled, ignoring")
                except Exception as e:
                    logger.error(f"Error stopping gRPC server: {e}")
        
        return asyncio.create_task(serve())
        
    except Exception as e:
        logger.error(f"Failed to start gRPC server with mapping: {e}")
        raise

def start_grpc_auto_discovery(bootstrap: Bootstrap, app_container=None):
    """自动发现服务并启动gRPC服务器（最简版本）"""
    global grpc_server_instance
    
    try:
        # 创建gRPC服务器
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        
        # 保存全局实例
        grpc_server_instance = server
        
        # 自动发现并注册服务
        setup_grpc_services_auto_discovery(server, app_container)
        
        # 绑定端口
        server_address = f"[::]:{bootstrap.service.grpc_port}"
        server.add_insecure_port(server_address)
        logger.info(f"gRPC server starting on {server_address}")
        
        # 启动服务器
        async def serve():
            await server.start()
            logger.info("gRPC server started successfully")
            try:
                await server.wait_for_termination()
            except asyncio.CancelledError:
                logger.info("gRPC server is being cancelled")
                # 正确关闭服务器
                try:
                    await server.stop(None)
                    logger.info("gRPC server stopped successfully")
                except asyncio.CancelledError:
                    # 忽略在关闭过程中可能出现的CancelledError
                    logger.info("gRPC server stop was cancelled, ignoring")
                except Exception as e:
                    logger.error(f"Error stopping gRPC server: {e}")
        
        return asyncio.create_task(serve())
        
    except Exception as e:
        logger.error(f"Failed to start gRPC server with auto discovery: {e}")
        raise

def stop_grpc():
    """停止gRPC服务器"""
    global grpc_server_instance
    if grpc_server_instance:
        try:
            # 在当前事件循环中运行停止任务
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务并等待
                task = loop.create_task(grpc_server_instance.stop(None))
                # 等待任务完成以避免协程未等待的警告
                loop.run_until_complete(task)
            else:
                # 如果事件循环没有运行，直接运行直到完成
                loop.run_until_complete(grpc_server_instance.stop(None))
                
            logger.info("gRPC server stopped successfully")
        except asyncio.CancelledError:
            # 忽略CancelledError异常
            logger.info("gRPC server stop was cancelled, ignoring")
        except Exception as e:
            logger.error(f"Error stopping gRPC server: {e}")
        finally:
            grpc_server_instance = None