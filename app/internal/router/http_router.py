import uvicorn
from fastapi import FastAPI
from app.api.router_health import router as health_router
from app.internal.config.bootstrap import Bootstrap
from loguru import logger


async def start_http(app: FastAPI, container, bootstrap: Bootstrap):
    """启动HTTP服务"""
    # 添加健康检查路由
    app.include_router(health_router)
    
    # 添加用户路由
    user_router = container.api_container().user_router()
    app.include_router(user_router)
    
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=bootstrap.service.http_port, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


def register_http_services(registry, bootstrap, local_ip):
    """注册HTTP服务到注册中心"""
    http_service_name = f"{bootstrap.service.name}.http"
    http_service_id = f"{bootstrap.service.name}-http"
    
    registry.register_service(
        http_service_name, 
        http_service_id, 
        local_ip, 
        bootstrap.service.http_port, 
        "http"
    )