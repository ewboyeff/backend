from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    user_id: int | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
