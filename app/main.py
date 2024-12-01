import logging
from fastapi import FastAPI #type: ignore  
from fastapi.middleware.cors import CORSMiddleware #type: ignore
from fastapi.middleware.gzip import GZipMiddleware #type: ignore
from app.api.routes import router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION
)

# Add CORS middleware first, before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(router, prefix="/api")

# Add root endpoint for health check
@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {
        "status": "online",
        "message": "Code Analysis API is running"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Code Analysis API...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Code Analysis API...") 