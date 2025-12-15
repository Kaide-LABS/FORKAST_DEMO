import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import sessionmaker
from models import Base, Competitor, MenuItem
from decimal import Decimal

async def test_query():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Seed data
        c = Competitor(name="Test Comp", scraping_enabled=True)
        db.add(c)
        await db.commit()
        await db.refresh(c)
        
        m = MenuItem(competitor_id=c.id, name="Burger", platform="doordash", current_price=Decimal("10.00"))
        db.add(m)
        await db.commit()

        print("Running query...")
        try:
            competitors_stmt = select(
                Competitor.id,
                Competitor.name,
                Competitor.last_scraped_at,
                func.count(MenuItem.id).label("item_count"),
                func.avg(MenuItem.current_price).label("avg_price"),
            ).outerjoin(
                MenuItem, Competitor.id == MenuItem.competitor_id
            ).where(
                Competitor.scraping_enabled == True
            ).group_by(Competitor.id)

            result = await db.execute(competitors_stmt)
            rows = result.all()
            print(f"Got {len(rows)} rows")
            for row in rows:
                print(f"Row: {row}")
                print(f"Avg Price type: {type(row.avg_price)}")
                print(f"Avg Price value: {row.avg_price}")
                
        except Exception as e:
            print(f"QUERY FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())
