from loguru import logger
import sys
import logging
import os
from opentelemetry.trace import get_current_span

# 定义一个日志过滤器类，用于在日志中添加 trace_id
class TraceIdFilter:
    def __call__(self, record):
        """
        每次日志记录时调用，向日志的 extra 字段添加 trace_id。
        record: dict, loguru 的日志记录对象
        """
        # 获取当前的 OpenTelemetry span
        span = get_current_span()
        # 将 trace_id 写入日志记录的 extra 中
        # 如果当前没有 span，则 trace_id 为 None
        record["extra"]["trace_id"] = span.get_span_context().trace_id if span else None
        # 返回 True 表示这个日志记录通过过滤器（始终返回 True）
        return True

# 初始化日志器函数
def init_logger():
    # 移除 loguru 默认的日志处理器（防止重复输出）
    logger.remove()

    # 从环境变量获取日志级别，默认为INFO
    log_level = os.getenv("LOGURU_LEVEL", "INFO")

    # 添加一个新的日志处理器，输出到标准输出
    # level=log_level 表示日志级别由环境变量或默认值决定
    # format 用于自定义日志输出格式
    # {extra[trace_id]} 会显示 trace_id
    # 给 logger 添加 TraceIdFilter 过滤器,每条日志记录都会经过 TraceIdFilter，将 trace_id 写入 extra
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time}</green> | <level>{level}</level> | <cyan>{extra[trace_id]}</cyan> | {message}",
        filter=TraceIdFilter(),
    )

    # 配置SQLAlchemy日志
    # 设置SQLAlchemy引擎日志级别为INFO，这样可以看到SQL语句
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # 也可以设置SQLAlchemy的其他日志器级别
    # logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
    # logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
    # logging.getLogger('sqlalchemy.orm').setLevel(logging.INFO)

    logger.info(f"Logger initialized with level: {log_level}")
