#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import os
import socket
import sys
import signal
from functools import lru_cache
from urllib.parse import urlparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.containers.root_container import RootContainer
from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.consul_registry import ConsulRegistry
from app.internal.registry.base import RegistryClient
from app.internal.server.application import Application
from loguru import logger

# -------------------- 命令行参数解析 --------------------
def parse_args():
    parser = argparse.ArgumentParser(description="User Service")
    parser.add_argument("--registry_dc", help="Consul data center", default="")
    parser.add_argument("--registry_address", help="Consul address", default="https://consul.dev.shijizhongyun.com")
    parser.add_argument("--registry_token", help="Consul ACL token", default="3f84201a-31a2-c843-bbc0-0a45983aa7b7")
    parser.add_argument("--config_path", help="Consul config path", default="bsi/hello_py")
    parser.add_argument("--local_ip", help="Local IP address to register to Consul", default="")
    parser.add_argument("--service_name", help="Service name", default="bsi.hello_py")
    parser.add_argument("--service_version", help="Service version", default="v0.0.1")
    parser.add_argument("--http_port", help="HTTP server port", type=int, default=8001)
    parser.add_argument("--grpc_port", help="gRPC server port", type=int, default=9001)
    parser.add_argument("--otlp_endpoint", help="OTLP collector endpoint", default="192.168.80.94:4317")
    parser.add_argument("--environment", help="Environment (dev/prod)", default="dev")
    return parser.parse_args()

# -------------------- 命令行参数解析 --------------------
args = parse_args()

# 初始化全局配置对象
bootstrap = Bootstrap.get_instance()
bootstrap.registry.dc = args.registry_dc
bootstrap.registry.address = args.registry_address
bootstrap.registry.token = args.registry_token
bootstrap.registry.config_path = args.config_path
bootstrap.registry.local_ip = args.local_ip
bootstrap.service.name = args.service_name
bootstrap.service.version = args.service_version
bootstrap.service.http_port = args.http_port
bootstrap.service.grpc_port = args.grpc_port
bootstrap.otlp.endpoint = args.otlp_endpoint
bootstrap.otlp.environment = args.environment

# -------------------- 注册中心 --------------------
# 解析Consul地址，使用urlparse来正确处理包含协议的URL
parsed_url = urlparse(bootstrap.registry.address)
consul_host = parsed_url.hostname or bootstrap.registry.address
# 设置默认端口
if parsed_url.port:
    consul_port = parsed_url.port
elif parsed_url.scheme == "https":
    consul_port = 443
elif parsed_url.scheme == "http":
    consul_port = 80
else:
    consul_port = 8500
    
scheme = parsed_url.scheme or "http"
registry = ConsulRegistry(host=consul_host, port=consul_port, scheme=scheme, token=bootstrap.registry.token)

def on_config_change(value):
    logger.info("配置更新: {}", value)

# 监听配置变化
registry.watch_config(bootstrap.registry.config_path, on_config_change)

# -------------------- 主程序 --------------------
async def main():
    # 一次性初始化所有配置
    if not bootstrap.init_from_consul(registry, bootstrap.registry.config_path):
        logger.error("Failed to initialize configurations from Consul")
        return
    
    # 初始化依赖注入容器
    from app.containers.application_container import ApplicationContainer
    container = ApplicationContainer()
    
    # 创建应用实例并运行
    application = Application(bootstrap)
    await application.run(container, registry)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
