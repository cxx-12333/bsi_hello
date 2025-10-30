import argparse
import asyncio
import signal
import socket
import sys
from urllib.parse import urlparse
from fastapi import FastAPI
from app.api.router_health import router as health_router
from app.internal.log.logger import init_logger
from app.internal.otel.tracing import setup_otel
from app.internal.registry.consul_registry import ConsulRegistry
from app.grpc_api.server import UserServiceGrpc
from app.grpc_api.generated import user_pb2_grpc
from app.internal.config.bootstrap import Bootstrap
from loguru import logger

# -------------------- 全局变量 --------------------
exit_event = None
http_task = None
grpc_task = None

# -------------------- 获取本机IP地址 --------------------
def get_local_ip():
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个远程地址（不会实际发送数据）
        s.connect(("8.8.8.8", 80))
        # 获取socket的本地地址
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # 如果无法获取，则回退到默认地址
        return "127.0.0.1"

# -------------------- 信号处理 --------------------
def setup_signal_handlers():
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}, 开始优雅关闭...")
        if exit_event:
            exit_event.set()
    
    # 注册SIGINT (Ctrl+C) 和 SIGTERM (kill) 信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def shutdown():
    """关闭服务"""
    global http_task, grpc_task
    
    # 取消任务
    if http_task and not http_task.done():
        http_task.cancel()
    if grpc_task and not grpc_task.done():
        grpc_task.cancel()
    
    # 注销服务
    http_service_id = f"{bootstrap.service.name}-http"
    grpc_service_id = f"{bootstrap.service.name}-grpc"
    registry.deregister_service(http_service_id)
    registry.deregister_service(grpc_service_id)

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

# -------------------- Hello Service --------------------
app = FastAPI(title=bootstrap.service.name, version=bootstrap.service.version)
app.include_router(health_router)

# -------------------- 日志 --------------------
init_logger()

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

# 注册服务
def register_services():
    local_ip = bootstrap.registry.local_ip if bootstrap.registry.local_ip else get_local_ip()
    http_service_name = f"{bootstrap.service.name}.http"
    grpc_service_name = f"{bootstrap.service.name}.grpc"
    http_service_id = f"{bootstrap.service.name}-http"
    grpc_service_id = f"{bootstrap.service.name}-grpc"
    
    registry.register_service(http_service_name, http_service_id, local_ip, bootstrap.service.http_port, "http")
    registry.register_service(grpc_service_name, grpc_service_id, local_ip, bootstrap.service.grpc_port, "grpc")

def on_config_change(value):
    logger.info("配置更新: {}", value)

# 监听配置变化
registry.watch_config(bootstrap.registry.config_path, on_config_change)

# -------------------- gRPC 服务 --------------------
async def start_grpc(container):
    import grpc
    from grpc_reflection.v1alpha import reflection
    from app.grpc_api.generated import user_pb2, user_pb2_grpc
    server = grpc.aio.server()
    # 修复：正确调用依赖注入容器中的服务
    user_service_grpc = container.grpc_container.user_service_grpc()
    user_pb2_grpc.add_UserServiceServicer_to_server(user_service_grpc, server)
    
    # 启用gRPC反射服务
    SERVICE_NAMES = (
        user_pb2.DESCRIPTOR.services_by_name['UserService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    
    server.add_insecure_port(f"[::]:{args.grpc_port}")
    await server.start()
    logger.info(f"gRPC server running on port {args.grpc_port}")
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        await server.stop(None)

# -------------------- HTTP 服务 --------------------
async def start_http(container):
    import uvicorn
    # 添加用户路由
    # 修复：正确调用依赖注入容器中的路由
    user_router = container.api_container().user_router()
    app.include_router(user_router)
    config = uvicorn.Config(app, host="0.0.0.0", port=args.http_port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

# -------------------- 主程序 --------------------
async def main():
    global exit_event, http_task, grpc_task
    
    # 初始化退出事件
    exit_event = asyncio.Event()
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 设置OpenTelemetry
    setup_otel(
        service_name=bootstrap.service.name,
        service_version=bootstrap.service.version,
        environment=bootstrap.otlp.environment,
        otlp_endpoint=bootstrap.otlp.endpoint,
        fastapi_app=app,
    )
    
    # 一次性初始化所有配置
    if not bootstrap.init_from_consul(registry, bootstrap.registry.config_path):
        logger.error("Failed to initialize configurations from Consul")
        return
    
    # 初始化Redis客户端（使用已初始化的全局配置）
    from app.internal.lock.red_lock import init_redis_client
    await init_redis_client()
    
    # 注册服务
    register_services()
    
    # 初始化依赖注入容器
    from app.containers.application_container import ApplicationContainer
    container = ApplicationContainer()
    
    # 创建任务并发运行HTTP和gRPC服务
    http_task = asyncio.create_task(start_http(container))
    grpc_task = asyncio.create_task(start_grpc(container))
    exit_event_task = asyncio.create_task(exit_event.wait())
    
    try:
        # 等待任一任务完成或接收到退出信号
        done, pending = await asyncio.wait(
            [http_task, grpc_task, exit_event_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # 检查是否是退出信号触发的
        exit_triggered = exit_event_task in done
        if exit_triggered:
            logger.info("接收到退出信号，开始优雅关闭...")
        
        # 取消未完成的任务
        tasks_to_cancel = [task for task in pending if task != exit_event_task]
        for task in tasks_to_cancel:
            task.cancel()
            
        # 等待被取消的任务完成
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            
    except asyncio.CancelledError:
        logger.info("主任务被取消")
    finally:
        # 注销服务
        shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)
