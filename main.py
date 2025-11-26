"""
FastAPI Main Application
Entry point for Movie Recommendation System with Collaborative Filtering
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from database import connect_to_mongodb, close_mongodb_connection
from database import connect_to_redis, close_redis_connection
from routes import (
    auth_router,
    interactions_router,
    recommendations_router,
    training_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Movie Recommendation System...")
    await connect_to_mongodb()
    await connect_to_redis()
    logger.info("✓ Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_mongodb_connection()
    await close_redis_connection()
    logger.info("✓ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Movie Recommendation System using Collaborative Filtering
    
    ## Features
    
    * **Authentication**: JWT-based user authentication
    * **Interactions**: Track user behavior (views, ratings, wishlist, bookings)
    * **Recommendations**: Personalized movie recommendations using CF
    * **Training**: Batch training of CF model
    * **TMDB Integration**: Fetch movie data from The Movie Database
    
    ## Workflow
    
    1. **Step 1**: Save interactions to database (POST /api/interactions)
    2. **Step 2-3**: Preprocessing and encoding (automatic during training)
    3. **Step 4**: Train CF model (POST /api/training/train-cf-model)
    4. **Step 5**: Model saved to disk (automatic)
    5. **Step 6**: Serve recommendations (GET /api/recommendations)
    6. **Step 7**: Frontend displays recommendations
    """,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(interactions_router)
app.include_router(recommendations_router)
app.include_router(training_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
