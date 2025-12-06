"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============= Experience Schemas =============

class ExperienceBase(BaseModel):
    """Base experience schema"""
    title: str
    description: Optional[str] = None
    category: str  # Food & Drink, Art & Culture, Nature, Sports
    subcategories: List[str] = []
    location: dict = {}
    duration_hours: Optional[float] = None
    price: float = 0.0
    currency: str = "USD"
    max_guests: int = 1
    language: List[str] = ["English"]
    includes: List[str] = []


class ExperienceCreate(ExperienceBase):
    """Create experience request"""
    host_name: Optional[str] = None
    image_urls: List[str] = []
    tags: List[str] = []


class ExperienceResponse(ExperienceBase):
    """Experience response"""
    id: str
    host_id: Optional[str] = None
    host_name: Optional[str] = None
    rating: float = 0.0
    review_count: int = 0
    image_urls: List[str] = []
    tags: List[str] = []
    is_active: bool = True
    
    class Config:
        from_attributes = True


class ExperienceDetail(ExperienceResponse):
    """Detailed experience with additional info"""
    availability: List[str] = []
    created_at: datetime
    updated_at: datetime


# ============= Interaction Schemas =============

class InteractionCreate(BaseModel):
    """Create interaction request (Step 1: Lưu interaction)"""
    experience_id: str
    interaction_type: str = Field(
        ...,
        description="Type: 'view', 'click', 'save', 'booking', 'review'"
    )
    rating: Optional[float] = Field(None, ge=0, le=5)
    booked: bool = False
    completed: bool = False
    liked: bool = False
    saved_to_wishlist: bool = False


class InteractionResponse(BaseModel):
    """Interaction response"""
    id: str
    user_id: str
    experience_id: str
    interaction_type: str
    rating: Optional[float] = None
    booked: bool
    completed: bool
    liked: bool
    saved_to_wishlist: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Recommendation Schemas =============

class RecommendationRequest(BaseModel):
    """Recommendation request"""
    user_id: Optional[str] = None  # If None, use current user
    top_k: int = Field(10, ge=1, le=50)
    exclude_watched: bool = True


class RecommendationItem(BaseModel):
    """Single recommendation item"""
    experience_id: str
    title: str
    score: float
    image_url: Optional[str] = None
    category: str
    rating: float = 0.0
    price: float = 0.0
    duration_hours: Optional[float] = None
    location: dict = {}
    description: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Top-K recommendation response (Step 6: API response)"""
    user_id: str
    recommendations: List[RecommendationItem]
    algorithm: str  # 'collaborative_filtering' or 'popularity'
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============= Training Schemas =============

class TrainingRequest(BaseModel):
    """Request to trigger model training"""
    min_interactions: int = Field(5, ge=1)
    test_size: float = Field(0.2, ge=0.1, le=0.5)


class TrainingResponse(BaseModel):
    """Training job response"""
    status: str
    message: str
    metrics: Optional[dict] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)


# ============= Statistics Schemas =============

class UserStats(BaseModel):
    """User statistics"""
    total_interactions: int
    total_experiences_booked: int
    favorite_categories: List[str]
    average_rating: float


class SystemStats(BaseModel):
    """System statistics"""
    total_users: int
    total_experiences: int
    total_interactions: int
    model_last_trained: Optional[datetime] = None
    model_performance: Optional[dict] = None
