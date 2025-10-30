#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consul注册中心测试脚本
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入公共初始化方法和默认配置
from tests.common import init_config_from_consul, parse_consul_address, DEFAULT_CONSUL_ADDRESS, DEFAULT_CONSUL_TOKEN
from app.internal.registry.consul_registry import ConsulRegistry

class TestConsulRegistry(unittest.TestCase):
    """Consul注册中心测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.consul_address = DEFAULT_CONSUL_ADDRESS
        self.service_name = "bsi/hello_py"
        self.consul_token = DEFAULT_CONSUL_TOKEN
        
        # 使用公共方法初始化Consul配置
        bootstrap, registry = init_config_from_consul(self.consul_address, self.consul_token)
        
        # 获取已初始化的registry实例
        self.registry = registry
    
    def test_consul_connection(self):
        """测试Consul连接"""
        # 这个测试主要验证能否成功创建ConsulRegistry实例
        self.assertIsInstance(self.registry, ConsulRegistry)
        # 注意：ConsulRegistry类没有address、service_name和token属性，这些信息存储在client中
        # 我们验证client的配置是否正确
        self.assertEqual(self.registry.client.token, self.consul_token)
    
    def test_config_loading(self):
        """测试配置加载"""
        import yaml
        # 使用get_config方法获取配置
        config_data = self.registry.get_config(self.service_name)
        self.assertIsNotNone(config_data)
        # 验证配置数据是字符串类型（YAML格式）
        self.assertIsInstance(config_data, str)
        
        # 解析YAML配置数据
        parsed_config = yaml.safe_load(config_data)
        
        # 验证必要的配置项存在
        self.assertIn('app_setting', parsed_config)
        self.assertIn('database', parsed_config)
        self.assertIn('redis', parsed_config)
        
        # 验证数据库配置结构
        database_config = parsed_config.get('database')
        self.assertIsNotNone(database_config)
        self.assertIn('host', database_config)
        self.assertIn('port', database_config)
        self.assertIn('user', database_config)
        self.assertIn('password', database_config)
        self.assertIn('database', database_config)
        
        # 验证Redis配置结构
        redis_config = parsed_config.get('redis')
        self.assertIsNotNone(redis_config)
        self.assertIn('host', redis_config)
        self.assertIn('port', redis_config)
        self.assertIn('db', redis_config)
        self.assertIn('password', redis_config)
    
    def test_config_loading_with_invalid_token(self):
        """测试使用无效token加载配置"""
        # 创建一个使用无效token的注册中心实例
        # 直接手动创建ConsulRegistry实例用于测试无效token情况
        consul_host, consul_port, scheme = parse_consul_address(self.consul_address)
        
        invalid_registry = ConsulRegistry(
            host=consul_host, 
            port=consul_port, 
            scheme=scheme,
            token="invalid-token"
        )

        # 使用get_config方法获取配置
        # 使用无效token会抛出ACLPermissionDenied异常，这是预期的行为
        with self.assertRaises(Exception):
            invalid_registry.get_config(self.service_name)

if __name__ == '__main__':
    unittest.main(verbosity=2)