@echo off
chcp 65001 >nul
REM 执行 Alembic migration
REM 此脚本用于在Windows环境下执行数据库迁移

REM 设置工作目录为项目根目录
cd /d "%~dp0.."

echo 执行数据库迁移...

REM 检查是否安装了alembic
where alembic >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到 alembic 命令，请确保已安装 alembic
    exit /b 1
)

REM 初始化 Alembic 环境变量
echo 正在初始化 Alembic 配置...
python scripts/init_alembic.py
if %errorlevel% neq 0 (
    echo 错误: Alembic 初始化失败
    exit /b 1
)

REM 执行升级到最新版本
alembic upgrade head

if %errorlevel% equ 0 (
    echo 数据库迁移执行成功
) else (
    echo 数据库迁移执行失败
    exit /b 1
)