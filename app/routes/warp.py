"""Warp management endpoints"""
import logging
from fastapi import APIRouter, HTTPException
from warp_agent_sdk import AsyncWarpAPI
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/warp", tags=["warp"])


@router.get("/environments")
async def list_environments():
    """List all available Warp environments"""
    try:
        client = AsyncWarpAPI(api_key=settings.warp_api_key)
        
        # Make a GET request to list environments
        response = await client.get("/environments")
        
        return {
            "success": True,
            "environments": response.get("data", [])
        }
    except Exception as e:
        logger.error(f"Error listing environments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environments/{environment_id}")
async def get_environment(environment_id: str):
    """Get details about a specific environment"""
    try:
        client = AsyncWarpAPI(api_key=settings.warp_api_key)
        
        # Make a GET request to get environment details
        response = await client.get(f"/environments/{environment_id}")
        
        return {
            "success": True,
            "environment": response
        }
    except Exception as e:
        logger.error(f"Error getting environment {environment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_warp_connection():
    """Test Warp API connection and show current config"""
    try:
        client = AsyncWarpAPI(api_key=settings.warp_api_key)
        
        # Try to list environments as a connection test
        response = await client.get("/environments")
        
        return {
            "success": True,
            "message": "Warp API connection successful",
            "configured_environment_id": settings.warp_environment_id or "Not set",
            "configured_model_id": settings.warp_model_id,
            "api_key_configured": bool(settings.warp_api_key),
            "environments_count": len(response.get("data", []))
        }
    except Exception as e:
        logger.error(f"Error testing Warp connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
