from fastapi import APIRouter

# Import routers
from . import health, strategies, backtests, paper_trading

# Create main router
api_router = APIRouter()

# Include routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(paper_trading.router, prefix="/paper-trading", tags=["paper-trading"])

__all__ = ["api_router"]
