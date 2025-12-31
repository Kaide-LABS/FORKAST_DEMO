"""
Operator Profile API router.

Provides endpoints for managing the operator's own restaurant profile,
menu scraping, and price comparison analysis.
"""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import OperatorProfile, OperatorMenuItem, Competitor, MenuItem
from schemas import (
    OperatorProfileCreate,
    OperatorProfileUpdate,
    OperatorProfileRead,
    OperatorProfileWithItems,
    OperatorMenuItemRead,
    PriceGap,
    PriceAnalysisResponse,
    ROIAnalysis,
)

router = APIRouter(prefix="/operator", tags=["operator"])

DB = Annotated[AsyncSession, Depends(get_db)]


# =============================================================================
# Operator Profile CRUD
# =============================================================================

@router.get("/profile", response_model=Optional[OperatorProfileWithItems])
async def get_operator_profile(db: DB) -> Optional[OperatorProfileWithItems]:
    """
    Get the operator's profile with menu items.

    Returns None if no profile exists yet.
    """
    stmt = select(OperatorProfile).options(
        selectinload(OperatorProfile.menu_items)
    ).limit(1)

    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return None

    return OperatorProfileWithItems.model_validate(profile)


@router.post("/profile", response_model=OperatorProfileRead)
async def create_operator_profile(
    profile_data: OperatorProfileCreate,
    db: DB,
) -> OperatorProfileRead:
    """
    Create the operator's profile.

    Only one profile can exist - returns error if one already exists.
    """
    # Check if profile already exists
    existing_stmt = select(OperatorProfile).limit(1)
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Operator profile already exists. Use PUT to update.",
        )

    profile = OperatorProfile(**profile_data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return OperatorProfileRead.model_validate(profile)


@router.put("/profile", response_model=OperatorProfileRead)
async def update_operator_profile(
    profile_data: OperatorProfileUpdate,
    db: DB,
) -> OperatorProfileRead:
    """
    Update the operator's profile.

    Creates a new profile if one doesn't exist.
    """
    stmt = select(OperatorProfile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        # Create new profile with the update data
        create_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}
        if "restaurant_name" not in create_data:
            raise HTTPException(
                status_code=400,
                detail="restaurant_name is required when creating a new profile",
            )
        profile = OperatorProfile(**create_data)
        db.add(profile)
    else:
        # Update existing profile
        for key, value in profile_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)

    return OperatorProfileRead.model_validate(profile)


@router.delete("/profile")
async def delete_operator_profile(db: DB) -> dict:
    """Delete the operator's profile and all associated menu items."""
    stmt = select(OperatorProfile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Operator profile not found")

    await db.delete(profile)
    await db.commit()

    return {"status": "success", "message": "Operator profile deleted"}


# =============================================================================
# Menu Scraping
# =============================================================================

@router.post("/scrape")
async def scrape_operator_menu(
    background_tasks: BackgroundTasks,
    db: DB,
    platform: str = Query(default="ubereats", pattern="^(ubereats|doordash)$"),
) -> dict:
    """
    Trigger a scrape of the operator's menu from their delivery platform URL.

    Runs in the background and updates the operator's menu items.
    """
    stmt = select(OperatorProfile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Operator profile not found")

    # Get the URL for the selected platform
    url = profile.ubereats_url if platform == "ubereats" else profile.doordash_url

    if not url:
        raise HTTPException(
            status_code=400,
            detail=f"No {platform} URL configured for operator profile",
        )

    # Import here to avoid circular imports
    from services.operator_scraper import scrape_operator_menu_task

    # Run scraping in background
    background_tasks.add_task(scrape_operator_menu_task, profile.id, url, platform)

    return {
        "status": "started",
        "message": f"Scraping {platform} menu in background",
        "platform": platform,
        "url": url,
    }


@router.get("/menu", response_model=list[OperatorMenuItemRead])
async def get_operator_menu(
    db: DB,
    category: Optional[str] = None,
) -> list[OperatorMenuItemRead]:
    """Get the operator's menu items."""
    stmt = select(OperatorProfile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return []

    items_stmt = select(OperatorMenuItem).where(
        OperatorMenuItem.operator_id == profile.id
    )

    if category:
        items_stmt = items_stmt.where(OperatorMenuItem.category == category)

    items_stmt = items_stmt.order_by(OperatorMenuItem.menu_position)

    items_result = await db.execute(items_stmt)
    items = items_result.scalars().all()

    return [OperatorMenuItemRead.model_validate(item) for item in items]


# =============================================================================
# Price Analysis
# =============================================================================

@router.get("/price-analysis", response_model=PriceAnalysisResponse)
async def get_price_analysis(
    db: DB,
    threshold: float = Query(default=10.0, description="Percentage threshold for underpriced/overpriced"),
) -> PriceAnalysisResponse:
    """
    Analyze operator's prices vs competitors.

    Returns price gaps and opportunities for optimization.
    """
    # Get operator profile and menu
    profile_stmt = select(OperatorProfile).options(
        selectinload(OperatorProfile.menu_items)
    ).limit(1)
    profile_result = await db.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()

    if not profile or not profile.menu_items:
        raise HTTPException(
            status_code=400,
            detail="No operator menu items found. Please add your restaurant and scrape your menu first.",
        )

    # Get all competitor menu items
    competitor_items_stmt = select(MenuItem, Competitor.name.label("competitor_name")).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(Competitor.scraping_enabled == True)  # noqa: E712

    competitor_result = await db.execute(competitor_items_stmt)
    competitor_items = competitor_result.all()

    # Build competitor price map by item name (lowercase for matching)
    competitor_prices: dict[str, list[tuple[Decimal, str]]] = defaultdict(list)
    for item, comp_name in competitor_items:
        competitor_prices[item.name.lower()].append((item.current_price, comp_name))

    # Analyze each operator item
    price_gaps = []
    underpriced_count = 0
    overpriced_count = 0
    competitive_count = 0
    total_potential_increase = Decimal("0.00")
    operator_prices = []
    market_prices = []

    for op_item in profile.menu_items:
        item_name_lower = op_item.name.lower()
        operator_prices.append(op_item.current_price)

        # Find matching competitor items
        matching = competitor_prices.get(item_name_lower, [])

        if not matching:
            continue

        # Calculate competitor average
        comp_avg = sum(p for p, _ in matching) / len(matching)
        market_prices.extend(p for p, _ in matching)

        # Calculate difference
        diff = op_item.current_price - comp_avg
        pct_diff = (diff / comp_avg * 100) if comp_avg > 0 else Decimal("0.00")

        # Determine opportunity type
        if pct_diff < -threshold:
            opportunity_type = "underpriced"
            underpriced_count += 1
            total_potential_increase += abs(diff)
        elif pct_diff > threshold:
            opportunity_type = "overpriced"
            overpriced_count += 1
        else:
            opportunity_type = "competitive"
            competitive_count += 1

        price_gaps.append(PriceGap(
            operator_item_name=op_item.name,
            operator_price=op_item.current_price,
            competitor_avg_price=round(comp_avg, 2),
            price_difference=round(diff, 2),
            percentage_difference=round(pct_diff, 2),
            opportunity_type=opportunity_type,
            matching_competitors=len(matching),
        ))

    # Sort by percentage difference (most underpriced first)
    price_gaps.sort(key=lambda x: x.percentage_difference)

    # Calculate averages
    operator_avg = sum(operator_prices) / len(operator_prices) if operator_prices else Decimal("0.00")
    market_avg = sum(market_prices) / len(market_prices) if market_prices else Decimal("0.00")

    return PriceAnalysisResponse(
        operator_avg_price=round(operator_avg, 2),
        market_avg_price=round(market_avg, 2),
        total_items_compared=len(price_gaps),
        underpriced_items=underpriced_count,
        overpriced_items=overpriced_count,
        competitive_items=competitive_count,
        potential_revenue_increase=round(total_potential_increase, 2),
        price_gaps=price_gaps,
    )


@router.get("/roi-analysis", response_model=ROIAnalysis)
async def get_roi_analysis(
    db: DB,
    monthly_orders: Optional[int] = Query(default=None),
    average_order_value: Optional[float] = Query(default=None),
    profit_margin: Optional[float] = Query(default=None),
    forkast_monthly_cost: float = Query(default=99.0),
) -> ROIAnalysis:
    """
    Calculate ROI based on actual price analysis data.

    Uses operator profile values as defaults, but can be overridden with query params.
    """
    # Get operator profile
    profile_stmt = select(OperatorProfile).options(
        selectinload(OperatorProfile.menu_items)
    ).limit(1)
    profile_result = await db.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()

    # Get values from profile or use defaults
    orders = monthly_orders
    if orders is None:
        orders = profile.monthly_orders if profile and profile.monthly_orders else 1000

    aov = average_order_value
    if aov is None:
        if profile and profile.average_order_value:
            aov = float(profile.average_order_value)
        else:
            # Calculate from market average if no profile value
            market_avg_stmt = select(func.avg(MenuItem.current_price)).join(
                Competitor, MenuItem.competitor_id == Competitor.id
            ).where(Competitor.scraping_enabled == True)  # noqa: E712
            market_result = await db.execute(market_avg_stmt)
            market_avg = market_result.scalar()
            aov = float(market_avg) if market_avg else 25.0

    margin = profit_margin
    if margin is None:
        margin = float(profile.profit_margin) if profile and profile.profit_margin else 15.0

    # Get price analysis for underpriced items
    underpriced_count = 0
    avg_underpricing_pct = Decimal("0.00")
    top_opportunities: list[PriceGap] = []

    if profile and profile.menu_items:
        try:
            analysis = await get_price_analysis(db, threshold=10.0)
            underpriced_count = analysis.underpriced_items
            top_opportunities = [g for g in analysis.price_gaps if g.opportunity_type == "underpriced"][:5]

            # Calculate average underpricing
            underpriced_gaps = [g for g in analysis.price_gaps if g.opportunity_type == "underpriced"]
            if underpriced_gaps:
                avg_underpricing_pct = abs(sum(g.percentage_difference for g in underpriced_gaps) / len(underpriced_gaps))
        except HTTPException:
            pass  # No menu items yet

    # Calculate potential price increase based on underpriced items
    # Use the average underpricing percentage, capped at 10%
    potential_increase_pct = min(float(avg_underpricing_pct), 10.0) if avg_underpricing_pct > 0 else 3.0

    # Calculate ROI
    current_revenue = Decimal(str(orders)) * Decimal(str(aov))
    new_aov = Decimal(str(aov)) * (1 + Decimal(str(potential_increase_pct)) / 100)
    new_revenue = Decimal(str(orders)) * new_aov
    additional_revenue = new_revenue - current_revenue
    additional_profit = additional_revenue * (Decimal(str(margin)) / 100)
    annual_impact = additional_profit * 12

    # Forkast ROI
    forkast_annual = Decimal(str(forkast_monthly_cost)) * 12
    net_roi = annual_impact - forkast_annual
    roi_multiple = annual_impact / forkast_annual if forkast_annual > 0 else Decimal("0.00")

    return ROIAnalysis(
        monthly_orders=orders,
        average_order_value=Decimal(str(aov)),
        profit_margin=Decimal(str(margin)),
        current_monthly_revenue=round(current_revenue, 2),
        potential_price_increase_pct=round(Decimal(str(potential_increase_pct)), 2),
        additional_monthly_revenue=round(additional_revenue, 2),
        additional_monthly_profit=round(additional_profit, 2),
        annual_impact=round(annual_impact, 2),
        forkast_monthly_cost=Decimal(str(forkast_monthly_cost)),
        forkast_annual_cost=round(forkast_annual, 2),
        net_annual_roi=round(net_roi, 2),
        roi_multiple=round(roi_multiple, 2),
        underpriced_items_count=underpriced_count,
        avg_underpricing_pct=round(avg_underpricing_pct, 2),
        top_opportunities=top_opportunities,
    )


@router.get("/categories")
async def get_operator_categories(db: DB) -> list[str]:
    """Get list of unique categories from operator's menu."""
    stmt = select(OperatorProfile).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return []

    cat_stmt = select(OperatorMenuItem.category).distinct().where(
        OperatorMenuItem.operator_id == profile.id,
        OperatorMenuItem.category.isnot(None),
    ).order_by(OperatorMenuItem.category)

    cat_result = await db.execute(cat_stmt)
    return [r[0] for r in cat_result.all() if r[0]]
