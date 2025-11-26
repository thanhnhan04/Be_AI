"""
Interaction Routes
Step 1: API để lưu interaction (wishlist/booking/click)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_active_user
from services import interaction_service
from schemas import InteractionCreate, InteractionResponse

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("/", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction: InteractionCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new interaction (Step 1)
    
    Interaction types:
    - view: User viewed the movie
    - click: User clicked on the movie
    - wishlist: User added to wishlist
    - booking: User booked/rented the movie
    - rating: User rated the movie
    - like: User liked the movie
    """
    user_id = str(current_user['_id'])
    
    try:
        interaction_doc = await interaction_service.create_interaction(
            user_id=user_id,
            interaction_data=interaction
        )
        
        return InteractionResponse(
            id=str(interaction_doc['_id']),
            user_id=str(interaction_doc['user_id']),
            movie_id=str(interaction_doc['movie_id']),
            interaction_type=interaction_doc['interaction_type'],
            rating=interaction_doc.get('rating'),
            watched=interaction_doc.get('watched', False),
            liked=interaction_doc.get('liked', False),
            created_at=interaction_doc['created_at']
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-interactions", response_model=List[InteractionResponse])
async def get_my_interactions(
    interaction_type: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get all interactions for current user"""
    user_id = str(current_user['_id'])
    
    interactions = await interaction_service.get_user_interactions(
        user_id=user_id,
        interaction_type=interaction_type
    )
    
    return [
        InteractionResponse(
            id=str(i['_id']),
            user_id=str(i['user_id']),
            movie_id=str(i['movie_id']),
            interaction_type=i['interaction_type'],
            rating=i.get('rating'),
            watched=i.get('watched', False),
            liked=i.get('liked', False),
            created_at=i['created_at']
        )
        for i in interactions
    ]


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(
    interaction_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete an interaction"""
    user_id = str(current_user['_id'])
    
    success = await interaction_service.delete_interaction(user_id, interaction_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Interaction not found")
