#!/usr/bin/env python3
"""
初始化Consul配置脚本
"""

import consul
import json
import argparse
import yaml
import os
from urllib.parse import urlparse

def init_consul_config_from_yaml(consul_client, config_path="bsi/hello_py", environment="dev", token=None):
    """
    从YAML文件初始化Consul配置
    
    Args:
        consul_client: Consul客户端实例
        config_path: 配置路径，默认为bsi/hello_py
        environment: 环境类型，默认为dev
        token: Consul ACL token
    """
    # 构建配置文件路径
    yaml_file_path = os.path.join(os.path.dirname(__file__), '..', 'consul_config.yaml')
    
    # 检查配置文件是否存在
    if not os.path.exists(yaml_file_path):
        print(f"配置文件不存在: {yaml_file_path}，使用默认配置")
        # 使用默认配置
        default_configs = {
            "database": {
                "user": "root",
                "password": "123456",
                "host": "127.0.0.1" if environment == "dev" else "prod-db-host",
                "port": "3306",
                "database": "testdb" if environment == "dev" else "production_db"
            },
            "redis": {
                "host": "localhost" if environment == "dev" else "prod-redis-host",
                "port": 6379,
                "db": 0,
                "password": ""  # Redis密码，默认为空
            },
            "app_setting": {
                "environment": environment,
                "debug": True if environment == "dev" else False
            }
        }
        
        # 将所有配置以YAML格式存储在单个key中
        yaml_content = yaml.dump(default_configs, allow_unicode=True, default_flow_style=False)
        consul_client.kv.put(f"{config_path}", yaml_content)
        print(f"已写入Consul配置: {config_path}")
        return
    
    # 读取YAML配置文件
    with open(yaml_file_path, 'r', encoding='utf-8') as file:
        config_data = yaml.safe_load(file)
    
    # 检查配置数据结构
    # 如果有config父级对象，则使用它；否则直接使用顶层配置
    if 'config' in config_data:
        configs = config_data.get('config', {})
    else:
        configs = config_data
    
    # 根据环境调整配置
    if environment == "prod":
        # 如果是生产环境，可能需要修改某些配置项
        if "database" in configs:
            configs["database"]["environment"] = "prod"
            configs["database"]["debug"] = False
        if "app_setting" in configs:
            configs["app_setting"]["environment"] = "prod"
            configs["app_setting"]["debug"] = False
    
    # 将所有配置以YAML格式存储在单个key中
    yaml_content = yaml.dump(configs, allow_unicode=True, default_flow_style=False)
    consul_client.kv.put(f"{config_path}", yaml_content)
    print(f"已写入Consul配置: {config_path}")

def init_consul_config(consul_addr, config_path="bsi/hello_py", environment="dev", token=None):
    """初始化Consul配置"""
    # 解析Consul地址，使用urlparse来正确处理包含协议的URL
    parsed_url = urlparse(consul_addr if "://" in consul_addr else f"http://{consul_addr}")
    host = parsed_url.hostname or consul_addr
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 8500)
    scheme = parsed_url.scheme or "http"
    
    # 创建Consul客户端实例，包含token（如果提供）
    client = consul.Consul(host=host, port=port, scheme=scheme, token=token)
    
    # 检查是否存在consul_config.yaml文件
    yaml_file_path = os.path.join(os.path.dirname(__file__), '..', 'consul_config.yaml')
    if os.path.exists(yaml_file_path):
        print(f"从consul_config.yaml文件初始化Consul配置 ({environment} 环境):")
        init_consul_config_from_yaml(client, config_path, environment, token)
    else:
        print(f"consul_config.yaml文件不存在，使用默认配置初始化 ({environment} 环境):")
        # 数据库配置
        db_config = {
            "user": "root",
            "password": "123456",
            "host": "127.0.0.1" if environment == "dev" else "prod-db-host",
            "port": "3306",
            "database": "testdb" if environment == "dev" else "production_db"
        }
        
        # Redis配置
        redis_config = {
            "host": "localhost" if environment == "dev" else "prod-redis-host",
            "port": 6379,
            "db": 0,
            "password": ""  # Redis密码，默认为空
        }
        
        # 应用配置
        app_config = {
            "environment": environment,
            "debug": True if environment == "dev" else False
        }
        
        # 组合所有配置
        all_configs = {
            "database": db_config,
            "redis": redis_config,
            "app_setting": app_config
        }
        
        # 将所有配置以YAML格式存储在单个key中
        yaml_content = yaml.dump(all_configs, allow_unicode=True, default_flow_style=False)
        client.kv.put(f"{config_path}", yaml_content)
        print(f"已写入Consul配置: {config_path}")
    
    print("Consul配置初始化完成")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Consul configuration")
    parser.add_argument("--registry_address", help="Consul address", default="https://consul.dev.shijizhongyun.com")
    parser.add_argument("--registry_token", help="Consul ACL token", default="3f84201a-31a2-c843-bbc0-0a45983aa7b7")
    parser.add_argument("--config_path", help="Consul config path", default="bsi/hello_py")
    parser.add_argument("--environment", help="Environment (dev/prod)", default="dev")
    args = parser.parse_args()
    
    init_consul_config(args.registry_address, args.config_path, args.environment, args.registry_token)