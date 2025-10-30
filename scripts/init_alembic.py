#!/usr/bin/env python3
"""
Alembic 初始化脚本
用于初始化 Alembic 数据库版本控制
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.common import init_config_from_consul
from app.internal.config.bootstrap import Bootstrap

def init_alembic():
    """初始化 Alembic 配置"""
    print("正在初始化 Alembic...")
    
    # 初始化 Consul 配置
    init_config_from_consul()
    
    # 获取数据库 URL
    bootstrap = Bootstrap.get_instance()
    database_url = bootstrap.get_database_url().replace(
        "mysql+aiomysql://", "mysql+pymysql://"
    )
    
    print(f"数据库 URL: {database_url}")
    
    # 设置环境变量供 Alembic 使用
    os.environ['ALEMBIC_DATABASE_URL'] = database_url
    
    print("Alembic 初始化完成")

if __name__ == "__main__":
    init_alembic()