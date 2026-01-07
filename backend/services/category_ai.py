"""
AI-powered category matching service using Gemini embeddings.

Uses Google's text-embedding-004 model to semantically match raw category names
from restaurants to canonical categories.
"""

import os
import re
import json
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

import numpy as np
import google.generativeai as genai


def strip_emojis(text: str) -> str:
    """Remove emojis and special unicode characters from text."""
    # Remove emojis and other non-ASCII characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # misc symbols
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0000200D"             # zero width joiner
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CanonicalCategory, CategoryMapping


# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class CategorySuggestion:
    """Suggestion for mapping a raw category to a canonical category."""
    raw_category: str
    canonical_category_id: str
    canonical_category_name: str
    confidence_score: float
    alternatives: list[tuple[str, str, float]]  # List of (id, name, score)


class CategoryAIService:
    """
    AI service for semantic category matching using Gemini embeddings.
    """

    def __init__(self):
        self.model_name = "models/text-embedding-004"
        self.similarity_threshold = 0.75  # Minimum similarity for auto-mapping
        self._embedding_cache: dict[str, list[float]] = {}

    def _get_embedding_sync(self, text: str) -> list[float]:
        """
        Get embedding vector for text (synchronous).
        Uses caching to avoid redundant API calls.
        Strips emojis for better matching.
        """
        # Strip emojis and normalize text for better matching
        clean_text = strip_emojis(text).lower().strip()
        cache_key = clean_text

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        if not GEMINI_API_KEY:
            # Fallback to keyword-based matching if no API key
            return self._keyword_vector(clean_text)

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=clean_text,
                task_type="semantic_similarity"
            )
            embedding = result['embedding']
            self._embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            print(f"Gemini embedding error: {e}")
            # Fallback to keyword-based matching
            return self._keyword_vector(clean_text)

    def _keyword_vector(self, text: str) -> list[float]:
        """
        Simple keyword-based vector for fallback matching.
        Creates a pseudo-embedding based on common food category keywords.
        """
        keywords = [
            "burger", "chicken", "sandwich", "wrap", "bowl", "salad",
            "vegan", "plant", "vegetarian", "side", "fries", "drink",
            "beverage", "dessert", "sweet", "breakfast", "combo", "meal",
            "appetizer", "starter", "pizza", "seafood", "fish", "taco",
            "burrito", "mexican", "asian", "noodle", "rice", "soup"
        ]

        text_lower = text.lower()
        vector = [1.0 if kw in text_lower else 0.0 for kw in keywords]

        # Normalize to unit length
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec_a) != len(vec_b):
            # Handle mismatched vector lengths (e.g., keyword vs embedding)
            return 0.0

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    async def get_all_canonical_categories(
        self,
        db: AsyncSession
    ) -> list[CanonicalCategory]:
        """Fetch all canonical categories from database."""
        stmt = select(CanonicalCategory).order_by(CanonicalCategory.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def find_best_match(
        self,
        raw_category: str,
        canonical_categories: list[CanonicalCategory]
    ) -> tuple[CanonicalCategory, float] | None:
        """
        Find the best matching canonical category for a raw category.

        Returns (canonical_category, similarity_score) or None if no good match.
        """
        if not canonical_categories:
            return None

        raw_embedding = self._get_embedding_sync(raw_category)

        best_match = None
        best_score = 0.0

        for canonical in canonical_categories:
            # Create search text from canonical name + keywords
            search_text = canonical.name
            if canonical.keywords:
                search_text += " " + canonical.keywords

            canonical_embedding = self._get_embedding_sync(search_text)
            score = self._cosine_similarity(raw_embedding, canonical_embedding)

            if score > best_score:
                best_score = score
                best_match = canonical

        if best_match and best_score >= 0.5:  # Minimum threshold for any match
            return (best_match, best_score)

        return None

    async def suggest_mappings(
        self,
        db: AsyncSession,
        raw_categories: list[str]
    ) -> list[CategorySuggestion]:
        """
        Generate mapping suggestions for a list of raw categories.
        Returns suggestions with confidence scores and alternatives.
        """
        canonical_categories = await self.get_all_canonical_categories(db)

        if not canonical_categories:
            return []

        suggestions = []

        for raw_cat in raw_categories:
            raw_embedding = self._get_embedding_sync(raw_cat)

            # Score all canonical categories
            scored = []
            for canonical in canonical_categories:
                search_text = canonical.name
                if canonical.keywords:
                    search_text += " " + canonical.keywords

                canonical_embedding = self._get_embedding_sync(search_text)
                score = self._cosine_similarity(raw_embedding, canonical_embedding)
                scored.append((canonical, score))

            # Sort by score descending
            scored.sort(key=lambda x: x[1], reverse=True)

            if scored and scored[0][1] >= 0.5:
                best = scored[0]
                alternatives = [
                    (cat.id, cat.name, round(score, 4))
                    for cat, score in scored[1:4]  # Top 3 alternatives
                    if score >= 0.4
                ]

                suggestions.append(CategorySuggestion(
                    raw_category=raw_cat,
                    canonical_category_id=best[0].id,
                    canonical_category_name=best[0].name,
                    confidence_score=round(best[1], 4),
                    alternatives=alternatives
                ))

        return suggestions

    async def auto_map_categories(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str,
        raw_categories: list[str],
        threshold: float = 0.8
    ) -> list[CategoryMapping]:
        """
        Automatically create mappings for categories with high confidence.

        Only creates mappings where confidence >= threshold.
        Returns list of created mappings.
        """
        suggestions = await self.suggest_mappings(db, raw_categories)
        created_mappings = []

        for suggestion in suggestions:
            if suggestion.confidence_score >= threshold:
                # Check if mapping already exists
                existing_stmt = select(CategoryMapping).where(
                    CategoryMapping.source_type == source_type,
                    CategoryMapping.source_id == source_id,
                    CategoryMapping.raw_category == suggestion.raw_category
                )
                existing_result = await db.execute(existing_stmt)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    # Update existing mapping if it was AI-generated (not manual)
                    if not existing.is_manual:
                        existing.canonical_category_id = suggestion.canonical_category_id
                        existing.confidence_score = Decimal(str(suggestion.confidence_score))
                        created_mappings.append(existing)
                else:
                    # Create new mapping
                    mapping = CategoryMapping(
                        source_type=source_type,
                        source_id=source_id,
                        raw_category=suggestion.raw_category,
                        canonical_category_id=suggestion.canonical_category_id,
                        confidence_score=Decimal(str(suggestion.confidence_score)),
                        is_manual=False
                    )
                    db.add(mapping)
                    created_mappings.append(mapping)

        if created_mappings:
            await db.commit()

        return created_mappings

    async def get_unmapped_categories(
        self,
        db: AsyncSession,
        source_type: str,
        source_id: str,
        raw_categories: list[str]
    ) -> list[str]:
        """Get list of raw categories that don't have mappings yet."""
        existing_stmt = select(CategoryMapping.raw_category).where(
            CategoryMapping.source_type == source_type,
            CategoryMapping.source_id == source_id,
            CategoryMapping.raw_category.in_(raw_categories)
        )
        result = await db.execute(existing_stmt)
        mapped = {r[0] for r in result.all()}

        return [cat for cat in raw_categories if cat not in mapped]


# Singleton instance
category_ai_service = CategoryAIService()
