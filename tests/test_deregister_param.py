#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.internal.registry.consul_registry import ConsulRegistry
from unittest.mock import Mock, patch

def test_deregister_critical_service_after_parameter():
    """测试deregister_critical_service_after参数是否正确传递"""
    # 创建ConsulRegistry实例
    registry = ConsulRegistry()
    
    # 使用mock来模拟consul client
    with patch.object(registry.client.agent.service, 'register') as mock_register:
        mock_register.return_value = True
        
        # 调用register_service方法
        registry.register_service(
            service_name="test-service",
            service_id="test-service-id",
            address="127.0.0.1",
            port=8000,
            protocol="http",
            deregister_critical_service_after="90s",
            ttl="30s"
        )
        
        # 验证register方法被正确调用，包括deregister_critical_service_after参数
        mock_register.assert_called_once_with(
            name="test-service",
            service_id="test-service-id",
            address="127.0.0.1",
            port=8000,
            check={
                'ttl': '30s',
                'DeregisterCriticalServiceAfter': '90s'
            }
        )
        
        print("测试通过: deregister_critical_service_after 参数已正确传递")

if __name__ == "__main__":
    test_deregister_critical_service_after_parameter()