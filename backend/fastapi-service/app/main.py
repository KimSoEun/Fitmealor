"""
Fitmealor FastAPI Service
AI-powered meal recommendation and OCR service for foreigners in Korea
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api import meals, ocr, health, auth, chatbot
from app.api import recommendations_simple as recommendations
from app.db.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Fitmealor FastAPI Service...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

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
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fitmealor API Service</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 800px;
                width: 100%;
            }
            h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-align: center;
            }
            .subtitle {
                color: #666;
                text-align: center;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .status {
                background: #10b981;
                color: white;
                padding: 10px 20px;
                border-radius: 50px;
                display: inline-block;
                margin-bottom: 30px;
                font-weight: bold;
            }
            .section {
                margin: 30px 0;
            }
            .section-title {
                color: #333;
                font-size: 1.3em;
                margin-bottom: 15px;
                font-weight: 600;
            }
            .card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 15px;
                transition: transform 0.2s;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .endpoint {
                color: #667eea;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .description {
                color: #666;
                font-size: 0.95em;
            }
            .button {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 30px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                transition: transform 0.2s;
                margin: 10px 10px 0 0;
            }
            .button:hover {
                transform: scale(1.05);
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🥗 Fitmealor API</h1>
            <p class="subtitle">AI-powered meal recommendations for foreigners in Korea</p>
            <div style="text-align: center;">
                <span class="status">✓ Service Running</span>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">5,941</div>
                    <div class="stat-label">Meals Database</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">v1.0.0</div>
                    <div class="stat-label">API Version</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">📚 API Documentation</h2>
                <a href="/docs" class="button">Swagger UI</a>
                <a href="/redoc" class="button">ReDoc</a>
            </div>

            <div class="section">
                <h2 class="section-title">🔗 Main Endpoints</h2>

                <div class="card">
                    <div class="endpoint">POST /api/v1/recommendations/recommend</div>
                    <div class="description">Get personalized meal recommendations based on user profile</div>
                </div>

                <div class="card">
                    <div class="endpoint">POST /api/v1/auth/register</div>
                    <div class="description">Register a new user account</div>
                </div>

                <div class="card">
                    <div class="endpoint">POST /api/v1/auth/login</div>
                    <div class="description">Login and get authentication token</div>
                </div>

                <div class="card">
                    <div class="endpoint">GET /api/v1/auth/profile</div>
                    <div class="description">Get authenticated user profile</div>
                </div>

                <div class="card">
                    <div class="endpoint">GET /api/v1/auth/demo-profile</div>
                    <div class="description">Get demo profile (no authentication required)</div>
                </div>

                <div class="card">
                    <div class="endpoint">POST /api/v1/ocr/analyze</div>
                    <div class="description">Analyze food image using OCR</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">ℹ️ Service Info</h2>
                <div class="card">
                    <div style="display: grid; grid-template-columns: 150px 1fr; gap: 10px;">
                        <strong>Service:</strong> <span>Fitmealor AI Service</span>
                        <strong>Version:</strong> <span>1.0.0</span>
                        <strong>Environment:</strong> <span>Development</span>
                        <strong>Database:</strong> <span>5,723 Korean + 218 English meals</span>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {
        "status": "healthy",
        "service": "fastapi",
        "environment": settings.ENVIRONMENT
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(meals.router, prefix="/api/v1/meals", tags=["Meals"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["Chatbot"])


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
