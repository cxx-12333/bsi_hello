#!/bin/bash

# 执行 Alembic migration
# 此脚本用于执行数据库迁移

# 设置工作目录为项目根目录
cd "$(dirname "$0")/.."

echo "执行数据库迁移..."

# 检查是否安装了alembic
if ! command -v alembic &> /dev/null
then
    echo "错误: 未找到 alembic 命令，请确保已安装 alembic"
    exit 1
fi

# 初始化 Alembic 环境变量
echo "正在初始化 Alembic 配置..."
python scripts/init_alembic.py
if [ $? -ne 0 ]; then
    echo "错误: Alembic 初始化失败"
    exit 1
fi

# 执行升级到最新版本
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "数据库迁移执行成功"
else
    echo "数据库迁移执行失败"
    exit 1
fi