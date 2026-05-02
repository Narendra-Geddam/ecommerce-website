"""
Self-contained tests that require NO external services.

These tests mock the database layer so they always run and pass in any
environment (local, CI, or container) without a running PostgreSQL instance
or Jaeger agent.
"""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

# conftest.py is loaded by pytest before this file, so by this point:
#   • the backend directory is already on sys.path
#   • the opentelemetry/jaeger mocks are already in sys.modules
# A direct import therefore works without any extra setup.
from app import app as _flask_app


# ---------------------------------------------------------------------------
# Module-local client fixture — no DB dependency, never skipped
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Lightweight Flask test client that does NOT require a database."""
    _flask_app.config['TESTING'] = True
    with _flask_app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cursor(rows=None, single_row=None):
    """Return a mock psycopg2 cursor."""
    cur = MagicMock()
    cur.fetchall.return_value = rows if rows is not None else []
    cur.fetchone.return_value = single_row
    return cur


def _make_conn(rows=None, single_row=None):
    """Return a mock psycopg2 connection whose cursor yields the given data."""
    conn = MagicMock()
    conn.cursor.return_value = _make_cursor(rows=rows, single_row=single_row)
    return conn


def _product(**overrides):
    """Return a minimal product dict (mirrors the DB schema)."""
    base = {
        'id': 1,
        'name': 'Test Phone',
        'description': 'A test product',
        'price': 9.99,
        'image_url': '/static/products/test.jpg',
        'category': 'Mobiles',
        'stock': 10,
        'created_at': None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Health / liveness probes  (no DB required)
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Health check endpoints that never touch the database."""

    def test_health_returns_200(self, client):
        r = client.get('/health')
        assert r.status_code == 200

    def test_health_status_field(self, client):
        r = client.get('/health')
        assert r.get_json()['status'] == 'healthy'

    def test_live_returns_200(self, client):
        r = client.get('/live')
        assert r.status_code == 200

    def test_live_status_field(self, client):
        r = client.get('/live')
        assert r.get_json()['status'] == 'alive'

    def test_unknown_route_is_404(self, client):
        r = client.get('/this/route/does/not/exist')
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Readiness probe  (DB access – mocked)
# ---------------------------------------------------------------------------

class TestReadinessEndpoint:
    """Readiness probe with a mocked DB connection."""

    def test_ready_when_db_available(self, client):
        with patch('app.get_db', return_value=_make_conn()):
            r = client.get('/ready')
        assert r.status_code == 200
        assert r.get_json()['status'] == 'ready'


# ---------------------------------------------------------------------------
# Metrics endpoint  (Prometheus – no DB required)
# ---------------------------------------------------------------------------

class TestMetricsEndpoint:
    """Prometheus /metrics endpoint."""

    def test_metrics_returns_200(self, client):
        r = client.get('/metrics')
        assert r.status_code == 200

    def test_metrics_content_type(self, client):
        r = client.get('/metrics')
        assert 'text/plain' in r.content_type

    def test_metrics_contains_prometheus_format(self, client):
        r = client.get('/metrics')
        content = r.data.decode('utf-8')
        assert '# HELP' in content or '# TYPE' in content


# ---------------------------------------------------------------------------
# Cart endpoints  (session-based, no DB required)
# ---------------------------------------------------------------------------

class TestCartWithoutDb:
    """Cart operations that only touch the server-side session."""

    def test_empty_cart_count(self, client):
        r = client.get('/api/cart/count')
        assert r.status_code == 200
        assert r.get_json()['count'] == 0

    def test_add_item_increments_count(self, client):
        r = client.post('/api/cart/add/1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['cart_count'] == 1

    def test_add_multiple_items(self, client):
        client.post('/api/cart/add/1')
        r = client.post('/api/cart/add/2')
        assert r.get_json()['cart_count'] == 2

    def test_cart_count_after_add(self, client):
        client.post('/api/cart/add/1')
        r = client.get('/api/cart/count')
        assert r.get_json()['count'] == 1

    def test_remove_item_decrements_count(self, client):
        client.post('/api/cart/add/1')
        r = client.post('/api/cart/remove/1')
        assert r.status_code == 200
        assert r.get_json()['success'] is True
        assert r.get_json()['cart_count'] == 0

    def test_remove_nonexistent_item_is_safe(self, client):
        r = client.post('/api/cart/remove/999')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_clear_cart(self, client):
        client.post('/api/cart/add/1')
        client.post('/api/cart/add/2')
        r = client.post('/api/cart/clear')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_count_is_zero_after_clear(self, client):
        client.post('/api/cart/add/1')
        client.post('/api/cart/clear')
        r = client.get('/api/cart/count')
        assert r.get_json()['count'] == 0


# ---------------------------------------------------------------------------
# Product endpoints  (DB mocked)
# ---------------------------------------------------------------------------

class TestProductEndpoints:
    """Product catalog routes with a mocked database."""

    def test_get_products_returns_list(self, client):
        with patch('app.get_db', return_value=_make_conn(rows=[_product()])):
            r = client.get('/products')
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_get_products_empty_catalog(self, client):
        with patch('app.get_db', return_value=_make_conn(rows=[])):
            r = client.get('/products')
        assert r.status_code == 200
        assert r.get_json() == []

    def test_get_product_by_id(self, client):
        p = _product(id=1, name='My Phone')
        with patch('app.get_db', return_value=_make_conn(single_row=p)):
            r = client.get('/products/1')
        assert r.status_code == 200
        assert r.get_json()['name'] == 'My Phone'

    def test_get_product_not_found(self, client):
        with patch('app.get_db', return_value=_make_conn(single_row=None)):
            r = client.get('/products/99999')
        assert r.status_code == 404

    def test_get_categories_includes_all(self, client):
        rows = [{'category': 'Mobiles'}, {'category': 'Books'}]
        with patch('app.get_db', return_value=_make_conn(rows=rows)):
            r = client.get('/categories')
        assert r.status_code == 200
        data = r.get_json()
        assert 'All' in data
        assert 'Mobiles' in data
        assert 'Books' in data


# ---------------------------------------------------------------------------
# Auth endpoints  (no DB or DB mocked)
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    """Authentication routes."""

    # --- Field-validation checks (no DB needed) ---

    def test_login_missing_password_returns_400(self, client):
        r = client.post('/api/login', json={'email': 'a@example.com'})
        assert r.status_code == 400

    def test_login_missing_email_returns_400(self, client):
        r = client.post('/api/login', json={'password': 'secret'})
        assert r.status_code == 400

    def test_register_missing_fields_returns_400(self, client):
        r = client.post('/api/register', json={'email': 'a@example.com'})
        assert r.status_code == 400

    # --- Invalid-credential check (DB returns no user) ---

    def test_login_unknown_user_returns_401(self, client):
        with patch('app.get_db', return_value=_make_conn(single_row=None)):
            r = client.post('/api/login', json={
                'email': 'nobody@example.com',
                'password': 'wrongpassword',
            })
        assert r.status_code == 401

    # --- Session-only routes (no DB needed) ---

    def test_logout_returns_success(self, client):
        r = client.post('/api/logout')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_me_unauthenticated(self, client):
        r = client.get('/api/me')
        assert r.status_code == 200
        assert r.get_json()['authenticated'] is False

    def test_orders_list_requires_auth(self, client):
        r = client.get('/api/orders')
        assert r.status_code == 401

    def test_create_order_requires_auth(self, client):
        r = client.post('/api/orders', json={})
        assert r.status_code == 401

    def test_update_profile_requires_auth(self, client):
        r = client.put('/api/profile', json={'name': 'New Name'})
        assert r.status_code == 401
