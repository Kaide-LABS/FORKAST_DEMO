"""
Scheduled scraping service using APScheduler.

Handles automated daily scrapes of competitor menus at 6am local time.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
import random

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import Competitor, MenuItem, PriceHistory, Alert
from services.category_ai import category_ai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None

# Track scheduler status
scheduler_status = {
    "is_running": False,
    "last_run": None,
    "last_run_result": None,
    "next_run": None,
    "competitors_scraped": 0,
    "total_items_updated": 0,
}


# Mock menu data for fallback (comprehensive categories for comparison)
MOCK_MENU_ITEMS = {
    "Burger": [
        {"name": "Classic Cheeseburger", "price": "11.99", "description": "1/4 lb beef patty with American cheese"},
        {"name": "Bacon BBQ Burger", "price": "14.99", "description": "1/3 lb patty with crispy bacon, BBQ sauce"},
        {"name": "Mushroom Swiss Burger", "price": "13.49", "description": "Sautéed mushrooms, Swiss cheese"},
        {"name": "Double Stack Burger", "price": "16.99", "description": "Two 1/4 lb patties, double cheese"},
    ],
    "Chicken": [
        {"name": "Crispy Chicken Sandwich", "price": "10.99", "description": "Breaded chicken breast, pickles, mayo"},
        {"name": "Grilled Chicken Sandwich", "price": "11.49", "description": "Grilled chicken breast with lettuce and tomato"},
        {"name": "Chicken Tenders (5pc)", "price": "9.99", "description": "Hand-breaded chicken tenders"},
        {"name": "Spicy Chicken Sandwich", "price": "11.99", "description": "Spicy breaded chicken with jalapeños"},
        {"name": "Buffalo Chicken Wrap", "price": "10.49", "description": "Crispy chicken, buffalo sauce, ranch"},
    ],
    "Plant-Based": [
        {"name": "Impossible Burger", "price": "13.99", "description": "Plant-based patty with vegan cheese"},
        {"name": "Beyond Chicken Sandwich", "price": "12.99", "description": "Plant-based chicken with veggies"},
        {"name": "Veggie Wrap", "price": "10.99", "description": "Grilled vegetables, hummus, spinach"},
    ],
    "Sides": [
        {"name": "French Fries", "price": "4.99", "description": "Crispy golden fries"},
        {"name": "Onion Rings", "price": "5.99", "description": "Beer-battered onion rings"},
        {"name": "Sweet Potato Fries", "price": "5.49", "description": "Crispy sweet potato fries"},
        {"name": "Loaded Nachos", "price": "8.99", "description": "Tortilla chips with cheese"},
    ],
    "Drinks": [
        {"name": "Soft Drink", "price": "2.99", "description": "Coca-Cola, Sprite, or Dr Pepper"},
        {"name": "Milkshake", "price": "6.99", "description": "Chocolate, Vanilla, or Strawberry"},
        {"name": "Iced Tea", "price": "2.49", "description": "Fresh brewed"},
    ],
    "Desserts": [
        {"name": "Chocolate Brownie", "price": "5.99", "description": "Warm fudge brownie"},
        {"name": "Apple Pie", "price": "4.99", "description": "Classic apple pie slice"},
    ],
    "Sauces": [
        {"name": "BBQ Sauce", "price": "0.75", "description": "Smoky barbecue dipping sauce"},
        {"name": "Ranch Dressing", "price": "0.75", "description": "Creamy ranch dip"},
        {"name": "Hot Sauce", "price": "0.50", "description": "Spicy buffalo sauce"},
        {"name": "Honey Mustard", "price": "0.75", "description": "Sweet and tangy dip"},
    ],
    "Meal Deals": [
        {"name": "Burger Combo", "price": "14.99", "description": "Any burger with fries and drink"},
        {"name": "Chicken Combo", "price": "13.99", "description": "Chicken sandwich with fries and drink"},
        {"name": "Family Pack", "price": "39.99", "description": "4 burgers, 2 large fries, 4 drinks"},
    ],
}


def generate_mock_items() -> list[dict]:
    """Generate mock menu items with price variations."""
    items = []
    position = 0

    for category, category_items in MOCK_MENU_ITEMS.items():
        for item in category_items:
            base_price = Decimal(item["price"])
            variation = Decimal(str(random.uniform(0.90, 1.15)))
            final_price = (base_price * variation).quantize(Decimal("0.01"))

            items.append({
                "name": item["name"],
                "category": category,
                "description": item["description"],
                "price": final_price,
                "position": position,
            })
            position += 1

    return items


async def scrape_competitor(db: AsyncSession, competitor: Competitor) -> dict:
    """
    Scrape a single competitor's menu.

    Returns dict with success status and item count.
    """
    items_data = []
    scrape_source = "mock"

    # Try real scraping if URL is available
    if competitor.doordash_url:
        try:
            from scraper.doordash_scraper import DoorDashScraper

            scraper = DoorDashScraper()
            result = await scraper.scrape(competitor.doordash_url)
            await scraper.close()

            if result.success and result.items:
                items_data = [
                    {
                        "name": item.name,
                        "category": item.category,
                        "description": item.description,
                        "price": item.price,
                        "position": item.position,
                    }
                    for item in result.items
                ]
                scrape_source = "doordash"
        except Exception as e:
            logger.warning(f"Scraper error for {competitor.name}: {e}")

    # Fallback to mock data
    if not items_data:
        items_data = generate_mock_items()
        scrape_source = "mock"

    # Get existing items for price change detection
    existing_stmt = select(MenuItem).where(MenuItem.competitor_id == competitor.id)
    existing_result = await db.execute(existing_stmt)
    existing_items = {item.name: item for item in existing_result.scalars().all()}

    # Clear existing menu items
    await db.execute(
        delete(MenuItem).where(MenuItem.competitor_id == competitor.id)
    )

    # Save new menu items and detect price changes
    new_items = []
    alerts_created = 0

    for item_data in items_data:
        menu_item = MenuItem(
            competitor_id=competitor.id,
            platform="doordash" if scrape_source == "doordash" else "mock",
            name=item_data["name"],
            category=item_data.get("category"),
            description=item_data.get("description"),
            current_price=item_data["price"],
            is_available=True,
            menu_position=item_data.get("position"),
        )
        db.add(menu_item)
        new_items.append(menu_item)

    await db.flush()

    # Record price history and create alerts for significant changes
    for menu_item in new_items:
        # Record price history
        price_record = PriceHistory(
            menu_item_id=menu_item.id,
            price=menu_item.current_price,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(price_record)

        # Check for price changes (>5% threshold)
        if menu_item.name in existing_items:
            old_item = existing_items[menu_item.name]
            old_price = float(old_item.current_price)
            new_price = float(menu_item.current_price)

            if old_price > 0:
                change_pct = ((new_price - old_price) / old_price) * 100

                if abs(change_pct) >= 5:
                    alert_type = "price_increase" if change_pct > 0 else "price_decrease"
                    alert = Alert(
                        menu_item_id=menu_item.id,
                        alert_type=alert_type,
                        old_value=f"${old_price:.2f}",
                        new_value=f"${new_price:.2f}",
                        change_percentage=Decimal(str(round(change_pct, 2))),
                        is_acknowledged=False,
                    )
                    db.add(alert)
                    alerts_created += 1

    # Update competitor's last_scraped_at
    competitor.last_scraped_at = datetime.now(timezone.utc)

    # Auto-map categories for the competitor
    categories_mapped = 0
    try:
        raw_categories = list(set(
            item_data.get("category") for item_data in items_data
            if item_data.get("category")
        ))
        if raw_categories:
            unmapped = await category_ai_service.get_unmapped_categories(
                db, "competitor", competitor.id, raw_categories, competitor.tenant_id
            )
            if unmapped:
                mapped = await category_ai_service.auto_map_categories(
                    db, "competitor", competitor.id, unmapped, threshold=0.5, tenant_id=competitor.tenant_id
                )
                categories_mapped = len(mapped)
                logger.info(f"Auto-mapped {categories_mapped} categories for {competitor.name}")
    except Exception as e:
        logger.warning(f"Category auto-mapping error for {competitor.name}: {e}")

    return {
        "success": True,
        "items_count": len(new_items),
        "alerts_created": alerts_created,
        "categories_mapped": categories_mapped,
        "source": scrape_source,
    }


async def run_scheduled_scrape():
    """
    Run scheduled scrape for all active competitors.

    This is the main job that runs daily at 6am.
    """
    global scheduler_status

    logger.info("Starting scheduled scrape for all competitors...")
    scheduler_status["last_run"] = datetime.now(timezone.utc).isoformat()

    total_items = 0
    total_alerts = 0
    competitors_processed = 0
    errors = []

    try:
        async with async_session() as db:
            # Get all active competitors
            stmt = select(Competitor).where(Competitor.scraping_enabled == True)  # noqa: E712
            result = await db.execute(stmt)
            competitors = result.scalars().all()

            logger.info(f"Found {len(competitors)} active competitors to scrape")

            for competitor in competitors:
                try:
                    logger.info(f"Scraping {competitor.name}...")
                    scrape_result = await scrape_competitor(db, competitor)

                    total_items += scrape_result["items_count"]
                    total_alerts += scrape_result["alerts_created"]
                    competitors_processed += 1

                    logger.info(
                        f"  - {competitor.name}: {scrape_result['items_count']} items, "
                        f"{scrape_result['alerts_created']} alerts ({scrape_result['source']})"
                    )

                except Exception as e:
                    error_msg = f"Error scraping {competitor.name}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            await db.commit()

        scheduler_status["last_run_result"] = {
            "success": True,
            "competitors_scraped": competitors_processed,
            "total_items": total_items,
            "total_alerts": total_alerts,
            "errors": errors,
        }
        scheduler_status["competitors_scraped"] = competitors_processed
        scheduler_status["total_items_updated"] = total_items

        logger.info(
            f"Scheduled scrape complete: {competitors_processed} competitors, "
            f"{total_items} items, {total_alerts} alerts"
        )

    except Exception as e:
        error_msg = f"Scheduled scrape failed: {str(e)}"
        logger.error(error_msg)
        scheduler_status["last_run_result"] = {
            "success": False,
            "error": error_msg,
        }


def get_scheduler_status() -> dict:
    """Get current scheduler status."""
    global scheduler, scheduler_status

    status = scheduler_status.copy()
    status["is_running"] = scheduler is not None and scheduler.running

    if scheduler and scheduler.running:
        job = scheduler.get_job("daily_scrape")
        if job and job.next_run_time:
            status["next_run"] = job.next_run_time.isoformat()

    return status


async def start_scheduler():
    """Initialize and start the scheduler."""
    global scheduler, scheduler_status

    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return

    scheduler = AsyncIOScheduler()

    # Schedule daily scrape at 6:00 AM local time
    scheduler.add_job(
        run_scheduled_scrape,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_scrape",
        name="Daily Competitor Scrape",
        replace_existing=True,
    )

    scheduler.start()
    scheduler_status["is_running"] = True

    # Get next run time
    job = scheduler.get_job("daily_scrape")
    if job and job.next_run_time:
        scheduler_status["next_run"] = job.next_run_time.isoformat()

    logger.info(f"Scheduler started. Next scrape at: {scheduler_status['next_run']}")


async def stop_scheduler():
    """Stop the scheduler."""
    global scheduler, scheduler_status

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        scheduler_status["is_running"] = False
        logger.info("Scheduler stopped")


async def trigger_manual_scrape():
    """Manually trigger an immediate scrape (for testing)."""
    logger.info("Manual scrape triggered")
    await run_scheduled_scrape()
