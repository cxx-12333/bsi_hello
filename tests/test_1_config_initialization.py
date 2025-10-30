import unittest
from tests.common import init_config_from_consul, DEFAULT_CONSUL_ADDRESS, DEFAULT_CONSUL_TOKEN, DEFAULT_CONFIG_PATH
from app.internal.config.bootstrap import Bootstrap

# Consul连接配置 - 使用默认配置
registryAddress = DEFAULT_CONSUL_ADDRESS
registryToken = DEFAULT_CONSUL_TOKEN
configPath = DEFAULT_CONFIG_PATH


class TestConfigInitialization(unittest.TestCase):
    def test_bootstrap_config_initialization(self):
        """测试Bootstrap配置管理初始化"""
        # 初始化全局配置对象
        bootstrap = Bootstrap.get_instance()
        print(
            f"Bootstrap初始状态 - Registry: address={bootstrap.registry.address}, token={bootstrap.registry.token}, config_path={bootstrap.registry.config_path}")
        print(f"Bootstrap初始状态 - Service: name={bootstrap.service.name}, version={bootstrap.service.version}")
        print(f"Bootstrap初始状态 - OTLP: endpoint={bootstrap.otlp.endpoint}")
        print(f"Bootstrap初始状态 - Database: user={bootstrap.database.user}, host={bootstrap.database.host}")
        print(
            f"Bootstrap初始状态 - Redis: host={bootstrap.redis.host}, port={bootstrap.redis.port}, db={bootstrap.redis.db}")

        # 验证配置对象默认值
        # self.assertEqual(bootstrap.registry.address, "")
        # self.assertEqual(bootstrap.registry.token, "")
        # self.assertEqual(bootstrap.registry.config_path, "")

        # 验证服务配置默认值
        self.assertEqual(bootstrap.service.name, "bsi.hello_py")
        self.assertEqual(bootstrap.service.version, "v0.0.1")

        # 验证OTLP配置默认值
        self.assertEqual(bootstrap.otlp.endpoint, "192.168.80.94:4317")

        # 从Consul初始化配置
        success = init_config_from_consul(registryAddress, registryToken, configPath)
        self.assertTrue(success, "从Consul初始化配置应该成功")

        # 打印从Consul获取的配置值
        print(
            f"从Consul获取的Database配置: user={bootstrap.database.user}, host={bootstrap.database.host}, port={bootstrap.database.port}, database={bootstrap.database.database}")
        print(
            f"从Consul获取的Redis配置: host={bootstrap.redis.host}, port={bootstrap.redis.port}, db={bootstrap.redis.db}")
        # print(f"从Consul获取的App配置: environment={bootstrap.otlp.environment}")

        print("Bootstrap配置对象初始化测试通过")

    def test_database_config_generation(self):
        """测试数据库配置生成"""
        # 初始化全局配置对象
        bootstrap = Bootstrap.get_instance()

        # 打印数据库配置
        print(
            f"初始化后的数据库配置: user={bootstrap.database.user}, host={bootstrap.database.host}, port={bootstrap.database.port}, database={bootstrap.database.database}")

        # 生成数据库URL
        database_url = bootstrap.get_database_url()

        print(f"生成的数据库URL: {database_url}")

        # 验证生成的URL格式包含必要部分（允许额外参数）
        self.assertIn(f"{bootstrap.database.user}", database_url)
        self.assertIn(f"{bootstrap.database.host}", database_url)
        self.assertIn(f"{bootstrap.database.port}", database_url)
        self.assertIn(f"{bootstrap.database.database}", database_url)

        print("数据库配置生成测试通过")

    def test_redis_config_generation(self):
        """测试Redis配置生成"""
        # 初始化全局配置对象
        bootstrap = Bootstrap.get_instance()

        # 打印Redis配置
        print(f"初始化后的Redis配置: host={bootstrap.redis.host}, port={bootstrap.redis.port}, db={bootstrap.redis.db}")

        # 获取Redis配置字典
        redis_config = bootstrap.get_redis_config_dict()

        print(f"生成的Redis配置字典: {redis_config}")

        # 验证配置字典内容
        self.assertEqual(redis_config["host"], bootstrap.redis.host)
        self.assertEqual(redis_config["port"], bootstrap.redis.port)
        self.assertEqual(redis_config["db"], bootstrap.redis.db)

        print("Redis配置生成测试通过")


if __name__ == '__main__':
    unittest.main()