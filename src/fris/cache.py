"""Dual TTL cache layer for FRIS data access.

Price cache: 1hr TTL
Fundamentals cache: 24hr TTL
"""

from cachetools import TTLCache
from typing import Any, Optional
from src.fris.models import StockInfo


# Cache configuration
PRICE_CACHE_TTL = 3600      # 1 hour in seconds
PRICE_CACHE_MAXSIZE = 500   # Max 500 tickers
FUNDAMENTALS_CACHE_TTL = 86400  # 24 hours in seconds
FUNDAMENTALS_CACHE_MAXSIZE = 1000  # Max 1000 tickers


class PriceCache:
    """Cache for price data with 1hr TTL."""

    def __init__(self, maxsize: int = PRICE_CACHE_MAXSIZE, ttl: int = PRICE_CACHE_TTL):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, ticker: str, key: str = "current") -> Optional[float]:
        """Get cached price. Returns None if not found or expired."""
        cache_key = f"{ticker}:{key}"
        return self._cache.get(cache_key)

    def set(self, ticker: str, price: float, key: str = "current") -> None:
        """Cache a price with 1hr TTL."""
        cache_key = f"{ticker}:{key}"
        self._cache[cache_key] = price

    def invalidate(self, ticker: str) -> None:
        """Remove all cached data for a ticker."""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{ticker}:")]
        for key in keys_to_delete:
            del self._cache[key]

    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)


class FundamentalsCache:
    """Cache for fundamental data with 24hr TTL."""

    def __init__(self, maxsize: int = FUNDAMENTALS_CACHE_MAXSIZE, ttl: int = FUNDAMENTALS_CACHE_TTL):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, ticker: str) -> Optional[StockInfo]:
        """Get cached StockInfo. Returns None if not found or expired."""
        return self._cache.get(ticker)

    def set(self, ticker: str, stock_info: StockInfo) -> None:
        """Cache StockInfo with 24hr TTL."""
        self._cache[ticker] = stock_info

    def invalidate(self, ticker: str) -> None:
        """Remove cached data for a ticker."""
        if ticker in self._cache:
            del self._cache[ticker]

    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)
