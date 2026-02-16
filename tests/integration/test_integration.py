"""Integration tests for backtest and paper trading services."""

import pytest
from backend.app.models import Strategy, StrategyType
from backend.app.services import BacktestService, PaperTradingService


def _create_test_strategy(db_session, owner_id):
    """Helper to create a test strategy in the database."""
    strategy = Strategy(
        owner_id=owner_id,
        name="MA_RSI Test",
        description="Test MA_RSI strategy",
        strategy_type=StrategyType.MA_RSI,
        config={
            "fast_window": 10,
            "slow_window": 20,
            "rsi_window": 14,
            "rsi_overbought": 70.0,
            "rsi_oversold": 30.0,
            "use_rsi_filter": False,
        },
        initial_capital=10000,
        stop_loss_pct=2,
        take_profit_rr=2,
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


@pytest.mark.integration
def test_backtest_service_run(db_session, test_user):
    """Test running a backtest via BacktestService.

    Marked as integration because it calls yfinance which requires network access.
    """
    strategy = _create_test_strategy(db_session, test_user.id)

    result = BacktestService.run_backtest(
        db=db_session,
        strategy_id=strategy.id,
        pair="USDJPY",
        timeframe="15m",
        period="60d",
        limit=2000,
        owner_id=test_user.id,
    )

    # If network is unavailable, the service returns an error dict rather than raising
    if "error" in result:
        pytest.skip(f"Skipping due to network/data issue: {result['error']}")

    assert result["status"] == "success"
    assert "backtest_id" in result
    assert isinstance(result["backtest_id"], int)
    assert "total_return_pct" in result
    assert "winrate_pct" in result
    assert "num_trades" in result
    assert result["pair"] == "USDJPY"
    assert result["timeframe"] == "15m"


def test_paper_trading_service_create_session(db_session, test_user):
    """Test creating a paper trading session."""
    strategy = _create_test_strategy(db_session, test_user.id)

    result = PaperTradingService.create_session(
        db=db_session,
        owner_id=test_user.id,
        strategy_id=strategy.id,
        pair="USDJPY",
        timeframe="15m",
        name="PT Test Session",
        initial_capital=10000.0,
    )

    assert "error" not in result
    assert result["status"] == "success"
    assert "session_id" in result
    assert isinstance(result["session_id"], int)
    assert result["name"] == "PT Test Session"
    assert result["pair"] == "USDJPY"
    assert result["timeframe"] == "15m"
    assert result["initial_capital"] == 10000.0


def test_paper_trading_service_close_session(db_session, test_user):
    """Test creating and then closing a paper trading session."""
    strategy = _create_test_strategy(db_session, test_user.id)

    create_result = PaperTradingService.create_session(
        db=db_session,
        owner_id=test_user.id,
        strategy_id=strategy.id,
        pair="USDJPY",
        timeframe="15m",
        name="PT Close Test",
        initial_capital=10000.0,
    )

    assert "error" not in create_result
    session_id = create_result["session_id"]

    close_result = PaperTradingService.close_session(
        db=db_session,
        session_id=session_id,
    )

    assert "error" not in close_result
    assert close_result["status"] == "success"
    assert close_result["session_id"] == session_id
    assert close_result["message"] == "Session closed"
    assert "final_capital" in close_result
    assert "total_return_pct" in close_result
