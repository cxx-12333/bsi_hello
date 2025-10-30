#!/usr/bin/env python3
"""
测试gRPC反射功能的脚本
"""

import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

def test_grpc_reflection():
    """测试gRPC反射功能"""
    print("=== 测试gRPC反射功能 ===")
    
    try:
        # 连接到gRPC服务
        channel = grpc.insecure_channel('localhost:9001')
        
        # 创建反射服务客户端
        reflection_stub = reflection_pb2_grpc.ServerReflectionStub(channel)
        
        # 发送服务列表请求
        request = reflection_pb2.ServerReflectionRequest(
            list_services=""
        )
        
        # 获取响应
        responses = reflection_stub.ServerReflectionInfo(iter([request]))
        
        for response in responses:
            if response.list_services_response:
                print("可用的gRPC服务:")
                for service in response.list_services_response.service:
                    print(f"  - {service.name}")
                return True
                
        print("未收到服务列表响应")
        return False
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'channel' in locals():
            channel.close()

if __name__ == "__main__":
    success = test_grpc_reflection()
    print(f"gRPC反射测试{'成功' if success else '失败'}")