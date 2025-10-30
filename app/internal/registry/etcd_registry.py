from .base import RegistryClient

class EtcdRegistry(RegistryClient):
    def register_service(self, service_name, service_id, address, port, protocol="http"):
        raise NotImplementedError

    def deregister_service(self, service_id):
        raise NotImplementedError

    def discover_service(self, service_name):
        raise NotImplementedError

    def get_config(self, key):
        raise NotImplementedError

    def watch_config(self, key, callback):
        raise NotImplementedError

