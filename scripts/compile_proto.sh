# 编译 gRPC proto 文件
protoc -I ./app/grpc_api/proto --python_out=./app/grpc_api/generated --grpc_python_out=./app/grpc_api/generated   ./app/grpc_api/proto/*.proto

# 纯python工具
uv add grpcio-tools
python -m grpc_tools.protoc -I ./app/grpc_api/proto --python_out=./app/grpc_api/generated --grpc_python_out=./app/grpc_api/generated ./app/grpc_api/proto/*.proto