"""API endpoint tests."""


class TestProductAPI:
    """Product endpoint tests."""

    def test_get_products(self, client):
        response = client.get('/products')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_product_by_id(self, client, sample_product):
        response = client.get(f"/products/{sample_product['id']}")
        assert response.status_code == 200

        product = response.get_json()
        assert product['id'] == sample_product['id']
        assert product['name'] == sample_product['name']

    def test_get_categories(self, client):
        response = client.get('/categories')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert 'All' in data


class TestCartAPI:
    """Shopping cart endpoint tests."""

    def test_get_cart(self, client):
        response = client.get('/api/cart')
        assert response.status_code == 200
        assert response.get_json() == []

    def test_add_to_cart(self, client, sample_product):
        response = client.post(f"/api/cart/add/{sample_product['id']}")
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['cart_count'] == 1

    def test_remove_from_cart(self, client, sample_product):
        client.post(f"/api/cart/add/{sample_product['id']}")

        response = client.post(f"/api/cart/remove/{sample_product['id']}")
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['cart_count'] == 0

    def test_clear_cart(self, client, sample_product):
        client.post(f"/api/cart/add/{sample_product['id']}")

        response = client.post('/api/cart/clear')
        assert response.status_code == 200
        assert response.get_json()['success'] is True

    def test_get_cart_count(self, client, sample_product):
        client.post(f"/api/cart/add/{sample_product['id']}")

        response = client.get('/api/cart/count')
        assert response.status_code == 200
        assert response.get_json()['count'] == 1


class TestOrderAPI:
    """Order endpoint tests."""

    def test_get_orders_requires_authentication(self, client):
        response = client.get('/api/orders')
        assert response.status_code == 401

    def test_place_and_fetch_order(self, client, sample_user, sample_product, sample_order):
        register_response = client.post('/api/register', json=sample_user)
        assert register_response.status_code == 200

        client.post(f"/api/cart/add/{sample_product['id']}")

        order_response = client.post('/api/orders', json=sample_order)
        assert order_response.status_code == 200

        order_id = order_response.get_json()['order_id']

        detail_response = client.get(f'/api/orders/{order_id}')
        assert detail_response.status_code == 200

        order = detail_response.get_json()
        assert order['id'] == order_id
        assert order['tracking_steps']


class TestHealthChecks:
    """Health and readiness check tests."""

    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'healthy'

    def test_readiness_check(self, client):
        response = client.get('/ready')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'ready'

    def test_liveness_check(self, client):
        response = client.get('/live')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'alive'


class TestMetricsEndpoint:
    """Prometheus metrics endpoint tests."""

    def test_metrics_endpoint(self, client):
        response = client.get('/metrics')
        assert response.status_code == 200
        assert b'# HELP' in response.data or b'# TYPE' in response.data


class TestErrorHandling:
    """Error handling tests."""

    def test_invalid_endpoint(self, client):
        response = client.get('/invalid/endpoint')
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        response = client.post('/products')
        assert response.status_code in [405, 404]
