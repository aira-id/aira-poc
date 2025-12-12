from fastapi import APIRouter
from datetime import datetime
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Add checks for ASR, LLM, TTS services when implemented
    return {
        "status": "ready",
        "services": {
            "asr": "not_configured",
            "llm": "not_configured",
            "tts": "not_configured"
        }
    }
