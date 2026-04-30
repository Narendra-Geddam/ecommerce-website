"""
Observability instrumentation for Flask application.
Includes metrics (Prometheus), logging (structured), and tracing (Jaeger).
"""

import os
import logging
import json
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# ============ PROMETHEUS METRICS ============

# HTTP Request metrics
http_requests_total = Counter(
    'flask_http_request_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

# Database metrics
db_connection_pool_size = Gauge(
    'ecommerce_db_connection_pool_size',
    'Database connection pool size'
)

db_query_duration_seconds = Histogram(
    'ecommerce_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# Business metrics
shopping_cart_items_total = Counter(
    'ecommerce_shopping_cart_items_total',
    'Total items added to shopping carts',
    ['product_id']
)

orders_total = Counter(
    'ecommerce_orders_total',
    'Total orders placed',
    ['status']
)

order_value_total = Counter(
    'ecommerce_order_value_total',
    'Total order value in currency',
    ['currency']
)

users_registered_total = Counter(
    'ecommerce_users_registered_total',
    'Total users registered'
)

# Application metrics
app_errors_total = Counter(
    'flask_errors_total',
    'Total application errors',
    ['error_type', 'endpoint']
)

app_version = Gauge(
    'app_version',
    'Application version',
    ['version']
)


def setup_metrics():
    """Initialize Prometheus metrics"""
    app_version.labels(version=os.environ.get('APP_VERSION', '1.0.0')).set(1)
    return {
        'http_requests_total': http_requests_total,
        'http_request_duration_seconds': http_request_duration_seconds,
        'db_query_duration_seconds': db_query_duration_seconds,
        'shopping_cart_items_total': shopping_cart_items_total,
        'orders_total': orders_total,
        'order_value_total': order_value_total,
        'users_registered_total': users_registered_total,
        'app_errors_total': app_errors_total,
    }


# ============ STRUCTURED LOGGING ============

def setup_logging():
    """Setup JSON structured logging"""
    # Remove default handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # JSON logger configuration
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    logHandler.setFormatter(formatter)

    root_logger.addHandler(logHandler)
    root_logger.setLevel(logging.INFO)

    return logging.getLogger(__name__)


# ============ DISTRIBUTED TRACING ============

def setup_tracing(service_name="ecommerce-backend"):
    """Setup Jaeger distributed tracing"""
    jaeger_host = os.environ.get('JAEGER_HOST', 'jaeger')
    jaeger_port = int(os.environ.get('JAEGER_PORT', 6831))

    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )

    trace_provider = TracerProvider()
    trace_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    trace.set_tracer_provider(trace_provider)

    # Instrument frameworks
    FlaskInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    RequestsInstrumentor().instrument()

    return trace.get_tracer(__name__)


# ============ HELPER FUNCTIONS ============

def record_request_metrics(method, endpoint, status, duration):
    """Record HTTP request metrics"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_db_query(query_type, duration):
    """Record database query metrics"""
    db_query_duration_seconds.labels(
        query_type=query_type
    ).observe(duration)


def record_cart_item(product_id):
    """Record shopping cart item"""
    shopping_cart_items_total.labels(
        product_id=product_id
    ).inc()


def record_order(status, value, currency='USD'):
    """Record order metrics"""
    orders_total.labels(status=status).inc()
    order_value_total.labels(currency=currency).inc(value)


def record_user_registration():
    """Record new user registration"""
    users_registered_total.inc()


def record_error(error_type, endpoint):
    """Record application error"""
    app_errors_total.labels(
        error_type=error_type,
        endpoint=endpoint
    ).inc()


def get_metrics():
    """Return Prometheus metrics in text format"""
    return generate_latest()
