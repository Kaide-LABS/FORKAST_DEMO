"""
Competitors API router.

Provides CRUD endpoints for managing competitor tracking.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Competitor, MenuItem
from schemas import (
    CompetitorCreate,
    CompetitorRead,
    CompetitorUpdate,
    MenuItemRead,
    MenuItemSimple,
)

router = APIRouter(prefix="/competitors", tags=["competitors"])

# Type alias for dependency injection
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[CompetitorRead])
async def list_competitors(
    db: DB,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Competitor]:
    """
    List all tracked competitors.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        active_only: If True, only return competitors with scraping_enabled=True
    """
    stmt = select(Competitor)

    if active_only:
        stmt = stmt.where(Competitor.scraping_enabled == True)  # noqa: E712

    stmt = stmt.offset(skip).limit(limit).order_by(Competitor.name)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/with-stats/all")
async def list_competitors_with_stats(
    db: DB,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """
    List all competitors with their item counts.
    """
    # Get competitors
    stmt = select(Competitor).offset(skip).limit(limit).order_by(Competitor.name)
    result = await db.execute(stmt)
    competitors = list(result.scalars().all())

    # Get item counts for all competitors in one query
    count_stmt = select(
        MenuItem.competitor_id,
        func.count(MenuItem.id).label("items_count")
    ).group_by(MenuItem.competitor_id)
    count_result = await db.execute(count_stmt)
    counts = {row.competitor_id: row.items_count for row in count_result.all()}

    # Combine data
    return [
        {
            "id": c.id,
            "name": c.name,
            "location": c.location,
            "concept_type": c.concept_type,
            "doordash_url": c.doordash_url,
            "ubereats_url": c.ubereats_url,
            "scraping_enabled": c.scraping_enabled,
            "last_scraped_at": c.last_scraped_at,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "items_count": counts.get(c.id, 0),
        }
        for c in competitors
    ]


@router.get("/{competitor_id}", response_model=CompetitorRead)
async def get_competitor(
    competitor_id: str,
    db: DB,
) -> Competitor:
    """
    Get a single competitor by ID.
    """
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )
    return competitor


@router.post("/", response_model=CompetitorRead, status_code=status.HTTP_201_CREATED)
async def create_competitor(
    competitor_data: CompetitorCreate,
    db: DB,
) -> Competitor:
    """
    Create a new competitor to track.
    """
    competitor = Competitor(**competitor_data.model_dump())
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.put("/{competitor_id}", response_model=CompetitorRead)
async def update_competitor(
    competitor_id: str,
    competitor_data: CompetitorUpdate,
    db: DB,
) -> Competitor:
    """
    Update an existing competitor.
    """
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

    # Update only provided fields
    update_data = competitor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competitor, field, value)

    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    competitor_id: str,
    db: DB,
) -> None:
    """
    Delete a competitor (and all associated menu items).
    """
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

    await db.delete(competitor)
    await db.commit()


@router.get("/{competitor_id}/menu", response_model=list[MenuItemSimple])
async def get_competitor_menu(
    competitor_id: str,
    db: DB,
) -> list[MenuItem]:
    """
    Get all menu items for a competitor.

    Args:
        competitor_id: UUID of the competitor
    """
    # Verify competitor exists
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

    stmt = select(MenuItem).where(MenuItem.competitor_id == competitor_id)
    stmt = stmt.order_by(MenuItem.category, MenuItem.menu_position)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{competitor_id}/stats")
async def get_competitor_stats(
    competitor_id: str,
    db: DB,
) -> dict:
    """
    Get statistics for a competitor (item count, avg price, etc.).
    """
    # Verify competitor exists
    competitor = await db.get(Competitor, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with id {competitor_id} not found",
        )

    # Get item count and average price
    stmt = select(
        func.count(MenuItem.id).label("item_count"),
        func.avg(MenuItem.current_price).label("avg_price"),
    ).where(MenuItem.competitor_id == competitor_id)

    result = await db.execute(stmt)
    row = result.one()

    # Get category breakdown
    category_stmt = select(
        MenuItem.category,
        func.count(MenuItem.id).label("count"),
        func.avg(MenuItem.current_price).label("avg_price"),
    ).where(
        MenuItem.competitor_id == competitor_id
    ).group_by(MenuItem.category)

    category_result = await db.execute(category_stmt)
    categories = [
        {
            "category": r.category or "Uncategorized",
            "count": r.count,
            "avg_price": float(r.avg_price) if r.avg_price else 0,
        }
        for r in category_result.all()
    ]

    return {
        "competitor_id": competitor_id,
        "competitor_name": competitor.name,
        "item_count": row.item_count or 0,
        "avg_price": float(row.avg_price) if row.avg_price else 0,
        "last_scraped_at": competitor.last_scraped_at,
        "categories": categories,
    }
