import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

def setup_logging_and_tracing():
    # 1. Setup Standard Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # 2. Setup OpenTelemetry Tracing
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging and OpenTelemetry initialized.")

def get_tracer(name: str):
    return trace.get_tracer(name)
