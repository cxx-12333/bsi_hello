#!/usr/bin/env python3
"""
检查数据库状态的脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.common import init_config_from_consul
from app.internal.config.bootstrap import Bootstrap
from sqlalchemy import create_engine, text

def check_database():
    """检查数据库状态"""
    print("正在检查数据库状态...")
    
    # 初始化 Consul 配置
    init_config_from_consul()
    
    # 获取数据库 URL
    bootstrap = Bootstrap.get_instance()
    database_url = bootstrap.get_database_url().replace(
        "mysql+aiomysql://", "mysql+pymysql://"
    )
    
    print(f"数据库 URL: {database_url}")
    
    # 创建数据库引擎
    engine = create_engine(database_url)
    
    # 检查 alembic_version 表是否存在
    with engine.connect() as conn:
        # 检查表是否存在
        result = conn.execute(text("SHOW TABLES LIKE 'alembic_version'"))
        tables = result.fetchall()
        
        if tables:
            print("alembic_version 表存在")
            
            # 检查表中的内容
            result = conn.execute(text("SELECT * FROM alembic_version"))
            rows = result.fetchall()
            
            if rows:
                print("alembic_version 表中的数据:")
                for row in rows:
                    print(f"  {row}")
            else:
                print("alembic_version 表为空")
        else:
            print("alembic_version 表不存在")
        
        # 检查 users 表是否存在
        result = conn.execute(text("SHOW TABLES LIKE 'users'"))
        tables = result.fetchall()
        
        if tables:
            print("users 表已存在")
        else:
            print("users 表不存在")

if __name__ == "__main__":
    check_database()