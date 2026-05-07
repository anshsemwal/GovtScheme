"""Production FastAPI application with authentication"""

import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import settings, validate_mistral_api_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="CivicScheme AI",
    version="3.0.0",
    docs_url="/docs",  # Always enable docs for user convenience
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.api.features_routes import router as features_router

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(features_router, prefix="/api/features", tags=["Features"])

# Static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    """Serve frontend or redirect to docs"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Redirect to docs if no frontend
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")




@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "mistral_api": "connected" if settings.mistral_api_key else "not_configured"
    }



@app.on_event("startup")
async def startup_event():
    """Validate configuration and initialize services"""
    logger.info(f"Starting {settings.app_name}...")
    
    # Initialize Database
    logger.info("Initializing database...")
    try:
        from app.database import engine, Base
        import app.models.user # Ensure models are registered
        Base.metadata.create_all(bind=engine)
        logger.info("[SUCCESS] Database initialized")
    except Exception as e:
        logger.error(f"[ERROR] Database initialization failed: {str(e)}")

    # Validate Mistral API
    logger.info("Validating Mistral API connection...")
    if settings.mistral_api_key:
        if not validate_mistral_api_connection(settings.mistral_api_key):
             logger.error("[ERROR] Mistral API validation failed")
             logger.warning("[WARNING] Application starting with potentially invalid API key.")
    else:
        logger.warning("[WARNING] No Mistral API key provided. AI features may be limited.")
    
    logger.info("Starting (Simplified) ...")
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    from app.services.rag_pipeline import rag_pipeline
    try:
        rag_pipeline.initialize()
        logger.info("[SUCCESS] RAG pipeline initialized")
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize RAG pipeline: {str(e)}")
        logger.warning("[WARNING] RAG features will be unavailable.")
    
    logger.info("[SUCCESS] Application started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
# Reload trigger
