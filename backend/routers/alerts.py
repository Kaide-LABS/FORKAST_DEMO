"""
Alerts API router.

Provides endpoints for managing price change alerts.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from models import Alert, MenuItem, Competitor, PriceHistory
from schemas import (
    AlertRead,
    AlertWithItem,
    AlertAcknowledge,
    AlertsResponse,
)
from tenant import get_tenant_id

router = APIRouter(prefix="/alerts", tags=["alerts"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=AlertsResponse)
async def list_alerts(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
    unacknowledged_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> AlertsResponse:
    """
    List all alerts, optionally filtered by acknowledgment status.

    Args:
        unacknowledged_only: If True, only return unacknowledged alerts
        limit: Maximum number of alerts to return
        offset: Number of alerts to skip (for pagination)
    """
    # Build base query with joins for item and competitor info (filtered by tenant)
    stmt = (
        select(Alert, MenuItem.name.label("item_name"), Competitor.name.label("competitor_name"))
        .join(MenuItem, Alert.menu_item_id == MenuItem.id)
        .join(Competitor, MenuItem.competitor_id == Competitor.id)
        .where(Competitor.tenant_id == tenant_id)
    )

    if unacknowledged_only:
        stmt = stmt.where(Alert.is_acknowledged == False)  # noqa: E712

    stmt = stmt.order_by(Alert.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    alerts_data = result.all()

    # Build response with item details
    alerts = [
        AlertWithItem(
            id=alert.id,
            menu_item_id=alert.menu_item_id,
            alert_type=alert.alert_type,
            old_value=alert.old_value,
            new_value=alert.new_value,
            change_percentage=alert.change_percentage,
            is_acknowledged=alert.is_acknowledged,
            created_at=alert.created_at,
            item_name=item_name,
            competitor_name=competitor_name,
        )
        for alert, item_name, competitor_name in alerts_data
    ]

    # Get counts (filtered by tenant)
    unack_count_stmt = select(func.count(Alert.id)).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Alert.is_acknowledged == False,  # noqa: E712
        Competitor.tenant_id == tenant_id,
    )
    unack_result = await db.execute(unack_count_stmt)
    unacknowledged_count = unack_result.scalar() or 0

    total_count_stmt = select(func.count(Alert.id)).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(Competitor.tenant_id == tenant_id)
    total_result = await db.execute(total_count_stmt)
    total_count = total_result.scalar() or 0

    return AlertsResponse(
        alerts=alerts,
        unacknowledged_count=unacknowledged_count,
        total_count=total_count,
    )


@router.get("/recent")
async def get_recent_alerts(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
    days: int = 7,
) -> list[AlertWithItem]:
    """
    Get alerts from the last N days.

    This also includes price changes detected in PriceHistory
    that exceed the 5% threshold.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get alerts from Alert table (filtered by tenant)
    alerts_stmt = (
        select(Alert, MenuItem.name.label("item_name"), Competitor.name.label("competitor_name"))
        .join(MenuItem, Alert.menu_item_id == MenuItem.id)
        .join(Competitor, MenuItem.competitor_id == Competitor.id)
        .where(
            Alert.created_at >= cutoff_date,
            Competitor.tenant_id == tenant_id,
        )
        .order_by(Alert.created_at.desc())
        .limit(100)
    )

    result = await db.execute(alerts_stmt)
    alerts_data = result.all()

    alerts = [
        AlertWithItem(
            id=alert.id,
            menu_item_id=alert.menu_item_id,
            alert_type=alert.alert_type,
            old_value=alert.old_value,
            new_value=alert.new_value,
            change_percentage=alert.change_percentage,
            is_acknowledged=alert.is_acknowledged,
            created_at=alert.created_at,
            item_name=item_name,
            competitor_name=competitor_name,
        )
        for alert, item_name, competitor_name in alerts_data
    ]

    return alerts


@router.get("/stats")
async def get_alert_stats(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Get alert statistics.
    """
    # Count by type (filtered by tenant)
    type_counts_stmt = select(
        Alert.alert_type,
        func.count(Alert.id).label("count"),
    ).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(Competitor.tenant_id == tenant_id).group_by(Alert.alert_type)

    type_result = await db.execute(type_counts_stmt)
    type_counts = {row.alert_type: row.count for row in type_result.all()}

    # Count unacknowledged (filtered by tenant)
    unack_stmt = select(func.count(Alert.id)).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Alert.is_acknowledged == False,  # noqa: E712
        Competitor.tenant_id == tenant_id,
    )
    unack_result = await db.execute(unack_stmt)
    unacknowledged = unack_result.scalar() or 0

    # Count total (filtered by tenant)
    total_stmt = select(func.count(Alert.id)).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(Competitor.tenant_id == tenant_id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    # Recent alerts (last 7 days, filtered by tenant)
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_stmt = select(func.count(Alert.id)).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Alert.created_at >= recent_cutoff,
        Competitor.tenant_id == tenant_id,
    )
    recent_result = await db.execute(recent_stmt)
    recent = recent_result.scalar() or 0

    return {
        "total_alerts": total,
        "unacknowledged": unacknowledged,
        "recent_7_days": recent,
        "by_type": type_counts,
    }


@router.get("/{alert_id}", response_model=AlertWithItem)
async def get_alert(
    alert_id: str,
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> AlertWithItem:
    """
    Get a single alert by ID.
    """
    stmt = (
        select(Alert, MenuItem.name.label("item_name"), Competitor.name.label("competitor_name"))
        .join(MenuItem, Alert.menu_item_id == MenuItem.id)
        .join(Competitor, MenuItem.competitor_id == Competitor.id)
        .where(
            Alert.id == alert_id,
            Competitor.tenant_id == tenant_id,
        )
    )

    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found",
        )

    alert, item_name, competitor_name = row

    return AlertWithItem(
        id=alert.id,
        menu_item_id=alert.menu_item_id,
        alert_type=alert.alert_type,
        old_value=alert.old_value,
        new_value=alert.new_value,
        change_percentage=alert.change_percentage,
        is_acknowledged=alert.is_acknowledged,
        created_at=alert.created_at,
        item_name=item_name,
        competitor_name=competitor_name,
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
async def acknowledge_alert(
    alert_id: str,
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> Alert:
    """
    Mark an alert as acknowledged.
    """
    # Verify alert belongs to tenant
    stmt = select(Alert).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Alert.id == alert_id,
        Competitor.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found",
        )

    alert.is_acknowledged = True
    await db.commit()
    await db.refresh(alert)

    return alert


@router.post("/acknowledge-all")
async def acknowledge_all_alerts(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Mark all unacknowledged alerts as acknowledged.
    """
    # Get all unacknowledged alerts (filtered by tenant)
    stmt = select(Alert).join(
        MenuItem, Alert.menu_item_id == MenuItem.id
    ).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Alert.is_acknowledged == False,  # noqa: E712
        Competitor.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    count = 0
    for alert in alerts:
        alert.is_acknowledged = True
        count += 1

    await db.commit()

    return {"acknowledged_count": count}


@router.get("/price-changes/significant")
async def get_significant_price_changes(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
    days: int = 7,
    threshold: float = 5.0,
) -> list[dict]:
    """
    Get significant price changes from PriceHistory.

    This queries the PriceHistory table directly for changes
    exceeding the specified threshold percentage.

    Args:
        days: Number of days to look back
        threshold: Minimum percentage change to include
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    threshold_decimal = Decimal(str(threshold))

    stmt = (
        select(
            PriceHistory,
            MenuItem.name.label("item_name"),
            Competitor.name.label("competitor_name"),
        )
        .join(MenuItem, PriceHistory.menu_item_id == MenuItem.id)
        .join(Competitor, MenuItem.competitor_id == Competitor.id)
        .where(
            and_(
                PriceHistory.recorded_at >= cutoff_date,
                PriceHistory.change_percentage.isnot(None),
                func.abs(PriceHistory.change_percentage) >= threshold_decimal,
                Competitor.tenant_id == tenant_id,
            )
        )
        .order_by(PriceHistory.recorded_at.desc())
        .limit(100)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": ph.id,
            "menu_item_id": ph.menu_item_id,
            "item_name": item_name,
            "competitor_name": competitor_name,
            "price": float(ph.price),
            "change_percentage": float(ph.change_percentage) if ph.change_percentage else None,
            "recorded_at": ph.recorded_at.isoformat(),
        }
        for ph, item_name, competitor_name in rows
    ]
