"""
Tests for history API endpoints
"""
import pytest
from fastapi import status


class TestHistoryAPI:
    """Tests for history endpoints"""

    @pytest.fixture
    def authenticated_user(self, client):
        """Create and authenticate a user, return token"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "historyuser@example.com",
                "password": "HistoryPass123!",
                "name": "History User"
            }
        )
        return response.json()["token"]

    def test_get_all_history_empty(self, client, authenticated_user):
        """Test getting history when user has no data"""
        response = client.get(
            "/api/v1/history/all",
            headers={"Authorization": f"Bearer {authenticated_user}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "recommendations" in data
        assert "products" in data
        assert data["recommendations"]["count"] == 0
        assert data["products"]["count"] == 0

    def test_add_recommendation_to_history(self, client, authenticated_user):
        """Test adding a meal recommendation to history"""
        recommendation_data = {
            "meal_code": "MEAL001",
            "meal_name_ko": "비빔밥",
            "meal_name_en": "Bibimbap",
            "calories": 500,
            "carbohydrates": 80,
            "protein": 20,
            "fat": 15,
            "sodium": 1000
        }

        response = client.post(
            "/api/v1/history/recommendations/add",
            headers={"Authorization": f"Bearer {authenticated_user}"},
            json=recommendation_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "history_id" in data

    def test_get_recommendation_history(self, client, authenticated_user):
        """Test getting recommendation history"""
        # First add a recommendation
        client.post(
            "/api/v1/history/recommendations/add",
            headers={"Authorization": f"Bearer {authenticated_user}"},
            json={
                "meal_code": "MEAL002",
                "meal_name_ko": "김치찌개",
                "meal_name_en": "Kimchi Stew",
                "calories": 300,
                "protein": 15,
                "fat": 10
            }
        )

        # Get history
        response = client.get(
            "/api/v1/history/recommendations",
            headers={"Authorization": f"Bearer {authenticated_user}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] >= 1
        assert len(data["history"]) >= 1

        # Check first item
        first_item = data["history"][0]
        assert first_item["meal_code"] == "MEAL002"
        assert first_item["meal_name_ko"] == "김치찌개"
        assert first_item["meal_name_en"] == "Kimchi Stew"
        assert first_item["nutrition_info"]["calories"] == 300

    def test_get_all_history_with_data(self, client, authenticated_user):
        """Test getting all history after adding recommendations"""
        # Add multiple recommendations
        for i in range(3):
            client.post(
                "/api/v1/history/recommendations/add",
                headers={"Authorization": f"Bearer {authenticated_user}"},
                json={
                    "meal_code": f"MEAL00{i}",
                    "meal_name_ko": f"음식{i}",
                    "calories": 400 + (i * 50)
                }
            )

        response = client.get(
            "/api/v1/history/all",
            headers={"Authorization": f"Bearer {authenticated_user}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["recommendations"]["count"] >= 3

    def test_history_pagination(self, client, authenticated_user):
        """Test history pagination"""
        # Add many recommendations
        for i in range(10):
            client.post(
                "/api/v1/history/recommendations/add",
                headers={"Authorization": f"Bearer {authenticated_user}"},
                json={
                    "meal_code": f"MEAL_{i:03d}",
                    "meal_name_ko": f"음식_{i}",
                    "calories": 300
                }
            )

        # Get first 5
        response = client.get(
            "/api/v1/history/recommendations?limit=5",
            headers={"Authorization": f"Bearer {authenticated_user}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["history"]) == 5

    def test_history_without_auth(self, client):
        """Test accessing history without authentication"""
        response = client.get("/api/v1/history/all")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_isolation(self, client):
        """Test that users can only see their own history"""
        # Create two users
        user1_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "password": "User1Pass123!",
            }
        )
        user1_token = user1_response.json()["token"]

        user2_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "password": "User2Pass123!",
            }
        )
        user2_token = user2_response.json()["token"]

        # User 1 adds a recommendation
        client.post(
            "/api/v1/history/recommendations/add",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "meal_code": "USER1_MEAL",
                "meal_name_ko": "사용자1 음식",
                "calories": 500
            }
        )

        # User 2 should not see User 1's history
        response = client.get(
            "/api/v1/history/all",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["recommendations"]["count"] == 0
