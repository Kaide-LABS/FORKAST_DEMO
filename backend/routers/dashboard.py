"""
Dashboard API router.

Provides endpoints for the main dashboard comparison views.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Competitor, MenuItem, Alert, PriceHistory, OperatorProfile, OperatorMenuItem
from schemas import (
    DashboardComparison,
    CompetitorPriceSummary,
    CategoryBreakdown,
    ItemComparison,
    CompetitorMenuItem,
    PriceHistoryResponse,
    ItemPriceHistory,
    PricePoint,
    OperatorComparison,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/comparison", response_model=DashboardComparison)
async def get_comparison(db: DB) -> DashboardComparison:
    """
    Get the main dashboard comparison view.

    Returns market averages, competitor summaries, and category breakdowns.
    """
    # Get all active competitors with their stats
    competitors_stmt = select(
        Competitor.id,
        Competitor.name,
        Competitor.last_scraped_at,
        func.count(MenuItem.id).label("item_count"),
        func.avg(MenuItem.current_price).label("avg_price"),
    ).outerjoin(
        MenuItem, Competitor.id == MenuItem.competitor_id
    ).where(
        Competitor.scraping_enabled == True  # noqa: E712
    ).group_by(Competitor.id)

    competitors_result = await db.execute(competitors_stmt)
    competitors_data = competitors_result.all()

    # Calculate market average
    all_prices_stmt = select(func.avg(MenuItem.current_price)).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(Competitor.scraping_enabled == True)  # noqa: E712

    market_avg_result = await db.execute(all_prices_stmt)
    market_avg_val = market_avg_result.scalar()
    market_average = Decimal(str(market_avg_val)) if market_avg_val is not None else Decimal("0.00")

    # Build competitor summaries
    competitor_summaries = []
    for comp in competitors_data:
        avg_price = Decimal(str(comp.avg_price)) if comp.avg_price else Decimal("0.00")

        # Calculate delta from market average
        if market_average > 0 and avg_price > 0:
            delta_pct = ((avg_price - market_average) / market_average) * 100
            delta_str = f"{delta_pct:+.1f}%"
        else:
            delta_str = None

        competitor_summaries.append(
            CompetitorPriceSummary(
                id=comp.id,
                name=comp.name,
                avg_price=avg_price,
                price_delta=delta_str,
                last_updated=comp.last_scraped_at,
                item_count=comp.item_count or 0,
            )
        )

    # Get category breakdown
    category_stmt = select(
        MenuItem.category,
        func.count(MenuItem.id).label("item_count"),
        func.avg(MenuItem.current_price).label("avg_price"),
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Competitor.scraping_enabled == True  # noqa: E712
    ).group_by(MenuItem.category)

    category_result = await db.execute(category_stmt)
    categories_data = category_result.all()

    category_breakdowns = []
    for cat in categories_data:
        cat_avg = Decimal(str(cat.avg_price)) if cat.avg_price else Decimal("0.00")
        category_breakdowns.append(
            CategoryBreakdown(
                category=cat.category or "Uncategorized",
                client_avg=None,  # Client menu not implemented yet
                market_avg=cat_avg,
                delta=None,
                items_compared=cat.item_count or 0,
            )
        )

    # Get total items count
    total_items_stmt = select(func.count(MenuItem.id)).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(Competitor.scraping_enabled == True)  # noqa: E712

    total_items_result = await db.execute(total_items_stmt)
    total_items = total_items_result.scalar() or 0

    # Get unacknowledged alerts count
    alerts_stmt = select(func.count(Alert.id)).where(
        Alert.is_acknowledged == False  # noqa: E712
    )
    alerts_result = await db.execute(alerts_stmt)
    alerts_count = alerts_result.scalar() or 0

    # Get operator comparison if profile exists
    operator_comparison = None
    op_profile_stmt = select(OperatorProfile).limit(1)
    op_profile_result = await db.execute(op_profile_stmt)
    op_profile = op_profile_result.scalar_one_or_none()

    if op_profile:
        # Get operator's menu items and calculate average
        op_items_stmt = select(
            func.count(OperatorMenuItem.id).label("item_count"),
            func.avg(OperatorMenuItem.current_price).label("avg_price"),
        ).where(OperatorMenuItem.operator_id == op_profile.id)

        op_items_result = await db.execute(op_items_stmt)
        op_stats = op_items_result.one_or_none()

        if op_stats and op_stats.item_count > 0:
            op_avg = Decimal(str(op_stats.avg_price)) if op_stats.avg_price else Decimal("0.00")

            # Calculate price comparison stats
            # Get all operator items for detailed comparison
            op_all_items_stmt = select(OperatorMenuItem).where(
                OperatorMenuItem.operator_id == op_profile.id
            )
            op_all_items_result = await db.execute(op_all_items_stmt)
            op_items = op_all_items_result.scalars().all()

            # Build competitor price map
            comp_items_stmt = select(MenuItem.name, MenuItem.current_price).join(
                Competitor, MenuItem.competitor_id == Competitor.id
            ).where(Competitor.scraping_enabled == True)  # noqa: E712

            comp_items_result = await db.execute(comp_items_stmt)
            comp_items = comp_items_result.all()

            from collections import defaultdict
            comp_prices: dict[str, list] = defaultdict(list)
            for name, price in comp_items:
                comp_prices[name.lower()].append(price)

            # Count underpriced, overpriced, competitive
            underpriced = 0
            overpriced = 0
            competitive = 0
            threshold = Decimal("10.0")  # 10% threshold

            for op_item in op_items:
                matching = comp_prices.get(op_item.name.lower(), [])
                if not matching:
                    continue

                comp_avg = sum(matching) / len(matching)
                pct_diff = ((op_item.current_price - comp_avg) / comp_avg * 100) if comp_avg > 0 else Decimal("0.00")

                if pct_diff < -threshold:
                    underpriced += 1
                elif pct_diff > threshold:
                    overpriced += 1
                else:
                    competitive += 1

            # Calculate overall difference
            price_diff = op_avg - market_average
            pct_diff = ((price_diff / market_average) * 100) if market_average > 0 else Decimal("0.00")

            operator_comparison = OperatorComparison(
                operator_name=op_profile.restaurant_name,
                operator_avg_price=round(op_avg, 2),
                market_avg_price=round(market_average, 2),
                price_difference=round(price_diff, 2),
                percentage_difference=round(pct_diff, 2),
                underpriced_items=underpriced,
                overpriced_items=overpriced,
                competitive_items=competitive,
                total_items=op_stats.item_count,
            )

    return DashboardComparison(
        market_average=Decimal(str(market_average)),
        total_items_tracked=total_items,
        total_competitors=len(competitors_data),
        competitors=competitor_summaries,
        category_breakdown=category_breakdowns,
        recent_alerts_count=alerts_count,
        operator_comparison=operator_comparison,
    )


@router.get("/items", response_model=list[ItemComparison])
async def get_item_comparisons(
    db: DB,
    category: str | None = None,
) -> list[ItemComparison]:
    """
    Get item-level price comparisons across competitors.

    Args:
        category: Optional filter by category
    """
    # Get all menu items from active competitors
    stmt = select(MenuItem, Competitor.name.label("competitor_name")).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Competitor.scraping_enabled == True  # noqa: E712
    )

    if category:
        stmt = stmt.where(MenuItem.category == category)

    stmt = stmt.order_by(MenuItem.name)

    result = await db.execute(stmt)
    items_data = result.all()

    # Group items by name (fuzzy matching could be added later)
    items_by_name: dict[str, list[tuple]] = defaultdict(list)
    for item, competitor_name in items_data:
        items_by_name[item.name.lower()].append((item, competitor_name))

    # Build comparison list
    comparisons = []
    for item_name, item_list in items_by_name.items():
        if len(item_list) == 0:
            continue

        # Calculate market average for this item
        prices = [item.current_price for item, _ in item_list]
        market_avg = sum(prices) / len(prices) if prices else Decimal("0.00")

        # Get category from first item
        first_item = item_list[0][0]

        competitor_items = [
            CompetitorMenuItem(
                id=item.id,
                name=item.name,
                category=item.category,
                price=item.current_price,
                competitor_id=item.competitor_id,
                competitor_name=competitor_name,
            )
            for item, competitor_name in item_list
        ]

        comparisons.append(
            ItemComparison(
                item_name=first_item.name,
                category=first_item.category,
                market_avg=market_avg,
                prices=competitor_items,
            )
        )

    return comparisons


@router.get("/categories")
async def get_categories(
    db: DB,
    competitor_id: Optional[str] = Query(default=None, description="Filter by competitor ID"),
) -> list[str]:
    """
    Get list of all unique categories.

    Args:
        competitor_id: Optional filter to get categories for a specific competitor
    """
    stmt = select(MenuItem.category).distinct().where(
        MenuItem.category.isnot(None)
    )

    if competitor_id:
        stmt = stmt.where(MenuItem.competitor_id == competitor_id)

    stmt = stmt.order_by(MenuItem.category)

    result = await db.execute(stmt)
    return [r[0] for r in result.all() if r[0]]


@router.get("/summary")
async def get_summary(db: DB) -> dict:
    """
    Get a quick summary of the dashboard data.
    """
    # Count competitors
    comp_count_stmt = select(func.count(Competitor.id)).where(
        Competitor.scraping_enabled == True  # noqa: E712
    )
    comp_result = await db.execute(comp_count_stmt)
    competitor_count = comp_result.scalar() or 0

    # Count items
    item_count_stmt = select(func.count(MenuItem.id))
    item_result = await db.execute(item_count_stmt)
    item_count = item_result.scalar() or 0

    # Count unacknowledged alerts
    alert_count_stmt = select(func.count(Alert.id)).where(
        Alert.is_acknowledged == False  # noqa: E712
    )
    alert_result = await db.execute(alert_count_stmt)
    alert_count = alert_result.scalar() or 0

    # Get market average
    avg_stmt = select(func.avg(MenuItem.current_price))
    avg_result = await db.execute(avg_stmt)
    market_avg = avg_result.scalar() or 0

    return {
        "competitors_tracked": competitor_count,
        "items_tracked": item_count,
        "unread_alerts": alert_count,
        "market_average_price": float(market_avg) if market_avg else 0,
    }


@router.get("/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    db: DB,
    days: int = Query(default=30, ge=1, le=90, description="Number of days of history"),
    competitor_id: Optional[str] = Query(default=None, description="Filter by competitor ID"),
    item_ids: Optional[str] = Query(default=None, description="Comma-separated item IDs"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    limit: int = Query(default=5, ge=1, le=20, description="Max items to return (used when competitor_id is set)"),
    limit_per_competitor: Optional[int] = Query(default=None, ge=1, le=100, description="Max items per competitor (for all competitors view)"),
) -> PriceHistoryResponse:
    """
    Get price history for menu items to display in charts.

    Returns price data points over time for visualization.

    Args:
        limit: Used when viewing a specific competitor
        limit_per_competitor: Used when viewing all competitors - returns N items per competitor
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    items_data = []

    # If limit_per_competitor is specified, get items for each competitor separately
    if limit_per_competitor is not None and not competitor_id:
        # Get all active competitors
        comp_stmt = select(Competitor.id).where(Competitor.scraping_enabled == True)  # noqa: E712
        comp_result = await db.execute(comp_stmt)
        competitor_ids = [c.id for c in comp_result.all()]

        # For each competitor, get up to limit_per_competitor items
        for comp_id in competitor_ids:
            items_stmt = select(
                MenuItem.id,
                MenuItem.name,
                Competitor.id.label("competitor_id"),
                Competitor.name.label("competitor_name"),
            ).join(
                Competitor, MenuItem.competitor_id == Competitor.id
            ).where(
                Competitor.id == comp_id
            ).limit(limit_per_competitor)

            result = await db.execute(items_stmt)
            items_data.extend(result.all())
    else:
        # Standard query with single limit
        items_stmt = select(
            MenuItem.id,
            MenuItem.name,
            Competitor.id.label("competitor_id"),
            Competitor.name.label("competitor_name"),
        ).join(
            Competitor, MenuItem.competitor_id == Competitor.id
        ).where(
            Competitor.scraping_enabled == True  # noqa: E712
        )

        # Apply filters
        if competitor_id:
            items_stmt = items_stmt.where(Competitor.id == competitor_id)

        if item_ids:
            item_id_list = [id.strip() for id in item_ids.split(",")]
            items_stmt = items_stmt.where(MenuItem.id.in_(item_id_list))

        if category:
            items_stmt = items_stmt.where(MenuItem.category == category)

        items_stmt = items_stmt.limit(limit)

        items_result = await db.execute(items_stmt)
        items_data = items_result.all()

    # Get price history for each item
    result_items = []
    for item in items_data:
        # Get price history records
        history_stmt = select(
            PriceHistory.price,
            PriceHistory.recorded_at,
        ).where(
            PriceHistory.menu_item_id == item.id,
            PriceHistory.recorded_at >= start_date,
        ).order_by(PriceHistory.recorded_at)

        history_result = await db.execute(history_stmt)
        history_data = history_result.all()

        # Convert to price points
        price_points = [
            PricePoint(
                date=record.recorded_at.strftime("%Y-%m-%d"),
                price=float(record.price),
            )
            for record in history_data
        ]

        if price_points:  # Only include items with history
            result_items.append(
                ItemPriceHistory(
                    item_id=item.id,
                    item_name=item.name,
                    competitor_id=item.competitor_id,
                    competitor_name=item.competitor_name,
                    data=price_points,
                )
            )

    return PriceHistoryResponse(
        items=result_items,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )
