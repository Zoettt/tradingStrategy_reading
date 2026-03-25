"""Data models for FRIS with N/A handling per FRIS-13."""

from dataclasses import dataclass, field
from typing import Optional

NA_STRING = "N/A"

@dataclass
class StockInfo:
    """Stock information with explicit N/A handling for missing fields."""
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    description: Optional[str] = None

    @property
    def sector_display(self) -> str:
        """Return sector or N/A string."""
        return self.sector if self.sector else NA_STRING

    @property
    def industry_display(self) -> str:
        """Return industry or N/A string."""
        return self.industry if self.industry else NA_STRING

    @property
    def market_cap_display(self) -> str:
        """Return market cap formatted or N/A string."""
        if self.market_cap is None:
            return NA_STRING
        if self.market_cap >= 1e12:
            return f"${self.market_cap / 1e12:.2f}T"
        elif self.market_cap >= 1e9:
            return f"${self.market_cap / 1e9:.2f}B"
        elif self.market_cap >= 1e6:
            return f"${self.market_cap / 1e6:.2f}M"
        return f"${self.market_cap:.2f}"

    @property
    def pe_ratio_display(self) -> str:
        """Return P/E ratio or N/A string."""
        if self.pe_ratio is None:
            return NA_STRING
        return f"{self.pe_ratio:.2f}"

    @property
    def pb_ratio_display(self) -> str:
        """Return P/B ratio or N/A string."""
        if self.pb_ratio is None:
            return NA_STRING
        return f"{self.pb_ratio:.2f}"

@dataclass
class StockSearchResult:
    """Result of topic-based stock search."""
    stocks: list[StockInfo]
    matched_industries: list[str]
    search_topic: str
    total_count: int
