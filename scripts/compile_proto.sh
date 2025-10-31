# 编译 gRPC proto 文件
protoc -I ./app/grpc_api/proto --python_out=./app/grpc_api/generated --grpc_python_out=./app/grpc_api/generated --mypy_out=./app/grpc_api/generated ./app/grpc_api/proto/*.proto

# 纯python工具
uv add grpcio-tools
# 安装 mypy-protobuf 以生成类型提示文件
uv add mypy-protobuf
python -m grpc_tools.protoc -I ./app/grpc_api/proto --python_out=./app/grpc_api/generated --grpc_python_out=./app/grpc_api/generated --mypy_out=./app/grpc_api/generated ./app/grpc_api/proto/*.proto