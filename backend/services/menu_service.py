"""
Menu ingestion service for processing scraped menu data.

This service handles:
- Creating/updating menu items in the database
- Tracking price changes and creating history records
- Generating alerts for significant price changes
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import MenuItem, PriceHistory, Alert, Competitor
from scraper.doordash_scraper import ScrapeResult, ScrapedMenuItem


# Threshold for generating price change alerts (5% as specified in PRD)
PRICE_CHANGE_ALERT_THRESHOLD = Decimal("0.05")


@dataclass
class MenuIngestionResult:
    """Result of a menu ingestion operation."""
    competitor_id: str
    items_processed: int = 0
    items_created: int = 0
    items_updated: int = 0
    price_changes_detected: int = 0
    alerts_generated: int = 0
    errors: list[str] = field(default_factory=list)


async def ingest_menu_data(
    db: AsyncSession,
    competitor_id: str,
    data: ScrapeResult,
) -> MenuIngestionResult:
    """
    Ingest scraped menu data into the database.

    This function:
    1. Creates new menu items or updates existing ones
    2. Tracks price changes in PriceHistory
    3. Generates alerts for significant price changes (>5%)

    Args:
        db: Async database session
        competitor_id: UUID of the competitor
        data: Scraped menu data from the scraper

    Returns:
        MenuIngestionResult with statistics about the ingestion
    """
    result = MenuIngestionResult(competitor_id=competitor_id)

    if not data.success:
        result.errors.append(f"Scrape failed: {data.error_message}")
        return result

    # Get the competitor and update last_scraped_at
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        result.errors.append(f"Competitor not found: {competitor_id}")
        return result

    competitor.last_scraped_at = datetime.utcnow()

    # Process each scraped item
    for scraped_item in data.items:
        result.items_processed += 1

        try:
            await _process_menu_item(
                db=db,
                competitor_id=competitor_id,
                platform=data.platform,
                scraped_item=scraped_item,
                result=result,
            )
        except Exception as e:
            result.errors.append(f"Error processing {scraped_item.name}: {str(e)}")

    # Commit all changes
    await db.commit()

    return result


async def _process_menu_item(
    db: AsyncSession,
    competitor_id: str,
    platform: str,
    scraped_item: ScrapedMenuItem,
    result: MenuIngestionResult,
) -> None:
    """
    Process a single scraped menu item.

    Creates new items, updates existing ones, and tracks price changes.
    """
    # Try to find existing item by name and platform
    stmt = select(MenuItem).where(
        MenuItem.competitor_id == competitor_id,
        MenuItem.platform == platform,
        MenuItem.name == scraped_item.name,
    )
    existing = await db.execute(stmt)
    existing_item = existing.scalar_one_or_none()

    if existing_item is None:
        # Create new menu item
        new_item = MenuItem(
            competitor_id=competitor_id,
            platform=platform,
            name=scraped_item.name,
            category=scraped_item.category,
            description=scraped_item.description,
            current_price=scraped_item.price,
            is_available=scraped_item.is_available,
            menu_position=scraped_item.position,
        )
        db.add(new_item)
        await db.flush()  # Get the ID

        # Create initial price history entry
        initial_history = PriceHistory(
            menu_item_id=new_item.id,
            price=scraped_item.price,
            recorded_at=datetime.utcnow(),
        )
        db.add(initial_history)

        # Generate alert for new item
        new_item_alert = Alert(
            menu_item_id=new_item.id,
            alert_type="new_item",
            new_value=f"${scraped_item.price}",
        )
        db.add(new_item_alert)

        result.items_created += 1
        result.alerts_generated += 1

    else:
        # Update existing item
        old_price = existing_item.current_price
        new_price = scraped_item.price

        # Check if price changed
        if old_price != new_price:
            # Calculate change percentage
            if old_price > 0:
                change_pct = (new_price - old_price) / old_price
            else:
                change_pct = Decimal("1.0") if new_price > 0 else Decimal("0.0")

            # Update the item
            existing_item.current_price = new_price
            existing_item.updated_at = datetime.utcnow()

            # Create price history entry
            history_entry = PriceHistory(
                menu_item_id=existing_item.id,
                price=new_price,
                recorded_at=datetime.utcnow(),
                change_percentage=change_pct * 100,  # Store as percentage
            )
            db.add(history_entry)

            result.price_changes_detected += 1

            # Generate alert if change exceeds threshold
            if abs(change_pct) >= PRICE_CHANGE_ALERT_THRESHOLD:
                alert_type = "price_increase" if change_pct > 0 else "price_decrease"
                alert = Alert(
                    menu_item_id=existing_item.id,
                    alert_type=alert_type,
                    old_value=f"${old_price}",
                    new_value=f"${new_price}",
                    change_percentage=change_pct * 100,
                )
                db.add(alert)
                result.alerts_generated += 1

        # Update other fields regardless of price change
        existing_item.category = scraped_item.category or existing_item.category
        existing_item.description = scraped_item.description or existing_item.description
        existing_item.is_available = scraped_item.is_available
        existing_item.menu_position = scraped_item.position
        existing_item.updated_at = datetime.utcnow()

        result.items_updated += 1


async def get_price_history(
    db: AsyncSession,
    menu_item_id: str,
    days: int = 30,
) -> list[PriceHistory]:
    """
    Get price history for a menu item.

    Args:
        db: Async database session
        menu_item_id: UUID of the menu item
        days: Number of days of history to retrieve

    Returns:
        List of PriceHistory records ordered by date
    """
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(PriceHistory)
        .where(
            PriceHistory.menu_item_id == menu_item_id,
            PriceHistory.recorded_at >= cutoff_date,
        )
        .order_by(PriceHistory.recorded_at.desc())
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_unacknowledged_alerts(
    db: AsyncSession,
    competitor_id: Optional[str] = None,
    limit: int = 50,
) -> list[Alert]:
    """
    Get unacknowledged alerts, optionally filtered by competitor.

    Args:
        db: Async database session
        competitor_id: Optional competitor UUID to filter by
        limit: Maximum number of alerts to return

    Returns:
        List of Alert records ordered by creation date
    """
    stmt = (
        select(Alert)
        .join(MenuItem)
        .where(Alert.is_acknowledged == False)  # noqa: E712
    )

    if competitor_id:
        stmt = stmt.where(MenuItem.competitor_id == competitor_id)

    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def acknowledge_alert(
    db: AsyncSession,
    alert_id: str,
) -> bool:
    """
    Mark an alert as acknowledged.

    Args:
        db: Async database session
        alert_id: UUID of the alert

    Returns:
        True if successful, False if alert not found
    """
    alert = await db.get(Alert, alert_id)
    if not alert:
        return False

    alert.is_acknowledged = True
    await db.commit()
    return True
