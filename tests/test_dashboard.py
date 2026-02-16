"""Tests for dashboard endpoints."""

from backend.app.models import Strategy, StrategyType


def test_get_stats_unauthenticated(client):
    """Test that getting stats without auth returns 401."""
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


def test_get_stats_empty(client, auth_headers):
    """Test getting stats with auth but no data returns zeros/defaults."""
    response = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_strategies"] == 0
    assert data["active_backtests"] == 0
    assert data["paper_trading_sessions"] == 0
    assert data["total_trades"] == 0
    assert data["portfolio_value"] == 10000.0
    assert data["daily_return"] == 0.0


def test_get_summary_unauthenticated(client):
    """Test that getting summary without auth returns 401."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


def test_get_summary_empty(client, auth_headers):
    """Test getting summary with auth but no data returns empty lists."""
    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["recent_backtests"] == []
    assert data["active_sessions"] == []
    assert data["best_strategies"] == []


def test_get_stats_with_strategies(client, auth_headers, db_session, test_user):
    """Test that stats reflect created strategies."""
    for i in range(3):
        strategy = Strategy(
            owner_id=test_user.id,
            name=f"Strategy {i}",
            strategy_type=StrategyType.MA_RSI,
            config={"fast_window": 10, "slow_window": 30, "rsi_window": 14},
        )
        db_session.add(strategy)
    db_session.commit()

    response = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_strategies"] == 3


def test_get_summary_structure(client, auth_headers):
    """Test that summary response has correct top-level keys."""
    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "recent_backtests" in data
    assert "active_sessions" in data
    assert "best_strategies" in data
