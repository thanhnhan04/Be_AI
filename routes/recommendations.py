"""
Recommendation Routes
Step 6: Serve API Top-K recommendation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from auth import get_current_active_user
from services import recommendation_service
from schemas import RecommendationResponse

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/", response_model=RecommendationResponse)
async def get_recommendations(
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    exclude_watched: bool = Query(True, description="Exclude already watched movies"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get top-K personalized recommendations (Step 6)
    
    Process:
    1. Load CF model + mappings
    2. Map user_id → user_idx
    3. Get items not interacted → predict score
    4. Get top-K → map item_idx → item info
    5. Return JSON list: top-K items
    """
    user_id = str(current_user['_id'])
    
    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            top_k=top_k,
            exclude_watched=exclude_watched
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/{user_id}", response_model=RecommendationResponse)
async def get_recommendations_for_user(
    user_id: str,
    top_k: int = Query(10, ge=1, le=50),
    exclude_watched: bool = Query(True),
    current_user: dict = Depends(get_current_active_user)
):
    """Get recommendations for specific user (admin/testing)"""
    # Only allow superusers to get recommendations for other users
    if not current_user.get('is_superuser', False):
        if str(current_user['_id']) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            top_k=top_k,
            exclude_watched=exclude_watched
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
