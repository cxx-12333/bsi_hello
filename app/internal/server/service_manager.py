#!/usr/bin/env python3
"""
服务管理器，用于自动收集gRPC服务名称
"""

import functools
from typing import List, Callable, Any

# 导入gRPC生成的模块
from app.grpc_api.generated import user_pb2_grpc
from grpc_health.v1 import health_pb2_grpc

# 全局列表用于存储已注册的服务名称
registered_service_names: List[str] = []


def collect_service_name(add_function: Callable) -> Callable:
    """
    装饰器，用于收集服务名称
    
    Args:
        add_function: add_*_to_server函数
        
    Returns:
        包装后的函数
    """
    @functools.wraps(add_function)
    def wrapper(servicer: Any, server: Any) -> Any:
        # 执行原始的注册函数
        result = add_function(servicer, server)
        
        # 从函数中提取服务名称
        service_name = _extract_service_name(add_function)
        
        # 将服务名称添加到全局列表
        if service_name and service_name not in registered_service_names:
            registered_service_names.append(service_name)
            print(f"自动收集服务名称: {service_name}")
        
        return result
    
    return wrapper


def _extract_service_name(add_function: Callable) -> str:
    """
    从add_*_to_server函数中提取服务名称
    
    Args:
        add_function: add_*_to_server函数
        
    Returns:
        服务名称
    """
    service_name = None
    
    # 方法1: 从函数的字节码常量中提取
    if hasattr(add_function, '__code__'):
        consts = add_function.__code__.co_consts
        for const in consts:
            if isinstance(const, str) and '.' in const and not const.startswith('<') and not const.endswith('>'):
                service_name = const
                break
    
    # 如果方法1没有找到，尝试其他方法
    if not service_name:
        # 方法2: 从函数名推断(这是一种备选方案)
        func_name = add_function.__name__
        if func_name.startswith('add_') and func_name.endswith('_to_server'):
            # 提取服务名称部分
            service_part = func_name[4:-9]  # 移除 "add_" 和 "_to_server"
            # 这里需要根据实际情况调整命名规则
            # 例如: add_UserServiceServicer_to_server -> user.UserService
            # 这种方法不够可靠，所以仅作为备选
            
            # 简单处理，实际项目中可能需要更复杂的映射规则
            if service_part.endswith('Servicer'):
                service_part = service_part[:-8]  # 移除 "Servicer"
            
            # 这里假设服务名称遵循某种约定
            # 在实际项目中，可能需要维护一个映射表
            service_name = f"unknown.{service_part}"
    
    return service_name





def get_registered_service_names() -> List[str]:
    """
    获取所有已注册的服务名称
    
    Returns:
        服务名称列表
    """
    return registered_service_names.copy()


def clear_registered_service_names() -> None:
    """
    清空已注册的服务名称列表
    """
    registered_service_names.clear()


# 创建一个字典来存储动态生成的装饰器实例
_collected_add_functions = {}

def get_collected_add_function(add_function):
    """
    获取或创建装饰器包装的add_*_to_server函数
    
    Args:
        add_function: 原始的add_*_to_server函数
        
    Returns:
        装饰器包装后的函数
    """
    if add_function not in _collected_add_functions:
        _collected_add_functions[add_function] = collect_service_name(add_function)
    return _collected_add_functions[add_function]

# 注意：在实际使用中，这些装饰器应该在grpc_router.py中应用
# 这里仅作为示例展示
if __name__ == "__main__":
    # 示例演示
    print("服务管理器模块已加载")