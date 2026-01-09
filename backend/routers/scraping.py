"""
Scraping API router.

Provides endpoint to trigger menu scraping for competitors with mock fallback.
"""

import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Competitor, MenuItem, PriceHistory
from services.category_ai import category_ai_service

router = APIRouter(prefix="/scraping", tags=["scraping"])

DB = Annotated[AsyncSession, Depends(get_db)]


# Mock menu data for fallback (comprehensive categories for comparison)
MOCK_MENU_ITEMS = {
    "Burger": [
        {"name": "Classic Cheeseburger", "price": "11.99", "description": "1/4 lb beef patty with American cheese, lettuce, tomato, onion"},
        {"name": "Bacon BBQ Burger", "price": "14.99", "description": "1/3 lb patty with crispy bacon, BBQ sauce, onion rings"},
        {"name": "Mushroom Swiss Burger", "price": "13.49", "description": "Sautéed mushrooms, Swiss cheese, garlic aioli"},
        {"name": "Double Stack Burger", "price": "16.99", "description": "Two 1/4 lb patties, double cheese, special sauce"},
    ],
    "Chicken": [
        {"name": "Crispy Chicken Sandwich", "price": "10.99", "description": "Breaded chicken breast, pickles, mayo"},
        {"name": "Grilled Chicken Sandwich", "price": "11.49", "description": "Grilled chicken breast with lettuce and tomato"},
        {"name": "Chicken Tenders (5pc)", "price": "9.99", "description": "Hand-breaded chicken tenders with dipping sauce"},
        {"name": "Spicy Chicken Sandwich", "price": "11.99", "description": "Spicy breaded chicken with jalapeños and sriracha mayo"},
        {"name": "Buffalo Chicken Wrap", "price": "10.49", "description": "Crispy chicken, buffalo sauce, ranch, lettuce"},
    ],
    "Plant-Based": [
        {"name": "Impossible Burger", "price": "13.99", "description": "Plant-based patty with vegan cheese"},
        {"name": "Beyond Chicken Sandwich", "price": "12.99", "description": "Plant-based chicken with veggies"},
        {"name": "Veggie Wrap", "price": "10.99", "description": "Grilled vegetables, hummus, spinach"},
    ],
    "Sides": [
        {"name": "French Fries", "price": "4.99", "description": "Crispy golden fries with sea salt"},
        {"name": "Onion Rings", "price": "5.99", "description": "Beer-battered onion rings"},
        {"name": "Sweet Potato Fries", "price": "5.49", "description": "Crispy sweet potato fries with chipotle mayo"},
        {"name": "Loaded Nachos", "price": "8.99", "description": "Tortilla chips with cheese, jalapeños, sour cream"},
    ],
    "Drinks": [
        {"name": "Soft Drink", "price": "2.99", "description": "Coca-Cola, Sprite, or Dr Pepper"},
        {"name": "Milkshake", "price": "6.99", "description": "Chocolate, Vanilla, or Strawberry"},
        {"name": "Iced Tea", "price": "2.49", "description": "Fresh brewed sweet or unsweetened"},
    ],
    "Desserts": [
        {"name": "Chocolate Brownie", "price": "5.99", "description": "Warm fudge brownie with vanilla ice cream"},
        {"name": "Apple Pie", "price": "4.99", "description": "Classic apple pie slice, served warm"},
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

MOCK_PIZZA_ITEMS = {
    "Pizza": [
        {"name": "Margherita Pizza", "price": "14.99", "description": "Fresh mozzarella, tomato sauce, basil"},
        {"name": "Pepperoni Pizza", "price": "16.99", "description": "Classic pepperoni with mozzarella"},
        {"name": "Supreme Pizza", "price": "18.99", "description": "Pepperoni, sausage, peppers, onions, mushrooms"},
        {"name": "BBQ Chicken Pizza", "price": "17.99", "description": "Grilled chicken, BBQ sauce, red onions"},
        {"name": "Hawaiian Pizza", "price": "16.49", "description": "Ham, pineapple, mozzarella"},
    ],
    "Sides": [
        {"name": "Garlic Bread", "price": "4.99", "description": "Toasted bread with garlic butter"},
        {"name": "Caesar Salad", "price": "7.99", "description": "Romaine, parmesan, croutons, Caesar dressing"},
        {"name": "Wings (8pc)", "price": "10.99", "description": "Buffalo, BBQ, or Garlic Parmesan"},
    ],
    "Drinks": [
        {"name": "2-Liter Soda", "price": "3.99", "description": "Coke, Sprite, or Fanta"},
        {"name": "Bottled Water", "price": "1.99", "description": "16oz bottled water"},
    ],
}

MOCK_MEXICAN_ITEMS = {
    "Tacos": [
        {"name": "Street Tacos (3)", "price": "9.99", "description": "Carne asada, onion, cilantro, lime"},
        {"name": "Fish Tacos (2)", "price": "11.99", "description": "Beer-battered fish, cabbage slaw, chipotle crema"},
        {"name": "Chicken Tacos (3)", "price": "8.99", "description": "Grilled chicken, pico de gallo, guacamole"},
    ],
    "Burritos": [
        {"name": "Carne Asada Burrito", "price": "12.99", "description": "Steak, rice, beans, cheese, sour cream"},
        {"name": "Chicken Burrito Bowl", "price": "11.49", "description": "No tortilla, extra veggies"},
        {"name": "Veggie Burrito", "price": "10.99", "description": "Grilled veggies, black beans, rice, guac"},
    ],
    "Sides": [
        {"name": "Chips & Guacamole", "price": "6.99", "description": "Fresh tortilla chips with house-made guac"},
        {"name": "Mexican Rice", "price": "3.49", "description": "Cilantro lime rice"},
        {"name": "Refried Beans", "price": "3.49", "description": "Topped with cheese"},
    ],
}


def get_mock_menu_for_concept(concept_type: str | None) -> dict:
    """Get appropriate mock menu based on concept type."""
    if concept_type:
        concept_lower = concept_type.lower()
        if "pizza" in concept_lower or "italian" in concept_lower:
            return MOCK_PIZZA_ITEMS
        elif "mexican" in concept_lower or "taco" in concept_lower:
            return MOCK_MEXICAN_ITEMS
    return MOCK_MENU_ITEMS


def generate_mock_items(concept_type: str | None) -> list[dict]:
    """Generate mock menu items with slight price variations."""
    menu_data = get_mock_menu_for_concept(concept_type)
    items = []
    position = 0

    for category, category_items in menu_data.items():
        for item in category_items:
            # Add slight random price variation (-10% to +15%)
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


@router.post("/trigger/{competitor_id}")
async def trigger_scrape(
    competitor_id: str,
    db: DB,
) -> dict:
    """
    Trigger a menu scrape for a competitor.

    Tries Uber Eats first (most reliable), then DoorDash.
    """
    # Fetch competitor
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

    items_data = []
    scrape_source = None

    # Try Uber Eats first (more reliable, no login required)
    if competitor.ubereats_url and not items_data:
        try:
            from scraper.ubereats_scraper import UberEatsScraper

            print(f"Scraping Uber Eats for {competitor.name}...")
            scraper = UberEatsScraper()
            result = await scraper.scrape(competitor.ubereats_url)
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
                scrape_source = "ubereats"
                print(f"Successfully scraped {len(items_data)} items from Uber Eats")
        except Exception as e:
            print(f"Uber Eats scraper error for {competitor.name}: {e}")

    # Try DoorDash as fallback
    if competitor.doordash_url and not items_data:
        try:
            from scraper.doordash_scraper import DoorDashScraper

            print(f"Scraping DoorDash for {competitor.name}...")
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
                print(f"Successfully scraped {len(items_data)} items from DoorDash")
        except Exception as e:
            print(f"DoorDash scraper error for {competitor.name}: {e}")

    # If no data scraped, return error
    if not items_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not scrape menu for {competitor.name}. Please check the URLs are valid.",
        )

    # Clear existing menu items for this competitor
    await db.execute(
        delete(MenuItem).where(MenuItem.competitor_id == competitor_id)
    )

    # Save new menu items
    new_items = []
    for item_data in items_data:
        menu_item = MenuItem(
            competitor_id=competitor_id,
            platform=scrape_source,
            name=item_data["name"],
            category=item_data.get("category"),
            description=item_data.get("description"),
            current_price=item_data["price"],
            is_available=True,
            menu_position=item_data.get("position"),
        )
        db.add(menu_item)
        new_items.append(menu_item)

    # Flush to get IDs for price history
    await db.flush()

    # Record price history for each item
    for menu_item in new_items:
        price_record = PriceHistory(
            menu_item_id=menu_item.id,
            price=menu_item.current_price,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(price_record)

    # Update competitor's last_scraped_at
    competitor.last_scraped_at = datetime.now(timezone.utc)

    await db.commit()

    # Auto-map categories for the competitor
    categories_mapped = 0
    try:
        raw_categories = list(set(
            item_data.get("category") for item_data in items_data
            if item_data.get("category")
        ))
        if raw_categories:
            unmapped = await category_ai_service.get_unmapped_categories(
                db, "competitor", competitor_id, raw_categories
            )
            if unmapped:
                mapped = await category_ai_service.auto_map_categories(
                    db, "competitor", competitor_id, unmapped, threshold=0.5
                )
                categories_mapped = len(mapped)
                print(f"Auto-mapped {categories_mapped} categories for competitor {competitor.name}")
    except Exception as e:
        print(f"Category auto-mapping error (non-fatal): {e}")

    return {
        "success": True,
        "competitor_id": competitor_id,
        "competitor_name": competitor.name,
        "items_count": len(new_items),
        "source": scrape_source,
        "categories_mapped": categories_mapped,
        "message": f"Successfully scraped {len(new_items)} menu items from {scrape_source}",
    }


@router.get("/status/{competitor_id}")
async def get_scrape_status(
    competitor_id: str,
    db: DB,
) -> dict:
    """Get scraping status and item count for a competitor."""
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

    # Count menu items
    stmt = select(MenuItem).where(MenuItem.competitor_id == competitor_id)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "competitor_id": competitor_id,
        "competitor_name": competitor.name,
        "items_count": len(items),
        "last_scraped_at": competitor.last_scraped_at,
        "has_doordash_url": bool(competitor.doordash_url),
        "has_ubereats_url": bool(competitor.ubereats_url),
    }


# =============================================================================
# Scheduler Endpoints
# =============================================================================

@router.get("/scheduler/status")
async def get_scheduler_status_endpoint() -> dict:
    """
    Get the current status of the automated scraping scheduler.

    Returns information about:
    - Whether the scheduler is running
    - Next scheduled scrape time
    - Last run results
    - Statistics from the last run
    """
    from services.scheduler import get_scheduler_status
    return get_scheduler_status()


@router.post("/scheduler/trigger")
async def trigger_scheduled_scrape() -> dict:
    """
    Manually trigger an immediate scrape of all active competitors.

    This runs the same job that would run at 6am daily.
    Useful for testing or when you need fresh data immediately.
    """
    from services.scheduler import trigger_manual_scrape
    await trigger_manual_scrape()

    from services.scheduler import get_scheduler_status
    return {
        "message": "Manual scrape triggered successfully",
        "status": get_scheduler_status(),
    }
