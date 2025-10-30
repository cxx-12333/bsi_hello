import json
import yaml
from typing import Optional, Dict, Any
from ..log.logger import logger
from ..registry.consul_registry import ConsulRegistry

class RegistryConfig:
    """注册中心配置"""
    _config_map = {
        "dc": "dc",
        "address": "address",
        "token": "token",
        "config_path": "config_path",
        "local_ip": "local_ip"
    }
    
    def __init__(self):
        self.dc: str = ""
        self.address: str = "https://consul.dev.shijizhongyun.com"
        self.token: str = "3f84201a-31a2-c843-bbc0-0a45983aa7b7"
        self.config_path: str = "bsi/hello_py"
        self.local_ip: str = ""

class ServiceConfig:
    """服务配置"""
    _config_map = {
        "name": "name",
        "version": "version",
        "http_port": "http_port",
        "grpc_port": "grpc_port"
    }
    
    def __init__(self):
        self.name: str = "bsi.hello_py"
        self.version: str = "v0.0.1"
        self.http_port: int = 8001
        self.grpc_port: int = 9001

class DatabaseConfig:
    """数据库配置"""
    _config_map = {
        "user": "user",
        "password": "password",
        "host": "host",
        "port": "port",
        "database": "database"
    }
    
    def __init__(self):
        self.user: str = "root"
        self.password: str = "123456"
        self.host: str = "127.0.0.1"
        self.port: str = "3306"
        self.database: str = "testdb"

class RedisConfig:
    """Redis配置"""
    _config_map = {
        "host": "host",
        "port": "port",
        "db": "db",
        "password": "password"
    }
    
    def __init__(self):
        self.host: str = "localhost"
        self.port: int = 6379
        self.db: int = 0
        self.password: str = ""  # 添加密码属性，默认为空

class OtlpConfig:
    """OTLP配置"""
    _config_map = {
        "endpoint": "endpoint",
        "environment": "environment"
    }
    
    def __init__(self):
        self.endpoint: str = "192.168.80.94:4317"
        self.environment: str = "dev"

class Bootstrap:
    """全局配置对象，统一管理所有配置"""
    
    _instance: Optional['Bootstrap'] = None
    
    def __init__(self):
        self.registry = RegistryConfig()
        self.service = ServiceConfig()
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.otlp = OtlpConfig()
        self.is_initialized = False
    
    @classmethod
    def get_instance(cls) -> 'Bootstrap':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def init_from_consul(self, consul_registry: ConsulRegistry, config_path: str = None) -> bool:
        """从Consul初始化所有配置"""
        # 如果没有提供config_path，则使用registry中的配置路径
        if config_path is None:
            config_path = consul_registry.config_path
            
        try:
            # 从单个YAML配置中读取所有配置
            self._init_all_configs_from_yaml(consul_registry, config_path)
            
            self.is_initialized = True
            logger.info("成功从Consul初始化配置")
            return True
            
        except Exception as e:
            logger.error(f"从Consul初始化配置时发生错误: {e}")
            return False
    
    def _init_all_configs_from_yaml(self, consul_registry: ConsulRegistry, config_path: str):
        """从单个YAML配置中初始化所有配置"""
        try:
            # 从单个键读取YAML配置
            config_yaml = consul_registry.get_config(f"{config_path}")
            if config_yaml:
                # 解析YAML配置
                all_configs = yaml.safe_load(config_yaml)
                
                # 定义配置类与Bootstrap属性的映射关系
                config_mapping = {
                    "database": self.database,
                    "redis": self.redis,
                    "otlp": self.otlp,
                    "registry": self.registry,
                    "service": self.service
                }
                
                # 自动化配置赋值
                for section_name, section_config in all_configs.items():
                    if section_name in config_mapping:
                        config_obj = config_mapping[section_name]
                        # 检查配置对象是否有_config_map属性
                        config_map = getattr(config_obj, "_config_map", None)
                        if config_map:
                            # 根据_config_map自动赋值
                            for attr_name, config_key in config_map.items():
                                if config_key in section_config:
                                    setattr(config_obj, attr_name, section_config[config_key])
                            logger.info(f"{section_name.capitalize()} config updated from Consul")
                        else:
                            # 如果没有_config_map，则使用原有的手动赋值方式（向后兼容）
                            if section_name == "database":
                                self._init_database_config(consul_registry, config_path)
                            elif section_name == "redis":
                                self._init_redis_config(consul_registry, config_path)
                            elif section_name == "app_setting":
                                self._init_app_config(consul_registry, config_path)
        except Exception as e:
            logger.error(f"Failed to update configs from Consul YAML: {e}")
            raise
    
    def _init_database_config(self, consul_registry: ConsulRegistry, config_path: str):
        """初始化数据库配置 (保留此方法以保持向后兼容)"""
        try:
            db_config_json = consul_registry.get_config(f"{config_path}/database")
            if db_config_json:
                db_config = json.loads(db_config_json)
                self.database.user = db_config.get("user", self.database.user)
                self.database.password = db_config.get("password", self.database.password)
                self.database.host = db_config.get("host", self.database.host)
                self.database.port = db_config.get("port", self.database.port)
                self.database.database = db_config.get("database", self.database.database)
                logger.info("Database config updated from Consul")
        except Exception as e:
            logger.error(f"Failed to update database config from Consul: {e}")
    
    def _init_redis_config(self, consul_registry: ConsulRegistry, config_path: str):
        """初始化Redis配置 (保留此方法以保持向后兼容)"""
        try:
            redis_config_json = consul_registry.get_config(f"{config_path}/redis")
            if redis_config_json:
                redis_config = json.loads(redis_config_json)
                self.redis.host = redis_config.get("host", self.redis.host)
                self.redis.port = redis_config.get("port", self.redis.port)
                self.redis.db = redis_config.get("db", self.redis.db)
                self.redis.password = redis_config.get("password", self.redis.password)  # 添加密码字段处理
                logger.info("Redis config updated from Consul")
        except Exception as e:
            logger.error(f"Failed to update Redis config from Consul: {e}")
    
    def _init_app_config(self, consul_registry: ConsulRegistry, config_path: str):
        """初始化应用配置 (保留此方法以保持向后兼容)"""
        try:
            app_config_json = consul_registry.get_config(f"{config_path}/app_setting")
            if app_config_json:
                app_config = json.loads(app_config_json)
                self.otlp.environment = app_config.get("environment", self.otlp.environment)
                logger.info("App config updated from Consul")
        except Exception as e:
            logger.error(f"Failed to update app config from Consul: {e}")
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        # 使用_database的_config_map访问配置属性
        user = getattr(self.database, 'user', 'root')
        password = getattr(self.database, 'password', '123456')
        host = getattr(self.database, 'host', '127.0.0.1')
        port = getattr(self.database, 'port', '3306')
        database = getattr(self.database, 'database', 'testdb')
        
        return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    
    def get_redis_config_dict(self) -> Dict[str, Any]:
        """获取Redis配置字典"""
        # 使用_redis的_config_map动态生成配置字典
        config_dict = {}
        config_map = getattr(self.redis, "_config_map", None)
        if config_map:
            for attr_name, config_key in config_map.items():
                config_dict[config_key] = getattr(self.redis, attr_name)
        else:
            # 如果没有_config_map，则使用原有的方式（向后兼容）
            config_dict = {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db,
                "password": self.redis.password
            }
        return config_dict