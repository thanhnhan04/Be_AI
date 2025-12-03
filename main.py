"""
FastAPI Main Application
Entry point for Experience Recommendation System with ALS Collaborative Filtering
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import logging

from config import settings
from database import connect_to_mongodb, close_mongodb_connection
from database import connect_to_redis, close_redis_connection
from routes.auth import router as auth_router
from routes.interactions import router as interactions_router
from routes.recommendations import router as recommendations_router
from routes.training import router as training_router
from routes.test import router as test_router
from routes.experiences import router as experiences_router

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
    logger.info("🚀 Starting Experience Recommendation System...")
    await connect_to_mongodb()
    await connect_to_redis()
    logger.info("✓ Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_mongodb_connection()
    await close_redis_connection()
    logger.info("✓ Application shutdown complete")


def retrain_job():
    """Background job to retrain ALS model every 6 hours"""
    try:
        logger.info("🔄 Starting scheduled model retraining...")
        
        # Run retrain from MongoDB
        result = subprocess.run(
            ["python", "retrain_from_mongodb.py"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Retraining failed: {result.stderr}")
            return
        
        logger.info("✓ Model retraining completed successfully")
        
        # RELOAD MODEL into memory
        from services.recommendation_service import recommendation_service
        recommendation_service.model_data = None  # Clear old model
        recommendation_service.encoders = None
        logger.info("✓ Cleared old model from memory, will reload on next request")
        
        # TODO: Reload model in recommendation service
        # recommendation_service.load_model()
        
    except subprocess.TimeoutExpired:
        logger.error("⚠️ Retraining timeout - process killed")
    except Exception as e:
        logger.error(f"❌ Retraining job failed: {e}")


# Scheduler setup: run every 6 hours
scheduler = BackgroundScheduler()
scheduler.add_job(
    retrain_job, 
    'interval', 
    hours=6,
    id='retrain_als_model',
    name='Retrain ALS Model',
    replace_existing=True
)
scheduler.start()
logger.info("📅 Scheduler started: Model will retrain every 6 hours") 

# Create FastAPI app
app = FastAPI(

    title="Experience Recommendation System",
    version="1.0.0",
    description="""
    Experience Recommendation System using ALS Collaborative Filtering
    
    ## Features
    
    * **Authentication**: JWT-based user authentication
    * **Interactions**: Track user behavior (view, click, wishlist, booking, rating, completed)
    * **Recommendations**: Personalized experience recommendations using ALS
    * **Training**: Automated training pipeline with preprocessing
    * **Caching**: Redis cache for fast recommendations
    
    ## 7-Step Workflow
    
    1. **Step 1**: User interaction → Save to database (POST /api/interactions)
    2. **Step 2**: Preprocessing → MongoDB to CSV (POST /api/training/preprocess)
    3. **Step 3**: Label encoding → user_id, experience_id to indices
    4. **Step 4**: Train ALS model (POST /api/training/train)
    5. **Step 5**: Save model + encoders to disk
    6. **Step 6**: Serve API → Get recommendations (GET /api/recommendations)
    7. **Step 7**: Frontend display → React components
    
    ## Interaction Types & Implicit Ratings
    
    - **view**: 1.0 (user viewed the experience)
    - **click**: 2.0 (user clicked for details)
    - **wishlist**: 3.0 (user added to wishlist)
    - **booking**: 5.0 (user booked the experience)
    - **rating**: 1-5 (explicit user rating)
    - **completed**: 5.0 (user completed the experience)
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
app.include_router(test_router)
app.include_router(experiences_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "Experience Recommendation System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/api/auth",
            "interactions": "/api/interactions",
            "recommendations": "/api/recommendations",
            "training": "/api/training"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "model_loaded": False  # TODO: Check if model exists
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
