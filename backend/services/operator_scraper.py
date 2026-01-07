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
from services.scrape_status import scrape_tracker, ScrapeState

# Timeout for scraping operations (in seconds)
SCRAPE_TIMEOUT = 180  # 3 minutes


async def scrape_operator_menu_task(
    operator_id: str,
    url: str,
    platform: str,
    job_id: str,
) -> None:
    """
    Background task to scrape operator's menu.

    Args:
        operator_id: ID of the operator profile
        url: URL to scrape
        platform: Platform name (ubereats or doordash)
        job_id: ID of the scrape job for status tracking
    """
    print(f"Starting operator menu scrape: {platform} - {url}")

    # Update status to running
    await scrape_tracker.update_state(job_id, ScrapeState.RUNNING)

    scraper = None
    try:
        # Initialize scraper based on platform
        if platform == "ubereats":
            scraper = UberEatsScraper()

            # Run scrape with timeout
            try:
                result = await asyncio.wait_for(
                    scraper.scrape(url),
                    timeout=SCRAPE_TIMEOUT
                )
            except asyncio.TimeoutError:
                print(f"Operator scrape timed out after {SCRAPE_TIMEOUT}s")
                await scrape_tracker.update_state(
                    job_id,
                    ScrapeState.TIMEOUT,
                    error_message=f"Scraping timed out after {SCRAPE_TIMEOUT} seconds. The restaurant page may be too large or slow to load."
                )
                return
        else:
            # DoorDash scraping
            print(f"DoorDash scraping not yet implemented")
            await scrape_tracker.update_state(
                job_id,
                ScrapeState.FAILED,
                error_message="DoorDash scraping is not yet implemented. Please use Uber Eats URL."
            )
            return

        if not result.success:
            print(f"Operator scrape failed: {result.error_message}")
            await scrape_tracker.update_state(
                job_id,
                ScrapeState.FAILED,
                error_message=result.error_message or "Failed to scrape menu items"
            )
            return

        if not result.items:
            print("No menu items found")
            await scrape_tracker.update_state(
                job_id,
                ScrapeState.FAILED,
                error_message="No menu items found on the page. Please check the URL is correct."
            )
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

        # Update status to success
        await scrape_tracker.update_state(
            job_id,
            ScrapeState.SUCCESS,
            items_scraped=len(result.items)
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Error scraping operator menu: {error_msg}")
        import traceback
        traceback.print_exc()

        # Provide user-friendly error messages
        if "timeout" in error_msg.lower():
            friendly_msg = "The page took too long to load. Please try again."
        elif "net::" in error_msg.lower():
            friendly_msg = "Could not connect to the website. Please check your URL."
        elif "browser" in error_msg.lower():
            friendly_msg = "Browser error occurred. Please try again later."
        else:
            friendly_msg = f"Scraping failed: {error_msg[:100]}"

        await scrape_tracker.update_state(
            job_id,
            ScrapeState.FAILED,
            error_message=friendly_msg
        )

    finally:
        if scraper:
            try:
                await scraper.close()
            except Exception:
                pass
