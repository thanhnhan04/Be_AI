from fastapi import APIRouter, Query
from schemas.experience_schemas import RecommendationResponse, ExperienceRecommendation
from datetime import datetime

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(user_id: str, top_k: int = Query(10, ge=1, le=50)):
    # TODO: Replace with real recommendation logic
    mock_recommendations = [
        ExperienceRecommendation(
            id="507f1f77bcf86cd799439011",
            name="Phong Nha Cave Tour",
            description="Explore the amazing Phong Nha cave...",
            location="Quang Binh, Vietnam",
            price=500000,
            average_rating=4.8,
            review_count=1523,
            images=["https://example.com/image1.jpg"],
            category="Adventure",
            score=0.892,
            reason="Based on your love for adventure activities"
        )
    ]
    return RecommendationResponse(
        user_id=user_id,
        recommendations=mock_recommendations,
        total=len(mock_recommendations),
        generated_at=datetime.utcnow(),
        model_version="1.0.0"
    )
"""
Recommendation Routes - Experience Domain
Step 6: Serve API Top-K personalized recommendations
"""

from fastapi import APIRouter, HTTPException, Query

from services.recommendation_service import recommendation_service

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str,
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    use_cache: bool = Query(True, description="Use Redis cache")
):
    """
    Get top-K personalized experience recommendations (Step 6)
    
    Flow:
    1. Load ALS model + encoders
    2. Map user_id → user_idx
    3. Calculate scores for all items
    4. Get top-K items
    5. Fetch experience details from MongoDB
    6. Return JSON with recommendations
    """
    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            top_k=top_k,
            use_cache=use_cache
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/test")
async def test_recommendations(
    user_id: str = Query("test_user", description="User ID for testing"),
    top_k: int = Query(10, ge=1, le=50)
):
    """
    Test endpoint without authentication
    Useful for testing recommendations before frontend integration
    """
    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            top_k=top_k,
            use_cache=False
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{experience_id}")
async def get_similar_experiences(
    experience_id: str,
    top_k: int = Query(10, ge=1, le=50)
):
    """
    Get similar experiences based on item-item similarity
    Uses item factors từ ALS model
    """
    try:
        similar = await recommendation_service.get_similar_experiences(
            experience_id=experience_id,
            top_k=top_k
        )
        return similar
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_recommendations_for_user(
    user_id: str,
    top_k: int = Query(10, ge=1, le=50)
):
    """
    Get recommendations for specific user
    """
    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            top_k=top_k,
            use_cache=True
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
