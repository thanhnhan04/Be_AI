"""
Training Routes
Step 4: Train CF model (batch job)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from auth import get_current_superuser
from services import recommendation_service
from schemas import TrainingResponse

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/train-cf-model", response_model=TrainingResponse)
async def train_cf_model(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_superuser)
):
    """
    Train CF model (Step 4)
    
    This is a batch job that should be run periodically:
    - Daily
    - Every 2-3 days
    - Weekly
    
    Process:
    1. Fetch interactions from DB
    2. Preprocess data
    3. Label encoding (user/item → idx)
    4. Train CF model (SVD/ALS)
    5. Save model + encoders
    """
    try:
        # Run training in background
        background_tasks.add_task(recommendation_service.train_cf_model)
        
        return TrainingResponse(
            status="started",
            message="CF model training started in background"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-cf-model-sync", response_model=TrainingResponse)
async def train_cf_model_sync(
    current_user: dict = Depends(get_current_superuser)
):
    """Train CF model synchronously (for testing)"""
    try:
        metrics = await recommendation_service.train_cf_model()
        
        return TrainingResponse(
            status="completed",
            message="CF model trained successfully",
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
