# -*- coding: utf-8 -*-
"""
根容器 - 管理基础设施层的依赖
"""

from dependency_injector import containers, providers
from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.consul_registry import ConsulRegistry


class RootContainer(containers.DeclarativeContainer):
    """根容器，管理基础设施层的依赖"""

    # 配置
    config = providers.Configuration()
    
    # Bootstrap单例
    bootstrap = providers.Singleton(
        Bootstrap.get_instance
    )
    
    # Consul注册中心单例
    consul_registry = providers.Singleton(
        ConsulRegistry,
        host=providers.Callable(
            lambda bootstrap: bootstrap.registry.address.replace("https://", "").replace("http://", "").split(":")[0] if "://" in bootstrap.registry.address else bootstrap.registry.address.split(":")[0] if ":" in bootstrap.registry.address else bootstrap.registry.address,
            bootstrap=bootstrap
        ),
        port=providers.Callable(
            lambda bootstrap: int(bootstrap.registry.address.replace("https://", "").replace("http://", "").split(":")[1]) if "://" in bootstrap.registry.address and ":" in bootstrap.registry.address.replace("https://", "").replace("http://", "") else int(bootstrap.registry.address.split(":")[1]) if ":" in bootstrap.registry.address and "://" not in bootstrap.registry.address else 443,
            bootstrap=bootstrap
        ),
        scheme=providers.Callable(
            lambda bootstrap: "https" if "https://" in bootstrap.registry.address else "http",
            bootstrap=bootstrap
        ),
        token=providers.Callable(
            lambda bootstrap: bootstrap.registry.token,
            bootstrap=bootstrap
        )
    )