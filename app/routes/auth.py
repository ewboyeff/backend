from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token
from app.services.auth_service import register_user, authenticate_user

router = APIRouter(prefix="/api", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await register_user(db, user_in)

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Haqiqiy loyiha/frontend uzatadigan JSON format uchun ochiq API"""
    return await authenticate_user(db, login_data.email, login_data.password)

@router.post("/token", response_model=Token, include_in_schema=False)
async def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Faqatgina Swagger UIdagi ishlashi uchun yordamchi yol"""
    return await authenticate_user(db, email=form_data.username, password=form_data.password)
