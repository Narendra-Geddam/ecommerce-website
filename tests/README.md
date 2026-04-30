# Testing Suite

This directory contains automated tests for the e-commerce application.

## Overview

The testing framework provides:
- **Unit Tests** - Individual component testing
- **Integration Tests** - Multi-component workflows
- **API Tests** - HTTP endpoint validation
- **Database Tests** - Schema and query verification

## Current Status

Currently empty (`./__pycache__/` only). Testing framework infrastructure ready for test development.

## Setup

### Install Test Dependencies

```bash
# From project root
pip install pytest pytest-cov pytest-flask pytest-postgresql
```

### Test Structure (Recommended)

```
tests/
├── __init__.py
├── conftest.py                  # Pytest fixtures
├── test_api/
│   ├── test_products.py
│   ├── test_auth.py
│   ├── test_orders.py
│   └── test_cart.py
├── test_integration/
│   ├── test_user_workflow.py
│   └── test_order_workflow.py
├── test_db/
│   ├── test_schema.py
│   ├── test_migrations.py
│   └── test_data_integrity.py
└── fixtures/
    ├── sample_users.json
    ├── sample_products.json
    └── sample_orders.json
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=application --cov-report=html
```

### Run Specific Test Category

```bash
# API tests only
pytest tests/test_api/ -v

# Integration tests only
pytest tests/test_integration/ -v

# Database tests only
pytest tests/test_db/ -v
```

### Run Single Test

```bash
# Specific test file
pytest tests/test_api/test_products.py -v

# Specific test function
pytest tests/test_api/test_products.py::test_get_products -v
```

## Test Examples

### Unit Test - API Endpoint

```python
# tests/test_api/test_products.py
import pytest
from application.app import app

@pytest.fixture
def client():
    """Test client for Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_products(client):
    """Test GET /api/products endpoint"""
    response = client.get('/api/products')
    
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    
def test_product_fields(client):
    """Verify product response contains required fields"""
    response = client.get('/api/products')
    data = response.get_json()
    
    required_fields = ['id', 'name', 'price', 'description']
    for product in data:
        for field in required_fields:
            assert field in product
```

### Integration Test - User Workflow

```python
# tests/test_integration/test_user_workflow.py
def test_complete_user_flow(client, db):
    """Test complete user journey: register -> login -> order"""
    
    # 1. Register user
    register_response = client.post('/api/register', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    })
    assert register_response.status_code == 201
    
    # 2. Login
    login_response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'TestPass123!'
    })
    assert login_response.status_code == 200
    token = login_response.get_json()['token']
    
    # 3. Browse products
    products_response = client.get('/api/products')
    products = products_response.get_json()
    assert len(products) > 0
    
    # 4. Add to cart
    cart_response = client.post('/api/cart/add', json={
        'product_id': products[0]['id'],
        'quantity': 2
    }, headers={'Authorization': f'Bearer {token}'})
    assert cart_response.status_code == 200
    
    # 5. Checkout
    order_response = client.post('/api/orders', json={
        'shipping_address': '123 Main St',
        'city': 'Springfield',
        'state': 'IL',
        'phone': '555-0123'
    }, headers={'Authorization': f'Bearer {token}'})
    assert order_response.status_code == 201
```

### Database Test

```python
# tests/test_db/test_schema.py
def test_users_table_exists(db):
    """Verify users table schema"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users'
    """)
    
    columns = {row[0]: row[1] for row in cursor.fetchall()}
    
    assert 'id' in columns
    assert 'email' in columns
    assert 'password' in columns
    assert columns['email'] == 'character varying'

def test_unique_email_constraint(db):
    """Verify email uniqueness constraint"""
    cursor = db.cursor()
    
    # Insert first user
    cursor.execute("""
        INSERT INTO users (name, email, password) 
        VALUES (%s, %s, %s)
    """, ('User1', 'test@example.com', 'hash1'))
    db.commit()
    
    # Attempt duplicate email - should fail
    with pytest.raises(psycopg2.IntegrityError):
        cursor.execute("""
            INSERT INTO users (name, email, password) 
            VALUES (%s, %s, %s)
        """, ('User2', 'test@example.com', 'hash2'))
        db.commit()
```

## Test Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from application.app import app
import psycopg2

@pytest.fixture(scope='session')
def db():
    """Database connection for tests"""
    conn = psycopg2.connect(
        "dbname=ecommerce_test user=postgres"
    )
    yield conn
    conn.close()

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'postgresql://postgres@localhost/ecommerce_test'
    
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_db(db):
    """Reset database before each test"""
    cursor = db.cursor()
    
    # Truncate all tables
    cursor.execute("TRUNCATE TABLE order_items CASCADE")
    cursor.execute("TRUNCATE TABLE orders CASCADE")
    cursor.execute("TRUNCATE TABLE cart_items CASCADE")
    cursor.execute("TRUNCATE TABLE users CASCADE")
    cursor.execute("TRUNCATE TABLE products CASCADE")
    
    db.commit()
    yield
```

## CI/CD Integration

### GitHub Actions (Recommended)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: ecommerce_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install -r requirements.txt pytest pytest-cov
    
    - name: Run tests
      run: pytest tests/ --cov=application
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/ecommerce_test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| API Endpoints | 90%+ | TBD |
| Business Logic | 85%+ | TBD |
| Database Layer | 80%+ | TBD |
| Overall | 85%+ | TBD |

### Generate Coverage Report

```bash
# Terminal report
pytest tests/ --cov=application --cov-report=term-missing

# HTML report
pytest tests/ --cov=application --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Data Management

### Seed Test Database

```python
# tests/fixtures/seed_data.py
def seed_users(db):
    """Insert test users"""
    users = [
        ('Alice', 'alice@test.com', 'hash1', '9876543210'),
        ('Bob', 'bob@test.com', 'hash2', '9876543211'),
        ('Carol', 'carol@test.com', 'hash3', '9876543212'),
    ]
    
    cursor = db.cursor()
    for name, email, password, phone in users:
        cursor.execute("""
            INSERT INTO users (name, email, password, phone)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, phone))
    db.commit()

def seed_products(db):
    """Insert test products"""
    products = [
        ('Test Phone', 'A test phone', 299.99, '/static/phone.jpg', 'Mobiles', 50),
        ('Test Laptop', 'A test laptop', 899.99, '/static/laptop.jpg', 'Laptops', 25),
    ]
    
    cursor = db.cursor()
    for name, desc, price, image, category, stock in products:
        cursor.execute("""
            INSERT INTO products (name, description, price, image_url, category, stock)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, desc, price, image, category, stock))
    db.commit()
```

## Performance & Load Testing

### Using Locust

```bash
pip install locust
```

```python
# locustfile.py
from locust import HttpUser, task, between

class EcommerceUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def browse_products(self):
        self.client.get('/api/products')
    
    @task
    def view_product(self):
        self.client.get('/api/products/1')
    
    @task
    def search(self):
        self.client.get('/api/products?search=phone')
```

Run: `locust -f locustfile.py --host=http://localhost:5000`

## Troubleshooting

### Common Issues

**"database does not exist" error**
```bash
# Create test database
createdb ecommerce_test -U postgres
psql ecommerce_test -U postgres < data/schema.sql
```

**"ModuleNotFoundError: No module named 'application'"**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

**Fixture scope conflicts**
- Use `@pytest.fixture(scope='function')` for test isolation
- Use `@pytest.fixture(scope='session')` for expensive setup

## Best Practices

1. **Isolation** - Each test should be independent
2. **Clarity** - Test names describe what's being tested
3. **Mocking** - Mock external services
4. **Coverage** - Aim for >80% code coverage
5. **Performance** - Keep tests fast (<5s total)
6. **Documentation** - Document complex test logic

## Links

- **Backend README**: [apps/backend/README.md](../apps/backend/README.md)
- **Main Guide**: [README.md](../README.md)
- **Pytest Docs**: https://docs.pytest.org/
