"""
医保接口SDK健康检查API
提供系统健康状态检查接口
"""

import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str
    timestamp: str
    uptime: float
    version: str
    message: str


router = APIRouter()

# 启动时间
START_TIME = time.time()


@router.get("/health")
async def health_check():
    """
    系统健康检查
    
    Returns:
        HealthStatus: 系统健康状态
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        uptime=time.time() - START_TIME,
        version="1.0.0",
        message="医保接口SDK服务运行正常"
    )


@router.get("/ready")
async def readiness_check():
    """
    就绪检查 - 检查服务是否准备好接收请求
    
    Returns:
        dict: 就绪状态
    """
    return {
        "status": "ready",
        "message": "服务已准备就绪",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/live")
async def liveness_check():
    """
    存活检查 - 检查服务是否存活
    
    Returns:
        dict: 存活状态
    """
    return {
        "status": "alive",
        "message": "服务正常运行",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - START_TIME
    }