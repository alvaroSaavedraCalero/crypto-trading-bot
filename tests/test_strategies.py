"""Tests for strategy CRUD endpoints."""


def test_list_strategies_unauthenticated(client):
    """Test that listing strategies without auth returns 401."""
    response = client.get("/api/v1/strategies/")
    assert response.status_code == 401


def test_list_strategies_empty(client, auth_headers):
    """Test listing strategies when none exist."""
    response = client.get("/api/v1/strategies/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_strategy(client, auth_headers):
    """Test creating a new strategy."""
    payload = {
        "name": "Test MA RSI",
        "description": "Test strategy",
        "strategy_type": "MA_RSI",
        "config": {"fast_window": 10, "slow_window": 30, "rsi_window": 14},
        "initial_capital": 10000,
        "stop_loss_pct": 2,
        "take_profit_rr": 2,
    }
    response = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test MA RSI"
    assert data["strategy_type"] == "MA_RSI"
    assert data["config"] == payload["config"]


def test_create_strategy_invalid_type(client, auth_headers):
    """Test creating a strategy with invalid type returns 400."""
    payload = {
        "name": "Bad Strategy",
        "strategy_type": "INVALID_TYPE",
        "config": {},
    }
    response = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid strategy_type" in response.json()["detail"]


def test_get_strategy(client, auth_headers):
    """Test getting a single strategy by ID."""
    # Create first
    payload = {
        "name": "Get Test",
        "strategy_type": "MA_RSI",
        "config": {"fast_window": 10, "slow_window": 30, "rsi_window": 14},
    }
    create_resp = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    strategy_id = create_resp.json()["id"]

    # Get
    response = client.get(f"/api/v1/strategies/{strategy_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test"


def test_update_strategy(client, auth_headers):
    """Test updating a strategy."""
    payload = {
        "name": "Update Test",
        "strategy_type": "MA_RSI",
        "config": {"fast_window": 10, "slow_window": 30, "rsi_window": 14},
    }
    create_resp = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    strategy_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/v1/strategies/{strategy_id}",
        json={"name": "Updated Name"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Name"


def test_delete_strategy(client, auth_headers):
    """Test deleting a strategy."""
    payload = {
        "name": "Delete Test",
        "strategy_type": "MA_RSI",
        "config": {"fast_window": 10, "slow_window": 30, "rsi_window": 14},
    }
    create_resp = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    strategy_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/strategies/{strategy_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    # Verify deleted
    get_resp = client.get(f"/api/v1/strategies/{strategy_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_clone_strategy(client, auth_headers):
    """Test cloning a strategy."""
    payload = {
        "name": "Clone Source",
        "strategy_type": "MA_RSI",
        "config": {"fast_window": 10, "slow_window": 30, "rsi_window": 14},
    }
    create_resp = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    strategy_id = create_resp.json()["id"]

    clone_resp = client.post(f"/api/v1/strategies/{strategy_id}/clone", headers=auth_headers)
    assert clone_resp.status_code == 200
    data = clone_resp.json()
    assert data["name"] == "Clone Source (copy)"
    assert data["config"] == payload["config"]
    assert data["id"] != strategy_id


def test_list_strategy_types(client):
    """Test listing available strategy types."""
    response = client.get("/api/v1/strategies/types")
    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert "MA_RSI" in data["types"]
    assert "MACD_ADX" in data["types"]


def test_strategy_not_found(client, auth_headers):
    """Test getting a non-existent strategy returns 404."""
    response = client.get("/api/v1/strategies/99999", headers=auth_headers)
    assert response.status_code == 404
