from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, hash_password, verify_password
from app.models.user import User
from app.schemas.base import DataResponse
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth import AuthService

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Authentication"])

_REFRESH_COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days in seconds


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=_REFRESH_COOKIE_MAX_AGE,
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[TokenResponse],
)
async def register(
    data: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, access_token, refresh_token = await service.register(data)
    _set_refresh_cookie(response, refresh_token)
    return DataResponse(
        message="Muvaffaqiyatli ro'yxatdan o'tdingiz",
        data=TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        ),
    )


@router.post("/login", response_model=DataResponse[TokenResponse])
@limiter.limit("30/15minutes")
async def login(
    request: Request,
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, access_token, refresh_token = await service.login(data)
    _set_refresh_cookie(response, refresh_token)
    return DataResponse(
        data=TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        ),
    )


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "NO_REFRESH_TOKEN",
                "message": "Refresh token topilmadi",
            },
        )
    service = AuthService(db)
    access_token = await service.refresh(refresh_token)
    return DataResponse(data={"access_token": access_token})


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token")
    return DataResponse(message="Tizimdan chiqdingiz", data=None)


@router.get("/me", response_model=DataResponse[UserResponse])
async def me(
    current_user: User = Depends(get_current_user),
):
    return DataResponse(data=UserResponse.model_validate(current_user))


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)


@router.post("/change-password", response_model=DataResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WRONG_PASSWORD", "message": "Joriy parol noto'g'ri"},
        )
    current_user.password_hash = hash_password(data.new_password)
    db.add(current_user)
    await db.commit()
    return DataResponse(message="Parol muvaffaqiyatli yangilandi", data=None)
