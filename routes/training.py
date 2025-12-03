"""
Training Routes - Experience Domain
API endpoints để trigger training pipeline
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from services.training_service import training_service

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/preprocess")
async def trigger_preprocess(background_tasks: BackgroundTasks):
    """
    Trigger preprocessing: MongoDB interactions → CSV
    Step 2 trong flow
    
    Process:
    1. Fetch interactions từ MongoDB
    2. Convert interaction types → implicit ratings
    3. Save to CSV file
    """
    background_tasks.add_task(training_service.run_preprocessing)
    return {
        "message": "Preprocessing started in background",
        "status": "pending"
    }


@router.post("/train")
async def trigger_training(background_tasks: BackgroundTasks):
    """
    Trigger model training: Train ALS model
    Steps 3-5 trong flow
    
    Process:
    1. Load CSV data
    2. Label encoding (user_id, experience_id → indices)
    3. Train ALS model
    4. Save model + encoders
    """
    background_tasks.add_task(training_service.run_training)
    return {
        "message": "Training started in background",
        "status": "pending"
    }


@router.post("/full-pipeline")
async def trigger_full_pipeline(background_tasks: BackgroundTasks):
    """
    Run full training pipeline: Preprocessing + Training
    
    Executes:
    1. Preprocess interactions
    2. Train ALS model
    3. Save all artifacts
    """
    background_tasks.add_task(training_service.run_full_pipeline)
    return {
        "message": "Full training pipeline started in background",
        "status": "pending"
    }


@router.get("/status")
async def get_training_status():
    """
    Get current training status
    
    Returns:
    - current_status: idle, preprocessing, training, completed, failed
    - last_training: metadata từ lần train trước
    """
    status = training_service.get_status()
    return status


@router.get("/metrics")
async def get_training_metrics():
    """
    Get metrics từ lần training cuối
    
    Returns training metrics nếu có
    """
    metrics = training_service.get_metrics()
    if metrics:
        return metrics
    else:
        raise HTTPException(
            status_code=404,
            detail="No training metrics found. Please train the model first."
        )
