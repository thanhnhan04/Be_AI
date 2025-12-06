"""
Test Routes - Endpoints để test server không cần authentication
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.interaction_service import interaction_service
from services.recommendation_service import recommendation_service

router = APIRouter(prefix="/api/test", tags=["testing"])


class TestInteractionCreate(BaseModel):
    """Schema for test interaction"""
    user_id: str
    experience_id: str
    interaction_type: str
    rating: Optional[float] = None


class TestExperienceCreate(BaseModel):
    """Schema for test experience creation"""
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stars: Optional[float] = 0.0
    review_count: Optional[int] = 0
    categories: Optional[str] = None
    attributes: Optional[dict] = None


@router.get("/health")
async def test_health():
    """Test endpoint đơn giản nhất"""
    return {
        "status": "ok",
        "message": "Server is running!"
    }


@router.post("/interaction")
async def test_create_interaction(data: TestInteractionCreate):
    """
    Test tạo interaction không cần auth
    
    Example body:
    {
        "user_id": "test_user_001",
        "experience_id": "692952824c45d78bb37baba0",
        "interaction_type": "view",
        "rating": null
    }
    
    Interaction types: view, click, wishlist, booking, rating, completed
    """
    try:
        from database import get_database, INTERACTIONS_COLLECTION
        from bson import ObjectId
        from datetime import datetime
        
        db = get_database()
        
        # Tạo interaction document
        interaction_doc = {
            "user_id": data.user_id,  # Lưu dưới dạng string cho test
            "experience_id": ObjectId(data.experience_id),
            "interaction_type": data.interaction_type,
            "rating": data.rating,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db[INTERACTIONS_COLLECTION].insert_one(interaction_doc)
        interaction_doc['_id'] = result.inserted_id
        
        return {
            "success": True,
            "message": "Interaction created",
            "data": {
                "id": str(interaction_doc['_id']),
                "user_id": interaction_doc['user_id'],
                "experience_id": str(interaction_doc['experience_id']),
                "interaction_type": interaction_doc['interaction_type'],
                "rating": interaction_doc.get('rating'),
                "created_at": str(interaction_doc['created_at'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/recommendations/{user_id}")
async def test_get_recommendations(user_id: str, top_k: int = 10):
    """
    Test lấy recommendations không cần auth
    
    Example: GET /api/test/recommendations/test_user_001?top_k=5
    """
    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            top_k=top_k
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "total": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/user/{user_id}/interactions")
async def test_get_user_interactions(user_id: str):
    """
    Test lấy interactions của user không cần auth
    
    Example: GET /api/test/user/test_user_001/interactions
    """
    try:
        from database import get_database, INTERACTIONS_COLLECTION
        
        db = get_database()
        
        # Tìm interactions theo string user_id
        interactions = await db[INTERACTIONS_COLLECTION].find({
            "user_id": user_id
        }).sort("created_at", -1).to_list(length=None)
        
        return {
            "success": True,
            "user_id": user_id,
            "total": len(interactions),
            "interactions": [
                {
                    "id": str(i['_id']),
                    "experience_id": str(i['experience_id']),
                    "interaction_type": i['interaction_type'],
                    "rating": i.get('rating'),
                    "created_at": str(i['created_at'])
                }
                for i in interactions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/popular")
async def test_get_popular_experiences(top_k: int = 10):
    """
    Test lấy popular experiences
    
    Example: GET /api/test/popular?top_k=5
    """
    try:
        # Lấy experiences phổ biến từ database
        from database import get_database, EXPERIENCES_COLLECTION
        
        db = get_database()
        
        experiences = await db[EXPERIENCES_COLLECTION].find().sort([
            ("stars", -1),
            ("review_count", -1)
        ]).limit(top_k).to_list(length=top_k)
        
        return {
            "success": True,
            "total": len(experiences),
            "experiences": [
                {
                    "id": str(exp['_id']),
                    "name": exp.get('name', 'Unknown'),
                    "city": exp.get('city', 'Unknown'),
                    "state": exp.get('state', 'Unknown'),
                    "stars": exp.get('stars', 0),
                    "review_count": exp.get('review_count', 0),
                    "categories": exp.get('categories', 'Unknown')
                }
                for exp in experiences
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.delete("/interaction/{user_id}/{experience_id}")
async def test_delete_interaction(user_id: str, experience_id: str):
    """
    Test xóa interaction
    
    Example: DELETE /api/test/interaction/test_user_001/692952824c45d78bb37baba0
    """
    try:
        from database import get_database, INTERACTIONS_COLLECTION
        from bson import ObjectId
        
        db = get_database()
        
        # Xóa theo string user_id
        result = await db[INTERACTIONS_COLLECTION].delete_one({
            "user_id": user_id,
            "experience_id": ObjectId(experience_id)
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        return {
            "success": True,
            "message": f"Deleted interaction for user {user_id} and experience {experience_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.post("/experience")
async def test_create_experience(data: TestExperienceCreate):
    """
    Test tạo experience mới không cần auth
    
    Example body:
    {
        "name": "Test Restaurant",
        "address": "123 Test St",
        "city": "Las Vegas",
        "state": "NV",
        "postal_code": "89101",
        "latitude": 36.1699,
        "longitude": -115.1398,
        "stars": 4.5,
        "review_count": 100,
        "categories": "Restaurants, Italian",
        "attributes": {"parking": true}
    }
    """
    try:
        from database import get_database, EXPERIENCES_COLLECTION
        from datetime import datetime
        
        db = get_database()
        
        # Tạo experience document
        experience_doc = {
            "name": data.name,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "postal_code": data.postal_code,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "stars": data.stars,
            "review_count": data.review_count,
            "categories": data.categories,
            "attributes": data.attributes or {},
            "is_open": 1,  # Default open
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db[EXPERIENCES_COLLECTION].insert_one(experience_doc)
        experience_doc['_id'] = result.inserted_id
        
        return {
            "success": True,
            "message": "Experience created successfully",
            "data": {
                "id": str(experience_doc['_id']),
                "name": experience_doc['name'],
                "city": experience_doc.get('city'),
                "state": experience_doc.get('state'),
                "stars": experience_doc.get('stars'),
                "review_count": experience_doc.get('review_count'),
                "categories": experience_doc.get('categories'),
                "created_at": str(experience_doc['created_at'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
