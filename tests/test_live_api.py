import os
import uuid

import requests


BASE_URL = os.environ.get('TEST_BASE_URL', 'http://gateway:5000')


def build_url(path):
    return f"{BASE_URL}{path}"


def get_csrf_token(session):
    response = session.get(build_url('/api/csrf-token'), timeout=10)
    response.raise_for_status()
    data = response.json()
    return data['csrf_token']


def test_guest_me_returns_authenticated_false():
    session = requests.Session()
    response = session.get(build_url('/api/me'), timeout=10)

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/json')
    assert response.json()['authenticated'] is False


def test_products_endpoint_returns_paginated_shape():
    response = requests.get(build_url('/api/products?page=1&page_size=5'), timeout=10)

    assert response.status_code == 200
    data = response.json()
    assert 'products' in data
    assert 'pagination' in data
    assert isinstance(data['products'], list)
    assert len(data['products']) <= 5
    assert data['pagination']['page'] == 1
    assert data['pagination']['page_size'] == 5


def test_register_validation_rejects_invalid_payload():
    session = requests.Session()
    csrf_token = get_csrf_token(session)
    response = session.post(
        build_url('/api/register'),
        json={
            'name': 'A',
            'email': 'bad-email',
            'password': '12345678',
            'phone': '123'
        },
        headers={'X-CSRF-Token': csrf_token},
        timeout=10,
    )

    assert response.status_code == 400
    data = response.json()
    assert data['success'] is False
    assert 'error' in data


def test_register_login_and_me_flow():
    session = requests.Session()
    csrf_token = get_csrf_token(session)
    unique_email = f"codex-{uuid.uuid4().hex[:10]}@example.com"
    password = 'Password123'

    register_response = session.post(
        build_url('/api/register'),
        json={
            'name': 'Codex Tester',
            'email': unique_email,
            'password': password,
            'phone': '9876543210',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560001'
        },
        headers={'X-CSRF-Token': csrf_token},
        timeout=10,
    )
    assert register_response.status_code == 200
    register_data = register_response.json()
    assert register_data['success'] is True
    assert register_data['access_token']

    me_response = session.get(
        build_url('/api/me'),
        headers={'Authorization': f"Bearer {register_data['access_token']}"},
        timeout=10,
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data['authenticated'] is True
    assert me_data['email'] == unique_email


def test_guest_cart_add_and_fetch_round_trip():
    session = requests.Session()
    csrf_token = get_csrf_token(session)

    add_response = session.post(
        build_url('/api/cart/add/1'),
        json={},
        headers={'X-CSRF-Token': csrf_token},
        timeout=10,
    )
    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data['success'] is True
    assert add_data['cart_id']

    cart_id = add_data['cart_id']
    cart_response = session.get(
        build_url('/api/cart'),
        headers={'X-Cart-ID': cart_id},
        timeout=10,
    )
    assert cart_response.status_code == 200
    cart_data = cart_response.json()
    assert cart_data['cart_id'] == cart_id
    assert len(cart_data['items']) >= 1
    assert cart_data['items'][0]['id'] == 1
