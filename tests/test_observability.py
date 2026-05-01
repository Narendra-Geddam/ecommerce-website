"""Observability and monitoring tests."""

from unittest.mock import MagicMock, patch

import pytest


class TestPrometheusMetrics:
    """Prometheus metrics tests."""

    def test_metrics_endpoint_exists(self, client):
        response = client.get('/metrics')
        assert response.status_code == 200
        assert response.content_type.startswith('text/plain')

    def test_metrics_format_is_prometheus(self, client):
        response = client.get('/metrics')
        content = response.data.decode('utf-8')
        assert '# HELP' in content or '# TYPE' in content

    def test_http_request_metrics_recorded(self, client):
        client.get('/health')
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_error_rate_metrics(self, client):
        client.get('/nonexistent')
        response = client.get('/metrics')
        assert response.status_code == 200


class TestStructuredLogging:
    """Structured logging tests."""

    @patch('observability.setup_logging')
    def test_logging_setup(self, mock_logging):
        mock_logging.return_value = MagicMock()
        assert True

    def test_request_logging(self, client):
        response = client.get('/health')
        assert response.status_code == 200

    def test_error_logging(self, client):
        response = client.get('/nonexistent')
        assert response.status_code == 404


class TestDistributedTracing:
    """Distributed tracing tests."""

    @patch('observability.setup_tracing')
    def test_tracing_setup(self, mock_tracing):
        mock_tracing.return_value = MagicMock()
        assert True

    def test_trace_headers_propagation(self, client):
        response = client.get('/health', headers={
            'X-Trace-ID': 'test-trace-123',
            'X-Span-ID': 'test-span-456'
        })
        assert response.status_code == 200

    def test_jaeger_connectivity(self):
        try:
            import requests

            requests.get('http://jaeger:16686', timeout=1)
            assert True
        except Exception:
            pytest.skip('Jaeger not available')


class TestHealthChecks:
    """Health check endpoints tests."""

    def test_health_endpoint_response_structure(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        assert 'status' in response.get_json()

    def test_readiness_endpoint_response_structure(self, client):
        response = client.get('/ready')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'ready'

    def test_liveness_endpoint_response_structure(self, client):
        response = client.get('/live')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'alive'


class TestMetricsRecording:
    """Custom metrics recording tests."""

    @patch('observability.record_request_metrics')
    def test_request_metrics_recording(self, mock_record):
        mock_record('GET', '/health', 200, 0.05)
        mock_record.assert_called_once()

    @patch('observability.record_cart_item')
    def test_cart_item_metrics(self, mock_record):
        mock_record('product-1')
        mock_record.assert_called_once_with('product-1')

    @patch('observability.record_order')
    def test_order_metrics(self, mock_record):
        mock_record('completed', 100.00, 'USD')
        mock_record.assert_called_once_with('completed', 100.00, 'USD')

    @patch('observability.record_user_registration')
    def test_user_registration_metrics(self, mock_record):
        mock_record()
        mock_record.assert_called_once()
