# 改进的gRPC服务注册机制

本文档介绍如何改进gRPC服务注册机制，避免每次添加新服务时都需要修改函数签名的问题。

## 目录
1. [问题分析](#问题分析)
2. [改进方案](#改进方案)
3. [实现细节](#实现细节)
4. [代码示例](#代码示例)
5. [优势对比](#优势对比)
6. [迁移指南](#迁移指南)

## 问题分析

当前实现存在以下问题：

1. **函数签名频繁变更**：每次添加新服务都需要修改 `start_grpc` 函数签名
2. **代码维护困难**：多个文件需要同步修改
3. **扩展性差**：添加服务需要修改核心启动逻辑
4. **耦合度高**：服务注册与启动逻辑紧密耦合

当前的 `start_grpc` 函数签名：
```python
def start_grpc(bootstrap: Bootstrap, user_service_grpc=None, health_servicer=None):
    # ...
```

每次添加新服务都需要修改为：
```python
def start_grpc(bootstrap: Bootstrap, user_service_grpc=None, order_service_grpc=None, health_servicer=None):
    # ...
```

## 改进方案

### 方案一：使用服务字典传递

通过字典传递所有gRPC服务实例，避免修改函数签名：

```python
def start_grpc(bootstrap: Bootstrap, grpc_services: dict = None):
    # 通过字典访问各个服务实例
    user_service = grpc_services.get('user_service_grpc')
    order_service = grpc_services.get('order_service_grpc')
    health_service = grpc_services.get('health_servicer')
```

### 方案二：使用服务容器传递

直接传递整个gRPC容器，由路由层解析所需服务：

```python
def start_grpc(bootstrap: Bootstrap, grpc_container=None):
    # 路由层直接从容器获取服务实例
    setup_grpc_services(server, grpc_container)
```

### 方案三：动态服务发现

通过容器自动发现并注册所有可用的gRPC服务：

```python
def start_grpc(bootstrap: Bootstrap, grpc_container=None):
    # 自动发现并注册所有gRPC服务
    setup_grpc_services(server, grpc_container)
```

## 实现细节

### 1. 修改服务管理器

增强服务管理器以支持动态服务注册：

```python
# app/internal/server/service_manager.py
from functools import wraps
from typing import List, Dict, Any

# 存储已注册的服务名称
_registered_service_names: List[str] = []

def collect_service_name(func):
    """装饰器，用于收集服务名称"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 提取服务名称
        service_name = _extract_service_name(func.__name__)
        if service_name and service_name not in _registered_service_names:
            _registered_service_names.append(service_name)
        return func(*args, **kwargs)
    return wrapper

def _extract_service_name(func_name: str) -> str:
    """从函数名中提取服务名称"""
    if func_name.startswith('add_') and func_name.endswith('_to_server'):
        # 例如：add_UserServiceServicer_to_server -> UserService
        service_part = func_name[4:-9]  # 移除 'add_' 和 '_to_server'
        # 处理 Servicer 后缀
        if service_part.endswith('Servicer'):
            service_part = service_part[:-8]
        return service_part
    return ""

def get_registered_service_names() -> List[str]:
    """获取已注册的服务名称列表"""
    return _registered_service_names.copy()

def clear_registered_service_names():
    """清空已注册的服务名称列表"""
    _registered_service_names.clear()

def get_collected_add_function(original_func):
    """装饰器工厂函数，返回一个包装后的函数，该函数会自动收集服务名称"""
    @wraps(original_func)
    def wrapper(servicer, server):
        # 执行原始的add_*_to_server函数
        result = original_func(servicer, server)
        
        # 提取服务名称并收集
        service_name = _extract_service_name(original_func.__name__)
        if service_name and service_name not in _registered_service_names:
            _registered_service_names.append(service_name)
            
        return result
    return wrapper

# 新增：批量注册服务的函数
def register_services(server, service_mapping: Dict[str, Any]):
    """批量注册gRPC服务
    
    Args:
        server: gRPC服务器实例
        service_mapping: 服务映射字典 {service_name: service_instance}
    """
    from app.internal.router.grpc_router import setup_grpc_services_with_mapping
    setup_grpc_services_with_mapping(server, service_mapping)
```

### 2. 修改gRPC路由配置

创建支持动态服务注册的路由配置：

```python
# app/internal/router/grpc_router.py
import logging
from grpc_reflection.v1alpha import reflection

from app.internal.server.service_manager import (
    clear_registered_service_names, 
    get_registered_service_names,
    get_collected_add_function
)

logger = logging.getLogger(__name__)

def setup_grpc_services(server, user_service_grpc=None, health_servicer=None):
    """设置gRPC服务（兼容旧版本）"""
    try:
        # 清空之前的服务名称列表
        clear_registered_service_names()
        
        # 注册服务（使用装饰器包装的函数，会自动收集服务名称）
        from app.grpc_api.generated import user_pb2_grpc
        from grpc_health.v1 import health_pb2_grpc
        
        if user_service_grpc:
            get_collected_add_function(user_pb2_grpc.add_UserServiceServicer_to_server)(user_service_grpc, server)
        if health_servicer:
            get_collected_add_function(health_pb2_grpc.add_HealthServicer_to_server)(health_servicer, server)
        
        # 获取已注册的服务名称列表
        service_names = get_registered_service_names()
        
        # 启用反射功能
        reflection.enable_server_reflection(service_names, server)
        
        logger.info(f"gRPC services registered: {service_names}")
        
    except Exception as e:
        logger.error(f"Failed to setup gRPC services: {e}")
        raise

def setup_grpc_services_with_mapping(server, service_mapping: dict):
    """使用服务映射字典设置gRPC服务（新版本）"""
    try:
        # 清空之前的服务名称列表
        clear_registered_service_names()
        
        # 动态注册服务
        from app.grpc_api.generated import user_pb2_grpc, order_pb2_grpc
        from grpc_health.v1 import health_pb2_grpc
        
        # 注册用户服务
        if 'user_service_grpc' in service_mapping and service_mapping['user_service_grpc']:
            get_collected_add_function(user_pb2_grpc.add_UserServiceServicer_to_server)(
                service_mapping['user_service_grpc'], server
            )
        
        # 注册订单服务
        if 'order_service_grpc' in service_mapping and service_mapping['order_service_grpc']:
            get_collected_add_function(order_pb2_grpc.add_OrderServiceServicer_to_server)(
                service_mapping['order_service_grpc'], server
            )
        
        # 注册健康检查服务
        if 'health_servicer' in service_mapping and service_mapping['health_servicer']:
            get_collected_add_function(health_pb2_grpc.add_HealthServicer_to_server)(
                service_mapping['health_servicer'], server
            )
        
        # 获取已注册的服务名称列表
        service_names = get_registered_service_names()
        
        # 启用反射功能
        reflection.enable_server_reflection(service_names, server)
        
        logger.info(f"gRPC services registered: {service_names}")
        
    except Exception as e:
        logger.error(f"Failed to setup gRPC services with mapping: {e}")
        raise

# 新增：自动发现并注册服务
def setup_grpc_services_auto_discovery(server, grpc_container):
    """自动发现并注册gRPC服务"""
    try:
        # 清空之前的服务名称列表
        clear_registered_service_names()
        
        # 从容器中获取可用的服务
        service_mapping = {}
        
        # 尝试获取用户服务
        try:
            user_service = grpc_container.user_service_grpc()
            if user_service:
                service_mapping['user_service_grpc'] = user_service
        except Exception:
            logger.debug("User service not available in container")
        
        # 尝试获取订单服务
        try:
            order_service = grpc_container.order_service_grpc()
            if order_service:
                service_mapping['order_service_grpc'] = order_service
        except Exception:
            logger.debug("Order service not available in container")
        
        # 创建健康检查服务
        from grpc_health.v1.health import HealthServicer
        service_mapping['health_servicer'] = HealthServicer()
        
        # 使用映射注册服务
        setup_grpc_services_with_mapping(server, service_mapping)
        
    except Exception as e:
        logger.error(f"Failed to auto-discover gRPC services: {e}")
        raise
```

### 3. 修改gRPC服务启动函数

创建更灵活的gRPC服务启动函数：

```python
# app/internal/server/grpc_srv/server.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from concurrent import futures
import uuid

import grpc
from grpc_reflection.v1alpha import reflection
from grpc_health.v1 import health_pb2, health_pb2_grpc

from app.grpc_api.generated import user_pb2_grpc
from app.internal.config.bootstrap import Bootstrap
from app.internal.registry.base import RegistryClient

# 导入服务管理器
from app.internal.server.service_manager import get_registered_service_names, clear_registered_service_names, get_collected_add_function
from app.internal.router.grpc_router import setup_grpc_services, setup_grpc_services_with_mapping, setup_grpc_services_auto_discovery

# 全局gRPC服务器实例，用于在程序退出时正确关闭
grpc_server_instance = None

logger = logging.getLogger(__name__)

def start_grpc(bootstrap: Bootstrap, user_service_grpc=None, health_servicer=None):
    """启动gRPC服务器（兼容旧版本）"""
    global grpc_server_instance
    
    try:
        # 创建gRPC服务器
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        
        # 保存全局实例
        grpc_server_instance = server
        
        # 注册服务（使用router目录中的配置）
        setup_grpc_services(server, user_service_grpc, health_servicer)
        
        # 绑定端口
        server_address = f"[::]:{bootstrap.service.grpc_port}"
        server.add_insecure_port(server_address)
        logger.info(f"gRPC server starting on {server_address}")
        
        # 启动服务器
        async def serve():
            await server.start()
            logger.info("gRPC server started successfully")
            try:
                await server.wait_for_termination()
            except asyncio.CancelledError:
                logger.info("gRPC server is being cancelled")
                # 正确关闭服务器
                try:
                    await server.stop(None)
                    logger.info("gRPC server stopped successfully")
                except asyncio.CancelledError:
                    # 忽略在关闭过程中可能出现的CancelledError
                    logger.info("gRPC server stop was cancelled, ignoring")
                except Exception as e:
                    logger.error(f"Error stopping gRPC server: {e}")
        
        return asyncio.create_task(serve())
        
    except Exception as e:
        logger.error(f"Failed to start gRPC server: {e}")
        raise

def start_grpc_with_mapping(bootstrap: Bootstrap, service_mapping: dict = None):
    """使用服务映射启动gRPC服务器（推荐新版本）"""
    global grpc_server_instance
    
    try:
        # 创建gRPC服务器
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        
        # 保存全局实例
        grpc_server_instance = server
        
        # 如果没有提供服务映射，创建空字典
        if service_mapping is None:
            service_mapping = {}
        
        # 注册服务（使用router目录中的配置）
        setup_grpc_services_with_mapping(server, service_mapping)
        
        # 绑定端口
        server_address = f"[::]:{bootstrap.service.grpc_port}"
        server.add_insecure_port(server_address)
        logger.info(f"gRPC server starting on {server_address}")
        
        # 启动服务器
        async def serve():
            await server.start()
            logger.info("gRPC server started successfully")
            try:
                await server.wait_for_termination()
            except asyncio.CancelledError:
                logger.info("gRPC server is being cancelled")
                # 正确关闭服务器
                try:
                    await server.stop(None)
                    logger.info("gRPC server stopped successfully")
                except asyncio.CancelledError:
                    # 忽略在关闭过程中可能出现的CancelledError
                    logger.info("gRPC server stop was cancelled, ignoring")
                except Exception as e:
                    logger.error(f"Error stopping gRPC server: {e}")
        
        return asyncio.create_task(serve())
        
    except Exception as e:
        logger.error(f"Failed to start gRPC server with mapping: {e}")
        raise

def start_grpc_auto_discovery(bootstrap: Bootstrap, grpc_container=None):
    """自动发现服务并启动gRPC服务器（最简版本）"""
    global grpc_server_instance
    
    try:
        # 创建gRPC服务器
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        
        # 保存全局实例
        grpc_server_instance = server
        
        # 自动发现并注册服务
        setup_grpc_services_auto_discovery(server, grpc_container)
        
        # 绑定端口
        server_address = f"[::]:{bootstrap.service.grpc_port}"
        server.add_insecure_port(server_address)
        logger.info(f"gRPC server starting on {server_address}")
        
        # 启动服务器
        async def serve():
            await server.start()
            logger.info("gRPC server started successfully")
            try:
                await server.wait_for_termination()
            except asyncio.CancelledError:
                logger.info("gRPC server is being cancelled")
                # 正确关闭服务器
                try:
                    await server.stop(None)
                    logger.info("gRPC server stopped successfully")
                except asyncio.CancelledError:
                    # 忽略在关闭过程中可能出现的CancelledError
                    logger.info("gRPC server stop was cancelled, ignoring")
                except Exception as e:
                    logger.error(f"Error stopping gRPC server: {e}")
        
        return asyncio.create_task(serve())
        
    except Exception as e:
        logger.error(f"Failed to start gRPC server with auto discovery: {e}")
        raise

def stop_grpc():
    """停止gRPC服务器"""
    global grpc_server_instance
    if grpc_server_instance:
        try:
            # 在当前事件循环中运行停止任务
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务并等待
                task = loop.create_task(grpc_server_instance.stop(None))
                # 等待任务完成以避免协程未等待的警告
                loop.run_until_complete(task)
            else:
                # 如果事件循环没有运行，直接运行直到完成
                loop.run_until_complete(grpc_server_instance.stop(None))
                
            logger.info("gRPC server stopped successfully")
        except asyncio.CancelledError:
            # 忽略CancelledError异常
            logger.info("gRPC server stop was cancelled, ignoring")
        except Exception as e:
            logger.error(f"Error stopping gRPC server: {e}")
        finally:
            grpc_server_instance = None
```

### 4. 修改应用启动代码

简化应用启动代码：

```python
# app/internal/server/application.py
import asyncio
import logging
from app.internal.config.bootstrap import Bootstrap
from app.internal.server.grpc_srv.server import start_grpc_with_mapping, start_grpc_auto_discovery

logger = logging.getLogger(__name__)

class Application:
    def __init__(self, bootstrap: Bootstrap):
        self.bootstrap = bootstrap
        self.grpc_task = None

    async def run(self, container, registry=None):
        """运行应用"""
        try:
            logger.info("Starting application...")
            
            # 方法1: 使用服务映射（推荐）
            service_mapping = {
                'user_service_grpc': container.grpc_container().user_service_grpc(),
                'order_service_grpc': container.grpc_container().order_service_grpc(),  # 新增服务无需修改函数签名
                'health_servicer': None  # 健康检查服务将在路由层创建
            }
            self.grpc_task = start_grpc_with_mapping(self.bootstrap, service_mapping)
            
            # 方法2: 使用自动发现（最简）
            # self.grpc_task = start_grpc_auto_discovery(self.bootstrap, container.grpc_container())
            
            logger.info("Application started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            raise

    async def stop(self):
        """停止应用"""
        try:
            logger.info("Stopping application...")
            
            # 取消gRPC任务
            if self.grpc_task:
                self.grpc_task.cancel()
                try:
                    await self.grpc_task
                except asyncio.CancelledError:
                    logger.info("gRPC task cancelled successfully")
            
            logger.info("Application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
```

## 代码示例

### 添加新服务的完整示例

1. **定义Proto文件**：
```protobuf
# app/grpc_api/proto/product.proto
syntax = "proto3";
package product;

service ProductService {
  rpc GetProduct (ProductRequest) returns (ProductReply);
  rpc CreateProduct (CreateProductRequest) returns (ProductReply);
}

message ProductRequest {
  string id = 1;
}

message ProductReply {
  string id = 1;
  string name = 2;
  float price = 3;
}

message CreateProductRequest {
  string name = 1;
  float price = 2;
}
```

2. **实现服务逻辑**：
```python
# app/core/product_service.py
from app.core.interfaces.product_service_interface import ProductServiceInterface

class ProductService(ProductServiceInterface):
    """产品服务实现"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def get_product(self, product_id: str) -> dict:
        """获取产品信息"""
        with self.db_session_factory() as session:
            return {
                "id": product_id,
                "name": "Product Name",
                "price": 99.99
            }
    
    def create_product(self, name: str, price: float) -> dict:
        """创建新产品"""
        with self.db_session_factory() as session:
            return {
                "id": "product123",
                "name": name,
                "price": price
            }
```

3. **实现gRPC服务端**：
```python
# app/grpc_api/server.py
from app.grpc_api.generated import product_pb2, product_pb2_grpc
from app.core.interfaces.product_service_interface import ProductServiceInterface

class ProductServiceGrpc(product_pb2_grpc.ProductServiceServicer):
    """gRPC产品服务实现"""
    
    def __init__(self, product_service: ProductServiceInterface):
        self.product_service = product_service
    
    def GetProduct(self, request, context):
        """获取产品的gRPC方法"""
        try:
            product_data = self.product_service.get_product(request.id)
            return product_pb2.ProductReply(
                id=product_data["id"],
                name=product_data["name"],
                price=product_data["price"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get product: {str(e)}")
            raise
    
    def CreateProduct(self, request, context):
        """创建产品的gRPC方法"""
        try:
            product_data = self.product_service.create_product(
                request.name,
                request.price
            )
            return product_pb2.ProductReply(
                id=product_data["id"],
                name=product_data["name"],
                price=product_data["price"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create product: {str(e)}")
            raise
```

4. **更新容器配置**：
```python
# app/containers/service_container.py
from app.core.user_service import UserService
from app.core.order_service import OrderService
from app.core.product_service import ProductService  # 新增

class ServiceContainer(containers.DeclarativeContainer):
    """服务容器，管理服务层的依赖"""
    
    # 数据访问容器
    data_access_container = providers.DependenciesContainer()
    
    # UserService工厂
    user_service = providers.Factory(
        UserService,
        db_session_factory=data_access_container.db_session.provider
    )
    
    # OrderService工厂
    order_service = providers.Factory(
        OrderService,
        db_session_factory=data_access_container.db_session.provider
    )
    
    # ProductService工厂 (新增)
    product_service = providers.Factory(
        ProductService,
        db_session_factory=data_access_container.db_session.provider
    )
```

```python
# app/containers/grpc_container.py
from app.grpc_api.server import UserServiceGrpc, OrderServiceGrpc, ProductServiceGrpc  # 更新导入
from app.containers.service_container import ServiceContainer

class GrpcContainer(containers.DeclarativeContainer):
    """gRPC服务端依赖注入容器"""
    
    # 依赖容器
    service_container = providers.DependenciesContainer()
    
    # UserServiceGrpc工厂
    user_service_grpc = providers.Factory(
        UserServiceGrpc,
        user_service=service_container.user_service
    )
    
    # OrderServiceGrpc工厂
    order_service_grpc = providers.Factory(
        OrderServiceGrpc,
        order_service=service_container.order_service
    )
    
    # ProductServiceGrpc工厂 (新增)
    product_service_grpc = providers.Factory(
        ProductServiceGrpc,
        product_service=service_container.product_service
    )
```

5. **更新应用启动代码**（无需修改函数签名）：
```python
# app/internal/server/application.py
async def run(self, container, registry=None):
    """运行应用"""
    try:
        logger.info("Starting application...")
        
        # 只需在这里添加新服务到映射中，无需修改函数签名
        service_mapping = {
            'user_service_grpc': container.grpc_container().user_service_grpc(),
            'order_service_grpc': container.grpc_container().order_service_grpc(),
            'product_service_grpc': container.grpc_container().product_service_grpc(),  # 新增服务
            'health_servicer': None
        }
        self.grpc_task = start_grpc_with_mapping(self.bootstrap, service_mapping)
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
```

## 优势对比

| 特性 | 旧方案 | 新方案 |
|------|--------|--------|
| 函数签名修改 | 每次添加服务都需要修改 | 无需修改 |
| 代码维护 | 多个文件需要同步修改 | 集中管理 |
| 扩展性 | 差 | 优秀 |
| 耦合度 | 高 | 低 |
| 可读性 | 一般 | 优秀 |
| 错误风险 | 高 | 低 |

## 迁移指南

### 第一步：更新服务管理器

替换 `app/internal/server/service_manager.py` 为新版本。

### 第二步：更新路由配置

替换 `app/internal/router/grpc_router.py` 为新版本。

### 第三步：更新gRPC服务启动函数

替换 `app/internal/server/grpc_srv/server.py` 为新版本。

### 第四步：更新应用启动代码

修改 `app/internal/server/application.py` 使用新的启动函数：

```python
# 旧代码
self.grpc_task = start_grpc(self.bootstrap, user_service_grpc, health_servicer)

# 新代码
service_mapping = {
    'user_service_grpc': user_service_grpc,
    'health_servicer': health_servicer
}
self.grpc_task = start_grpc_with_mapping(self.bootstrap, service_mapping)
```

### 第五步：验证功能

运行测试确保所有功能正常工作：

```bash
# 运行gRPC服务测试
python -m pytest tests/test_6_grpc_service.py -v

# 运行集成测试
python -m pytest tests/test_7_multi_service_grpc_client.py -v
```

通过以上改进，您可以轻松添加新服务而无需修改核心函数签名，大大提高了代码的可维护性和扩展性。