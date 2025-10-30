import time
from fastapi import FastAPI
from loguru import logger

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer


def setup_otel(
        service_name: str,
        service_version: str,
        environment: str,
        otlp_endpoint: str,
        fastapi_app: FastAPI = None,
):
    """
    初始化 OpenTelemetry OTLP tracing + metrics。

    :param service_name: 服务名
    :param service_version: 服务版本
    :param environment: 环境名（prod/dev）
    :param otlp_endpoint: OTLP Collector 地址，例如 'localhost:4317'
    :param fastapi_app: 可选 FastAPI 实例，用于自动追踪
    """

    # 1、设置资源信息
    resource = Resource.create(
        attributes={
            "service.name": f"{service_name}.{environment}",
            "service.version": service_version,
        }
    )

    # 2、设置全局传播器（trace + baggage）
    propagator = CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
    set_global_textmap(propagator)

    # 3、配置 TraceProvider 和 OTLP exporter
    trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(trace_exporter, schedule_delay_millis=5000)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    # 4、配置 Metrics MeterProvider 和 OTLP exporter
    metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10000)],
    )
    metrics.set_meter_provider(meter_provider)

    # 5、自动追踪 FastAPI 应用
    if fastapi_app:
        FastAPIInstrumentor.instrument_app(fastapi_app)

    # 6、自动追踪 gRPC 服务端
    GrpcInstrumentorServer().instrument()

    logger.info("OpenTelemetry tracing + metrics initialized.")


if __name__ == '__main__':
    # ==========================
    # 示例 FastAPI 应用
    # ==========================
    app = FastAPI()

    setup_otel(
        service_name="user-service",
        service_version="1.0.0",
        environment="dev",
        otlp_endpoint="localhost:4317",
        fastapi_app=app,
    )


    @app.get("/ping")
    def ping():
        return {"message": "pong"}
