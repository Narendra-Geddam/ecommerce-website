"""
Logging Middleware for Microservices

Provides structured logging, request tracing, and performance monitoring.
"""
import os
import sys
import time
import uuid
import logging
import json
from datetime import datetime
from flask import request, g, Response
from functools import wraps


# Configure JSON logging for microservices
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'service': os.environ.get('SERVICE_NAME', 'unknown'),
            'logger': record.name
        }

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(service_name: str = None, level: str = 'INFO'):
    """Setup structured logging for a microservice"""
    if service_name:
        os.environ['SERVICE_NAME'] = service_name

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add JSON handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class RequestLogger:
    """Request logging middleware for Flask apps"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the request logger with Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self):
        """Log request start and generate request ID"""
        g.request_id = str(uuid.uuid4())[:8]
        g.request_start_time = time.time()
        g.request_logger = get_logger('request')

    def _after_request(self, response: Response) -> Response:
        """Log request completion"""
        if not hasattr(g, 'request_start_time'):
            return response

        duration_ms = (time.time() - g.request_start_time) * 1000

        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f'{duration_ms:.2f}ms'

        # Log the request
        logger = getattr(g, 'request_logger', get_logger('request'))
        logger.info(
            f'{request.method} {request.path} - {response.status_code} - {duration_ms:.2f}ms',
            extra={'request_id': g.request_id}
        )

        return response


# Global request logger instance
request_logger = RequestLogger()


def log_performance(endpoint_name: str = None):
    """Decorator to log performance of specific endpoints"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            name = endpoint_name or f.__name__
            logger = get_logger('performance')

            try:
                result = f(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(f'{name} completed in {duration_ms:.2f}ms')
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f'{name} failed after {duration_ms:.2f}ms: {str(e)}')
                raise

        return wrapped
    return decorator


class HealthChecker:
    """Health check utilities for microservices"""

    @staticmethod
    def check_database(pool) -> dict:
        """Check database connectivity"""
        try:
            start = time.time()
            with pool.connection() as cursor:
                cursor.execute('SELECT 1')
            latency = (time.time() - start) * 1000
            return {'status': 'healthy', 'latency_ms': round(latency, 2)}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    @staticmethod
    def check_redis(redis_client) -> dict:
        """Check Redis connectivity"""
        if not redis_client:
            return {'status': 'not_configured'}

        try:
            start = time.time()
            redis_client.ping()
            latency = (time.time() - start) * 1000
            return {'status': 'healthy', 'latency_ms': round(latency, 2)}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    @staticmethod
    def get_service_info() -> dict:
        """Get service information"""
        import socket
        import platform

        return {
            'hostname': socket.gethostname(),
            'service_name': os.environ.get('SERVICE_NAME', 'unknown'),
            'service_tier': os.environ.get('SERVICE_TIER', 'unknown'),
            'platform': platform.system(),
            'python_version': platform.python_version()
        }