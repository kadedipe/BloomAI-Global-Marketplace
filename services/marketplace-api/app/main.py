import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal

import sentry_sdk
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .config import get_settings
from .database import create_schema, get_db
from .events import publish_event
from .media import delete_product_image, upload_product_image
from .models import Order, OrderStatus, Product, Role, User
from .payments import request as paystack_request, valid_webhook_signature
from .protection import enforce_csrf_origin, rate_limit
from .schemas import (
    LoginRequest,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ImageUploadResponse,
    OrderResponse,
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from .security import (
    clear_auth_cookie,
    create_token,
    current_user,
    password_hash,
    set_auth_cookie,
)

settings = get_settings()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=settings.environment,
        release=os.getenv("RAILWAY_GIT_COMMIT_SHA"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment != "production":
        await create_schema()
    yield


docs_enabled = settings.environment != "production" or settings.enable_api_docs
app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def csrf_origin_guard(request: Request, call_next):
    try:
        await enforce_csrf_origin(request)
    except HTTPException as error:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
    return await call_next(request)


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "ok", "service": "marketplace-api"}


@app.get("/health/ready", tags=["health"])
async def ready(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    await rate_limit(request, "register", 5, 600)
    if payload.role == Role.admin:
        raise HTTPException(403, "Admin registration is disabled")
    user = User(
        email=payload.email.lower(),
        name=payload.name.strip(),
        role=payload.role,
        password_hash=password_hash.hash(payload.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Email is already registered")
    await db.refresh(user)
    return user


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await rate_limit(request, "login", 10, 600)
    user = (
        await db.execute(select(User).where(User.email == payload.email.lower()))
    ).scalar_one_or_none()
    if not user or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    token = create_token(user)
    set_auth_cookie(response, token)
    return TokenResponse(access_token=token)


@app.post("/api/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    clear_auth_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT


@app.get("/api/v1/auth/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/products", response_model=list[ProductResponse])
async def products(
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return (
        (
            await db.execute(
                select(Product)
                .order_by(Product.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )


@app.post(
    "/api/v1/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: ProductCreate,
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await rate_limit(request, "product-write", 30, 3600)
    if user.role not in {Role.vendor, Role.admin}:
        raise HTTPException(403, "Vendor access required")
    if payload.image_public_id and not payload.image_public_id.startswith(f"bloomai/vendors/{user.id}/"):
        raise HTTPException(403, "Image does not belong to this vendor")
    product = Product(vendor_id=user.id, **payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    await publish_event(
        "product.created",
        {"product_id": product.id, "vendor_id": user.id, "name": product.name},
    )
    return product


async def owned_product(product_id: int, user: User, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if user.role != Role.admin and product.vendor_id != user.id:
        raise HTTPException(403, "You do not own this product")
    return product


@app.post("/api/v1/product-images", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    request: Request,
    image: UploadFile = File(...),
    user: User = Depends(current_user),
):
    if user.role not in {Role.vendor, Role.admin}:
        raise HTTPException(403, "Vendor access required")
    await rate_limit(request, "product-image", 20, 3600)
    return await upload_product_image(image, user.id)


@app.patch("/api/v1/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await rate_limit(request, "product-write", 30, 3600)
    product = await owned_product(product_id, user, db)
    changes = payload.model_dump(exclude_unset=True)
    public_id = changes.get("image_public_id")
    if public_id and not public_id.startswith(f"bloomai/vendors/{product.vendor_id}/"):
        raise HTTPException(403, "Image does not belong to this vendor")
    old_public_id = product.image_public_id
    for field, value in changes.items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    if old_public_id and old_public_id != product.image_public_id:
        await delete_product_image(old_public_id)
    return product


@app.delete("/api/v1/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await rate_limit(request, "product-write", 30, 3600)
    product = await owned_product(product_id, user, db)
    public_id = product.image_public_id
    await db.delete(product)
    await db.commit()
    await delete_product_image(public_id)


@app.post("/api/v1/payments/initialize", response_model=PaymentInitializeResponse, status_code=201)
async def initialize_payment(
    payload: PaymentInitializeRequest,
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await rate_limit(request, "payment-initialize", 10, 600)
    product = await db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if product.vendor_id == user.id:
        raise HTTPException(409, "Vendors cannot purchase their own product")
    supported = {item.strip().upper() for item in settings.paystack_currencies.split(",")}
    if product.currency not in supported:
        raise HTTPException(422, f"Paystack checkout is not enabled for {product.currency}")
    total = product.price * payload.quantity
    reference = f"bloom-{uuid.uuid4().hex}"
    order = Order(
        reference=reference,
        buyer_id=user.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.price,
        total=total,
        currency=product.currency,
        status=OrderStatus.pending,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    data = await paystack_request(
        "POST",
        "/transaction/initialize",
        json={
            "email": user.email,
            "amount": int(total * Decimal("100")),
            "currency": product.currency,
            "reference": reference,
            "callback_url": settings.paystack_callback_url,
            "metadata": {"order_id": order.id, "product_id": product.id, "buyer_id": user.id},
        },
    )
    return PaymentInitializeResponse(order_id=order.id, reference=reference, **data)


async def settle_order(reference: str, data: dict, db: AsyncSession) -> Order:
    order = (await db.execute(select(Order).where(Order.reference == reference))).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    expected_amount = int(order.total * Decimal("100"))
    if data.get("status") != "success" or data.get("amount") != expected_amount or data.get("currency") != order.currency:
        order.status = OrderStatus.failed
    else:
        order.status = OrderStatus.paid
        order.provider_transaction_id = str(data.get("id"))
        order.paid_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)
    return order


@app.get("/api/v1/payments/{reference}/verify", response_model=OrderResponse)
async def verify_payment(
    reference: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order = (await db.execute(select(Order).where(Order.reference == reference))).scalar_one_or_none()
    if not order or (user.role != Role.admin and order.buyer_id != user.id):
        raise HTTPException(404, "Order not found")
    if order.status == OrderStatus.paid:
        return order
    data = await paystack_request("GET", f"/transaction/verify/{reference}")
    return await settle_order(reference, data, db)


@app.post("/api/v1/payments/webhook", include_in_schema=False)
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    if not valid_webhook_signature(payload, request.headers.get("x-paystack-signature")):
        raise HTTPException(401, "Invalid webhook signature")
    body = await request.json()
    if body.get("event") == "charge.success":
        data = body.get("data", {})
        try:
            await settle_order(data.get("reference", ""), data, db)
        except HTTPException as error:
            if error.status_code != 404:
                raise
    return {"status": "accepted"}
