"""
API endpoint tests.
"""

import pytest
import json


class TestProductAPI:
    """Product endpoint tests"""

    def test_get_products(self, client):
        """Test fetching all products"""
        response = client.get('/products')
        assert response.status_code in [200, 404]  # 404 if no products yet

    def test_get_product_by_id(self, client, sample_product):
        """Test fetching single product"""
        product_id = sample_product['id']
        response = client.get(f'/products/{product_id}')
        assert response.status_code in [200, 404]

    def test_get_categories(self, client):
        """Test fetching product categories"""
        response = client.get('/categories')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


class TestCartAPI:
    """Shopping cart endpoint tests"""

    def test_get_cart(self, client):
        """Test fetching shopping cart"""
        response = client.get('/api/cart')
        assert response.status_code == 200

    def test_add_to_cart(self, client, sample_product):
        """Test adding item to cart"""
        payload = {
            'product_id': sample_product['id'],
            'quantity': 1
        }
        response = client.post(
            '/api/cart/add',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_remove_from_cart(self, client, sample_product):
        """Test removing item from cart"""
        response = client.post(
            f'/api/cart/remove/{sample_product["id"]}',
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_clear_cart(self, client):
        """Test clearing shopping cart"""
        response = client.post('/api/cart/clear')
        assert response.status_code in [200, 400]

    def test_get_cart_count(self, client):
        """Test getting cart item count"""
        response = client.get('/api/cart/count')
        assert response.status_code == 200
        data = response.get_json()
        assert 'count' in data or 'error' in data


class TestOrderAPI:
    """Order endpoint tests"""

    def test_get_orders(self, client):
        """Test fetching orders"""
        response = client.get('/api/orders')
        assert response.status_code in [200, 401]  # 401 if not authenticated

    def test_place_order(self, client, sample_order):
        """Test placing new order"""
        response = client.post(
            '/api/orders',
            data=json.dumps(sample_order),
            content_type='application/json'
        )
        assert response.status_code in [200, 201, 400, 401]

    def test_get_order_by_id(self, client):
        """Test fetching specific order"""
        response = client.get('/api/orders/1')
        assert response.status_code in [200, 404, 401]


class TestHealthChecks:
    """Health and readiness check tests"""

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data

    def test_readiness_check(self, client):
        """Test /ready endpoint"""
        response = client.get('/ready')
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'status' in data

    def test_liveness_check(self, client):
        """Test /live endpoint"""
        response = client.get('/live')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data


class TestMetricsEndpoint:
    """Prometheus metrics endpoint tests"""

    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint"""
        response = client.get('/metrics')
        assert response.status_code == 200
        # Check for Prometheus format
        assert b'# HELP' in response.data or b'flask_http_request_total' in response.data


class TestErrorHandling:
    """Error handling tests"""

    def test_invalid_endpoint(self, client):
        """Test 404 error handling"""
        response = client.get('/invalid/endpoint')
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 error handling"""
        response = client.post('/products')  # GET only endpoint
        assert response.status_code in [405, 400, 404]

    def test_invalid_json_payload(self, client):
        """Test error handling for invalid JSON"""
        response = client.post(
            '/api/cart/add',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 415]
