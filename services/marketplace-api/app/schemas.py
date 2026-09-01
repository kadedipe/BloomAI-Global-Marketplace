from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .models import OrderStatus, Role


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
    avatar_url: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=5000)
    price: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    image_url: str | None = None
    image_public_id: str | None = Field(default=None, max_length=512)
    inventory_quantity: int | None = Field(default=None, ge=0, le=1000000)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    image_url: str | None = None
    image_public_id: str | None = Field(default=None, max_length=512)
    inventory_quantity: int | None = Field(default=None, ge=0, le=1000000)
    is_active: bool | None = None


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vendor_id: int
    created_at: datetime


class ImageUploadResponse(BaseModel):
    image_url: str
    image_public_id: str


class PaymentInitializeRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class PaymentInitializeResponse(BaseModel):
    order_id: int
    reference: str
    authorization_url: str
    access_code: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    product_id: int
    quantity: int
    unit_price: Decimal
    total: Decimal
    currency: str
    status: OrderStatus
    created_at: datetime
    paid_at: datetime | None
