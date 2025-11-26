from .auth import router as auth_router
from .interactions import router as interactions_router
from .recommendations import router as recommendations_router
from .training import router as training_router

__all__ = [
    "auth_router",
    "interactions_router",
    "recommendations_router",
    "training_router"
]
