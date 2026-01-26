from fastapi import APIRouter
from . import health, strategies, backtests, paper_trading, dashboard

router = APIRouter()

# Include route modules
router.include_router(health.router, tags=["health"])
router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
router.include_router(paper_trading.router, prefix="/paper-trading", tags=["paper-trading"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
