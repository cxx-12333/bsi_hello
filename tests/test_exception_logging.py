import sys
import os
import asyncio
from unittest.mock import Mock, patch

# 添加项目路径到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.internal.server.application import Application
from app.internal.registry.consul_registry import ConsulRegistry
from app.internal.config.bootstrap import Bootstrap


def test_app_exception_logging():
    """测试应用程序中的异常日志记录"""
    print("测试应用程序中的异常日志记录...")
    
    # 创建Bootstrap实例
    bootstrap = Bootstrap()
    
    # 创建一个mock registry，模拟抛出异常的情况
    mock_registry = Mock()
    mock_registry.deregister_service.side_effect = Exception("模拟的注销异常")
    
    # 创建应用实例
    app = Application(bootstrap)
    app.registry = mock_registry
    app.registered_service_ids = ["test_service_1", "test_service_2"]
    
    # 调用注销服务方法，应该会记录异常信息
    app.deregister_services()
    
    print("应用程序异常日志记录测试完成\n")


def test_consul_exception_logging():
    """测试Consul注册中心中的异常日志记录"""
    print("测试Consul注册中心中的异常日志记录...")
    
    # 创建ConsulRegistry实例
    consul_registry = ConsulRegistry()
    
    # 使用patch模拟Consul客户端抛出异常
    with patch.object(consul_registry.client.agent.service, 'deregister') as mock_deregister:
        mock_deregister.side_effect = Exception("模拟的Consul注销异常")
        
        # 调用注销服务方法，应该会记录异常信息
        result = consul_registry.deregister_service("test_service")
        print(f"注销结果: {result}")
    
    print("Consul注册中心异常日志记录测试完成\n")


if __name__ == "__main__":
    print("开始测试异常日志记录改进...")
    test_app_exception_logging()
    test_consul_exception_logging()
    print("所有测试完成!")