"""Tests for paper trading endpoints."""


def _create_strategy(client, auth_headers):
    """Helper to create a strategy and return its ID."""
    payload = {
        "name": "Test Strategy",
        "strategy_type": "MA_RSI",
        "config": {"fast_window": 10, "slow_window": 30, "rsi_window": 14},
        "initial_capital": 10000,
        "stop_loss_pct": 2,
        "take_profit_rr": 2,
    }
    resp = client.post("/api/v1/strategies/", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    return resp.json()["id"]


def test_list_sessions_unauthenticated(client):
    """Test that listing paper trading sessions without auth returns 401."""
    response = client.get("/api/v1/paper-trading")
    assert response.status_code == 401


def test_list_sessions_empty(client, auth_headers):
    """Test listing paper trading sessions when none exist."""
    response = client.get("/api/v1/paper-trading", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_session(client, auth_headers):
    """Test creating a paper trading session."""
    strategy_id = _create_strategy(client, auth_headers)

    payload = {
        "name": "Test Session",
        "strategy_id": strategy_id,
        "pair": "BTCUSD",
        "timeframe": "15m",
    }
    response = client.post("/api/v1/paper-trading", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["name"] == "Test Session"
    assert data["pair"] == "BTCUSD"
    assert data["timeframe"] == "15m"
    assert "session_id" in data


def test_get_session_not_found(client, auth_headers):
    """Test getting a non-existent paper trading session returns 404."""
    response = client.get("/api/v1/paper-trading/99999", headers=auth_headers)
    assert response.status_code == 404


def test_get_session_trades_not_found(client, auth_headers):
    """Test getting trades for a non-existent session returns 404."""
    response = client.get("/api/v1/paper-trading/99999/trades", headers=auth_headers)
    assert response.status_code == 404


def test_close_session_not_found(client, auth_headers):
    """Test closing a non-existent session returns 404."""
    response = client.post("/api/v1/paper-trading/99999/close", headers=auth_headers)
    assert response.status_code == 404
