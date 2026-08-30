from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .models import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(min_length=2, max_length=120)
    role: Role = Role.customer


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str
    role: Role


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=5000)
    price: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    image_url: str | None = None


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vendor_id: int
    created_at: datetime
