"""
User Sync Routes - Nhận user data từ server chính
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_database

router = APIRouter(prefix="/api/sync", tags=["sync"])


class UserSyncData(BaseModel):
    """Schema cho user data từ server chính - chỉ cần user_id"""
    user_id: str  # ID từ server chính (bắt buộc)
    email: Optional[str] = None  # Optional metadata
    username: Optional[str] = None
    full_name: Optional[str] = None
    preferences: Optional[list] = []
    metadata: Optional[dict] = {}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def sync_user(
    user_data: UserSyncData
):
    """
    Sync user từ server chính vào recommendation DB
    
    Body:
    {
        "user_id": "user123",
        "email": "user@example.com",
        "username": "user123",
        "full_name": "John Doe",
        "preferences": ["Italian", "Asian"],
        "metadata": {}
    }
    """
    db = get_database()
    
    # Check if user already exists
    existing = await db.users.find_one({"user_id": user_data.user_id})
    
    if existing:
        # Update existing user
        update_data = {
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "preferences": user_data.preferences,
            "metadata": user_data.metadata,
            "updated_at": datetime.now()
        }
        
        await db.users.update_one(
            {"user_id": user_data.user_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "User updated",
            "user_id": user_data.user_id,
            "action": "updated"
        }
    else:
        # Create new user
        new_user = {
            "user_id": user_data.user_id,
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "preferences": user_data.preferences,
            "metadata": user_data.metadata,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = await db.users.insert_one(new_user)
        
        return {
            "success": True,
            "message": "User created",
            "user_id": user_data.user_id,
            "db_id": str(result.inserted_id),
            "action": "created"
        }


@router.delete("/users/{user_id}")
async def delete_synced_user(
    user_id: str
):
    """
    Xóa user khỏi recommendation DB (khi user bị xóa ở server chính)
    """
    db = get_database()
    
    # Delete user
    result = await db.users.delete_one({"user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Note: Không xóa interactions của user (giữ lại cho historical data)
    
    return {
        "success": True,
        "message": "User deleted from recommendation system",
        "user_id": user_id
    }


@router.get("/users/{user_id}")
async def get_synced_user(
    user_id: str
):
    """
    Lấy thông tin user từ recommendation DB
    """
    db = get_database()
    
    user = await db.users.find_one({"user_id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "email": user.get("email"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "preferences": user.get("preferences", []),
            "created_at": str(user.get("created_at")),
            "updated_at": str(user.get("updated_at"))
        }
    }
