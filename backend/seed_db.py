#!/usr/bin/env python3
"""
Database seeding script for the Competitive Intelligence Dashboard.

Populates the database with sample competitors and menu items
for testing and demonstration purposes.

Run with: python seed_db.py
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random


def utc_now() -> datetime:
    """Return current UTC datetime with timezone information."""
    return datetime.now(timezone.utc)

from database import async_session, init_db
from models import Competitor, MenuItem, PriceHistory, Alert


# Sample data for seeding
COMPETITORS_DATA = [
    {
        "name": "Burger King",
        "location": "123 Main St, Austin, TX 78701",
        "concept_type": "burger",
        "doordash_url": "https://www.doordash.com/store/burger-king-austin-12345/",
        "ubereats_url": "https://www.ubereats.com/store/burger-king-austin/",
        "items": [
            {"name": "Whopper", "category": "Burgers", "price": "7.99", "description": "Flame-grilled beef patty with tomatoes, lettuce, mayo, pickles, and onions on a sesame seed bun"},
            {"name": "Whopper Jr.", "category": "Burgers", "price": "4.99", "description": "A smaller version of the iconic Whopper"},
            {"name": "Bacon King", "category": "Burgers", "price": "9.49", "description": "Two flame-grilled beef patties with bacon, cheese, and savory sauce"},
            {"name": "Chicken Fries", "category": "Sides", "price": "3.99", "description": "Crispy chicken strips shaped like fries"},
            {"name": "Onion Rings", "category": "Sides", "price": "2.99", "description": "Crispy breaded onion rings"},
            {"name": "Large Fries", "category": "Sides", "price": "3.49", "description": "Thick-cut golden french fries"},
        ]
    },
    {
        "name": "McDonald's",
        "location": "456 Congress Ave, Austin, TX 78701",
        "concept_type": "burger",
        "doordash_url": "https://www.doordash.com/store/mcdonalds-austin-67890/",
        "ubereats_url": "https://www.ubereats.com/store/mcdonalds-austin/",
        "items": [
            {"name": "Big Mac", "category": "Burgers", "price": "6.99", "description": "Two all-beef patties, special sauce, lettuce, cheese, pickles, onions on a sesame seed bun"},
            {"name": "Quarter Pounder", "category": "Burgers", "price": "7.49", "description": "Quarter pound beef patty with cheese, onions, pickles, and condiments"},
            {"name": "McChicken", "category": "Chicken", "price": "4.49", "description": "Crispy chicken patty with lettuce and mayo"},
            {"name": "10pc McNuggets", "category": "Chicken", "price": "5.99", "description": "10 piece Chicken McNuggets"},
            {"name": "Large Fries", "category": "Sides", "price": "3.29", "description": "Golden crispy french fries"},
            {"name": "Apple Pie", "category": "Desserts", "price": "1.99", "description": "Warm apple pie with a flaky crust"},
        ]
    },
]


async def clear_database():
    """Clear all existing data from the database."""
    async with async_session() as session:
        # Delete in order due to foreign key constraints
        await session.execute(Alert.__table__.delete())
        await session.execute(PriceHistory.__table__.delete())
        await session.execute(MenuItem.__table__.delete())
        await session.execute(Competitor.__table__.delete())
        await session.commit()
        print("Database cleared.")


async def seed_competitors():
    """Seed the database with sample competitors and menu items."""
    async with async_session() as session:
        for comp_data in COMPETITORS_DATA:
            # Create competitor
            competitor = Competitor(
                name=comp_data["name"],
                location=comp_data["location"],
                concept_type=comp_data["concept_type"],
                doordash_url=comp_data["doordash_url"],
                ubereats_url=comp_data["ubereats_url"],
                scraping_enabled=True,
                last_scraped_at=utc_now() - timedelta(hours=random.randint(1, 24)),
            )
            session.add(competitor)
            await session.flush()  # Get the competitor ID

            print(f"Created competitor: {competitor.name} (ID: {competitor.id})")

            # Create menu items for this competitor
            for i, item_data in enumerate(comp_data["items"]):
                menu_item = MenuItem(
                    competitor_id=competitor.id,
                    platform="doordash",
                    name=item_data["name"],
                    category=item_data["category"],
                    description=item_data["description"],
                    current_price=Decimal(item_data["price"]),
                    is_available=True,
                    menu_position=i + 1,
                )
                session.add(menu_item)
                await session.flush()

                # Create price history entries (last 7 days)
                await create_price_history(session, menu_item)

                print(f"  - Created item: {menu_item.name} (${menu_item.current_price})")

        await session.commit()
        print("\nSeeding complete!")


async def create_price_history(session, menu_item: MenuItem):
    """Create historical price entries for a menu item."""
    current_price = menu_item.current_price
    base_time = utc_now()

    # Create 7 days of price history
    for day in range(7, 0, -1):
        # Add some price variation
        variation = Decimal(str(random.uniform(-0.5, 0.5)))
        historical_price = max(current_price + variation, Decimal("0.99"))

        # Occasionally add a bigger price change (simulates a real change)
        if random.random() < 0.2:  # 20% chance
            change_direction = random.choice([-1, 1])
            historical_price = current_price + (current_price * Decimal(str(change_direction * random.uniform(0.05, 0.15))))

        record_time = base_time - timedelta(days=day, hours=random.randint(0, 12))

        # Calculate change percentage from previous day (simplified)
        change_pct = None
        if day < 7:
            prev_price = current_price  # Simplified
            if prev_price > 0:
                change_pct = ((historical_price - prev_price) / prev_price) * 100

        price_history = PriceHistory(
            menu_item_id=menu_item.id,
            price=round(historical_price, 2),
            recorded_at=record_time,
            change_percentage=round(change_pct, 2) if change_pct else None,
        )
        session.add(price_history)

        # Create alert for significant changes
        if change_pct and abs(change_pct) >= 5:
            alert = Alert(
                menu_item_id=menu_item.id,
                alert_type="price_increase" if change_pct > 0 else "price_decrease",
                old_value=f"${prev_price:.2f}",
                new_value=f"${historical_price:.2f}",
                change_percentage=round(change_pct, 2),
                is_acknowledged=random.random() < 0.3,  # 30% acknowledged
                created_at=record_time,
            )
            session.add(alert)

    # Add current price as most recent entry
    current_history = PriceHistory(
        menu_item_id=menu_item.id,
        price=current_price,
        recorded_at=base_time,
    )
    session.add(current_history)


async def add_sample_alerts():
    """Add some additional sample alerts for demonstration."""
    async with async_session() as session:
        # Get some menu items
        from sqlalchemy import select
        stmt = select(MenuItem).limit(5)
        result = await session.execute(stmt)
        items = result.scalars().all()

        for item in items[:3]:
            # Create a price change alert
            alert = Alert(
                menu_item_id=item.id,
                alert_type=random.choice(["price_increase", "price_decrease"]),
                old_value=f"${float(item.current_price) - 1:.2f}",
                new_value=f"${item.current_price:.2f}",
                change_percentage=Decimal(str(random.uniform(5, 15))),
                is_acknowledged=False,
                created_at=utc_now() - timedelta(hours=random.randint(1, 48)),
            )
            session.add(alert)
            print(f"Created alert for: {item.name}")

        await session.commit()


async def main():
    """Main entry point for the seeding script."""
    print("=" * 60)
    print("Competitive Intelligence Dashboard - Database Seeder")
    print("=" * 60)
    print()

    # Initialize database tables
    print("Initializing database...")
    await init_db()

    # Clear existing data
    print("\nClearing existing data...")
    await clear_database()

    # Seed new data
    print("\nSeeding competitors and menu items...")
    await seed_competitors()

    # Add extra sample alerts
    print("\nAdding sample alerts...")
    await add_sample_alerts()

    print("\n" + "=" * 60)
    print("Database seeding complete!")
    print("=" * 60)
    print("\nYou can now start the server and test the API:")
    print("  uvicorn main:app --reload")
    print("\nAPI endpoints:")
    print("  GET  /api/v1/competitors")
    print("  GET  /api/v1/dashboard/comparison")
    print("  GET  /api/v1/alerts")


if __name__ == "__main__":
    asyncio.run(main())
