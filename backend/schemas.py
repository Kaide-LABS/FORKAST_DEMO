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


class MenuItemSimple(MenuItemBase):
    """Schema for reading menu item data without price history."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    competitor_id: str
    platform: str
    created_at: datetime
    updated_at: datetime


class MenuItemRead(MenuItemSimple):
    """Schema for reading menu item data with optional price history."""
    price_history: Optional[list[PriceHistoryRead]] = None


class MenuItemWithCompetitor(MenuItemSimple):
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


class OperatorComparison(BaseModel):
    """Operator vs market comparison summary."""
    operator_name: str
    operator_avg_price: Decimal
    market_avg_price: Decimal
    price_difference: Decimal
    percentage_difference: Decimal
    underpriced_items: int
    overpriced_items: int
    competitive_items: int
    total_items: int


class DashboardComparison(BaseModel):
    """Main dashboard comparison view."""
    market_average: Decimal
    total_items_tracked: int
    total_competitors: int
    competitors: list[CompetitorPriceSummary]
    category_breakdown: list[CategoryBreakdown]
    recent_alerts_count: int
    operator_comparison: Optional[OperatorComparison] = None


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


# =============================================================================
# Price History Chart Schemas
# =============================================================================

class PricePoint(BaseModel):
    """Single price point for chart."""
    date: str
    price: float


class ItemPriceHistory(BaseModel):
    """Price history for a single menu item."""
    item_id: str
    item_name: str
    competitor_id: str
    competitor_name: str
    data: list[PricePoint]


class PriceHistoryResponse(BaseModel):
    """Response for price history chart endpoint."""
    items: list[ItemPriceHistory]
    start_date: str
    end_date: str


# =============================================================================
# Operator Profile Schemas
# =============================================================================

class OperatorProfileBase(BaseModel):
    """Base schema for operator profile."""
    restaurant_name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    concept_type: Optional[str] = Field(None, max_length=100)
    ubereats_url: Optional[str] = Field(None, max_length=500)
    doordash_url: Optional[str] = Field(None, max_length=500)
    monthly_orders: Optional[int] = Field(None, ge=0)
    average_order_value: Optional[Decimal] = Field(None, ge=0)
    profit_margin: Optional[Decimal] = Field(None, ge=0, le=100)


class OperatorProfileCreate(OperatorProfileBase):
    """Schema for creating operator profile."""
    pass


class OperatorProfileUpdate(BaseModel):
    """Schema for updating operator profile (all fields optional)."""
    restaurant_name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    concept_type: Optional[str] = Field(None, max_length=100)
    ubereats_url: Optional[str] = Field(None, max_length=500)
    doordash_url: Optional[str] = Field(None, max_length=500)
    monthly_orders: Optional[int] = Field(None, ge=0)
    average_order_value: Optional[Decimal] = Field(None, ge=0)
    profit_margin: Optional[Decimal] = Field(None, ge=0, le=100)


class OperatorProfileRead(OperatorProfileBase):
    """Schema for reading operator profile."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OperatorMenuItemRead(BaseModel):
    """Schema for reading operator menu item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    current_price: Decimal
    is_available: bool
    menu_position: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class OperatorProfileWithItems(OperatorProfileRead):
    """Operator profile with menu items."""
    menu_items: list[OperatorMenuItemRead] = []


# =============================================================================
# Price Comparison Schemas (Operator vs Competitors)
# =============================================================================

class PriceGap(BaseModel):
    """Represents a price gap between operator and competitors."""
    operator_item_name: str
    operator_price: Decimal
    competitor_avg_price: Decimal
    price_difference: Decimal
    percentage_difference: Decimal
    opportunity_type: str  # "underpriced", "overpriced", "competitive"
    matching_competitors: int


class PriceAnalysisResponse(BaseModel):
    """Response for price analysis endpoint."""
    operator_avg_price: Decimal
    market_avg_price: Decimal
    total_items_compared: int
    underpriced_items: int
    overpriced_items: int
    competitive_items: int
    potential_revenue_increase: Decimal
    price_gaps: list[PriceGap]


# =============================================================================
# ROI Analysis Schemas
# =============================================================================

class ROIAnalysis(BaseModel):
    """Enhanced ROI analysis with real data."""
    # Business inputs
    monthly_orders: int
    average_order_value: Decimal
    profit_margin: Decimal

    # Calculated values
    current_monthly_revenue: Decimal
    potential_price_increase_pct: Decimal
    additional_monthly_revenue: Decimal
    additional_monthly_profit: Decimal
    annual_impact: Decimal

    # Forkast ROI
    forkast_monthly_cost: Decimal = Decimal("99.00")
    forkast_annual_cost: Decimal = Decimal("1188.00")
    net_annual_roi: Decimal
    roi_multiple: Decimal  # How many times the subscription cost is returned

    # Price gap insights
    underpriced_items_count: int
    avg_underpricing_pct: Decimal
    top_opportunities: list[PriceGap]


# =============================================================================
# Category Mapping Schemas
# =============================================================================

class CanonicalCategoryBase(BaseModel):
    """Base schema for canonical category."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    keywords: Optional[str] = None  # Comma-separated keywords


class CanonicalCategoryCreate(CanonicalCategoryBase):
    """Schema for creating a canonical category."""
    pass


class CanonicalCategoryRead(CanonicalCategoryBase):
    """Schema for reading a canonical category."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class CategoryMappingBase(BaseModel):
    """Base schema for category mapping."""
    source_type: str = Field(..., pattern="^(competitor|operator)$")
    source_id: str
    raw_category: str = Field(..., min_length=1, max_length=100)
    canonical_category_id: str


class CategoryMappingCreate(CategoryMappingBase):
    """Schema for creating a category mapping."""
    is_manual: bool = True  # Manual mappings by default


class CategoryMappingUpdate(BaseModel):
    """Schema for updating a category mapping."""
    canonical_category_id: Optional[str] = None
    is_manual: Optional[bool] = None


class CategoryMappingRead(BaseModel):
    """Schema for reading a category mapping."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    source_id: str
    raw_category: str
    canonical_category_id: str
    canonical_category: Optional[CanonicalCategoryRead] = None
    confidence_score: Optional[Decimal] = None
    is_manual: bool
    created_at: datetime
    updated_at: datetime


class CategorySuggestionAlt(BaseModel):
    """Alternative suggestion for category mapping."""
    id: str
    name: str
    score: float


class CategorySuggestionRead(BaseModel):
    """AI-generated suggestion for mapping a category."""
    raw_category: str
    canonical_category_id: str
    canonical_category_name: str
    confidence_score: float
    alternatives: list[CategorySuggestionAlt]


class CategoryComparisonItem(BaseModel):
    """Single item in semantic category comparison."""
    canonical_category_id: str
    canonical_category_name: str
    operator_avg: Optional[Decimal] = None
    operator_items: int = 0
    market_avg: Optional[Decimal] = None
    market_items: int = 0
    delta_pct: Optional[Decimal] = None


class CategoryComparisonResponse(BaseModel):
    """Response for semantic category comparison."""
    comparisons: list[CategoryComparisonItem]
    unmapped_operator_categories: list[str]
    unmapped_competitor_categories: list[str]
