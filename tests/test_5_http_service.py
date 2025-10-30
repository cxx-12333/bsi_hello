#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP服务测试脚本
"""

import unittest
import requests
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestHTTPService(unittest.TestCase):
    """HTTP服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.base_url = "http://localhost:8001"

    
    def test_http_service_health_check(self):
        """测试HTTP服务健康检查"""
        try:
            # 测试健康检查端点
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # 验证响应内容
            data = response.json()
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'ok')
        except requests.exceptions.ConnectionError:
            self.fail("无法连接到HTTP服务，请确保服务已启动")
        except requests.exceptions.Timeout:
            self.fail("HTTP服务健康检查超时")
    
    def test_http_service_user_endpoints(self):
        """测试HTTP服务用户相关端点"""
        # 测试创建用户
        user_data = {"name": "Test User"}
        try:
            response = requests.post(
                f"{self.base_url}/user", 
                json=user_data, 
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            
            # 验证响应内容
            data = response.json()
            self.assertIn('id', data)
            self.assertIn('name', data)
            self.assertEqual(data['name'], 'Test User')
            
            # 保存用户ID用于后续测试
            user_id = data['id']
            
            # 测试获取用户
            response = requests.get(f"{self.base_url}/user/{user_id}", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # 验证响应内容
            data = response.json()
            self.assertIn('id', data)
            self.assertIn('name', data)
            self.assertEqual(data['id'], user_id)
            self.assertEqual(data['name'], 'Test User')
        except requests.exceptions.ConnectionError:
            self.fail("无法连接到HTTP服务，请确保服务已启动")
        except requests.exceptions.Timeout:
            self.fail("HTTP服务用户端点测试超时")
    
    def test_http_service_nonexistent_user(self):
        """测试HTTP服务获取不存在的用户"""
        try:
            # 测试获取不存在的用户
            response = requests.get(f"{self.base_url}/user/999999", timeout=5)
            # 根据API设计，可能返回404或其他状态码
            self.assertIn(response.status_code, [404, 200])
            
            # 如果返回200，验证响应内容为空或表示用户不存在
            if response.status_code == 200:
                data = response.json()
                # 根据实际实现调整验证方式
                self.assertIsNone(data)
        except requests.exceptions.ConnectionError:
            self.fail("无法连接到HTTP服务，请确保服务已启动")
        except requests.exceptions.Timeout:
            self.fail("HTTP服务获取不存在用户测试超时")

if __name__ == '__main__':
    unittest.main(verbosity=2)