"""
Fitmealor FastAPI Service
AI-powered meal recommendation and OCR service for foreigners in Korea
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api import meals, ocr, recommendations, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Fitmealor FastAPI Service...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL[:30]}...")
    
    # Initialize AI models here
    # await load_ai_models()
    
    yield
    
    logger.info("👋 Shutting down Fitmealor FastAPI Service...")


app = FastAPI(
    title="Fitmealor AI Service",
    description="AI-powered meal recommendation and OCR analysis service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    return {
        "service": "Fitmealor AI Service",
        "version": "1.0.0",
        "status": "running",
        "message": "Welcome to Fitmealor - AI-powered meal recommendations"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {
        "status": "healthy",
        "service": "fastapi",
        "environment": settings.ENVIRONMENT
    }


# Include routers
app.include_router(meals.router, prefix="/api/v1/meals", tags=["Meals"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
