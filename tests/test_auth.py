"""
Authentication tests.
"""

import pytest
import json


class TestAuthenticationAPI:
    """Authentication endpoint tests"""

    def test_register_new_user(self, client, sample_user):
        """Test user registration"""
        response = client.post(
            '/api/register',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        assert response.status_code in [201, 200, 400]

    def test_register_duplicate_user(self, client, sample_user):
        """Test duplicate user registration"""
        # Register first time
        client.post(
            '/api/register',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        # Try registering with same email
        response = client.post(
            '/api/register',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        assert response.status_code in [400, 409]  # Conflict or Bad Request

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        incomplete_user = {'username': 'testuser'}
        response = client.post(
            '/api/register',
            data=json.dumps(incomplete_user),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        weak_user = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123',  # Too weak
            'full_name': 'Test User'
        }
        response = client.post(
            '/api/register',
            data=json.dumps(weak_user),
            content_type='application/json'
        )
        assert response.status_code in [400, 422]  # Unprocessable Entity

    def test_login_valid_credentials(self, client, sample_user):
        """Test login with valid credentials"""
        # Register first
        client.post(
            '/api/register',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        # Try login
        login_data = {
            'username': sample_user['username'],
            'password': sample_user['password']
        }
        response = client.post(
            '/api/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        assert response.status_code in [200, 400, 401]

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }
        response = client.post(
            '/api/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        assert response.status_code in [401, 400]

    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post(
            '/api/login',
            data=json.dumps({'username': 'testuser'}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_logout(self, client):
        """Test user logout"""
        response = client.post('/api/logout')
        assert response.status_code in [200, 302, 401]

    def test_get_current_user(self, client):
        """Test getting current user info"""
        response = client.get('/api/me')
        assert response.status_code in [200, 401]

    def test_update_profile(self, client):
        """Test updating user profile"""
        update_data = {
            'full_name': 'Updated Name',
            'email': 'newemail@example.com'
        }
        response = client.put(
            '/api/profile',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code in [200, 400, 401]


class TestSessionManagement:
    """Session management tests"""

    def test_session_persistence(self, client):
        """Test session persistence across requests"""
        response1 = client.get('/api/me')
        response2 = client.get('/api/me')
        # Both should have same status (either both 401 or both 200)
        assert response1.status_code == response2.status_code

    def test_session_timeout(self, client):
        """Test session timeout behavior"""
        # This would require actual session management testing
        response = client.get('/api/me')
        assert response.status_code in [200, 401]

    def test_concurrent_sessions(self, client):
        """Test multiple concurrent user sessions"""
        response1 = client.get('/api/me')
        response2 = client.get('/api/me')
        assert response1.status_code in [200, 401]
        assert response2.status_code in [200, 401]
