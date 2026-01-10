"""
Categories API router.

Provides endpoints for managing canonical categories and category mappings
for semantic price comparison across restaurants.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import (
    CanonicalCategory,
    CategoryMapping,
    Competitor,
    MenuItem,
    OperatorProfile,
    OperatorMenuItem,
)
from schemas import (
    CanonicalCategoryCreate,
    CanonicalCategoryRead,
    CategoryMappingCreate,
    CategoryMappingRead,
    CategoryMappingUpdate,
    CategorySuggestionRead,
    CategorySuggestionAlt,
    CategoryComparisonItem,
    CategoryComparisonResponse,
)
from services.category_ai import category_ai_service
from tenant import get_tenant_id

router = APIRouter(prefix="/categories", tags=["categories"])

DB = Annotated[AsyncSession, Depends(get_db)]


# Seed data for canonical categories
SEED_CATEGORIES = [
    ("Burgers", "Hamburgers, cheeseburgers, specialty burgers, beef", "burger,hamburger,cheeseburger,patty,beef,burgers"),
    ("Chicken", "Fried chicken, grilled chicken, wings, nuggets, tenders", "chicken,wings,nuggets,tenders,fried,poultry"),
    ("Sandwiches & Wraps", "Subs, wraps, paninis, hoagies", "sandwich,wrap,sub,panini,hoagie,deli,sandwiches,wraps"),
    ("Bowls & Salads", "Rice bowls, grain bowls, salads, poke", "bowl,salad,poke,grain,rice bowl,bowls,salads"),
    ("Vegan & Plant-Based", "Vegan, vegetarian, plant-based options", "vegan,vegetarian,plant-based,veggie,meatless,plant"),
    ("Sides", "Fries, onion rings, coleslaw, sides", "side,fries,onion rings,coleslaw,potato,sides"),
    ("Beverages", "Drinks, sodas, shakes, smoothies", "drink,beverage,soda,shake,smoothie,coffee,tea,drinks,beverages"),
    ("Desserts", "Ice cream, cookies, cakes, sweets", "dessert,ice cream,cookie,cake,sweet,pie,desserts"),
    ("Breakfast", "Morning items, eggs, pancakes, breakfast sandwiches", "breakfast,eggs,pancake,waffle,morning,brunch"),
    ("Combos & Meals", "Value meals, combo deals, family packs", "combo,meal,value,deal,family,bundle,meals,deals"),
    ("Appetizers", "Starters, shareables, apps", "appetizer,starter,shareable,app,snack,appetizers"),
    ("Pizza & Flatbreads", "Pizzas, flatbreads, calzones", "pizza,flatbread,calzone,slice,pizzas"),
    ("Seafood", "Fish, shrimp, seafood items", "seafood,fish,shrimp,crab,lobster,salmon"),
    ("Mexican", "Tacos, burritos, quesadillas, nachos", "taco,burrito,quesadilla,nacho,mexican,tex-mex,tacos,burritos"),
    ("Asian", "Noodles, rice dishes, stir-fry, Asian cuisine", "asian,noodle,rice,stir-fry,chinese,japanese,thai,noodles"),
]


# =============================================================================
# Canonical Categories Endpoints
# =============================================================================

@router.get("/canonical", response_model=list[CanonicalCategoryRead])
async def list_canonical_categories(db: DB) -> list[CanonicalCategory]:
    """List all canonical categories."""
    stmt = select(CanonicalCategory).order_by(CanonicalCategory.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/canonical", response_model=CanonicalCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_canonical_category(
    data: CanonicalCategoryCreate,
    db: DB
) -> CanonicalCategory:
    """Create a new canonical category."""
    # Check if name already exists
    existing_stmt = select(CanonicalCategory).where(
        CanonicalCategory.name == data.name
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{data.name}' already exists"
        )

    category = CanonicalCategory(
        name=data.name,
        description=data.description,
        keywords=data.keywords
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.post("/canonical/seed", response_model=list[CanonicalCategoryRead])
async def seed_canonical_categories(db: DB) -> list[CanonicalCategory]:
    """
    Seed the database with predefined canonical categories.
    Skips categories that already exist.
    """
    created = []

    for name, description, keywords in SEED_CATEGORIES:
        # Check if exists
        existing_stmt = select(CanonicalCategory).where(
            CanonicalCategory.name == name
        )
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            continue

        category = CanonicalCategory(
            name=name,
            description=description,
            keywords=keywords
        )
        db.add(category)
        created.append(category)

    if created:
        await db.commit()
        for cat in created:
            await db.refresh(cat)

    return created


@router.delete("/canonical/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canonical_category(category_id: str, db: DB) -> None:
    """Delete a canonical category (and all its mappings)."""
    stmt = select(CanonicalCategory).where(CanonicalCategory.id == category_id)
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    await db.delete(category)
    await db.commit()


# =============================================================================
# Category Mappings Endpoints
# =============================================================================

@router.get("/mappings", response_model=list[CategoryMappingRead])
async def list_mappings(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
    source_type: Optional[str] = Query(default=None, pattern="^(competitor|operator)$"),
    source_id: Optional[str] = Query(default=None),
) -> list[CategoryMapping]:
    """
    List category mappings with optional filters.

    Args:
        source_type: Filter by "competitor" or "operator"
        source_id: Filter by specific competitor or operator ID
    """
    stmt = select(CategoryMapping).options(
        selectinload(CategoryMapping.canonical_category)
    ).where(CategoryMapping.tenant_id == tenant_id)

    if source_type:
        stmt = stmt.where(CategoryMapping.source_type == source_type)
    if source_id:
        stmt = stmt.where(CategoryMapping.source_id == source_id)

    stmt = stmt.order_by(CategoryMapping.raw_category)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/mappings", response_model=CategoryMappingRead, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: CategoryMappingCreate,
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> CategoryMapping:
    """
    Create or update a category mapping.

    If a mapping already exists for the same source + raw_category, it will be updated.
    """
    # Verify canonical category exists
    canonical_stmt = select(CanonicalCategory).where(
        CanonicalCategory.id == data.canonical_category_id
    )
    canonical_result = await db.execute(canonical_stmt)
    if not canonical_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canonical category not found"
        )

    # Check for existing mapping (within this tenant)
    existing_stmt = select(CategoryMapping).where(
        CategoryMapping.source_type == data.source_type,
        CategoryMapping.source_id == data.source_id,
        CategoryMapping.raw_category == data.raw_category,
        CategoryMapping.tenant_id == tenant_id,
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.canonical_category_id = data.canonical_category_id
        existing.is_manual = data.is_manual
        existing.confidence_score = None if data.is_manual else existing.confidence_score
        await db.commit()
        await db.refresh(existing)

        # Load relationship
        stmt = select(CategoryMapping).options(
            selectinload(CategoryMapping.canonical_category)
        ).where(CategoryMapping.id == existing.id)
        result = await db.execute(stmt)
        return result.scalar_one()

    # Create new
    mapping = CategoryMapping(
        tenant_id=tenant_id,
        source_type=data.source_type,
        source_id=data.source_id,
        raw_category=data.raw_category,
        canonical_category_id=data.canonical_category_id,
        is_manual=data.is_manual,
        confidence_score=None
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    # Load relationship
    stmt = select(CategoryMapping).options(
        selectinload(CategoryMapping.canonical_category)
    ).where(CategoryMapping.id == mapping.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.put("/mappings/{mapping_id}", response_model=CategoryMappingRead)
async def update_mapping(
    mapping_id: str,
    data: CategoryMappingUpdate,
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> CategoryMapping:
    """Update an existing category mapping."""
    stmt = select(CategoryMapping).where(
        CategoryMapping.id == mapping_id,
        CategoryMapping.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    if data.canonical_category_id:
        # Verify new canonical category exists
        canonical_stmt = select(CanonicalCategory).where(
            CanonicalCategory.id == data.canonical_category_id
        )
        canonical_result = await db.execute(canonical_stmt)
        if not canonical_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canonical category not found"
            )
        mapping.canonical_category_id = data.canonical_category_id

    if data.is_manual is not None:
        mapping.is_manual = data.is_manual

    await db.commit()
    await db.refresh(mapping)

    # Load relationship
    stmt = select(CategoryMapping).options(
        selectinload(CategoryMapping.canonical_category)
    ).where(CategoryMapping.id == mapping.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: str,
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    """Delete a category mapping."""
    stmt = select(CategoryMapping).where(
        CategoryMapping.id == mapping_id,
        CategoryMapping.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    await db.delete(mapping)
    await db.commit()


# =============================================================================
# AI Suggestion Endpoints
# =============================================================================

@router.get("/suggest", response_model=list[CategorySuggestionRead])
async def suggest_mappings(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
    source_type: str = Query(..., pattern="^(competitor|operator)$"),
    source_id: str = Query(...),
) -> list[CategorySuggestionRead]:
    """
    Get AI-suggested mappings for unmapped categories.

    Returns suggestions with confidence scores for categories that don't have
    mappings yet for the specified source.
    """
    # Get raw categories from the source
    raw_categories: list[str] = []

    if source_type == "competitor":
        stmt = select(MenuItem.category).where(
            MenuItem.competitor_id == source_id,
            MenuItem.category.isnot(None)
        ).distinct()
        result = await db.execute(stmt)
        raw_categories = [r[0] for r in result.all() if r[0]]
    else:  # operator
        stmt = select(OperatorMenuItem.category).where(
            OperatorMenuItem.operator_id == source_id,
            OperatorMenuItem.category.isnot(None)
        ).distinct()
        result = await db.execute(stmt)
        raw_categories = [r[0] for r in result.all() if r[0]]

    if not raw_categories:
        return []

    # Get unmapped categories
    unmapped = await category_ai_service.get_unmapped_categories(
        db, source_type, source_id, raw_categories, tenant_id
    )

    if not unmapped:
        return []

    # Get AI suggestions
    suggestions = await category_ai_service.suggest_mappings(db, unmapped)

    # Convert to response schema
    return [
        CategorySuggestionRead(
            raw_category=s.raw_category,
            canonical_category_id=s.canonical_category_id,
            canonical_category_name=s.canonical_category_name,
            confidence_score=s.confidence_score,
            alternatives=[
                CategorySuggestionAlt(id=alt[0], name=alt[1], score=alt[2])
                for alt in s.alternatives
            ]
        )
        for s in suggestions
    ]


@router.post("/auto-map")
async def auto_map_categories(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
    source_type: str = Query(..., pattern="^(competitor|operator)$"),
    source_id: str = Query(...),
    threshold: float = Query(default=0.4, ge=0.3, le=1.0),
) -> dict:
    """
    Automatically map categories with high AI confidence.

    Only creates mappings where confidence >= threshold.
    """
    # Get raw categories from the source
    raw_categories: list[str] = []

    if source_type == "competitor":
        stmt = select(MenuItem.category).where(
            MenuItem.competitor_id == source_id,
            MenuItem.category.isnot(None)
        ).distinct()
        result = await db.execute(stmt)
        raw_categories = [r[0] for r in result.all() if r[0]]
    else:  # operator
        stmt = select(OperatorMenuItem.category).where(
            OperatorMenuItem.operator_id == source_id,
            OperatorMenuItem.category.isnot(None)
        ).distinct()
        result = await db.execute(stmt)
        raw_categories = [r[0] for r in result.all() if r[0]]

    if not raw_categories:
        return {"mapped": 0, "skipped": len(raw_categories)}

    # Get unmapped categories
    unmapped = await category_ai_service.get_unmapped_categories(
        db, source_type, source_id, raw_categories, tenant_id
    )

    if not unmapped:
        return {"mapped": 0, "skipped": 0, "message": "All categories already mapped"}

    # Auto-map
    created = await category_ai_service.auto_map_categories(
        db, source_type, source_id, unmapped, threshold, tenant_id
    )

    return {
        "mapped": len(created),
        "skipped": len(unmapped) - len(created),
        "threshold": threshold
    }


# =============================================================================
# Semantic Comparison Endpoint
# =============================================================================

@router.get("/comparison", response_model=CategoryComparisonResponse)
async def get_category_comparison(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> CategoryComparisonResponse:
    """
    Get semantic category comparison between operator and market.

    Uses canonical categories to group items semantically across different
    restaurants' category naming conventions.
    """
    # Get operator profile (filtered by tenant)
    op_stmt = select(OperatorProfile).where(
        OperatorProfile.tenant_id == tenant_id
    ).limit(1)
    op_result = await db.execute(op_stmt)
    operator = op_result.scalar_one_or_none()

    if not operator:
        return CategoryComparisonResponse(
            comparisons=[],
            unmapped_operator_categories=[],
            unmapped_competitor_categories=[]
        )

    # Get all canonical categories
    canonical_stmt = select(CanonicalCategory)
    canonical_result = await db.execute(canonical_stmt)
    canonical_categories = {c.id: c for c in canonical_result.scalars().all()}

    # Get operator category mappings
    op_mappings_stmt = select(CategoryMapping).where(
        CategoryMapping.source_type == "operator",
        CategoryMapping.source_id == operator.id
    )
    op_mappings_result = await db.execute(op_mappings_stmt)
    op_mappings = {m.raw_category: m.canonical_category_id for m in op_mappings_result.scalars().all()}

    # Get competitor category mappings (filtered by tenant)
    comp_mappings_stmt = select(CategoryMapping).where(
        CategoryMapping.source_type == "competitor",
        CategoryMapping.tenant_id == tenant_id,
    )
    comp_mappings_result = await db.execute(comp_mappings_stmt)
    comp_mappings_raw = comp_mappings_result.scalars().all()

    # Build competitor mappings dict: raw_category -> canonical_id (per competitor)
    comp_mappings: dict[str, dict[str, str]] = defaultdict(dict)
    for m in comp_mappings_raw:
        comp_mappings[m.source_id][m.raw_category] = m.canonical_category_id

    # Get operator items grouped by canonical category
    op_items_stmt = select(OperatorMenuItem).where(
        OperatorMenuItem.operator_id == operator.id
    )
    op_items_result = await db.execute(op_items_stmt)
    op_items = op_items_result.scalars().all()

    # Group operator items by canonical category
    op_by_canonical: dict[str, list[Decimal]] = defaultdict(list)
    unmapped_op_categories = set()

    for item in op_items:
        if item.category and item.category in op_mappings:
            canonical_id = op_mappings[item.category]
            op_by_canonical[canonical_id].append(item.current_price)
        elif item.category:
            unmapped_op_categories.add(item.category)

    # Get competitor items grouped by canonical category (filtered by tenant)
    comp_items_stmt = select(MenuItem, Competitor.id.label("comp_id")).join(
        Competitor, MenuItem.competitor_id == Competitor.id
    ).where(
        Competitor.scraping_enabled == True,  # noqa: E712
        Competitor.tenant_id == tenant_id,
    )
    comp_items_result = await db.execute(comp_items_stmt)
    comp_items = comp_items_result.all()

    # Group competitor items by canonical category
    market_by_canonical: dict[str, list[Decimal]] = defaultdict(list)
    unmapped_comp_categories = set()

    for item, comp_id in comp_items:
        if item.category:
            comp_mapping = comp_mappings.get(comp_id, {})
            if item.category in comp_mapping:
                canonical_id = comp_mapping[item.category]
                market_by_canonical[canonical_id].append(item.current_price)
            else:
                unmapped_comp_categories.add(item.category)

    # Build comparison response
    comparisons = []

    for canonical_id, canonical in canonical_categories.items():
        op_prices = op_by_canonical.get(canonical_id, [])
        market_prices = market_by_canonical.get(canonical_id, [])

        if not op_prices and not market_prices:
            continue

        op_avg = sum(op_prices) / len(op_prices) if op_prices else None
        market_avg = sum(market_prices) / len(market_prices) if market_prices else None

        delta_pct = None
        if op_avg is not None and market_avg is not None and market_avg > 0:
            delta_pct = ((op_avg - market_avg) / market_avg) * 100

        comparisons.append(CategoryComparisonItem(
            canonical_category_id=canonical_id,
            canonical_category_name=canonical.name,
            operator_avg=Decimal(str(round(op_avg, 2))) if op_avg else None,
            operator_items=len(op_prices),
            market_avg=Decimal(str(round(market_avg, 2))) if market_avg else None,
            market_items=len(market_prices),
            delta_pct=Decimal(str(round(delta_pct, 2))) if delta_pct else None
        ))

    # Sort by operator items count (most items first)
    comparisons.sort(key=lambda x: x.operator_items, reverse=True)

    return CategoryComparisonResponse(
        comparisons=comparisons,
        unmapped_operator_categories=sorted(unmapped_op_categories),
        unmapped_competitor_categories=sorted(unmapped_comp_categories)
    )


# =============================================================================
# AI Insights Endpoint
# =============================================================================

@router.get("/insights")
async def get_ai_insights(
    db: DB,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Get AI-generated pricing insights based on category comparison data.

    Uses Gemini to analyze the comparison data and generate actionable recommendations.
    """
    import os

    # Get comparison data first
    comparison = await get_category_comparison(db, tenant_id)

    if not comparison.comparisons:
        return {
            "insights": [],
            "summary": "No comparison data available. Please map your menu categories first."
        }

    # Build context for AI
    insights_data = []
    for comp in comparison.comparisons:
        if comp.operator_avg is not None and comp.market_avg is not None:
            insights_data.append({
                "category": comp.canonical_category_name,
                "your_avg": float(comp.operator_avg),
                "market_avg": float(comp.market_avg),
                "delta_pct": float(comp.delta_pct) if comp.delta_pct else 0,
                "your_items": comp.operator_items,
                "market_items": comp.market_items
            })

    if not insights_data:
        return {
            "insights": [],
            "summary": "Need more data for AI analysis. Map competitor categories to enable insights."
        }

    # Try to generate AI insights
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback to rule-based insights
            return generate_rule_based_insights(insights_data)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are a restaurant pricing consultant. Analyze this category pricing data and provide 3-4 specific, actionable insights.

Data (your prices vs market average):
{insights_data}

Rules:
- Be specific about which categories and by how much
- Focus on revenue opportunities
- Keep each insight to 1-2 sentences
- If significantly underpriced (>15% below market), suggest price increase
- If overpriced, suggest competitive positioning strategy
- Consider category importance (item count)

Format your response as JSON:
{{"insights": ["insight 1", "insight 2", ...], "summary": "one sentence overall assessment"}}"""

        response = model.generate_content(prompt)

        # Parse JSON response
        import json
        text = response.text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        result = json.loads(text)
        return result

    except Exception as e:
        print(f"AI insights error: {e}")
        # Fallback to rule-based insights
        return generate_rule_based_insights(insights_data)


def generate_rule_based_insights(data: list[dict]) -> dict:
    """Generate insights using simple rules when AI is unavailable."""
    insights = []

    # Find biggest underpriced category
    underpriced = [d for d in data if d["delta_pct"] < -10]
    underpriced.sort(key=lambda x: x["delta_pct"])

    if underpriced:
        worst = underpriced[0]
        potential_increase = abs(worst["delta_pct"]) * 0.5  # Suggest half the gap
        insights.append(
            f"Your {worst['category']} prices are {abs(worst['delta_pct']):.0f}% below market. "
            f"Consider a {potential_increase:.0f}% price increase to capture additional margin."
        )

    # Find overpriced categories
    overpriced = [d for d in data if d["delta_pct"] > 10]
    if overpriced:
        worst = max(overpriced, key=lambda x: x["delta_pct"])
        insights.append(
            f"Your {worst['category']} prices are {worst['delta_pct']:.0f}% above market. "
            f"Ensure quality justifies the premium or consider promotional pricing."
        )

    # Find competitive categories
    competitive = [d for d in data if -5 <= d["delta_pct"] <= 5]
    if competitive:
        names = [c["category"] for c in competitive[:2]]
        insights.append(
            f"Your {', '.join(names)} pricing is well-aligned with the market. "
            f"Focus differentiation efforts elsewhere."
        )

    # Revenue opportunity
    total_underpriced = sum(1 for d in data if d["delta_pct"] < -10)
    if total_underpriced > 0:
        insights.append(
            f"{total_underpriced} categories are significantly underpriced. "
            f"Addressing these could improve margins without losing competitiveness."
        )

    # Summary
    avg_delta = sum(d["delta_pct"] for d in data) / len(data) if data else 0
    if avg_delta < -10:
        summary = "Overall, your prices are significantly below market. There's room to increase prices and improve margins."
    elif avg_delta > 10:
        summary = "Overall, your prices are above market average. Ensure your value proposition supports premium pricing."
    else:
        summary = "Your pricing is generally competitive with the market. Focus on optimizing specific categories."

    return {"insights": insights, "summary": summary}
