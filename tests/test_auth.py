"""Authentication tests."""


class TestAuthenticationAPI:
    """Authentication endpoint tests."""

    def test_register_new_user(self, client, sample_user):
        response = client.post('/api/register', json=sample_user)
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['user']['email'] == sample_user['email']

    def test_register_duplicate_user(self, client, sample_user):
        client.post('/api/register', json=sample_user)

        response = client.post('/api/register', json=sample_user)
        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        response = client.post('/api/register', json={'email': 'test@example.com'})
        assert response.status_code == 400

    def test_login_valid_credentials(self, client, sample_user):
        client.post('/api/register', json=sample_user)

        response = client.post('/api/login', json={
            'email': sample_user['email'],
            'password': sample_user['password']
        })
        assert response.status_code == 200
        assert response.get_json()['success'] is True

    def test_login_invalid_credentials(self, client):
        response = client.post('/api/login', json={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post('/api/login', json={'email': 'test@example.com'})
        assert response.status_code == 400

    def test_logout(self, client, sample_user):
        client.post('/api/register', json=sample_user)
        client.post('/api/login', json={
            'email': sample_user['email'],
            'password': sample_user['password']
        })

        response = client.post('/api/logout')
        assert response.status_code == 200
        assert response.get_json()['success'] is True

    def test_get_current_user(self, client, sample_user):
        response = client.get('/api/me')
        assert response.status_code == 200
        assert response.get_json()['authenticated'] is False

        client.post('/api/register', json=sample_user)
        response = client.get('/api/me')
        assert response.status_code == 200
        assert response.get_json()['authenticated'] is True

    def test_update_profile(self, client, sample_user):
        client.post('/api/register', json=sample_user)

        response = client.put('/api/profile', json={
            'name': 'Updated Name',
            'phone': '555-0202',
            'address': '456 Updated Street',
            'city': 'New City',
            'state': 'NC',
            'pincode': '654321'
        })
        assert response.status_code == 200
        assert response.get_json()['success'] is True


class TestSessionManagement:
    """Session management tests."""

    def test_session_persistence(self, client, sample_user):
        client.post('/api/register', json=sample_user)
        client.post('/api/login', json={
            'email': sample_user['email'],
            'password': sample_user['password']
        })

        response1 = client.get('/api/me')
        response2 = client.get('/api/me')
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.get_json()['authenticated'] is True
        assert response2.get_json()['authenticated'] is True

    def test_concurrent_sessions(self, client, sample_user):
        client.post('/api/register', json=sample_user)

        response1 = client.get('/api/me')
        response2 = client.get('/api/me')
        assert response1.status_code == 200
        assert response2.status_code == 200
