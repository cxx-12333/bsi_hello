import grpc
from grpc_reflection.v1alpha import reflection
from app.grpc_api.generated import user_pb2, user_pb2_grpc
from app.internal.config.bootstrap import Bootstrap
from loguru import logger


async def start_grpc(container, bootstrap: Bootstrap):
    """启动gRPC服务"""
    server = grpc.aio.server()
    
    # 添加用户服务
    user_service_grpc = container.grpc_container.user_service_grpc()
    user_pb2_grpc.add_UserServiceServicer_to_server(user_service_grpc, server)
    
    # 启用gRPC反射服务
    SERVICE_NAMES = (
        user_pb2.DESCRIPTOR.services_by_name['UserService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    
    server.add_insecure_port(f"[::]:{bootstrap.service.grpc_port}")
    await server.start()
    logger.info(f"gRPC server running on port {bootstrap.service.grpc_port}")
    
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        await server.stop(None)


def register_grpc_services(registry, bootstrap, local_ip):
    """注册gRPC服务到注册中心"""
    grpc_service_name = f"{bootstrap.service.name}.grpc"
    grpc_service_id = f"{bootstrap.service.name}-grpc"
    
    registry.register_service(
        grpc_service_name, 
        grpc_service_id, 
        local_ip, 
        bootstrap.service.grpc_port, 
        "grpc"
    )