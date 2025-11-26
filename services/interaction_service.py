"""
Interaction Service
Step 1: Lưu interaction vào DB
"""

from datetime import datetime
from typing import List
from bson import ObjectId

from database import get_database, INTERACTIONS_COLLECTION, get_redis
from schemas import InteractionCreate, InteractionResponse
import logging

logger = logging.getLogger(__name__)


class InteractionService:
    """Service for managing user-movie interactions"""
    
    @staticmethod
    async def create_interaction(
        user_id: str,
        interaction_data: InteractionCreate
    ) -> dict:
        """
        Create a new interaction (Step 1: Lưu interaction vào DB)
        
        FE gửi POST request → Backend nhận và lưu vào DB
        """
        db = get_database()
        
        # Check if interaction already exists
        existing = await db[INTERACTIONS_COLLECTION].find_one({
            "user_id": ObjectId(user_id),
            "experience_id": ObjectId(interaction_data.experience_id),
            "interaction_type": interaction_data.interaction_type
        })
        
        if existing:
            # Update existing interaction
            update_data = {
                "updated_at": datetime.utcnow()
            }
            
            if interaction_data.rating is not None:
                update_data["rating"] = interaction_data.rating
            if interaction_data.booked:
                update_data["booked"] = True
            if interaction_data.completed:
                update_data["completed"] = True
            if interaction_data.liked:
                update_data["liked"] = True
            if interaction_data.saved_to_wishlist:
                update_data["saved_to_wishlist"] = True
            
            await db[INTERACTIONS_COLLECTION].update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
            
            interaction = await db[INTERACTIONS_COLLECTION].find_one(
                {"_id": existing["_id"]}
            )
            logger.info(f"Updated interaction for user {user_id}")
        else:
            # Create new interaction
            interaction_doc = {
                "user_id": ObjectId(user_id),
                "experience_id": ObjectId(interaction_data.experience_id),
                "interaction_type": interaction_data.interaction_type,
                "rating": interaction_data.rating,
                "booked": interaction_data.booked,
                "completed": interaction_data.completed,
                "liked": interaction_data.liked,
                "saved_to_wishlist": interaction_data.saved_to_wishlist,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await db[INTERACTIONS_COLLECTION].insert_one(interaction_doc)
            interaction = await db[INTERACTIONS_COLLECTION].find_one(
                {"_id": result.inserted_id}
            )
            logger.info(f"Created new interaction for user {user_id}")
        
        # Invalidate recommendation cache for this user
        redis_client = get_redis()
        if redis_client:
            try:
                keys = await redis_client.keys(f"recommendations:{user_id}:*")
                if keys:
                    await redis_client.delete(*keys)
                    logger.info(f"Cleared cache for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to clear cache: {e}")
        
        return interaction
    
    @staticmethod
    async def get_user_interactions(
        user_id: str,
        interaction_type: str = None
    ) -> List[dict]:
        """Get all interactions for a user"""
        db = get_database()
        
        query = {"user_id": ObjectId(user_id)}
        if interaction_type:
            query["interaction_type"] = interaction_type
        
        interactions = await db[INTERACTIONS_COLLECTION].find(
            query
        ).sort("created_at", -1).to_list(length=None)
        
        return interactions
    
    @staticmethod
    async def get_experience_interactions(experience_id: str) -> List[dict]:
        """Get all interactions for an experience"""
        db = get_database()
        
        interactions = await db[INTERACTIONS_COLLECTION].find(
            {"experience_id": ObjectId(experience_id)}
        ).to_list(length=None)
        
        return interactions
    
    @staticmethod
    async def delete_interaction(user_id: str, interaction_id: str) -> bool:
        """Delete an interaction"""
        db = get_database()
        
        result = await db[INTERACTIONS_COLLECTION].delete_one({
            "_id": ObjectId(interaction_id),
            "user_id": ObjectId(user_id)
        })
        
        if result.deleted_count > 0:
            # Invalidate cache
            redis_client = get_redis()
            if redis_client:
                try:
                    keys = await redis_client.keys(f"recommendations:{user_id}:*")
                    if keys:
                        await redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Failed to clear cache: {e}")
            
            return True
        return False


interaction_service = InteractionService()
