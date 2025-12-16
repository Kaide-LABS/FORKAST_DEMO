"""
Seed script for demo data.

Creates realistic Austin-area burger competitors with price history
spanning 14 days to demonstrate trends and generate alerts.

Usage:
    cd backend
    python scripts/seed_demo_data.py
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import sys
sys.path.insert(0, '.')

from sqlalchemy import delete
from database import async_session, engine, Base
from models import Competitor, MenuItem, PriceHistory, Alert


# Austin-area burger competitors (realistic data)
DEMO_COMPETITORS = [
    {
        "name": "P. Terry's Burger Stand",
        "location": "Austin, TX - South Lamar",
        "concept_type": "Burger",
        "doordash_url": "https://www.doordash.com/store/p-terry's-burger-stand-austin-24284/",
    },
    {
        "name": "Hopdoddy Burger Bar",
        "location": "Austin, TX - South Congress",
        "concept_type": "Burger",
        "doordash_url": "https://www.doordash.com/store/hopdoddy-burger-bar-austin-48839/",
    },
    {
        "name": "Hat Creek Burger Company",
        "location": "Austin, TX - Anderson Lane",
        "concept_type": "Burger",
        "doordash_url": "https://www.doordash.com/store/hat-creek-burger-company-austin-267398/",
    },
    {
        "name": "Shake Shack",
        "location": "Austin, TX - Domain",
        "concept_type": "Burger",
        "doordash_url": "https://www.doordash.com/store/shake-shack-austin-519889/",
    },
    {
        "name": "Five Guys",
        "location": "Austin, TX - Guadalupe",
        "concept_type": "Burger",
        "doordash_url": "https://www.doordash.com/store/five-guys-austin-23556/",
    },
]

# Menu items with base prices (will vary by competitor)
MENU_TEMPLATES = {
    "Burgers": [
        {"name": "Classic Cheeseburger", "base_price": 9.99, "description": "Quarter-pound beef patty with American cheese, lettuce, tomato, onion"},
        {"name": "Bacon Burger", "base_price": 11.99, "description": "Crispy bacon, cheddar cheese, special sauce"},
        {"name": "Mushroom Swiss Burger", "base_price": 12.49, "description": "Sautéed mushrooms, Swiss cheese, garlic aioli"},
        {"name": "Double Meat Burger", "base_price": 13.99, "description": "Two beef patties, double cheese"},
        {"name": "Veggie Burger", "base_price": 10.99, "description": "Plant-based patty with avocado"},
        {"name": "Jalapeño Burger", "base_price": 11.49, "description": "Pepper jack cheese, jalapeños, chipotle mayo"},
    ],
    "Chicken": [
        {"name": "Crispy Chicken Sandwich", "base_price": 10.99, "description": "Breaded chicken breast, pickles, mayo"},
        {"name": "Grilled Chicken Sandwich", "base_price": 11.49, "description": "Grilled chicken, lettuce, tomato, honey mustard"},
    ],
    "Sides": [
        {"name": "French Fries", "base_price": 3.99, "description": "Crispy golden fries with sea salt"},
        {"name": "Onion Rings", "base_price": 4.99, "description": "Beer-battered onion rings"},
        {"name": "Sweet Potato Fries", "base_price": 4.49, "description": "Crispy sweet potato fries"},
        {"name": "Side Salad", "base_price": 4.99, "description": "Mixed greens, tomato, cucumber"},
    ],
    "Drinks": [
        {"name": "Soft Drink", "base_price": 2.49, "description": "Coke, Sprite, Dr Pepper, Lemonade"},
        {"name": "Milkshake", "base_price": 5.99, "description": "Vanilla, Chocolate, or Strawberry"},
        {"name": "Iced Tea", "base_price": 2.29, "description": "Fresh brewed sweet or unsweet"},
    ],
    "Desserts": [
        {"name": "Brownie", "base_price": 3.99, "description": "Warm chocolate brownie"},
        {"name": "Cookies (3)", "base_price": 2.99, "description": "Fresh baked chocolate chip cookies"},
    ],
}


def get_price_with_variation(base_price: float, competitor_tier: str) -> Decimal:
    """Apply competitor-specific pricing tier and random variation."""
    # Competitor pricing tiers
    tier_multipliers = {
        "premium": 1.25,    # Hopdoddy, Shake Shack
        "mid": 1.0,         # Hat Creek
        "value": 0.85,      # P. Terry's, Five Guys
    }

    multiplier = tier_multipliers.get(competitor_tier, 1.0)
    variation = random.uniform(0.95, 1.05)  # +/- 5% random

    final_price = base_price * multiplier * variation
    return Decimal(str(round(final_price, 2)))


def get_competitor_tier(name: str) -> str:
    """Assign pricing tier based on competitor."""
    if "Hopdoddy" in name or "Shake Shack" in name:
        return "premium"
    elif "P. Terry" in name or "Five Guys" in name:
        return "value"
    return "mid"


async def clear_existing_data(db):
    """Clear all existing demo data."""
    print("Clearing existing data...")
    await db.execute(delete(Alert))
    await db.execute(delete(PriceHistory))
    await db.execute(delete(MenuItem))
    await db.execute(delete(Competitor))
    await db.commit()
    print("✓ Existing data cleared")


async def create_competitors(db) -> list[Competitor]:
    """Create demo competitors."""
    print("\nCreating competitors...")
    competitors = []

    for comp_data in DEMO_COMPETITORS:
        competitor = Competitor(
            id=str(uuid4()),
            name=comp_data["name"],
            location=comp_data["location"],
            concept_type=comp_data["concept_type"],
            doordash_url=comp_data["doordash_url"],
            scraping_enabled=True,
            last_scraped_at=datetime.now(timezone.utc),
        )
        db.add(competitor)
        competitors.append(competitor)
        print(f"  + {competitor.name}")

    await db.commit()
    print(f"✓ Created {len(competitors)} competitors")
    return competitors


async def create_menu_items_with_history(db, competitors: list[Competitor]):
    """Create menu items with 14 days of price history."""
    print("\nCreating menu items and price history...")

    total_items = 0
    total_history = 0
    alerts_created = 0

    for competitor in competitors:
        tier = get_competitor_tier(competitor.name)
        position = 0

        for category, items in MENU_TEMPLATES.items():
            for item_template in items:
                # Create menu item
                current_price = get_price_with_variation(item_template["base_price"], tier)

                menu_item = MenuItem(
                    id=str(uuid4()),
                    competitor_id=competitor.id,
                    platform="doordash",
                    name=item_template["name"],
                    category=category,
                    description=item_template["description"],
                    current_price=current_price,
                    is_available=True,
                    menu_position=position,
                )
                db.add(menu_item)
                await db.flush()  # Get the ID
                total_items += 1
                position += 1

                # Create 14 days of price history with realistic variations
                base_historical_price = float(current_price)

                for days_ago in range(14, -1, -1):
                    record_date = datetime.now(timezone.utc) - timedelta(days=days_ago)

                    # Simulate price changes
                    # - Tuesday discount for some competitors (Kiran mentioned patterns)
                    # - Gradual price increases
                    # - Random small variations

                    day_of_week = record_date.weekday()

                    if "P. Terry" in competitor.name and day_of_week == 1:  # Tuesday
                        # Tuesday special - 10% off
                        price_variation = 0.90
                    elif days_ago > 7:
                        # Older prices were slightly lower
                        price_variation = random.uniform(0.92, 0.98)
                    else:
                        # Recent prices closer to current
                        price_variation = random.uniform(0.97, 1.03)

                    historical_price = Decimal(str(round(base_historical_price * price_variation, 2)))

                    price_record = PriceHistory(
                        id=str(uuid4()),
                        menu_item_id=menu_item.id,
                        price=historical_price,
                        recorded_at=record_date,
                    )
                    db.add(price_record)
                    total_history += 1

                # Create alerts for significant recent price changes (last 3 days)
                if random.random() < 0.15:  # 15% chance of alert
                    change_pct = random.choice([-12, -8, -6, 6, 8, 10, 15])
                    old_price = float(current_price) / (1 + change_pct / 100)

                    alert = Alert(
                        id=str(uuid4()),
                        menu_item_id=menu_item.id,
                        alert_type="price_increase" if change_pct > 0 else "price_decrease",
                        old_value=f"${old_price:.2f}",
                        new_value=f"${current_price:.2f}",
                        change_percentage=Decimal(str(change_pct)),
                        is_acknowledged=random.random() < 0.3,  # 30% acknowledged
                        created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 3)),
                    )
                    db.add(alert)
                    alerts_created += 1

        print(f"  + {competitor.name}: {position} items")

    await db.commit()
    print(f"✓ Created {total_items} menu items")
    print(f"✓ Created {total_history} price history records")
    print(f"✓ Created {alerts_created} alerts")


async def main():
    """Main seed function."""
    print("=" * 50)
    print("FORKAST DEMO DATA SEEDER")
    print("=" * 50)

    async with async_session() as db:
        # Clear existing data
        await clear_existing_data(db)

        # Create competitors
        competitors = await create_competitors(db)

        # Create menu items with price history
        await create_menu_items_with_history(db, competitors)

    print("\n" + "=" * 50)
    print("✅ DEMO DATA SEEDED SUCCESSFULLY!")
    print("=" * 50)
    print("\nYour dashboard now has:")
    print("  • 5 Austin-area burger competitors")
    print("  • ~90 menu items with realistic pricing")
    print("  • 14 days of price history")
    print("  • Price change alerts")
    print("\nTry these insights in your demo:")
    print("  • P. Terry's has Tuesday discounts")
    print("  • Hopdoddy/Shake Shack are premium-priced")
    print("  • Check the price trends chart for patterns")


if __name__ == "__main__":
    asyncio.run(main())
