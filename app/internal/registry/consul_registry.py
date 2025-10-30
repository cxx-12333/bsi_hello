import consul
import threading
import time
import json
from .base import RegistryClient
from ..log.logger import logger

class ConsulRegistry(RegistryClient):
    def __init__(self, host="127.0.0.1", port=8500, scheme="http", verify=True, token=None):
        self.client = consul.Consul(host=host, port=port, scheme=scheme, verify=verify, token=token)
        self._watch_threads = {}
        self._config_cache = {}

    # -------------------- 服务注册 --------------------
    def register_service(self, service_name, service_id, address, port, protocol="http", deregister_critical_service_after="10s"):
        if protocol == "http":
            check = consul.Check.http(f"http://{address}:{port}/health", interval="10s", deregister=deregister_critical_service_after)
        else:
            # 对于gRPC服务，使用TCP检查
            check = consul.Check.tcp(address, port, interval="10s", deregister=deregister_critical_service_after)
        self.client.agent.service.register(
            name=service_name, service_id=service_id, address=address, port=port, check=check
        )

    def deregister_service(self, service_id):
        try:
            # 使用Consul Python库的正确API调用方式
            # 通过params传递token参数
            params = []
            if self.client.token:
                params.append(('token', self.client.token))
            
            # 调用Consul库的deregister方法并传递参数
            result = self.client.agent.service.deregister(service_id)
            
            if result:
                logger.info(f"成功注销服务: {service_id}")
            else:
                logger.info(f"注销服务失败: {service_id}")
            return result
        except Exception as e:
            logger.error(f"注销服务 {service_id} 失败: {e}")
            return False

    # -------------------- 服务发现 --------------------
    def discover_service(self, service_name):
        _, services = self.client.catalog.service(service_name)
        nodes = [{"Address": s["ServiceAddress"], "Port": s["ServicePort"]} for s in services]
        return nodes

    # -------------------- 配置读取 --------------------
    def get_config(self, key):
        # 先从缓存获取
        if key in self._config_cache:
            return self._config_cache[key]
        
        index, data = self.client.kv.get(key)
        value = data["Value"].decode() if data and data["Value"] else None
        
        # 缓存结果
        self._config_cache[key] = value
        return value

    def set_config(self, key, value):
        """设置配置值"""
        self.client.kv.put(key, value)
        # 更新缓存
        self._config_cache[key] = value

    def watch_config(self, key, callback, interval=10):
        def _watch():
            last_value = None
            while True:
                try:
                    value = self.get_config(key)
                    if value != last_value:
                        last_value = value
                        callback(value)
                except Exception as e:
                    logger.error(f"Error watching config {key}: {e}")
                time.sleep(interval)

        t = threading.Thread(target=_watch, daemon=True)
        t.start()
        self._watch_threads[key] = t

    def get_configs_by_prefix(self, prefix):
        """根据前缀获取多个配置"""
        index, data = self.client.kv.get(prefix, recurse=True)
        configs = {}
        if data:
            for item in data:
                key = item["Key"]
                value = item["Value"].decode() if item["Value"] else None
                configs[key] = value
        return configs
