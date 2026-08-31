import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .models import User


class OrganizationSize(str, enum.Enum):
    individual = "individual"
    micro = "micro"
    small = "small"
    mid_size = "mid_size"
    large = "large"
    enterprise = "enterprise"
    unclassified = "unclassified"


class ParticipantCategory(str, enum.Enum):
    individual_consumer = "individual_consumer"
    hobbyist_collector = "hobbyist_collector"
    florist_landscaper = "florist_landscaper"
    professional_grower = "professional_grower"
    botanical_garden = "botanical_garden"
    nursery_garden_center = "nursery_garden_center"
    farm_agriculture_business = "farm_agriculture_business"
    small_business = "small_business"
    mid_size_business = "mid_size_business"
    large_enterprise = "large_enterprise"
    government_agency = "government_agency"
    university = "university"
    research_institution = "research_institution"
    nonprofit_ngo = "nonprofit_ngo"
    conservation_organization = "conservation_organization"
    other = "other"
    unclassified = "unclassified"


class ParticipantProfile(Base):
    __tablename__ = "participant_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    organization_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    organization_size: Mapped[OrganizationSize] = mapped_column(
        Enum(OrganizationSize), default=OrganizationSize.unclassified, index=True
    )
    category: Mapped[ParticipantCategory] = mapped_column(
        Enum(ParticipantCategory), default=ParticipantCategory.unclassified, index=True
    )
    country: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address_line1: Mapped[str | None] = mapped_column(String(180), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    geocoding_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    geocoded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship()
