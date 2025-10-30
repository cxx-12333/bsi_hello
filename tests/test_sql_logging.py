#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SQL日志功能的脚本
"""
import asyncio
import sys
import os
import logging

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.internal.log.logger import init_logger
from sqlalchemy import create_engine, text

def test_sql_logging():
    """测试SQL日志功能"""
    print("初始化日志系统...")
    init_logger()
    
    # 直接测试SQLAlchemy日志
    print("测试SQLAlchemy日志功能...")
    
    # 创建一个内存SQLite数据库用于测试
    engine = create_engine('sqlite:///./test.db', echo=True)
    
    # 执行一个简单的查询来测试SQL日志
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"查询结果: {result.fetchone()}")
    
    print("SQL日志测试完成")

if __name__ == "__main__":
    test_sql_logging()