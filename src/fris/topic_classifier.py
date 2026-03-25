"""Topic-to-GICS classification for FRIS.

Maps free-text user topics (e.g., "AI chips") to GICS industries
via keyword matching against a curated mapping table.
"""

from dataclasses import dataclass
from typing import Optional


# GICS Industry keyword mapping
# Each industry maps to a list of keywords that indicate user interest
GICS_KEYWORD_MAP: dict[str, list[str]] = {
    "Semiconductors": [
        "chip", "semiconductor", "ai chip", "gpu", "cpu",
        "processor", "foundry", "wafer", "integrated circuit"
    ],
    "Software Infrastructure": [
        "cloud", "saas", "software", "infrastructure",
        "data center", "enterprise software", "cloud computing"
    ],
    "Auto Manufacturers": [
        "electric vehicle", "ev", "automobile", "car",
        "auto", "vehicle", "tesla", "ford", "gm"
    ],
    "Financial Services": [
        "bank", "financial", "fintech", "payment",
        "insurance", "lending", "wealth management"
    ],
    "Healthcare": [
        "hospital", "healthcare", "medical", "pharma",
        "biotech", "drug", "pharmaceutical", "clinical"
    ],
    "Retail": [
        "retail", "e-commerce", "ecommerce", "shopping",
        "store", "consumer goods", "amazon"
    ],
    "Energy": [
        "oil", "gas", "energy", "renewable", "solar",
        "wind", "petroleum", "lng"
    ],
    "Telecommunications": [
        "telecom", "wireless", "5g", "mobile", "communication",
        "satellite", "broadband"
    ],
    "Real Estate": [
        "real estate", "reit", "property", "housing",
        "commercial property", "residential"
    ],
    "Industrials": [
        "industrial", "manufacturing", "aerospace", "defense",
        "machinery", "construction"
    ],
    "Consumer Discretionary": [
        "discretionary", "restaurant", "hotel", "travel",
        "leisure", "entertainment"
    ],
    "Materials": [
        "materials", "mining", "steel", "aluminum",
        "chemical", "gold", "copper"
    ],
    "Utilities": [
        "utility", "electric", "water", "gas utility",
        "power", "renewable energy"
    ],
}


@dataclass
class IndustryMatch:
    """Represents a matched GICS industry with confidence info."""
    industry: str
    matched_keywords: list[str]
    confidence: float  # 0.0 to 1.0

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.5


class TopicClassifier:
    """Classifies user topics into GICS industries via keyword matching."""

    def __init__(self, keyword_map: dict[str, list[str]] | None = None):
        """
        Args:
            keyword_map: Custom keyword map. Uses GICS_KEYWORD_MAP if None.
        """
        self._keyword_map = keyword_map or GICS_KEYWORD_MAP.copy()

    def classify(self, topic: str) -> list[IndustryMatch]:
        """
        Classify a topic into matching GICS industries.

        Args:
            topic: Free-text topic (e.g., "AI chips", "electric vehicles")

        Returns:
            List of IndustryMatch objects sorted by confidence (highest first)
        """
        topic_lower = topic.lower().strip()
        if not topic_lower:
            return []

        matches: list[IndustryMatch] = []

        for industry, keywords in self._keyword_map.items():
            matched_keywords = [
                kw for kw in keywords
                if kw.lower() in topic_lower
            ]
            if matched_keywords:
                confidence = len(matched_keywords) / len(keywords)
                matches.append(IndustryMatch(
                    industry=industry,
                    matched_keywords=matched_keywords,
                    confidence=min(confidence, 1.0)
                ))

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def find_industries(self, topic: str) -> list[str]:
        """
        Get list of industry names matching a topic.

        Args:
            topic: Free-text topic

        Returns:
            List of matching industry names
        """
        return [m.industry for m in self.classify(topic)]

    def add_keyword(self, industry: str, keyword: str) -> None:
        """Add a keyword to an industry's mapping."""
        if industry not in self._keyword_map:
            self._keyword_map[industry] = []
        if keyword.lower() not in [k.lower() for k in self._keyword_map[industry]]:
            self._keyword_map[industry].append(keyword.lower())

    def get_all_industries(self) -> list[str]:
        """Get list of all supported industries."""
        return list(self._keyword_map.keys())
