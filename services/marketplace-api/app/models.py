import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Role(str, enum.Enum):
    customer = "customer"
    vendor = "vendor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.customer)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    avatar_public_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_public_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    inventory_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    vendor: Mapped[User] = relationship()


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"


class FulfillmentStatus(str, enum.Enum):
    unfulfilled = "unfulfilled"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class RefundStatus(str, enum.Enum):
    none = "none"
    requested = "requested"
    approved = "approved"
    processing = "processing"
    refunded = "refunded"
    rejected = "rejected"


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    provider: Mapped[str] = mapped_column(String(32), default="paystack")
    provider_transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(240), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    buyer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    inventory_reserved: Mapped[bool] = mapped_column(Boolean, default=False)
    reservation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(Enum(FulfillmentStatus), default=FulfillmentStatus.unfulfilled)
    carrier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(160), nullable=True)
    tracking_provider_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    tracking_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tracking_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_status: Mapped[RefundStatus] = mapped_column(Enum(RefundStatus), default=RefundStatus.none)
    refund_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    refund_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_provider_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    refund_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buyer: Mapped[User] = relationship()
    product: Mapped[Product] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    user: Mapped[User] = relationship()


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    account_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    orders_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    payments_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    vendor_activity_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    system_in_app: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped[User] = relationship()
