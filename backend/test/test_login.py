import pytest
from httpx import AsyncClient

import pytest
from httpx import AsyncClient
from app.users.schemas import UserRegister  # Add this import

@pytest.mark.asyncio
async def test_sign_new_user(default_client: AsyncClient):
    payload = {
            "email": "test_unique@example.com", 
            "password": "SecurePass123",
            "first_name": "Test", 
            "last_name": "User",
            "phone_number": "+380987654321"
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    test_response = {
        "message": "You are successfully registered!"
    }

    response = await default_client.post("/auth/register", json=payload, headers=headers)
    
    # Add debug print if needed
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
    assert response.status_code == 200
    assert response.json() == test_response


@pytest.mark.asyncio
async def test_successful_login(default_client: AsyncClient):

    login_payload = {
        "email": "test_unique@example.com",
        "password": "SecurePass123"
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = await default_client.post("/auth/login", json=login_payload, headers=headers)
    
    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert "message" in response_data
    assert f"User {login_payload['email']} successfully logged in" in response_data["message"]
    assert "user_access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(default_client: AsyncClient):
    login_payload = {
        "email": "test_login@example.com",
        "password": "WrongPassword123"
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = await default_client.post("/auth/login", json=login_payload, headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(default_client: AsyncClient):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "TestPass123"
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    response = await default_client.post("/auth/login", json=login_payload, headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"