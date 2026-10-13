from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from backend.models.user import UserRole

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.EMPLOYEE

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return value

class UserLogin(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(self):
        identifier = (self.email or self.username or "").strip()
        if not identifier:
            raise ValueError("Either email or username is required")
        if self.username and "@" in self.username:
            self.email = self.username
            self.username = None
        return self

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    classroom_id: int | None = None
    created_at: datetime | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
