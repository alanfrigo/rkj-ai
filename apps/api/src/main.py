"""
Meeting Assistant - Backend API
FastAPI application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import settings
from .routers import calendar, meetings, recordings, transcriptions
from .core.redis import init_redis, close_redis

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting Meeting Assistant API...")
    await init_redis()
    logger.info("Connected to Redis")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Meeting Assistant API...")
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title="Meeting Assistant API",
    description="API for the Meeting Assistant - automated meeting recording and transcription",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    calendar.router,
    prefix="/api/calendar",
    tags=["Calendar"]
)

app.include_router(
    meetings.router,
    prefix="/api/meetings",
    tags=["Meetings"]
)

app.include_router(
    recordings.router,
    prefix="/api/recordings",
    tags=["Recordings"]
)

app.include_router(
    transcriptions.router,
    prefix="/api/transcriptions",
    tags=["Transcriptions"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "meeting-assistant-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Meeting Assistant API",
        "docs": "/docs",
        "health": "/health"
    }
