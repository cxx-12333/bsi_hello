#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import uvicorn
import uuid
from fastapi import FastAPI
from loguru import logger

from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.base import RegistryClient
from app.internal.otel.tracing import setup_otel
from app.internal.router import setup_routes


def start_http(container, bootstrap: Bootstrap):
    """启动HTTP服务"""
    # 初始化FastAPI应用
    app = FastAPI(
        title=bootstrap.service.name, 
        version=bootstrap.service.version
    )
    
    # 设置OpenTelemetry
    setup_otel(
        service_name=bootstrap.service.name,
        service_version=bootstrap.service.version,
        environment=bootstrap.otlp.environment,
        otlp_endpoint=bootstrap.otlp.endpoint,
        fastapi_app=app,
    )
    
    # 注册路由（使用router目录中的配置）
    setup_routes(app, container)
    
    # 启动服务器
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=bootstrap.service.http_port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    async def serve():
        await server.serve()
    
    return asyncio.create_task(serve())