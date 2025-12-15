"""
Pydantic V2 schemas for the Competitive Intelligence Dashboard API.

These schemas handle request/response serialization and validation.
Uses ConfigDict(from_attributes=True) for ORM compatibility.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Competitor Schemas
# =============================================================================

class CompetitorBase(BaseModel):
    """Base schema for competitor data."""
    name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    concept_type: Optional[str] = Field(None, max_length=100)
    doordash_url: Optional[str] = Field(None, max_length=500)
    ubereats_url: Optional[str] = Field(None, max_length=500)
    scraping_enabled: bool = True


class CompetitorCreate(CompetitorBase):
    """Schema for creating a new competitor."""
    pass


class CompetitorUpdate(BaseModel):
    """Schema for updating a competitor (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    concept_type: Optional[str] = Field(None, max_length=100)
    doordash_url: Optional[str] = Field(None, max_length=500)
    ubereats_url: Optional[str] = Field(None, max_length=500)
    scraping_enabled: Optional[bool] = None


class CompetitorRead(CompetitorBase):
    """Schema for reading competitor data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Price History Schemas
# =============================================================================

class PriceHistoryRead(BaseModel):
    """Schema for reading price history data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    price: Decimal
    recorded_at: datetime
    change_percentage: Optional[Decimal] = None


# =============================================================================
# Menu Item Schemas
# =============================================================================

class MenuItemBase(BaseModel):
    """Base schema for menu item data."""
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    current_price: Decimal = Field(..., ge=0)
    is_available: bool = True
    menu_position: Optional[int] = None


class MenuItemCreate(MenuItemBase):
    """Schema for creating a menu item."""
    competitor_id: str
    platform: str = Field(..., pattern="^(doordash|ubereats)$")


class MenuItemRead(MenuItemBase):
    """Schema for reading menu item data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    competitor_id: str
    platform: str
    created_at: datetime
    updated_at: datetime
    price_history: Optional[list[PriceHistoryRead]] = None


class MenuItemWithCompetitor(MenuItemRead):
    """Menu item with competitor name for display."""
    competitor_name: Optional[str] = None


# =============================================================================
# Alert Schemas
# =============================================================================

class AlertRead(BaseModel):
    """Schema for reading alert data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    menu_item_id: str
    alert_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_percentage: Optional[Decimal] = None
    is_acknowledged: bool
    created_at: datetime


class AlertWithItem(AlertRead):
    """Alert with menu item and competitor details."""
    item_name: Optional[str] = None
    competitor_name: Optional[str] = None


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    is_acknowledged: bool = True


# =============================================================================
# Dashboard Schemas
# =============================================================================

class CategoryBreakdown(BaseModel):
    """Price breakdown by category."""
    category: str
    client_avg: Optional[Decimal] = None
    market_avg: Decimal
    delta: Optional[str] = None
    items_compared: int


class CompetitorPriceSummary(BaseModel):
    """Summary of competitor pricing."""
    id: str
    name: str
    avg_price: Decimal
    price_delta: Optional[str] = None
    last_updated: Optional[datetime] = None
    item_count: int


class DashboardComparison(BaseModel):
    """Main dashboard comparison view."""
    market_average: Decimal
    total_items_tracked: int
    total_competitors: int
    competitors: list[CompetitorPriceSummary]
    category_breakdown: list[CategoryBreakdown]
    recent_alerts_count: int


class CompetitorMenuItem(BaseModel):
    """Menu item for comparison grid."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: Optional[str]
    price: Decimal
    competitor_id: str
    competitor_name: str


class ItemComparison(BaseModel):
    """Comparison of a single item across competitors."""
    item_name: str
    category: Optional[str]
    market_avg: Decimal
    prices: list[CompetitorMenuItem]


# =============================================================================
# Response Wrappers
# =============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: list
    total: int
    page: int
    page_size: int
    pages: int


class AlertsResponse(BaseModel):
    """Response for alerts endpoint."""
    alerts: list[AlertWithItem]
    unacknowledged_count: int
    total_count: int
