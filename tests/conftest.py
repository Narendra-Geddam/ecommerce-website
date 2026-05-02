"""E-Commerce testing configuration and fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import psycopg2
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / '1-apps' / 'backend'
SCHEMA_FILE = REPO_ROOT / 'data' / 'schema.sql'

sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('TEST_MODE', 'true')
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ecommerce_test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')

# Mock opentelemetry modules that have version-compatibility issues in test
# environments.  The Jaeger exporter is only used by setup_tracing() which
# app.py never calls, so it is safe to stub the whole package tree here.
_ot_modules_to_mock = [
    'opentelemetry.exporter.jaeger',
    'opentelemetry.exporter.jaeger.thrift',
    'opentelemetry.instrumentation.flask',
    'opentelemetry.instrumentation.psycopg2',
    'opentelemetry.instrumentation.requests',
]
for _mod_name in _ot_modules_to_mock:
    sys.modules[_mod_name] = MagicMock()

from app import app as flask_app


@pytest.fixture(scope='session')
def db_connection():
    """Open the test database connection used by the Flask app.

    Yields ``None`` when the database is not reachable so that autouse
    fixtures can stay no-ops rather than propagating a session-wide skip that
    would cancel tests that don't need a database at all.
    """
    try:
        connection = psycopg2.connect(os.environ['DATABASE_URL'])
    except psycopg2.OperationalError:
        yield None
        return

    connection.autocommit = True
    yield connection
    connection.close()


@pytest.fixture(scope='session', autouse=True)
def initialize_database(db_connection):
    """Create schema and seed data once for the whole test session."""
    if db_connection is None:
        yield
        return
    with SCHEMA_FILE.open('r', encoding='utf-8') as schema_file:
        db_connection.cursor().execute(schema_file.read())
    yield


@pytest.fixture(autouse=True)
def reset_database(db_connection):
    """Keep database state isolated between tests."""
    if db_connection is None:
        yield
        return
    cursor = db_connection.cursor()
    cursor.execute('TRUNCATE TABLE order_items, orders, users RESTART IDENTITY CASCADE')
    yield


@pytest.fixture
def client(db_connection):
    """Flask test client backed by the real app with a live database.

    Tests that use this fixture are automatically skipped when the database
    is not reachable.
    """
    if db_connection is None:
        pytest.skip('Test database not available')
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def sample_product():
    """Sample product data."""
    return {
        'id': 1,
        'name': 'Redmi 9A (Nature Green, 2GB RAM, 32GB Storage)',
        'category': 'Mobiles',
        'price': 6999.00,
        'stock': 40,
        'description': '13MP AI rear camera with portrait, scene recognition, HDR, pro mode | 5MP front camera | 6.53-inch HD+ display, 1600x720, 268ppi | 5000mAh battery | MediaTek Helio G25 processor'
    }


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'phone': '555-0101',
        'address': '123 Test Street',
        'city': 'Testville',
        'state': 'TS',
        'pincode': '123456'
    }


@pytest.fixture
def sample_order():
    """Sample order data."""
    return {
        'address': '123 Test Street',
        'city': 'Testville',
        'state': 'TS',
        'pincode': '123456',
        'phone': '555-0101',
        'payment_method': 'COD'
    }
