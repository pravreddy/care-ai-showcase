"""Unit tests for authentication service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.auth_service import (
    register_user,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.models.database import User


class TestAuthService:
    """Test authentication service functions."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session: AsyncSession):
        """Test successful user registration."""
        user = await register_user(
            db=db_session,
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User",
            organisation="Test Org",
            role="Developer"
        )
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_admin is False
        assert user.hashed_password != "SecurePass123!"  # Password should be hashed
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db_session: AsyncSession):
        """Test registration with duplicate email fails."""
        # Create first user
        await register_user(
            db=db_session,
            email="duplicate@example.com",
            password="Pass123!",
            full_name="First User",
        )
        
        # Try to create second user with same email
        with pytest.raises(Exception):  # Should raise an integrity error
            await register_user(
                db=db_session,
                email="duplicate@example.com",
                password="Pass456!",
                full_name="Second User",
            )
    
    @pytest.mark.asyncio
    async def test_password_verification(self, db_session: AsyncSession):
        """Test password hashing and verification."""
        user = await register_user(
            db=db_session,
            email="passtest@example.com",
            password="MySecretPass123!",
            full_name="Pass Test",
        )
        
        # Correct password should verify
        assert verify_password("MySecretPass123!", user.hashed_password) is True
        
        # Wrong password should not verify
        assert verify_password("WrongPassword", user.hashed_password) is False
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        from jose import jwt
        from app.core.config import settings
        
        token = create_access_token(
            data={"sub": "test@example.com", "user_id": "123"}
        )
        
        assert token is not None
        
        # Decode and verify
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == "123"
        assert "exp" in decoded
    
    @pytest.mark.asyncio
    async def test_user_has_required_fields(self, db_session: AsyncSession):
        """Test that user model has all required fields including is_admin."""
        user = await register_user(
            db=db_session,
            email="fieldtest@example.com",
            password="Pass123!",
            full_name="Field Test",
        )
        
        # Check all expected fields exist
        assert hasattr(user, 'id')
        assert hasattr(user, 'email')
        assert hasattr(user, 'hashed_password')
        assert hasattr(user, 'full_name')
        assert hasattr(user, 'organisation')
        assert hasattr(user, 'role')
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'is_verified')
        assert hasattr(user, 'is_admin')  # This is the field that was missing!
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')
        assert hasattr(user, 'last_login')
        assert hasattr(user, 'totp_secret')
        assert hasattr(user, 'totp_enabled')
        assert hasattr(user, 'totp_verified')
        assert hasattr(user, 'recovery_codes_hash')
        assert hasattr(user, 'coupon_code')
