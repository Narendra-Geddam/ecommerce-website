"""
JWT Handler for Microservices

Provides JWT token creation, verification, and management.
Supports access tokens and refresh tokens with Redis blacklisting.
"""
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
import redis


class JWTHandler:
    """JWT token handler with Redis support for token blacklisting"""

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expires: int = 3600,  # 1 hour
        refresh_token_expires: int = 604800,  # 7 days
        redis_client: redis.Redis = None
    ):
        self.secret_key = secret_key or os.environ.get('JWT_SECRET_KEY')
        if not self.secret_key:
            raise RuntimeError('JWT_SECRET_KEY environment variable is required')
        self.algorithm = algorithm
        self.access_token_expires = access_token_expires
        self.refresh_token_expires = refresh_token_expires
        self.redis_client = redis_client

    def create_access_token(self, user_id: int, email: str, name: str, is_admin: bool = False) -> str:
        """Create an access token for authenticated user"""
        payload = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'is_admin': bool(is_admin),
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(seconds=self.access_token_expires),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        """Create a refresh token for token renewal"""
        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(seconds=self.refresh_token_expires),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token and return the payload if valid.
        Returns None if token is invalid or blacklisted.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get('type') != token_type:
                return None

            # Check if token is blacklisted (if Redis is available)
            if self.redis_client and self._is_blacklisted(token):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode a token without verification (useful for debugging)"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return None

    def blacklist_token(self, token: str, expires_in: int = None) -> bool:
        """
        Add a token to the blacklist (requires Redis).
        Used for logout and token revocation.
        """
        if not self.redis_client:
            return False

        try:
            # Get token expiry if not provided
            if expires_in is None:
                payload = self.decode_token(token)
                if payload and 'exp' in payload:
                    expires_in = max(0, int(payload['exp'] - time.time()))
                else:
                    expires_in = 86400  # Default 24 hours

            self.redis_client.setex(f"blacklist:{token}", expires_in, "1")
            return True
        except Exception:
            return False

    def _is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        if not self.redis_client:
            return False
        return bool(self.redis_client.exists(f"blacklist:{token}"))

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# Module-level functions for convenience
_handler: Optional[JWTHandler] = None


def get_handler() -> JWTHandler:
    """Get the global JWT handler instance"""
    global _handler
    if _handler is None:
        redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
        try:
            redis_client = redis.from_url(redis_url)
        except Exception:
            redis_client = None
        _handler = JWTHandler(redis_client=redis_client)
    return _handler


def create_token(user_id: int, email: str, name: str, token_type: str = 'access', is_admin: bool = False) -> str:
    """Create an access or refresh token"""
    handler = get_handler()
    if token_type == 'refresh':
        return handler.create_refresh_token(user_id)
    return handler.create_access_token(user_id, email, name, is_admin=is_admin)


def verify_token(token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
    """Verify a token"""
    handler = get_handler()
    return handler.verify_token(token, token_type)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a token without verification"""
    handler = get_handler()
    return handler.decode_token(token)
