"""SkillPilot Main Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from skillpilot.api.routes import auth, orchestration, skill, vector_search
from skillpilot.core.config import settings
from skillpilot.core.utils.logger import configure_logging, get_logger
from skillpilot.db.seekdb import seekdb_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    configure_logging(debug=settings.debug)
    logger.info("SkillPilot starting up", version="0.2.0", debug=settings.debug)
    
    try:
        # Connect to SeekDB
        seekdb_client.connect()
        logger.info("Database connection established")
        
        # Create tables if they don't exist
        await seekdb_client.create_tables()
        logger.info("Database tables initialized")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("SkillPilot shutting down")
    seekdb_client.close()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="AI Skill Search Engine with Vector Search and Multi-Platform Catalog",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(skill.router, prefix=settings.api_v1_prefix)
app.include_router(orchestration.router, prefix=settings.api_v1_prefix)
app.include_router(vector_search.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.project_name,
        "version": "0.2.0",
        "description": "AI Skill Search Engine",
        "features": [
            "Semantic Vector Search",
            "Multi-Platform Skill Catalog (Coze, Dify, LangChain)",
            "AI-Powered Skill Matching",
            "Skill Recommendation",
        ],
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if seekdb_client._client else "disconnected"
    
    return {
        "status": "healthy",
        "version": "0.2.0",
        "database": db_status,
        "debug": settings.debug,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "skillpilot.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
