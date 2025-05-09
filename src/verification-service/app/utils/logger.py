import logging
import sys
import os
from typing import Optional
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.logging import LoggingInstrumentor

OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://lgtm:4318")
SERVICE_NAME = os.getenv("SERVICE_NAME", "undefined-service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

class OpenTelemetryLogger:
    """
    Self-initializing OpenTelemetry logger with fail-safe defaults
    """
    _initialized = False
    _service_name: str = SERVICE_NAME
    _log_level: int = getattr(logging, LOG_LEVEL, logging.INFO)

    @classmethod
    def _ensure_initialized(cls):
        if not cls._initialized:
            cls.initialize(
                service_name=cls._service_name,
                log_level=cls._log_level
            )

    @classmethod
    def initialize(cls, service_name: Optional[str] = None, log_level: Optional[int] = None):
        if cls._initialized:
            return
        
        LoggingInstrumentor().instrument(set_logging_format=False)

        # Use parameters or fallback to environment variables
        cls._service_name = service_name or SERVICE_NAME
        cls._log_level = log_level or getattr(logging, LOG_LEVEL, logging.INFO)

        # Setup OpenTelemetry components
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: cls._service_name,
            ResourceAttributes.SERVICE_VERSION: os.getenv("SERVICE_VERSION", "1.0.0"),
        })
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)

        # Configure exporters
        log_exporter = OTLPLogExporter(endpoint=f"{OTLP_ENDPOINT}/v1/logs")
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        
        # Configure logging handler
        handler = LoggingHandler(
            level=cls._log_level,
            logger_provider=logger_provider,
        )

         # Configure logging format with OpenTelemetry context
        formatter = logging.Formatter(
            "[%(asctime)s] - [%(service_name)s] - [%(levelname)s] - [trace_id=%(trace_id)s span_id=%(span_id)s] - %(message)s"
        )
        handler.setFormatter(formatter)      
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(cls._log_level)
        root_logger.addHandler(handler)

        # Auto-initialize tracing if not already configured
        if not isinstance(get_tracer_provider(), TracerProvider):
            trace_provider = TracerProvider(resource=resource)
            trace_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces")))
            set_tracer_provider(trace_provider)
            
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        cls._ensure_initialized()
        logger = logging.getLogger(name or cls._service_name)
        return logging.LoggerAdapter(logger, {"service_name": cls._service_name})


class DefaultLogger:
    """
    Auto-initializing logger with fail-safe defaults
    Usage: 
    DefaultLogger.get_logger().info("Message")
    """
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        OpenTelemetryLogger._ensure_initialized()
        return OpenTelemetryLogger.get_logger(name)