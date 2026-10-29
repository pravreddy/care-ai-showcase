"""Integration tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_endpoint(self, client: AsyncClient, test_user_data: dict):
        """Test user registration endpoint."""
        response = await client.post("/api/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data: dict):
        """Test that registering with duplicate email fails."""
        # Register first user
        response1 = await client.post("/api/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Try to register with same email
        response2 = await client.post("/api/auth/register", json=test_user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful login."""
        # First register
        await client.post("/api/auth/register", json=test_user_data)
        
        # Then login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user_data: dict):
        """Test login with wrong password fails."""
        # Register user
        await client.post("/api/auth/register", json=test_user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = await client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client: AsyncClient):
        """Test getting current user info with valid token."""
        response = await authenticated_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email" in data
        assert "full_name" in data
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without token fails."""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_validates_email(self, client: AsyncClient):
        """Test that registration validates email format."""
        invalid_data = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        response = await client.post("/api/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_requires_password(self, client: AsyncClient):
        """Test that registration requires password."""
        invalid_data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        response = await client.post("/api/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_user_has_admin_field(self, authenticated_client: AsyncClient):
        """Test that user response includes is_admin field."""
        response = await authenticated_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        # This is the critical test - is_admin should be present
        assert "is_admin" in data
        assert isinstance(data["is_admin"], bool)
        assert data["is_admin"] is False  # Should be False by default
