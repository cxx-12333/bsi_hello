#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试公共模块
包含可在多个测试文件中复用的公共方法和配置
"""

import sys
import os
from urllib.parse import urlparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.consul_registry import ConsulRegistry

# 默认Consul连接配置
DEFAULT_CONSUL_ADDRESS = "https://consul.dev.shijizhongyun.com"
DEFAULT_CONSUL_TOKEN = "3f84201a-31a2-c843-bbc0-0a45983aa7b7"  # 本地开发环境通常不需要token
DEFAULT_CONFIG_PATH = "bsi/hello_py"


def parse_consul_address(consul_address):
    """
    解析Consul地址，提取主机、端口和协议
    
    Args:
        consul_address (str): Consul地址
        
    Returns:
        tuple: (host, port, scheme) 主机、端口和协议
    """
    parsed_url = urlparse(consul_address)
    consul_host = parsed_url.hostname or consul_address
    
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
    
    return consul_host, consul_port, scheme


def init_config_from_consul(consul_address=DEFAULT_CONSUL_ADDRESS, consul_token=DEFAULT_CONSUL_TOKEN, config_path=DEFAULT_CONFIG_PATH):
    """
    从Consul初始化配置的公共方法
    
    Args:
        consul_address (str): Consul地址
        consul_token (str): Consul访问令牌
        config_path (str): 配置路径
        
    Returns:
        tuple: (bootstrap, registry) Bootstrap配置对象和Consul注册中心实例
    """
    print(f"从Consul初始化配置: {consul_address}, 路径: {config_path}")

    # 解析Consul地址
    consul_host, consul_port, scheme = parse_consul_address(consul_address)

    # 创建Consul注册中心实例
    registry = ConsulRegistry(host=consul_host, port=consul_port, scheme=scheme, token=consul_token)

    # 初始化全局配置对象
    bootstrap = Bootstrap.get_instance()
    bootstrap.registry.address = consul_address
    bootstrap.registry.token = consul_token
    bootstrap.registry.config_path = config_path

    # 一次性初始化所有配置
    success = bootstrap.init_from_consul(registry, config_path)
    if not success:
        raise RuntimeError("Consul配置初始化失败")
    return bootstrap, registry