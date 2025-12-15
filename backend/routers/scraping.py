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

router = APIRouter(prefix="/scraping", tags=["scraping"])

DB = Annotated[AsyncSession, Depends(get_db)]


# Mock menu data for fallback
MOCK_MENU_ITEMS = {
    "Burger": [
        {"name": "Classic Cheeseburger", "price": "11.99", "description": "1/4 lb beef patty with American cheese, lettuce, tomato, onion"},
        {"name": "Bacon BBQ Burger", "price": "14.99", "description": "1/3 lb patty with crispy bacon, BBQ sauce, onion rings"},
        {"name": "Mushroom Swiss Burger", "price": "13.49", "description": "Sautéed mushrooms, Swiss cheese, garlic aioli"},
        {"name": "Double Stack Burger", "price": "16.99", "description": "Two 1/4 lb patties, double cheese, special sauce"},
        {"name": "Veggie Burger", "price": "12.49", "description": "Plant-based patty with avocado and sprouts"},
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

    If the real scraper fails or returns no results, falls back to mock data.
    """
    # Fetch competitor
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

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
            print(f"Scraper error for {competitor.name}: {e}")
            # Fall through to mock data

    # Fallback to mock data if scraping failed or returned nothing
    if not items_data:
        items_data = generate_mock_items(competitor.concept_type)
        scrape_source = "mock"

    # Clear existing menu items for this competitor
    await db.execute(
        delete(MenuItem).where(MenuItem.competitor_id == competitor_id)
    )

    # Save new menu items
    new_items = []
    for item_data in items_data:
        menu_item = MenuItem(
            competitor_id=competitor_id,
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

    return {
        "success": True,
        "competitor_id": competitor_id,
        "competitor_name": competitor.name,
        "items_count": len(new_items),
        "source": scrape_source,
        "message": f"Successfully loaded {len(new_items)} menu items from {scrape_source} data",
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
