# -*- coding: utf-8 -*-
"""
用户服务实现
"""

from typing import Dict, Any, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import User
from app.core.interfaces.user_service_interface import UserServiceInterface
from app.internal.log.logger import logger


class UserService(UserServiceInterface):
    """用户服务实现"""
    
    def __init__(self, db_session_factory):
        """
        初始化UserService
        
        Args:
            db_session_factory: 数据库会话工厂，用于创建数据库会话
        """
        self.db_session_factory = db_session_factory
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """根据ID获取用户信息"""
        try:
            # 使用依赖注入的数据库会话工厂
            async with self.db_session_factory() as session:
                logger.info(f"Attempting to get user with id: {user_id}")
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                logger.info(f"Query result for user {user_id}: {user}")
                if user:
                    user_dict = {"id": user.id, "name": user.name}
                    logger.info(f"Returning user dict: {user_dict}")
                    return user_dict
                else:
                    logger.warning(f"User with id {user_id} not found")
                    return {"error": "User not found"}
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting user {user_id}: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error when getting user {user_id}: {str(e)}")
            logger.exception("Full traceback:")
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def create_user(self, name: str) -> Dict[str, Any]:
        """创建新用户"""
        try:
            # 使用依赖注入的数据库会话工厂
            async with self.db_session_factory() as session:
                user = User(name=name)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return {"id": user.id, "name": user.name}
        except SQLAlchemyError as e:
            return {"error": f"Database error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}