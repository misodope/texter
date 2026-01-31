"""FastAPI application entry point for Texter"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.config import settings
from app.routes.webhook import router as webhook_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info(f"Starting {settings.app_name}")
    yield
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="SMS to GitHub PR Bot via Twilio and Warp AI",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(webhook_router)


@app.get("/")
async def root():
    """Redirect root to API docs"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
