# utils/logger.py
import logging
import sys
import os
from typing import Optional
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.trace import get_tracer_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://otel-collector:4318")

class OpenTelemetryLogger:
    """
    OpenTelemetry-integrated logger with singleton pattern and lazy initialization
    """
    _instance = None
    _initialized = False
    _service_name: str = "undefined-service"
    _log_level: int = logging.INFO

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenTelemetryLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, service_name: str, log_level: int = logging.INFO):
        """
        Initialize once during FastAPI lifespan startup
        """
        if cls._initialized:
            return

        cls._service_name = service_name
        cls._log_level = log_level

        # Setup OpenTelemetry logging
        logger_provider = LoggerProvider()
        set_logger_provider(logger_provider)
        
        # OTLP Log Exporter
        log_exporter = OTLPLogExporter(endpoint=OTLP_ENDPOINT + "/v1/logs")
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter)
        )

        # Add LoggingHandler to root logger
        handler = LoggingHandler(
            level=log_level,
            logger_provider=logger_provider,
        )
        
        # Configure logging format with OpenTelemetry context
        formatter = logging.Formatter(
            "[%(asctime)s] - [%(service_name)s] - [%(levelname)s] - [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s"
        )
        handler.setFormatter(formatter)
        
        # Get the root logger and add handler
        logger = logging.getLogger()
        logger.setLevel(log_level)
        logger.addHandler(handler)

        # Initialize tracing if not already initialized
        if not isinstance(get_tracer_provider(), TracerProvider):
            trace_provider = TracerProvider()
            span_processor = BatchSpanProcessor(
                OTLPSpanExporter(endpoint=OTLP_ENDPOINT + "/v1/traces")
            )
            trace_provider.add_span_processor(span_processor)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Get logger instance with OpenTelemetry context
        """
        if not cls._initialized:
            raise RuntimeError("Logger not initialized. Call initialize() first.")
            
        logger = logging.getLogger(name or cls._service_name)
        logger = logging.LoggerAdapter(logger, {"service_name": cls._service_name})
        return logger

class DefaultLogger:
    """
    Singleton logger with OpenTelemetry integration
    Usage:
    1. Initialize in lifespan: DefaultLogger.initialize("ServiceName")
    2. Get logger anywhere: logger = DefaultLogger.get_logger()
    """
    _otel_logger = OpenTelemetryLogger()

    @classmethod
    def initialize(cls, service_name: str, log_level: int = logging.INFO):
        cls._otel_logger.initialize(service_name, log_level)

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls._otel_logger.get_logger()