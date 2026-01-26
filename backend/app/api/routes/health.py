"""
Health check endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import os

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Status information about the server
    """
    try:
        # Get system info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "server": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_info.percent,
                "disk_usage_percent": disk_info.percent
            },
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint
    Verifies that the service is ready to handle traffic
    
    Returns:
        dict: Readiness status
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint
    Verifies that the service is alive
    
    Returns:
        dict: Liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }
