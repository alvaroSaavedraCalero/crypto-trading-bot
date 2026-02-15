"""Health check endpoints."""

import asyncio
from datetime import datetime

import psutil
from fastapi import APIRouter, HTTPException

from ...config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Health check endpoint with system metrics."""
    try:
        cpu_percent = await asyncio.to_thread(psutil.cpu_percent)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage("/")

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_info.percent,
                "disk_usage_percent": disk_info.percent,
            },
            "version": settings.APP_VERSION,
        }
    except Exception:
        if settings.DEBUG:
            raise
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"ready": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}
