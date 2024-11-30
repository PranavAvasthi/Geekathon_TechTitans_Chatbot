import logging
from fastapi import FastAPI #type: ignore  
from fastapi.middleware.cors import CORSMiddleware #type: ignore
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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
    expose_headers=["*"],
    max_age=3600,
)

# Include API routes
app.include_router(router, prefix="/api")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Code Analysis API...")
    # Log CORS configuration
    logger.info(f"CORS Origins: {settings.ALLOWED_ORIGINS}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Code Analysis API...") 