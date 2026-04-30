"""
E-Commerce testing configuration and fixtures.
"""

import pytest
import os
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(app_dir))

# Test database configuration
os.environ['TEST_MODE'] = 'true'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/ecommerce_test'


@pytest.fixture
def app():
    """Create application for tests"""
    # Mock app creation for testing
    from flask import Flask
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner for commands"""
    return app.test_cli_runner()


@pytest.fixture(scope='session')
def test_database():
    """Setup test database"""
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            user='test',
            password='test',
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop existing test db if exists
        cursor.execute("DROP DATABASE IF EXISTS ecommerce_test;")
        # Create fresh test db
        cursor.execute("CREATE DATABASE ecommerce_test;")
        
        cursor.close()
        conn.close()
        
        yield True
        
        # Cleanup
        conn = psycopg2.connect(
            host='localhost',
            user='test',
            password='test',
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DROP DATABASE IF EXISTS ecommerce_test;")
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError:
        pytest.skip("Test database not available")


@pytest.fixture
def sample_product():
    """Sample product data"""
    return {
        'id': 1,
        'name': 'Laptop',
        'category': 'Electronics',
        'price': 999.99,
        'stock': 10,
        'description': 'High performance laptop'
    }


@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123',
        'full_name': 'Test User'
    }


@pytest.fixture
def sample_order():
    """Sample order data"""
    return {
        'user_id': 1,
        'items': [
            {'product_id': 1, 'quantity': 2},
            {'product_id': 2, 'quantity': 1}
        ],
        'total_price': 2499.97,
        'status': 'pending'
    }
