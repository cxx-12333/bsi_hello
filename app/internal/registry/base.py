from abc import ABC, abstractmethod

class RegistryClient(ABC):
    """注册中心抽象接口"""

    @abstractmethod
    def register_service(self, service_name: str, service_id: str, address: str, port: int, protocol: str):
        """服务注册"""

    @abstractmethod
    def deregister_service(self, service_id: str):
        """服务注销"""

    @abstractmethod
    def discover_service(self, service_name: str) -> list:
        """服务发现，返回可用节点列表"""

    @abstractmethod
    def get_config(self, key: str):
        """读取配置"""

    @abstractmethod
    def watch_config(self, key: str, callback):
        """监听配置变化"""
