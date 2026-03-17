from enum import Enum
import re

from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError, field_validator

PHONE_PATTERN = re.compile(r"^\+?[0-9()\-\s]{7,20}$")
EMAIL_ADAPTER = TypeAdapter(EmailStr)


class PositionEnum(str, Enum):
    FRONTEND_DEVELOPER = "Frontend Developer"
    BACKEND_DEVELOPER = "Backend Developer"
    FULL_STACK_DEVELOPER = "Full Stack Developer"
    UI_UX_DESIGNER = "UI/UX Designer"
    TESTER = "Tester"
    PROJECT_MANAGER = "Project Manager"
    ADMINISTRATION = "Administration"
    HR_MANAGER = "HR Manager"

    def __str__(self) -> str:
        return self.value


class ApplicationCreate(BaseModel):
    full_name: str
    phone: str
    email: str
    position: PositionEnum

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name is required")
        if len(value) < 3:
            raise ValueError("Full name must be at least 3 characters long")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Phone number is required")
        if not PHONE_PATTERN.fullmatch(value):
            raise ValueError("Invalid phone number")

        digit_count = sum(character.isdigit() for character in value)
        if digit_count < 7 or digit_count > 15:
            raise ValueError("Invalid phone number")

        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Email is required")

        try:
            validated_email = EMAIL_ADAPTER.validate_python(value)
        except ValidationError as exc:
            raise ValueError("Invalid email address") from exc

        return str(validated_email)

    @field_validator("position", mode="before")
    @classmethod
    def validate_position(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Position is required")
        return value


class ApiResponse(BaseModel):
    success: bool
    message: str
