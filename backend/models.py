import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Boolean, DateTime, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return current UTC datetime with timezone information."""
    return datetime.now(timezone.utc)


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    concept_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    doordash_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ubereats_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scraping_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    menu_items: Mapped[list["MenuItem"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Competitor(id={self.id}, name={self.name})>"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    competitor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # doordash, ubereats
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    menu_position: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    competitor: Mapped["Competitor"] = relationship(back_populates="menu_items")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name={self.name}, price={self.current_price})>"


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    menu_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    change_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    menu_item: Mapped["MenuItem"] = relationship(back_populates="price_history")

    def __repr__(self) -> str:
        return f"<PriceHistory(id={self.id}, price={self.price}, recorded_at={self.recorded_at})>"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    menu_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # price_increase, price_decrease, new_item, item_removed
    old_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    change_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    menu_item: Mapped["MenuItem"] = relationship()

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type})>"


class OperatorProfile(Base):
    """
    Operator profile represents the restaurant owner's own business.
    This allows comparison between the operator's prices and competitors.
    """
    __tablename__ = "operator_profile"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    restaurant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    concept_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ubereats_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doordash_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Business metrics for ROI calculation
    monthly_orders: Mapped[Optional[int]] = mapped_column(nullable=True)
    average_order_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    profit_margin: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True  # Stored as percentage, e.g., 15.00 = 15%
    )

    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationship to operator's menu items
    menu_items: Mapped[list["OperatorMenuItem"]] = relationship(
        back_populates="operator", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<OperatorProfile(id={self.id}, name={self.restaurant_name})>"


class OperatorMenuItem(Base):
    """Menu items belonging to the operator's own restaurant."""
    __tablename__ = "operator_menu_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    operator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operator_profile.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    menu_position: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    operator: Mapped["OperatorProfile"] = relationship(back_populates="menu_items")

    def __repr__(self) -> str:
        return f"<OperatorMenuItem(id={self.id}, name={self.name}, price={self.current_price})>"


class CanonicalCategory(Base):
    """
    Standard category definitions for semantic grouping.
    Examples: Burgers, Chicken, Vegan & Plant-Based, Sides, Beverages, etc.
    """
    __tablename__ = "canonical_categories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated keywords for matching
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    # Relationship to mappings
    mappings: Mapped[list["CategoryMapping"]] = relationship(
        back_populates="canonical_category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CanonicalCategory(id={self.id}, name={self.name})>"


class CategoryMapping(Base):
    """
    Maps raw category names from restaurants to canonical categories.
    Supports per-restaurant mappings (different restaurants can map the same
    raw category differently if needed).
    """
    __tablename__ = "category_mappings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "competitor" or "operator"
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)  # competitor_id or operator_id
    raw_category: Mapped[str] = mapped_column(String(100), nullable=False)
    canonical_category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("canonical_categories.id", ondelete="CASCADE"), nullable=False
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True  # AI confidence score (0.0000 to 1.0000)
    )
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)  # True if manually set by user
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationship to canonical category
    canonical_category: Mapped["CanonicalCategory"] = relationship(back_populates="mappings")

    # Unique constraint: one mapping per source + raw_category
    __table_args__ = (
        UniqueConstraint('source_type', 'source_id', 'raw_category', name='uq_category_mapping'),
    )

    def __repr__(self) -> str:
        return f"<CategoryMapping(id={self.id}, raw={self.raw_category}, canonical_id={self.canonical_category_id})>"
