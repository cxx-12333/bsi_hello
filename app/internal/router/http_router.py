#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from loguru import logger

from app.api.router_health import router as health_router


def setup_routes(app: FastAPI, container):
    """设置HTTP路由"""
    # 注册用户路由
    user_router = container.api_container().user_router()
    app.include_router(user_router, prefix="/api/v1")
    
    # 注册健康检查路由
    app.include_router(health_router, prefix="")
    
    logger.info("HTTP routes registered successfully")