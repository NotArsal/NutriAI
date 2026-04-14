"""
tests/test_auth.py — Testing User registration and login logic with mock DB.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, AsyncMock

from app.models.user import User

def test_register_user_success(client, monkeypatch):
    """Verify registration logic: check for existing user, then create."""
    user_data = {"email": "new@example.com", "password": "password123"}
    
    # Mock UserRepository.get_by_email to return None (user doesn't exist)
    # Mock UserRepository.create to return a User object
    mock_user = User(id=1, email="new@example.com", role="patient", is_active=True)
    
    async def mock_get_by_email(*args, **kwargs): return None
    async def mock_create(*args, **kwargs): return mock_user
    
    monkeypatch.setattr("app.repositories.user_repo.UserRepository.get_by_email", mock_get_by_email)
    monkeypatch.setattr("app.repositories.user_repo.UserRepository.create", mock_create)
    
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert "id" in response.json()

def test_login_success(client, monkeypatch):
    """Verify login logic: check password and return token."""
    from app.core.security import get_password_hash
    
    hashed = get_password_hash("password123")
    mock_user = User(id=1, email="test@example.com", hashed_password=hashed, is_active=True)
    
    async def mock_get_by_email(*args, **kwargs): return mock_user
    monkeypatch.setattr("app.repositories.user_repo.UserRepository.get_by_email", mock_get_by_email)
    
    login_data = {"username": "test@example.com", "password": "password123"}
    response = client.post("/auth/login", data=login_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
