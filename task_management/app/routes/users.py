from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
