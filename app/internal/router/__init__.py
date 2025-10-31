from .http_router import setup_routes
from .grpc_router import setup_grpc_services

__all__ = [
    "setup_routes",
    "setup_grpc_services"
]