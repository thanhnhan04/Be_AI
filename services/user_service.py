"""
User Service
Handle user-related business logic
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId

from database import get_database, USERS_COLLECTION
from auth import get_password_hash, verify_password
from schemas import UserRegister, UserResponse
import logging

logger = logging.getLogger(__name__)


class UserService:
    """User management service"""
    
    @staticmethod
    async def create_user(user_data: UserRegister) -> dict:
        """Create a new user"""
        db = get_database()
        
        # Check if user exists
        existing_user = await db[USERS_COLLECTION].find_one(
            {"$or": [
                {"email": user_data.email},
                {"username": user_data.username}
            ]}
        )
        
        if existing_user:
            if existing_user.get('email') == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "username": user_data.username,
            "hashed_password": get_password_hash(user_data.password),
            "full_name": user_data.full_name,
            "is_active": True,
            "is_superuser": False,
            "preferences": user_data.preferences,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db[USERS_COLLECTION].insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        logger.info(f"Created user: {user_data.username}")
        return user_doc
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[dict]:
        """Authenticate user with username and password"""
        db = get_database()
        
        user = await db[USERS_COLLECTION].find_one({"username": username})
        
        if not user:
            return None
        
        if not verify_password(password, user['hashed_password']):
            return None
        
        return user
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[dict]:
        """Get user by ID"""
        db = get_database()
        
        user = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
        return user
    
    @staticmethod
    async def update_user_preferences(user_id: str, preferences: list) -> dict:
        """Update user genre preferences"""
        db = get_database()
        
        result = await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "preferences": preferences,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError("User not found")
        
        user = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
        return user


user_service = UserService()
