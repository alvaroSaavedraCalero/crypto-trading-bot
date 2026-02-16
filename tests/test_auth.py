"""Tests for authentication endpoints (register, login, protected access)."""


def test_register_success(client):
    """Test registering a new user returns a JWT."""
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_username(client, test_user):
    """Test registering with an existing username returns 400."""
    payload = {
        "username": "testuser",
        "email": "different@example.com",
        "password": "somepassword",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_duplicate_email(client, test_user):
    """Test registering with an existing email returns 400."""
    payload = {
        "username": "differentuser",
        "email": "test@example.com",
        "password": "somepassword",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    """Test logging in with valid credentials returns a JWT."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test logging in with wrong password returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_wrong_username(client):
    """Test logging in with nonexistent username returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "anypassword"},
    )
    assert response.status_code == 401


def test_access_protected_without_token(client):
    """Test accessing a protected endpoint without auth returns 401."""
    response = client.get("/api/v1/strategies/")
    assert response.status_code == 401


def test_access_protected_with_invalid_token(client):
    """Test accessing a protected endpoint with an invalid token returns 401."""
    headers = {"Authorization": "Bearer invalid-token-value"}
    response = client.get("/api/v1/strategies/", headers=headers)
    assert response.status_code == 401
