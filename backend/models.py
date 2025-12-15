import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Boolean, DateTime, Numeric
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
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
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
        DateTime, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
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
        DateTime, default=utc_now
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
        DateTime, default=utc_now
    )

    menu_item: Mapped["MenuItem"] = relationship()

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type})>"
