# -*- coding: utf-8 -*-
"""
用户API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from app.core.interfaces.user_service_interface import UserServiceInterface
from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    name: str


def create_router(user_service: UserServiceInterface) -> APIRouter:
    """
    创建用户路由
    
    Args:
        user_service: 用户服务实例（通过依赖注入提供）
        
    Returns:
        APIRouter: 配置好的路由
    """
    router = APIRouter()
    
    @router.get("/user/{user_id}")
    async def get_user(user_id: int):
        result = await user_service.get_user(user_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    @router.post("/user")
    async def create_user(request: UserCreateRequest):
        result = await user_service.create_user(request.name)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    
    return router
