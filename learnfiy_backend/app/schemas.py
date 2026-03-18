from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    video_url: str = Field(..., min_length=1)

    @field_validator("title", "description", "video_url")
    @classmethod
    def validate_course_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class CourseUpdate(CourseCreate):
    pass


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    video_url: str | None

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=3)
    email: EmailStr
    phone: str = Field(..., min_length=1)

    @field_validator("full_name", "phone")
    @classmethod
    def validate_user_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    course_id: int = Field(..., gt=0)
    full_name: str = Field(..., min_length=3)
    email: EmailStr
    phone: str = Field(..., min_length=1)

    @field_validator("full_name", "phone")
    @classmethod
    def validate_enrollment_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class MessageResponse(BaseModel):
    message: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
