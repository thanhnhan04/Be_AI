"""
Schema cho Experience Recommendation System
Adapted từ Movie → Experience
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InteractionType(str, Enum):
    """Các loại interaction"""
    VIEW = "view"              # User xem experience
    CLICK = "click"            # User click vào experience
    WISHLIST = "wishlist"      # User thêm vào wishlist
    BOOKING = "booking"        # User booking experience
    RATING = "rating"          # User đánh giá experience
    COMPLETED = "completed"    # User hoàn thành experience


class InteractionCreate(BaseModel):
    """Schema để tạo interaction mới - nhận từ server chính"""
    user_id: str = Field(..., description="ID của user từ server chính")
    experience_id: str = Field(..., description="ID của experience")
    interaction_type: InteractionType = Field(..., description="Loại interaction")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Rating 1-5 sao")
    booked: bool = Field(default=False, description="Đã booking chưa")
    completed: bool = Field(default=False, description="Đã hoàn thành chưa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "experience_id": "507f1f77bcf86cd799439011",
                "interaction_type": "wishlist",
                "rating": 4.5,
                "booked": False,
                "completed": False
            }
        }


class InteractionResponse(BaseModel):
    """Schema response cho interaction"""
    id: str
    user_id: str
    experience_id: str
    interaction_type: InteractionType
    rating: Optional[float] = None
    booked: bool = False
    completed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExperienceCreate(BaseModel):
    """Schema để tạo experience mới từ server chính"""
    experience_id: str = Field(..., description="Unique experience ID từ server chính")
    name: str = Field(..., description="Tên experience")
    description: Optional[str] = Field("", description="Mô tả")
    city: Optional[str] = Field("", description="Thành phố")
    state: Optional[str] = Field("", description="Tỉnh/Bang")
    address: Optional[str] = Field("", description="Địa chỉ")
    postal_code: Optional[str] = Field("", description="Mã bưu điện")
    stars: Optional[float] = Field(0.0, ge=0, le=5, description="Rating trung bình")
    review_count: Optional[int] = Field(0, description="Số lượng review")
    categories: Optional[str] = Field("", description="Danh mục (comma separated)")
    price: Optional[float] = Field(0.0, description="Giá tham khảo")
    images: Optional[List[str]] = Field(default_factory=list, description="Danh sách URL ảnh")
    
    class Config:
        json_schema_extra = {
            "example": {
                "experience_id": "exp_12345",
                "name": "Phong Nha Cave Tour",
                "description": "Explore the amazing cave",
                "city": "Quang Binh",
                "state": "Vietnam",
                "stars": 4.8,
                "review_count": 1523,
                "categories": "Adventure, Nature",
                "price": 500000,
                "images": ["https://example.com/img.jpg"]
            }
        }


class ExperienceRecommendation(BaseModel):
    """Schema cho một experience được recommend"""
    id: str = Field(..., description="Experience ID")
    name: str = Field(..., description="Tên experience")
    description: str = Field(..., description="Mô tả")
    location: str = Field(..., description="Địa điểm")
    price: float = Field(..., description="Giá")
    average_rating: float = Field(..., description="Rating trung bình")
    review_count: int = Field(..., description="Số lượng review")
    images: List[str] = Field(default=[], description="Danh sách ảnh")
    category: str = Field(..., description="Danh mục (Adventure, Culture, Food, etc.)")
    score: float = Field(..., description="CF confidence score")
    reason: str = Field(default="Based on your preferences", description="Lý do recommend")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Phong Nha Cave Tour",
                "description": "Explore the amazing Phong Nha cave...",
                "location": "Quang Binh, Vietnam",
                "price": 500000,
                "average_rating": 4.8,
                "review_count": 1523,
                "images": ["https://example.com/image1.jpg"],
                "category": "Adventure",
                "score": 0.892,
                "reason": "Based on your love for adventure activities"
            }
        }


class RecommendationResponse(BaseModel):
    """Schema response cho recommendations"""
    user_id: str
    recommendations: List[ExperienceRecommendation]
    total: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(default="1.0.0", description="Version của model")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "recommendations": [],
                "total": 10,
                "generated_at": "2025-11-27T10:30:00Z",
                "model_version": "1.0.0"
            }
        }


class TrainingStatus(BaseModel):
    """Schema cho training status"""
    status: str = Field(..., description="Status: pending, running, completed, failed")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    message: str = Field(default="", description="Status message")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "running",
                "progress": 45.5,
                "message": "Training model iteration 7/15",
                "started_at": "2025-11-27T10:00:00Z",
                "completed_at": None
            }
        }


class TrainingMetrics(BaseModel):
    """Schema cho training metrics"""
    precision_at_5: float
    precision_at_10: float
    precision_at_20: float
    recall_at_5: float
    recall_at_10: float
    recall_at_20: float
    ndcg_at_5: float
    ndcg_at_10: float
    ndcg_at_20: float
    hit_rate_at_5: float
    hit_rate_at_10: float
    hit_rate_at_20: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "precision_at_5": 0.0554,
                "precision_at_10": 0.0493,
                "precision_at_20": 0.0419,
                "recall_at_5": 0.0322,
                "recall_at_10": 0.0572,
                "recall_at_20": 0.0984,
                "ndcg_at_5": 0.0619,
                "ndcg_at_10": 0.0661,
                "ndcg_at_20": 0.0775,
                "hit_rate_at_5": 0.2288,
                "hit_rate_at_10": 0.3460,
                "hit_rate_at_20": 0.4767
            }
        }


class TrainingResponse(BaseModel):
    """Schema response cho training"""
    training_id: str
    status: TrainingStatus
    metrics: Optional[TrainingMetrics] = None
    num_users: int = 0
    num_experiences: int = 0
    num_interactions: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "training_id": "train_20251127_103000",
                "status": {
                    "status": "completed",
                    "progress": 100.0,
                    "message": "Training completed successfully"
                },
                "metrics": {},
                "num_users": 2519,
                "num_experiences": 9862,
                "num_interactions": 169110
            }
        }
