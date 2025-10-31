# 新增gRPC服务指南（动态服务发现模式）

本文档介绍了如何在现有项目中新增一个gRPC服务。我们将以订单服务(OrderService)为例，展示完整的添加过程。

## 概述

我们的gRPC服务架构采用动态服务发现模式，这意味着当你添加一个新的gRPC服务时，大部分配置会自动生效，你只需要关注业务逻辑的实现。

## 优势

1. **自动发现**：新增服务后，系统会自动识别并注册
2. **低耦合**：服务之间松耦合，易于维护和扩展
3. **统一管理**：通过依赖注入容器统一管理服务依赖关系

## 完整步骤

### 步骤1：定义Proto文件

首先需要定义你的服务接口。创建一个新的proto文件，例如`app/grpc_api/proto/order.proto`：

```protobuf
syntax = "proto3";

package order;

// 订单服务
service OrderService {
  // 创建订单
  rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse);
}

// 创建订单请求
message CreateOrderRequest {
  string user_id = 1;
  repeated OrderItem items = 2;
}

// 订单项
message OrderItem {
  string product_id = 1;
  int32 quantity = 2;
}

// 创建订单响应
message CreateOrderResponse {
  string order_id = 1;
  string status = 2;
}
```

### 步骤2：编译Proto文件

运行以下命令编译proto文件：

```bash
python -m grpc_tools.protoc -I./app/grpc_api/proto \
  --python_out=./app/grpc_api/generated \
  --grpc_python_out=./app/grpc_api/generated \
  ./app/grpc_api/proto/order.proto
```

### 步骤3：创建服务接口

创建服务接口类`app/core/order_service.py`：

```python
# -*- coding: utf-8 -*-
"""
订单服务接口
"""

class OrderService:
    """订单服务接口"""
    
    def __init__(self, db_session_factory):
        """
        初始化订单服务
        
        Args:
            db_session_factory: 数据库会话工厂
        """
        self.db_session_factory = db_session_factory
    
    def create_order(self, user_id: str, items: list) -> dict:
        """
        创建订单
        
        Args:
            user_id: 用户ID
            items: 订单项列表
            
        Returns:
            dict: 包含订单ID和状态的字典
        """
        # 实现创建订单的业务逻辑
        # 这里只是一个示例，实际实现应包含数据库操作等
        order_id = f"order_{user_id}_{len(items)}"
        return {
            "order_id": order_id,
            "status": "created"
        }
```

### 步骤4：实现gRPC服务端

创建gRPC服务实现类`app/grpc_api/server.py`：

```python
# 在文件中添加OrderServiceGrpc类

class OrderServiceGrpc:
    """订单gRPC服务实现"""
    
    def __init__(self, order_service):
        """
        初始化订单gRPC服务
        
        Args:
            order_service: 订单服务实例
        """
        self.order_service = order_service
    
    def CreateOrder(self, request, context):
        """
        创建订单
        
        Args:
            request: CreateOrderRequest请求对象
            context: gRPC上下文
            
        Returns:
            CreateOrderResponse响应对象
        """
        # 将请求转换为服务方法参数
        items = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in request.items
        ]
        
        # 调用服务方法
        result = self.order_service.create_order(request.user_id, items)
        
        # 构造响应对象
        from app.grpc_api.generated import order_pb2
        return order_pb2.CreateOrderResponse(
            order_id=result["order_id"],
            status=result["status"]
        )
```

### 步骤5：更新服务容器

在`app/containers/service_container.py`中添加订单服务的工厂方法：

```python
# 添加到ServiceContainer类中

# OrderService工厂
order_service = providers.Factory(
    OrderService,
    db_session_factory=data_access_container.db_session.provider
)
```

### 步骤6：更新gRPC容器

在`app/containers/grpc_container.py`中添加订单gRPC服务的工厂方法，并更新`get_all_grpc_services`方法：

```python
# 添加到GrpcContainer类中

# OrderServiceGrpc工厂
order_service_grpc = providers.Factory(
    OrderServiceGrpc,
    order_service=service_container.order_service
)

# 更新get_all_grpc_services方法
def get_all_grpc_services(self):
    """
    获取所有可用的gRPC服务实例
    用于自动服务发现
    """
    services = {}
    
    # 检查并添加用户服务
    if hasattr(self, 'user_service_grpc'):
        try:
            services['user_service_grpc'] = self.user_service_grpc()
        except Exception as e:
            # 如果服务初始化失败，记录日志但不中断整个过程
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize user_service_grpc: {e}")
    
    # 检查并添加订单服务
    if hasattr(self, 'order_service_grpc'):
        try:
            services['order_service_grpc'] = self.order_service_grpc()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize order_service_grpc: {e}")
    
    # 检查并添加产品服务
    if hasattr(self, 'product_service_grpc'):
        try:
            services['product_service_grpc'] = self.product_service_grpc()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize product_service_grpc: {e}")
    
    return services
```

### 步骤7：更新gRPC路由器

在`app/internal/router/grpc_router.py`中更新服务处理器映射：

```python
# 更新setup_grpc_services_with_mapping函数中的service_handlers

# 服务处理器映射
service_handlers = {
    'user_service_grpc': {
        'adder': user_pb2_grpc.add_UserServiceServicer_to_server,
        'instance': service_mapping.get('user_service_grpc')
    },
    'order_service_grpc': {
        'adder': order_pb2_grpc.add_OrderServiceServicer_to_server,
        'instance': service_mapping.get('order_service_grpc')
    },
    'product_service_grpc': {
        'adder': product_pb2_grpc.add_ProductServiceServicer_to_server,
        'instance': service_mapping.get('product_service_grpc')
    },
    'health_servicer': {
        'adder': health_pb2_grpc.add_HealthServicer_to_server,
        'instance': service_mapping.get('health_servicer')
    }
}
```

## 测试验证

添加完服务后，你可以编写简单的测试来验证服务是否正常工作：

```python
# test_order_service.py

import unittest
from app.containers.application_container import ApplicationContainer

class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.app_container = ApplicationContainer()
    
    def test_order_service_creation(self):
        """测试订单服务是否能正确创建"""
        # 获取订单服务
        order_service = self.app_container.service_container.order_service()
        
        # 测试创建订单功能
        items = [{"product_id": "prod_1", "quantity": 2}]
        result = order_service.create_order("user_123", items)
        
        # 验证结果
        self.assertIn("order_id", result)
        self.assertEqual(result["status"], "created")

if __name__ == '__main__':
    unittest.main()
```

## 最佳实践

1. **服务命名规范**：
   - Proto服务名使用PascalCase（如`OrderService`）
   - 方法名使用CamelCase（如`createOrder`）
   - gRPC实现类命名为`{ServiceName}Grpc`

2. **错误处理**：
   - 在gRPC服务实现中妥善处理异常
   - 使用适当的gRPC状态码返回错误信息

3. **日志记录**：
   - 在关键操作处添加日志记录
   - 区分不同级别的日志（DEBUG/INFO/WARNING/ERROR）

4. **服务发现配置**：
   - 确保在`get_all_grpc_services`方法中添加新服务的初始化逻辑
   - 添加适当的异常处理以避免单个服务故障影响整体服务启动

## 总结

按照以上步骤，你就可以成功地向项目中添加一个新的gRPC服务。由于我们采用了动态服务发现机制，大部分配置都会自动生效，你只需要专注于业务逻辑的实现即可。