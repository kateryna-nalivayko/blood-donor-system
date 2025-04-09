import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from app.users.models import User

@pytest.mark.asyncio
async def test_register_user(client, monkeypatch):
    """Test user registration endpoint with proper mocking"""
    find_mock = AsyncMock(return_value=None)  
    add_mock = AsyncMock(return_value=None)   
    
    monkeypatch.setattr("app.users.dao.UsersDAO.find_one_or_none", find_mock)
    monkeypatch.setattr("app.users.dao.UsersDAO.add", add_mock)
    

    response = await client.post(
        "/auth/register",
        json={
            "email": "test_unique@example.com", 
            "password": "SecurePass123",
            "first_name": "Test", 
            "last_name": "User",
            "phone_number": "+380987654321"
        }
    )
    

    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
    

    assert response.status_code == 200
    assert response.json() == {"message": "You are successfully registered!"}
    

    find_mock.assert_called_once()
    add_mock.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_already_exists(client, monkeypatch):
    """Test registration when user already exists"""

    existing_user = AsyncMock()
    existing_user.email = "test_unique@example.com"
    

    find_mock = AsyncMock(return_value=existing_user)
    add_mock = AsyncMock(return_value=None)
    

    monkeypatch.setattr("app.users.dao.UsersDAO.find_one_or_none", find_mock)
    monkeypatch.setattr("app.users.dao.UsersDAO.add", add_mock)
    

    response = await client.post(
        "/auth/register",
        json={
            "email": "test_unique@example.com", 
            "password": "SecurePass123",
            "first_name": "Test", 
            "last_name": "User",
            "phone_number": "+380987654321"
        }
    )
    

    assert response.status_code == 409
    assert "User already exists" in response.json()["detail"]
    

    find_mock.assert_called_once()
    add_mock.assert_not_called()  

@pytest.mark.asyncio
async def test_login_user(client, mock_users_dao, monkeypatch):
    """Test user login endpoint"""

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    
    async def mock_authenticate_user(email, password):
        return mock_user
    
    monkeypatch.setattr("app.users.router.authenticate_user", mock_authenticate_user)
    
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "SecurePass123"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "User test@example.com successfully logged in" in response.json()["message"]


@pytest.mark.asyncio
async def test_logout_user(client):
    """Test user logout endpoint successfully deletes access token cookie"""
    
    response = await client.post("/auth/logout/")
    
    assert response.status_code == status.HTTP_200_OK
    
    assert response.json() == {"message": "User successfully logged out!"}
    
    cookie_header = response.headers.get("set-cookie", "")
    assert "user_access_token=" in cookie_header