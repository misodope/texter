"""Warp management endpoints"""
import logging
from fastapi import APIRouter, HTTPException
from oz_agent_sdk import AsyncOzAPI
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/warp", tags=["warp"])


def _get_client() -> AsyncOzAPI:
    return AsyncOzAPI(api_key=settings.warp_api_key)


@router.get("/test")
async def test_warp_connection():
    """Test Warp API connection and show current config"""
    try:
        client = _get_client()
        runs = await client.agent.runs.list()

        return {
            "success": True,
            "message": "Warp API connection successful",
            "api_key_configured": bool(settings.warp_api_key),
            "environment_configured": bool(settings.warp_environment_id),
            "recent_runs": len(runs.data) if runs.data else 0,
        }
    except Exception as e:
        logger.error(f"Error testing Warp connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
