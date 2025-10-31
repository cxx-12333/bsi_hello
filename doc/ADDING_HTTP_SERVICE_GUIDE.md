# 新增HTTP服务指南

本文档介绍了如何在现有项目中新增一个HTTP服务。我们将以订单服务(OrderService)为例，展示完整的添加过程。

## 概述

我们的HTTP服务架构采用依赖注入模式，通过FastAPI框架提供RESTful API。当你添加一个新的HTTP服务时，需要遵循特定的模式，以确保与现有架构保持一致。

## 优势

1. **统一架构**：所有服务遵循相同的架构模式
2. **依赖注入**：通过Dependency Injector管理服务依赖关系
3. **自动注册**：新服务会自动注册到路由系统
4. **易于测试**：清晰的分层结构便于单元测试和集成测试

## 完整步骤

### 步骤1：创建服务接口

首先在`app/core/interfaces/`目录下创建服务接口：

```python
# app/core/interfaces/order_service_interface.py
from abc import ABC, abstractmethod

class OrderServiceInterface(ABC):
    """订单服务接口"""
    
    @abstractmethod
    async def get_order(self, order_id: str) -> dict:
        """获取订单信息"""
        pass
    
    @abstractmethod
    async def create_order(self, user_id: str, items: list) -> dict:
        """创建新订单"""
        pass
```

### 步骤2：实现核心业务逻辑

在`app/core/`目录下创建服务实现类：

```python
# app/core/order_service.py
from app.core.interfaces.order_service_interface import OrderServiceInterface

class OrderService(OrderServiceInterface):
    """订单服务实现"""
    
    def __init__(self, db_session_factory):
        """
        初始化订单服务
        
        Args:
            db_session_factory: 数据库会话工厂
        """
        self.db_session_factory = db_session_factory
    
    async def get_order(self, order_id: str) -> dict:
        """
        获取订单信息
        
        Args:
            order_id: 订单ID
            
        Returns:
            dict: 订单信息
        """
        # 实现获取订单逻辑
        # 这里只是一个示例，实际实现应包含数据库操作等
        return {
            "id": order_id,
            "user_id": "user123",
            "items": [{"product_id": "prod_1", "quantity": 2}],
            "status": "created"
        }
    
    async def create_order(self, user_id: str, items: list) -> dict:
        """
        创建新订单
        
        Args:
            user_id: 用户ID
            items: 订单项列表
            
        Returns:
            dict: 创建的订单信息
        """
        # 实现创建订单逻辑
        # 这里只是一个示例，实际实现应包含数据库操作等
        order_id = f"order_{user_id}_{len(items)}"
        return {
            "id": order_id,
            "user_id": user_id,
            "items": items,
            "status": "created"
        }
```

### 步骤3：创建Pydantic模型

在`app/api/models/`目录下创建请求和响应的数据模型：

```python
# app/api/models/order_models.py
from pydantic import BaseModel
from typing import List, Optional

class OrderItem(BaseModel):
    """订单项模型"""
    product_id: str
    quantity: int

class OrderRequest(BaseModel):
    """订单请求模型"""
    id: str

class CreateOrderRequest(BaseModel):
    """创建订单请求模型"""
    user_id: str
    items: List[OrderItem]

class OrderResponse(BaseModel):
    """订单响应模型"""
    id: str
    user_id: str
    items: List[OrderItem]
    status: str
    message: Optional[str] = None
```

### 步骤4：创建API路由

在`app/api/`目录下创建新的API路由文件：

```python
# app/api/router_order.py
# -*- coding: utf-8 -*-
"""
订单API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from app.core.interfaces.order_service_interface import OrderServiceInterface
from app.api.models.order_models import OrderRequest, CreateOrderRequest, OrderResponse


def create_router(order_service: OrderServiceInterface) -> APIRouter:
    """
    创建订单路由
    
    Args:
        order_service: 订单服务实例（通过依赖注入提供）
        
    Returns:
        APIRouter: 配置好的路由
    """
    router = APIRouter()
    
    @router.get("/order/{order_id}", response_model=OrderResponse)
    async def get_order(order_id: str):
        """
        获取订单信息
        
        Args:
            order_id: 订单ID
            
        Returns:
            OrderResponse: 订单信息响应
        """
        try:
            result = await order_service.get_order(order_id)
            return OrderResponse(**result, message="Order retrieved successfully")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")

    @router.post("/order", response_model=OrderResponse)
    async def create_order(request: CreateOrderRequest):
        """
        创建新订单
        
        Args:
            request: 创建订单请求
            
        Returns:
            OrderResponse: 创建的订单信息响应
        """
        try:
            result = await order_service.create_order(request.user_id, 
                                                    [item.dict() for item in request.items])
            return OrderResponse(**result, message="Order created successfully")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
    
    return router
```

### 步骤5：更新服务容器

在`app/containers/service_container.py`中添加订单服务的工厂方法：

```python
# 在ServiceContainer类中添加

# OrderService工厂
order_service = providers.Factory(
    OrderService,
    db_session_factory=data_access_container.db_session.provider
)
```

### 步骤6：更新API容器

在`app/containers/api_container.py`中添加订单路由的工厂方法：

```python
# 添加导入
from app.api.router_order import create_router

# 在ApiContainer类中添加

# 订单路由工厂
order_router = providers.Factory(
    create_router,
    order_service=service_container.order_service
)
```

### 步骤7：注册路由

在`app/internal/router/http_router.py`中注册新的路由：

```python
# 添加导入
from app.api.router_order import router as order_router

# 更新setup_routes函数
def setup_routes(app: FastAPI, container):
    """设置HTTP路由"""
    # 注册用户路由
    user_router = container.api_container().user_router()
    app.include_router(user_router, prefix="/api/v1")
    
    # 注册订单路由
    order_router = container.api_container().order_router()
    app.include_router(order_router, prefix="/api/v1")
    
    # 注册健康检查路由
    app.include_router(health_router, prefix="")
    
    logger.info("HTTP routes registered successfully")
```

## 测试验证

添加完服务后，你可以编写简单的测试来验证服务是否正常工作：

```python
# tests/test_order_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.internal.config.settings import Settings

@pytest.fixture
def client():
    """测试客户端"""
    settings = Settings()
    app = create_app(settings)
    return TestClient(app)

def test_create_order(client):
    """测试创建订单"""
    order_data = {
        "user_id": "user123",
        "items": [
            {"product_id": "prod_1", "quantity": 2},
            {"product_id": "prod_2", "quantity": 1}
        ]
    }
    response = client.post("/api/v1/order", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["user_id"] == "user123"
    assert len(data["items"]) == 2
    assert data["message"] == "Order created successfully"

def test_get_order(client):
    """测试获取订单"""
    # 先创建一个订单
    order_data = {
        "user_id": "user123",
        "items": [{"product_id": "prod_1", "quantity": 2}]
    }
    create_response = client.post("/api/v1/order", json=order_data)
    assert create_response.status_code == 200
    order_id = create_response.json()["id"]
    
    # 然后获取该订单
    get_response = client.get(f"/api/v1/order/{order_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == order_id
    assert data["user_id"] == "user123"
    assert data["message"] == "Order retrieved successfully"
```

## 最佳实践

1. **路由设计原则**：
   - 遵循RESTful风格
   - 使用名词复数形式表示资源集合
   - 合理使用HTTP动词

2. **数据模型设计**：
   - 充分利用Pydantic的数据验证功能
   - 设计易于生成文档的模型
   - 考虑未来可能的字段扩展

3. **错误处理**：
   - 使用FastAPI的异常处理机制
   - 提供有用的错误信息
   - 避免泄露敏感信息

4. **依赖注入**：
   - 通过容器管理服务依赖
   - 避免在路由中直接创建服务实例
   - 确保服务生命周期正确管理

5. **日志记录**：
   - 在关键操作处添加日志记录
   - 区分不同级别的日志
   - 记录重要事件和错误信息

## 总结

按照以上步骤，你就可以成功地向项目中添加一个新的HTTP服务。我们的架构设计确保了服务的一致性和可维护性，通过依赖注入模式简化了服务间的依赖关系管理。新服务会自动注册到路由系统，无需修改主应用代码。