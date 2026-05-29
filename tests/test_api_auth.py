"""Tests for the authentication API endpoints."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/register/"

    def test_register_success(self):
        payload = {
            "email": "new@lexora.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "tokens" in data["data"]
        assert User.objects.filter(email="new@lexora.com").exists()

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email="dup@lexora.com", username="dup", password="Pass123!", role="member"
        )
        payload = {
            "email": "dup@lexora.com",
            "username": "dup2",
            "first_name": "D",
            "last_name": "U",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == 400

    def test_register_password_mismatch(self):
        payload = {
            "email": "x@lexora.com",
            "username": "xuser",
            "first_name": "X",
            "last_name": "Y",
            "password": "StrongPass123!",
            "password_confirm": "WrongPass123!",
        }
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/login/"
        self.user = User.objects.create_user(
            email="login@lexora.com", username="loginuser", password="Pass123!", role="member"
        )

    def test_login_success(self):
        response = self.client.post(self.url, {"email": "login@lexora.com", "password": "Pass123!"}, format="json")
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {"email": "login@lexora.com", "password": "Wrong!"}, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestMeAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="me@lexora.com", username="meuser",
            first_name="Me", last_name="User",
            password="Pass123!", role="member"
        )

    def _auth(self):
        resp = self.client.post("/api/v1/auth/login/", {"email": "me@lexora.com", "password": "Pass123!"}, format="json")
        token = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_me_authenticated(self):
        self._auth()
        response = self.client.get("/api/v1/auth/me/")
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "me@lexora.com"

    def test_me_unauthenticated(self):
        response = self.client.get("/api/v1/auth/me/")
        assert response.status_code == 401

    def test_change_password(self):
        self._auth()
        response = self.client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "Pass123!", "new_password": "NewPass456!", "new_password_confirm": "NewPass456!"},
            format="json",
        )
        assert response.status_code == 200
