# logger.py - Structured logging with OTLP export
import structlog
import logging
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Set up OTLP exporter
resource = Resource.create({"service.name": "ai-factory-os"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

tracer = trace.get_tracer(__name__)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def log_task_start(task):
    with tracer.start_as_span("task_start") as span:
        span.set_attribute("task.id", task['task_id'])
        span.set_attribute("task.assignee", task['assignee'])
        logger.info("task_started", task_id=task['task_id'], assignee=task['assignee'], description=task['description'], files=task['files'])

def log_success(task_id, duration):
    with tracer.start_as_span("task_success") as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("duration", duration)
        logger.info("task_completed", task_id=task_id, duration=duration)

def log_error(msg):
    with tracer.start_as_span("task_error") as span:
        span.set_attribute("error.message", msg)
        logger.error("task_error", message=msg)

def log_retry(task_id, attempt):
    with tracer.start_as_span("task_retry") as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("retry.attempt", attempt)
        logger.warning("task_retry", task_id=task_id, attempt=attempt)