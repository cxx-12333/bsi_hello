# BSI Hello Python 微服务项目

## 项目简介

BSI Hello Python 是一个基于微服务架构的Python项目，实现了用户管理功能。项目采用现代化的技术栈，包括FastAPI、gRPC、Consul、SQLAlchemy等，展示了如何构建一个完整的微服务系统。

## 技术栈

- **核心框架**: Python 3.12+
- **Web框架**: FastAPI
- **RPC框架**: gRPC
- **服务发现**: Consul
- **数据库**: SQLAlchemy (支持MySQL/PostgreSQL)
- **缓存**: Redis
- **依赖注入**: dependency-injector
- **日志**: loguru
- **配置管理**: Consul KV存储
- **监控追踪**: OpenTelemetry
- **异步支持**: asyncio
- **ORM**: SQLAlchemy 2.0

## 项目目录结构

```
bsi_hello/
├── app/                          # 应用核心代码
│   ├── api/                      # HTTP API路由
│   │   ├── router_health.py      # 健康检查路由
│   │   └── router_user.py        # 用户相关路由
│   ├── containers/               # 依赖注入容器
│   │   ├── api_container.py      # API容器
│   │   ├── application_container.py  # 应用容器
│   │   ├── data_access_container.py  # 数据访问容器
│   │   ├── grpc_container.py     # gRPC容器
│   │   ├── root_container.py     # 根容器
│   │   └── service_container.py  # 服务容器
│   ├── core/                     # 核心业务逻辑
│   │   ├── interfaces/           # 接口定义
│   │   └── user_service.py       # 用户服务实现
│   ├── db/                       # 数据库相关
│   │   ├── migrations/           # 数据库迁移文件
│   │   ├── models.py             # 数据模型定义
│   │   └── session.py            # 数据库会话管理
│   ├── grpc_api/                 # gRPC API
│   │   ├── generated/            # 自动生成的gRPC代码
│   │   ├── proto/                # protobuf定义文件
│   │   └── server.py             # gRPC服务端实现
│   ├── internal/                 # 内部模块
│   │   ├── client/               # gRPC客户端
│   │   ├── config/               # 配置管理
│   │   ├── lock/                 # 分布式锁
│   │   ├── log/                  # 日志配置
│   │   ├── otel/                 # OpenTelemetry追踪
│   │   └── registry/             # 服务注册发现
│   └── main.py                   # 应用入口
├── configs/                      # 配置文件
│   └── consul_config.yaml        # Consul配置文件
├── consul/                       # Consul本地开发环境
├── docs/                         # 文档
├── scripts/                      # 脚本文件
│   ├── compile_proto.sh
│   ├── init_consul_config.py
│   ├── init_alembic.py           # Alembic初始化脚本
│   ├── run_migrations.sh         # 数据库迁移脚本 (Linux/macOS)
│   ├── run_migrations.bat        # 数据库迁移脚本 (Windows)
│   └── start_app.py
├── tests/                        # 测试文件
│   ├── test_1_config_initialization.py      # 配置初始化测试
│   ├── test_2_consul_registry.py           # Consul注册中心测试
│   ├── test_3_database_redis_initialization.py  # 数据库和Redis初始化测试
│   ├── test_4_dependency_injection.py       # 依赖注入测试
│   ├── test_5_http_service.py              # HTTP服务测试
│   ├── test_6_grpc_service.py              # gRPC服务测试
│   └── test_7_multi_service_grpc_client.py  # 多服务gRPC客户端测试
├── pyproject.toml                # 项目依赖配置
└── README.md                     # 项目说明文档
```

## 测试脚本运行说明

项目包含一系列测试脚本，用于验证各个组件的功能。以下按顺序说明每个测试脚本的内容和运行方法：

## 数据库迁移 (Alembic)

项目使用Alembic进行数据库迁移管理。Alembic是一个轻量级的数据库迁移工具，与SQLAlchemy配合使用。

### 迁移脚本位置

迁移脚本位于 `app/db/migrations` 目录中，包含以下文件：
- `env.py`: Alembic环境配置文件
- `script.py.mako`: 迁移脚本模板
- `versions/`: 存放具体的迁移脚本

### 运行迁移

使用提供的脚本执行数据库迁移（推荐方式）：

```bash
# Linux/macOS
./scripts/run_migrations.sh

# Windows (PowerShell)
.\scripts\run_migrations.bat
```

这些脚本会自动初始化Alembic环境变量，然后执行迁移命令。

或者直接使用Alembic命令（需要手动设置环境变量）：

```bash
# 先初始化Alembic环境变量
python scripts/init_alembic.py

# 生成新的迁移脚本
alembic revision --autogenerate -m "描述迁移内容"

# 查看当前迁移状态
alembic current

# 升级到最新版本
alembic upgrade head

# 执行特定版本的迁移
alembic upgrade <revision_id>

# 回滚到上一个版本
alembic downgrade -1

```

### 初始化Alembic（如遇到问题）

如果遇到Alembic初始化问题，可以使用以下脚本：

```bash
python scripts/init_alembic.py
```

然后再执行Alembic命令。

### 注意事项

1. 确保在项目根目录运行迁移命令
2. 数据库配置通过Consul获取，确保Consul服务正常运行
3. 首次运行需要先执行 `alembic upgrade head` 创建表结构

### Test 1: 配置初始化测试

测试配置系统的初始化功能，包括Bootstrap配置、数据库配置和Redis配置的生成。

```bash
python -m unittest tests.test_1_config_initialization
```

### Test 2: Consul注册中心测试

测试Consul注册中心的连接、配置加载和异常处理功能。

```bash
python -m unittest tests.test_2_consul_registry
```

### Test 3: 数据库和Redis初始化测试

测试数据库引擎和Redis客户端的初始化及连接功能。

```bash
python -m unittest tests.test_3_database_redis_initialization
```

### Test 4: 依赖注入测试

测试依赖注入容器的创建和服务注入功能。

```bash
python -m unittest tests.test_4_dependency_injection
```

### Test 5: HTTP服务测试

测试HTTP服务的健康检查和用户相关端点功能。

```bash
python -m unittest tests.test_5_http_service
```

### Test 6: gRPC服务测试

测试gRPC服务的连接和用户服务功能。

```bash
python -m unittest tests.test_6_grpc_service
```

### Test 7: 多服务gRPC客户端测试

测试多服务gRPC客户端的连接和服务调用功能。

```bash
python -m unittest tests.test_7_multi_service_grpc_client
```

### 运行所有测试

```bash
python -m unittest discover tests
```

或者按顺序运行所有测试：

```bash
python -m unittest tests.test_1_config_initialization tests.test_2_consul_registry tests.test_3_database_redis_initialization tests.test_4_dependency_injection tests.test_5_http_service tests.test_6_grpc_service tests.test_7_multi_service_grpc_client
```

## 依赖注入顺序

项目采用分层依赖注入架构，各层之间的依赖关系如下：

### 1. 根容器 (Root Container)
- **Bootstrap**: 全局配置单例，提供应用的基础配置
- **ConsulRegistry**: Consul注册中心单例，提供服务注册发现功能

### 2. 数据访问容器 (Data Access Container)
- **Database Session**: 数据库会话工厂，依赖Bootstrap配置中的数据库信息

### 3. 服务容器 (Service Container)
- **UserService**: 用户服务实现，依赖数据库会话工厂

### 4. API容器 (API Container)
- **User Router**: 用户HTTP路由，依赖UserService

### 5. gRPC容器 (gRPC Container)
- **UserServiceGrpc**: gRPC服务端实现，依赖UserService

### 6. 应用容器 (Application Container)
- 整合所有容器，提供统一的依赖注入入口
- 包含RootContainer、DataAccessContainer、ServiceContainer、ApiContainer、GrpcContainer

### 7. 客户端容器 (Client Container)
- **MultiServiceGrpcClient**: 多服务gRPC客户端，依赖Bootstrap和ConsulRegistry
- **UserServiceClient**: 用户服务客户端，依赖MultiServiceGrpcClient
- **NotificationServiceClient**: 通知服务客户端，依赖MultiServiceGrpcClient

依赖注入的顺序遵循从基础设施层到应用层的原则，确保各组件能够正确获取其依赖项。

