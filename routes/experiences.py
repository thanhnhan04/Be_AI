from fastapi import APIRouter, HTTPException, status
from schemas.experience_schemas import ExperienceCreate
from database import get_database
from datetime import datetime

router = APIRouter(prefix="/api/experiences", tags=["experiences"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_experience(
    experience: ExperienceCreate
):
    """
    Tạo mới một experience/business từ server chính
    
    Body example:
    {
      "experience_id": "exp_001",
      "name": "Restaurant ABC",
      "city": "Ho Chi Minh",
      "stars": 4.5,
      "categories": "Food, Asian"
    }
    """
    db = get_database()
    try:
        doc = experience.dict()
        doc['created_at'] = datetime.utcnow()
        doc['updated_at'] = datetime.utcnow()
        
        result = await db["experiences"].insert_one(doc)
        
        return {
            "success": True,
            "message": "Experience created",
            "experience_id": experience.experience_id,
            "db_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
