"""
Auth Service

Handles user authentication with JWT tokens:
- User registration
- Login with JWT token generation
- Token refresh
- Logout with token blacklisting
- User profile management
"""
import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, g

# Add shared libraries to path (in Docker, shared is at /app/shared)
sys.path.insert(0, '/app/shared')

from database.pool import get_connection_pool, get_db_connection
from auth.jwt_handler import JWTHandler
from middleware.logging import setup_logging, request_logger
from validation.input_validators import (
    normalize_email,
    validate_profile_payload,
    validate_registration_payload,
)

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required')
if not SECRET_KEY:
    raise RuntimeError('JWT_SECRET_KEY or SECRET_KEY environment variable is required')
ACCESS_TOKEN_EXPIRES = int(os.environ.get('ACCESS_TOKEN_EXPIPIRES', 3600))  # 1 hour
REFRESH_TOKEN_EXPIPIRES = int(os.environ.get('REFRESH_TOKEN_EXPIPIRES', 604800))  # 7 days

# Setup logging
setup_logging('auth-service')
request_logger.init_app(app)

# Initialize database pool
db_pool = get_connection_pool(DATABASE_URL)

# Initialize Redis for token blacklisting
import redis
try:
    redis_client = redis.from_url(REDIS_URL)
except Exception:
    redis_client = None

# JWT Handler
jwt_handler = JWTHandler(
    secret_key=SECRET_KEY,
    access_token_expires=ACCESS_TOKEN_EXPIRES,
    refresh_token_expires=REFRESH_TOKEN_EXPIPIRES,
    redis_client=redis_client
)


def is_admin_email(email: str) -> bool:
    admin_emails = {
        value.strip().lower()
        for value in os.environ.get('ADMIN_EMAILS', 'admin@shopeasy.local').split(',')
        if value.strip()
    }
    return email.strip().lower() in admin_emails


def get_request_user():
    """Extract user info from request headers (set by API Gateway)"""
    user_id = request.headers.get('X-User-ID')
    if user_id:
        g.user_id = int(user_id)
        g.user_email = request.headers.get('X-User-Email', '')
        g.user_name = request.headers.get('X-User-Name', '')
        g.user_is_admin = request.headers.get('X-User-Is-Admin', '').lower() == 'true'
        return True
    return False


def require_admin_request():
    """Ensure the forwarded request is from an admin user."""
    if not get_request_user():
        return False, (jsonify({'error': 'Not authenticated'}), 401)
    if not getattr(g, 'user_is_admin', False):
        return False, (jsonify({'error': 'Admin access required'}), 403)
    return True, None


# Health endpoints
@app.route('/health')
def health():
    """Health check for liveness probe"""
    return jsonify({'status': 'healthy', 'service': 'auth-service'})


@app.route('/ready')
def ready():
    """Readiness probe - checks database connection"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT 1')
        db_status = 'connected'
        status_code = 200
    except Exception as e:
        db_status = f'error: {str(e)}'
        status_code = 503

    return jsonify({
        'status': 'ready' if status_code == 200 else 'not_ready',
        'service': 'auth-service',
        'database': db_status,
        'redis': 'connected' if redis_client and redis_client.ping() else 'not_configured'
    }), status_code


@app.route('/live')
def live():
    """Liveness probe"""
    return jsonify({'status': 'alive', 'service': 'auth-service'})


# Auth endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json() or {}

    required = ['name', 'email', 'password']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    is_valid, error, sanitized = validate_registration_payload(data)
    if not is_valid:
        return jsonify({'success': False, 'error': error}), 400

    # Hash password
    hashed_pw = jwt_handler.hash_password(sanitized['password'])

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO users (name, email, password, phone, address, city, state, pincode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, email
            ''', (
                sanitized['name'],
                sanitized['email'],
                hashed_pw,
                sanitized['phone'],
                sanitized['address'],
                sanitized['city'],
                sanitized['state'],
                sanitized['pincode']
            ))

            user = cursor.fetchone()

            # Generate tokens
            access_token = jwt_handler.create_access_token(
                user['id'],
                user['email'],
                user['name'],
                is_admin=is_admin_email(user['email'])
            )
            refresh_token = jwt_handler.create_refresh_token(user['id'])

            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'is_admin': is_admin_email(user['email'])
                },
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': ACCESS_TOKEN_EXPIRES
            })

    except Exception as e:
        if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return JWT tokens"""
    data = request.get_json() or {}

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    email = normalize_email(data.get('email'))
    password = str(data.get('password', ''))
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT id, name, email, password, is_active, is_banned FROM users
                WHERE email = %s
            ''', (email,))

            user = cursor.fetchone()

            if user and jwt_handler.verify_password(password, user['password']):
                if user.get('is_banned'):
                    return jsonify({'success': False, 'error': 'This account has been banned'}), 403
                if not user.get('is_active', True):
                    return jsonify({'success': False, 'error': 'This account is inactive'}), 403

                # Generate tokens
                access_token = jwt_handler.create_access_token(
                    user['id'],
                    user['email'],
                    user['name'],
                    is_admin=is_admin_email(user['email'])
                )
                refresh_token = jwt_handler.create_refresh_token(user['id'])

                return jsonify({
                    'success': True,
                    'user': {
                        'id': user['id'],
                        'name': user['name'],
                        'email': user['email'],
                        'is_admin': is_admin_email(user['email'])
                    },
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'Bearer',
                    'expires_in': ACCESS_TOKEN_EXPIRES
                })

            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    except Exception as e:
        return jsonify({'success': False, 'error': 'Login failed'}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user by blacklisting the token"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Missing Authorization header'}), 401

    token = auth_header[7:]  # Remove 'Bearer ' prefix

    # Blacklist the token
    if jwt_handler.blacklist_token(token):
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    else:
        return jsonify({'success': True, 'message': 'Logged out (token not tracked)'})


@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        return jsonify({'success': False, 'error': 'Refresh token required'}), 400

    # Verify refresh token
    payload = jwt_handler.verify_token(refresh_token, token_type='refresh')

    if not payload:
        return jsonify({'success': False, 'error': 'Invalid or expired refresh token'}), 401

    user_id = payload.get('user_id')

    # Get user details
    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT id, name, email FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404

            # Generate new access token
            access_token = jwt_handler.create_access_token(
                user['id'],
                user['email'],
                user['name'],
                is_admin=is_admin_email(user['email'])
            )

            return jsonify({
                'success': True,
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': ACCESS_TOKEN_EXPIRES
            })

    except Exception as e:
        return jsonify({'success': False, 'error': 'Token refresh failed'}), 500


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info - returns authenticated: false for guests"""
    if not get_request_user():
        return jsonify({'authenticated': False})

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT id, name, email, phone, address, city, state, pincode, created_at, is_active, is_banned
                FROM users WHERE id = %s
            ''', (g.user_id,))

            user = cursor.fetchone()

            if user:
                user['authenticated'] = True
                user['is_admin'] = is_admin_email(user['email'])
                return jsonify(user)

            return jsonify({'authenticated': False, 'error': 'User not found'}), 404

    except Exception as e:
            return jsonify({'authenticated': False, 'error': 'Failed to get user'}), 500


@app.route('/api/auth/admin/users', methods=['GET'])
def admin_list_users():
    """List users for the admin portal."""
    allowed, error_response = require_admin_request()
    if not allowed:
        return error_response

    page = max(1, int(request.args.get('page', 1)))
    page_size = min(100, max(1, int(request.args.get('page_size', 25))))
    offset = (page - 1) * page_size
    search = str(request.args.get('search', '') or '').strip()

    try:
        with db_pool.connection() as cursor:
            base_where = 'WHERE 1=1'
            params = []
            if search:
                base_where += ' AND (name ILIKE %s OR email ILIKE %s)'
                term = f'%{search}%'
                params.extend([term, term])

            cursor.execute(f'SELECT COUNT(*) AS total FROM users {base_where}', params)
            total = cursor.fetchone()['total']

            cursor.execute(f'''
                SELECT id, name, email, phone, city, state, created_at, is_active, is_banned
                FROM users
                {base_where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            ''', params + [page_size, offset])
            users = cursor.fetchall()

            for user in users:
                user['is_admin'] = is_admin_email(user['email'])

            return jsonify({
                'users': users,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size
                }
            })
    except Exception:
        return jsonify({'error': 'Failed to fetch users'}), 500


@app.route('/api/auth/admin/users/<int:user_id>/status', methods=['PUT'])
def admin_update_user_status(user_id):
    """Ban/unban or activate/deactivate users from the admin portal."""
    allowed, error_response = require_admin_request()
    if not allowed:
        return error_response

    data = request.get_json() or {}
    is_banned = bool(data.get('is_banned', False))
    is_active = bool(data.get('is_active', True))

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                UPDATE users
                SET is_banned = %s, is_active = %s
                WHERE id = %s
                RETURNING id, name, email, is_banned, is_active
            ''', (is_banned, is_active, user_id))
            user = cursor.fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            user['is_admin'] = is_admin_email(user['email'])
            return jsonify({'success': True, 'user': user})
    except Exception:
        return jsonify({'error': 'Failed to update user status'}), 500


@app.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    """Update user profile (requires authentication via API Gateway)"""
    if not get_request_user():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    is_valid, error, sanitized = validate_profile_payload(data)
    if not is_valid:
        return jsonify({'success': False, 'error': error}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                UPDATE users SET name = %s, phone = %s, address = %s, city = %s, state = %s, pincode = %s
                WHERE id = %s
            ''', (
                sanitized['name'],
                sanitized['phone'],
                sanitized['address'],
                sanitized['city'],
                sanitized['state'],
                sanitized['pincode'],
                g.user_id
            ))

            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
