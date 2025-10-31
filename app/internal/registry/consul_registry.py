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
        self._health_threads = {}  # 存储健康检查线程
        # 确保token也被存储以便在其他方法中使用
        self.token = token

    # -------------------- 服务注册 --------------------
    def register_service(self, service_name, service_id, address, port, protocol="http", deregister_critical_service_after="90s", ttl="30s"):
        """
        使用TTL检查注册服务，替代原来的HTTP/TCP检查
        :param service_name: 服务名称
        :param service_id: 服务ID
        :param address: 服务地址
        :param port: 服务端口
        :param protocol: 协议类型
        :param deregister_critical_service_after: 服务失效后多久注销
        :param ttl: TTL检查间隔
        """
        # 使用TTL检查替代HTTP/TCP检查，并添加deregister_critical_service_after配置
        check = consul.Check.ttl(ttl)
        # 手动添加DeregisterCriticalServiceAfter字段
        check['DeregisterCriticalServiceAfter'] = deregister_critical_service_after

        result = self.client.agent.service.register(
            name=service_name, service_id=service_id, address=address, port=port, check=check
        )
        
        if result:
            # 注册成功后立即更新一次健康状态，避免初始状态为critical
            try:
                # 使用正确的检查ID格式：service:{service_id}
                check_id = f"service:{service_id}"
                # 直接构造HTTP请求并手动传递token参数
                params = []
                if self.token:
                    params.append(('token', self.token))
                
                # 使用Consul客户端的HTTP PUT方法直接调用API
                from consul.base import CB
                self.client.http.put(
                    CB.bool(),
                    f'/v1/agent/check/pass/{check_id}',
                    params=params
                )
                logger.info(f"服务 {service_id} 注册成功并已更新初始健康状态")
            except Exception as e:
                logger.error(f"服务 {service_id} 注册后更新初始健康状态失败: {e}")
        else:
            logger.error(f"服务 {service_id} 注册失败")
            return False
        
        # 启动健康状态更新线程
        self._start_health_updates(service_id, ttl)
        return result

    def _start_health_updates(self, service_id, ttl):
        """
        启动定期更新健康状态的线程
        :param service_id: 服务ID
        :param ttl: TTL时间
        """
        def _update_health():
            # 计算更新间隔，设置为TTL的一半以确保及时更新
            interval = self._parse_duration(ttl) / 2.0
            # 设置最大重试次数
            max_retries = 5
            retry_count = 0
            
            # 使用正确的检查ID格式：service:{service_id}
            check_id = f"service:{service_id}"
            
            logger.info(f"开始健康状态更新线程，服务ID: {service_id}, 检查ID: {check_id}, 更新间隔: {interval}秒")
            
            while True:
                try:
                    # 直接构造HTTP请求并手动传递token参数
                    params = []
                    if self.token:
                        params.append(('token', self.token))
                    
                    # 使用Consul客户端的HTTP PUT方法直接调用API
                    from consul.base import CB
                    self.client.http.put(
                        CB.bool(),
                        f'/v1/agent/check/pass/{check_id}',
                        params=params
                    )
                    
                    logger.debug(f"服务 {service_id} 健康状态已更新")
                    # 重置重试计数
                    retry_count = 0
                    
                    # 记录成功更新健康状态的日志
                    # logger.info(f"服务 {service_id} 健康状态更新成功")
                except Exception as e:
                    retry_count += 1
                    logger.error(f"更新服务 {service_id} 健康状态失败 (尝试 {retry_count}/{max_retries}): {e}")
                    
                    # 如果达到最大重试次数，记录警告但继续尝试
                    if retry_count >= max_retries:
                        logger.warning(f"服务 {service_id} 健康状态更新连续失败 {max_retries} 次，将继续尝试")
                        retry_count = 0  # 重置计数，避免日志重复
                
                # 睡眠指定间隔
                time.sleep(interval)
        
        # 启动健康检查线程
        thread_name = f"consul-health-{service_id}"
        thread = threading.Thread(target=_update_health, daemon=True, name=thread_name)
        thread.start()
        self._health_threads[service_id] = thread
        logger.info(f"已启动服务 {service_id} 的健康状态更新线程 [{thread_name}]，更新间隔: {self._parse_duration(ttl)/2.0}秒")

    def _parse_duration(self, duration_str):
        """
        解析持续时间字符串为秒数
        :param duration_str: 持续时间字符串，如 "30s", "1m"
        :return: 秒数
        """
        if duration_str.endswith('s'):
            return float(duration_str[:-1])
        elif duration_str.endswith('m'):
            return float(duration_str[:-1]) * 60
        elif duration_str.endswith('h'):
            return float(duration_str[:-1]) * 3600
        else:
            # 默认认为是秒
            return float(duration_str)

    def deregister_service(self, service_id):
        try:
            # 使用Consul Python库的正确API调用方式
            result = self.client.agent.service.deregister(service_id)
            
            # 停止健康状态更新线程
            if service_id in self._health_threads:
                # 线程是守护线程，不需要显式停止，从字典中移除引用即可
                del self._health_threads[service_id]
            
            if result:
                logger.info(f"成功注销服务: {service_id}")
            else:
                # 当result为False时，尝试获取更多关于服务状态的信息
                try:
                    # 尝试查询服务是否存在来提供更多上下文信息
                    services = self.client.agent.services()
                    if service_id in services:
                        logger.error(f"注销服务失败: {service_id}，服务仍然存在于Consul中")
                    else:
                        logger.error(f"注销服务失败: {service_id}，服务可能已被删除或不存在")
                except Exception as query_e:
                    logger.error(f"注销服务失败: {service_id}，无法查询服务状态: {str(query_e)}")
            return result
        except Exception as e:
            # 记录详细的错误信息，包括异常类型和消息
            logger.error(f"注销服务 {service_id} 失败: {str(e)}")
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
