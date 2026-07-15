"""
 ============================================================================
 FastAPI Main Application
 ============================================================================
 Description: Main FastAPI application entry point
 Integrates all routers: location, GIS, and zone checks
 Port: 8000 (default)
 Focus: Bengaluru GIS Engine & Reverse Geocoding Service
 ============================================================================
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from app.config import settings
from app.database import Database
from app.cache import CacheManager
from app.routers import location, gis, zone

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events for database and cache connections.
    """
    # Startup
    logger.info("Starting FastAPI application...")
    await Database.create_pool()
    await CacheManager.connect()
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await Database.close_pool()
    await CacheManager.close()
    logger.info("Application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="Bengaluru GIS Engine & Reverse Geocoding Service",
    description="""
    Comprehensive GIS backend service for Bengaluru Urban and Rural districts.
    
    Features:
    - Reverse geocoding with Google/Nominatim fallback
    - Administrative hierarchy validation
    - Survey number lookup with PostGIS spatial queries
    - Environmental zone checks (BDA, NGT, AAI)
    - Redis caching for sub-50ms response times
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    logger.error(f"Request path: {request.url}")
    logger.error(f"Request method: {request.method}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url)
        }
    )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Bengaluru GIS Engine",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "gis-engine",
        "database": "connected" if Database.pool else "disconnected",
        "cache": "connected" if CacheManager.client else "disconnected"
    }


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(location.router)
app.include_router(gis.router)
app.include_router(zone.router)


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,  # Enable auto-reload for development
        log_level=settings.LOG_LEVEL.lower()
    )
