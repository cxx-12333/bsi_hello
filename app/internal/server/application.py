import asyncio
import signal
import sys
from fastapi import FastAPI
from app.internal.log.logger import init_logger
from app.internal.otel.tracing import setup_otel
from app.internal.config.bootstrap import Bootstrap
from loguru import logger


class Application:
    """应用启动类，负责初始化和运行HTTP/gRPC服务"""
    
    def __init__(self, bootstrap: Bootstrap):
        self.bootstrap = bootstrap
        self.exit_event = None
        self.http_task = None
        self.grpc_task = None
        
        # 初始化FastAPI应用
        self.app = FastAPI(
            title=self.bootstrap.service.name, 
            version=self.bootstrap.service.version
        )
        
        # 初始化日志
        init_logger()
        
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}, 开始优雅关闭...")
            if self.exit_event:
                self.exit_event.set()
        
        # 注册SIGINT (Ctrl+C) 和 SIGTERM (kill) 信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def run(self, container):
        """运行应用"""
        try:
            # 初始化退出事件
            self.exit_event = asyncio.Event()
            
            # 设置信号处理器
            self.setup_signal_handlers()
            
            # 设置OpenTelemetry
            setup_otel(
                service_name=self.bootstrap.service.name,
                service_version=self.bootstrap.service.version,
                environment=self.bootstrap.otlp.environment,
                otlp_endpoint=self.bootstrap.otlp.endpoint,
                fastapi_app=self.app,
            )
            
            # 初始化Redis客户端
            from app.internal.lock.red_lock import init_redis_client
            await init_redis_client()
            
            # 初始化依赖注入容器已在main.py中完成
            
            # 创建任务并发运行HTTP和gRPC服务
            # 注意：实际的HTTP和gRPC启动逻辑将在router模块中实现
            from app.internal.router import start_http, start_grpc
            
            self.http_task = asyncio.create_task(start_http(self.app, container, self.bootstrap))
            self.grpc_task = asyncio.create_task(start_grpc(container, self.bootstrap))
            exit_event_task = asyncio.create_task(self.exit_event.wait())
            
            try:
                # 等待任一任务完成或接收到退出信号
                done, pending = await asyncio.wait(
                    [self.http_task, self.grpc_task, exit_event_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 检查是否是退出信号触发的
                exit_triggered = exit_event_task in done
                if exit_triggered:
                    logger.info("接收到退出信号，开始优雅关闭...")
                
                # 取消未完成的任务
                tasks_to_cancel = [task for task in pending if task != exit_event_task]
                for task in tasks_to_cancel:
                    task.cancel()
                    
                # 等待被取消的任务完成
                if tasks_to_cancel:
                    await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
                    
            except asyncio.CancelledError:
                logger.info("主任务被取消")
            finally:
                # 注销服务
                self.shutdown()
                
        except Exception as e:
            logger.error(f"应用运行出错: {e}")
            sys.exit(1)
            
    def shutdown(self):
        """关闭服务"""
        # 取消任务
        if self.http_task and not self.http_task.done():
            self.http_task.cancel()
        if self.grpc_task and not self.grpc_task.done():
            self.grpc_task.cancel()
            
        # 注销服务的逻辑将在registry模块中处理
        logger.info("服务已关闭")