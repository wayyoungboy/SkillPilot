"""Authentication Service Unit Tests"""

import pytest

from skillpilot.core.models import UserRole
from skillpilot.core.services.auth import AuthService


class TestAuthService:
    """Authentication service tests"""

    @pytest.mark.skip(reason="bcrypt version compatibility issue")
    def test_hash_password(self):
        """Test password hashing"""
        service = AuthService()
        password = "test_password123"
        hashed = service.hash_password(password)

        assert hashed != password
        assert service.verify_password(password, hashed)
        assert not service.verify_password("wrong_password", hashed)

    def test_create_access_token(self):
        """Test access token creation"""
        service = AuthService()
        token = service.create_access_token(
            user_id="usr_test123",
            email="test@example.com",
            role=UserRole.PERSONAL,
            permissions=["skill:read", "skill:write"],
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        service = AuthService()
        token = service.create_refresh_token("usr_test123")

        assert token is not None
        assert isinstance(token, str)

    def test_decode_token_valid(self):
        """Test token decoding - valid token"""
        service = AuthService()
        token = service.create_access_token(
            user_id="usr_test123",
            email="test@example.com",
            role=UserRole.FREE,
            permissions=["skill:read"],
        )

        payload = service.decode_token(token)

        assert payload is not None
        assert payload.sub == "usr_test123"
        assert payload.email == "test@example.com"
        assert payload.role == UserRole.FREE

    def test_decode_token_invalid(self):
        """Test token decoding - invalid token"""
        service = AuthService()
        payload = service.decode_token("invalid_token")

        assert payload is None

    def test_get_permissions(self):
        """Test permission retrieval"""
        free_perms = AuthService._get_permissions(UserRole.FREE)
        assert "skill:read" in free_perms

        admin_perms = AuthService._get_permissions(UserRole.ADMIN)
        assert "*" in admin_perms
