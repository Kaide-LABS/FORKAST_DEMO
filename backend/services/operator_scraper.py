"""
Operator menu scraper service.

Handles background scraping of the operator's own restaurant menu.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import OperatorProfile, OperatorMenuItem
from scraper.ubereats_scraper import UberEatsScraper


async def scrape_operator_menu_task(
    operator_id: str,
    url: str,
    platform: str,
) -> None:
    """
    Background task to scrape operator's menu.

    Args:
        operator_id: ID of the operator profile
        url: URL to scrape
        platform: Platform name (ubereats or doordash)
    """
    print(f"Starting operator menu scrape: {platform} - {url}")

    scraper = None
    try:
        # Initialize scraper based on platform
        if platform == "ubereats":
            scraper = UberEatsScraper()
            result = await scraper.scrape(url)
        else:
            # TODO: Add DoorDash scraper support
            print(f"DoorDash scraping not yet implemented")
            return

        if not result.success:
            print(f"Operator scrape failed: {result.error_message}")
            return

        print(f"Scraped {len(result.items)} items from operator menu")

        # Save to database
        async with async_session() as session:
            # Clear existing menu items for this operator
            delete_stmt = delete(OperatorMenuItem).where(
                OperatorMenuItem.operator_id == operator_id
            )
            await session.execute(delete_stmt)

            # Add new items
            for scraped_item in result.items:
                menu_item = OperatorMenuItem(
                    operator_id=operator_id,
                    platform=platform,
                    name=scraped_item.name,
                    category=scraped_item.category,
                    description=scraped_item.description,
                    current_price=scraped_item.price,
                    is_available=scraped_item.is_available,
                    menu_position=scraped_item.position,
                )
                session.add(menu_item)

            # Update operator's last_scraped_at
            profile_stmt = select(OperatorProfile).where(
                OperatorProfile.id == operator_id
            )
            profile_result = await session.execute(profile_stmt)
            profile = profile_result.scalar_one_or_none()

            if profile:
                profile.last_scraped_at = datetime.now(timezone.utc)

            await session.commit()
            print(f"Saved {len(result.items)} operator menu items to database")

    except Exception as e:
        print(f"Error scraping operator menu: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if scraper:
            await scraper.close()
