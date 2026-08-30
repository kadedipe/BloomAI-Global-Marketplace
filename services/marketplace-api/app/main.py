import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .config import get_settings
from .database import create_schema, get_db
from .events import publish_event
from .models import Product, Role, User
from .schemas import (
    LoginRequest,
    ProductCreate,
    ProductResponse,
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
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "ok", "service": "marketplace-api"}


@app.get("/health/ready", tags=["health"])
async def ready(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
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
    response: Response,
    db: AsyncSession = Depends(get_db),
):
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
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in {Role.vendor, Role.admin}:
        raise HTTPException(403, "Vendor access required")
    product = Product(vendor_id=user.id, **payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    await publish_event(
        "product.created",
        {"product_id": product.id, "vendor_id": user.id, "name": product.name},
    )
    return product
