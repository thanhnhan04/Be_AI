"""
Authentication Routes
Login, Register, Token management
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import create_access_token, get_current_active_user
from services import user_service
from schemas import UserRegister, UserLogin, Token, UserResponse
from config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        user = await user_service.create_user(user_data)
        return UserResponse(
            id=str(user['_id']),
            email=user['email'],
            username=user['username'],
            full_name=user.get('full_name'),
            is_active=user['is_active'],
            preferences=user.get('preferences', []),
            created_at=user['created_at']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = await user_service.authenticate_user(
        form_data.username,
        form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get('is_active'):
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user['_id'])},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user['_id']),
        email=current_user['email'],
        username=current_user['username'],
        full_name=current_user.get('full_name'),
        is_active=current_user['is_active'],
        preferences=current_user.get('preferences', []),
        created_at=current_user['created_at']
    )
