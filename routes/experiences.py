from fastapi import APIRouter, HTTPException, status, Depends
from schemas.experience_schemas import ExperienceRecommendation
from database import get_database
from auth import get_current_active_user

router = APIRouter(prefix="/api/experiences", tags=["experiences"])

@router.post("/", response_model=ExperienceRecommendation, status_code=status.HTTP_201_CREATED)
async def create_experience(
    experience: ExperienceRecommendation,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Tạo mới một experience/business
    """
    db = get_database()
    try:
        doc = experience.dict()
        doc['created_by'] = str(current_user['_id'])
        result = await db["experiences"].insert_one(doc)
        doc['_id'] = result.inserted_id
        return ExperienceRecommendation(**doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
