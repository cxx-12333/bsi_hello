import requests
import grpc
import time
import argparse
from app.grpc_api.generated import user_pb2, user_pb2_grpc

def test_http_service(http_port):
    """测试HTTP服务"""
    print("Testing HTTP service...")
    try:
        # 测试创建用户
        response = requests.post(
            f"http://localhost:{http_port}/api/v1/user",
            json={"name": "Test User"},
            timeout=5
        )
        print(f"HTTP create user status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("id")
            print(f"Created user with ID: {user_id}")
            
            # 测试获取用户
            response = requests.get(
                f"http://localhost:{http_port}/api/v1/user/{user_id}",
                timeout=5
            )
            print(f"HTTP get user status: {response.status_code}")
            if response.status_code == 200:
                print(f"Retrieved user: {response.json()}")
        else:
            print(f"Failed to create user: {response.text}")
    except Exception as e:
        print(f"HTTP test failed: {e}")

def test_grpc_service(grpc_port):
    """测试gRPC服务"""
    print("\nTesting gRPC service...")
    try:
        # 创建gRPC通道和存根
        channel = grpc.insecure_channel(f'localhost:{grpc_port}')
        stub = user_pb2_grpc.UserServiceStub(channel)
        
        # 测试创建用户
        request = user_pb2.CreateUserRequest(
            name="Test gRPC User"
        )
        response = stub.CreateUser(request)
        print(f"gRPC create user response: {response}")
        
        if response.id:
            # 测试获取用户
            get_request = user_pb2.UserRequest(id=response.id)
            get_response = stub.GetUser(get_request)
            print(f"gRPC get user response: {get_response}")
        
        # 关闭通道
        channel.close()
    except Exception as e:
        print(f"gRPC test failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test HTTP and gRPC services')
    parser.add_argument('--http_port', type=int, default=8003, help='HTTP service port')
    parser.add_argument('--grpc_port', type=int, default=9003, help='gRPC service port')
    args = parser.parse_args()
    
    print("Starting service tests...")
    test_http_service(args.http_port)
    test_grpc_service(args.grpc_port)
    print("Service tests completed.")