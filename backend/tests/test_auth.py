"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status


class TestUserRegistration:
    """Tests for user registration endpoint"""

    def test_register_new_user_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
                "age": 25,
                "gender": "male"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["token"]) > 0

    def test_register_duplicate_email(self, client):
        """Test registration with existing email"""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Password123!",
            }
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass123!",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "Password123!",
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_with_profile_info(self, client):
        """Test registration with full profile information"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "fullprofile@example.com",
                "password": "Password123!",
                "name": "Full Profile User",
                "age": 30,
                "gender": "female",
                "height_cm": 165.0,
                "weight_kg": 60.0,
                "target_weight_kg": 55.0,
                "activity_level": "moderately_active",
                "health_goal": "weight_loss"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "token" in data


class TestUserLogin:
    """Tests for user login endpoint"""

    def test_login_success(self, client):
        """Test successful user login"""
        # First register a user
        register_data = {
            "email": "loginuser@example.com",
            "password": "LoginPass123!",
        }
        client.post("/api/v1/auth/register", json=register_data)

        # Now login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginuser@example.com",
                "password": "LoginPass123!",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Test login with incorrect password"""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123!",
            }
        )

        # Try login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass123!",
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!",
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserProfile:
    """Tests for user profile endpoints"""

    @pytest.fixture
    def authenticated_user(self, client):
        """Create and authenticate a user, return token"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "authuser@example.com",
                "password": "AuthPass123!",
                "name": "Auth User",
                "age": 28,
                "gender": "male",
                "height_cm": 180.0,
                "weight_kg": 75.0
            }
        )
        return response.json()["token"]

    def test_get_profile_authenticated(self, client, authenticated_user):
        """Test getting profile with valid authentication"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {authenticated_user}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "authuser@example.com"
        assert data["name"] == "Auth User"
        assert data["age"] == 28

    def test_get_profile_without_auth(self, client):
        """Test getting profile without authentication"""
        response = client.get("/api/v1/auth/profile")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self, client, authenticated_user):
        """Test updating user profile"""
        response = client.put(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {authenticated_user}"},
            json={
                "name": "Updated Name",
                "age": 29,
                "weight_kg": 73.0,
                "target_weight_kg": 70.0
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["age"] == 29
        assert data["weight_kg"] == 73.0

    def test_get_me_endpoint(self, client, authenticated_user):
        """Test /me endpoint"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {authenticated_user}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "authuser@example.com"

    def test_get_demo_profile(self, client):
        """Test demo profile endpoint (no auth required)"""
        response = client.get("/api/v1/auth/demo-profile")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "demo@fitmealor.com"
        assert data["id"] == 0
