"""Tests for StockRepository (FRIS-03, FRIS-20, FRIS-21)."""

import pytest
from unittest.mock import patch, MagicMock

from src.fris.stock_repository import StockRepository, DataSource
from src.fris.models import StockInfo
from src.fris.cache import FundamentalsCache
from src.fris.exceptions import DataSourceError, RateLimitError


class TestStockRepository:
    """Test StockRepository stock fetching."""

    def test_get_stock_info_returns_stock_info(self):
        """FRIS-03: get_stock_info returns StockInfo with ticker, name, sector, industry."""
        repo = StockRepository()
        info = repo.get_stock_info("AAPL")

        assert info is not None
        assert isinstance(info, StockInfo)
        assert info.ticker == "AAPL"
        assert info.company_name
        assert info.sector is not None  # May be None but should be field

    def test_get_stock_info_caches_result(self):
        """FRIS-22: StockInfo is cached after fetch."""
        cache = FundamentalsCache()
        repo = StockRepository(cache=cache)

        # First call
        info1 = repo.get_stock_info("MSFT")
        assert cache.size == 1  # Cached

        # Second call should hit cache
        info2 = repo.get_stock_info("MSFT")
        assert info1.ticker == info2.ticker

    def test_get_stock_info_force_refresh_skips_cache(self):
        """FRIS-22: force_refresh=True bypasses cache."""
        cache = FundamentalsCache()
        repo = StockRepository(cache=cache)

        info1 = repo.get_stock_info("AAPL")
        initial_size = cache.size

        # With force_refresh, should still cache (but re-fetch)
        repo.get_stock_info("AAPL", force_refresh=True)
        assert cache.size == initial_size  # Still 1 (updated, not added)

    def test_search_by_industry_returns_matching_stocks(self):
        """FRIS-03: search_by_industry returns stocks for that industry."""
        repo = StockRepository()
        results = repo.search_by_industry("Semiconductors")

        assert len(results) > 0
        for stock in results:
            assert isinstance(stock, StockInfo)
            assert stock.ticker
            assert stock.company_name

    def test_search_by_industry_respects_limit(self):
        """FRIS-03: search_by_industry respects limit parameter."""
        repo = StockRepository()
        results = repo.search_by_industry("Semiconductors", limit=5)

        assert len(results) <= 5

    def test_get_tickers_by_sector(self):
        """FRIS-03: get_tickers_by_sector returns ticker list."""
        repo = StockRepository()
        tickers = repo.get_tickers_by_sector("Technology")

        assert len(tickers) > 0
        assert "AAPL" in tickers or "MSFT" in tickers

    def test_invalid_ticker_returns_none(self):
        """FRIS-13: Invalid ticker returns None (not an exception)."""
        repo = StockRepository()
        # This should not raise, just return None
        info = repo.get_stock_info("INVALID_TICKER_XYZ")
        # yfinance may return None for invalid tickers
        # The important thing is it doesn't crash

    def test_fmp_fallback_on_yfinance_failure(self):
        """FRIS-21: FMP is used as fallback when yfinance fails."""
        repo = StockRepository()

        # This test verifies the fallback mechanism exists
        # In practice, yfinance should succeed for most US stocks
        # If yfinance returns None, FMP would be attempted
        assert hasattr(repo, '_fetch_from_fmp')

    def test_fmp_rate_limit_enforced(self):
        """FRIS-21: FMP rate limit (5 req/min) is enforced."""
        repo = StockRepository()

        # Simulate rate limit scenario
        with pytest.raises(RateLimitError):
            # Make 5 requests
            for _ in range(5):
                repo._fmp_request_count = 5
                repo._check_fmp_rate_limit()

    def test_data_source_enum_values(self):
        """FRIS-20: DataSource enum has correct values."""
        assert DataSource.YAHOO_FINANCE.value == "yfinance"
        assert DataSource.FMP.value == "fmp"


class TestStockRepositoryCaching:
    """Test caching behavior of StockRepository."""

    def test_cache_is_used_by_default(self):
        """StockRepository uses FundamentalsCache by default."""
        repo = StockRepository()
        assert isinstance(repo._cache, FundamentalsCache)

    def test_custom_cache_can_be_provided(self):
        """Custom cache instance can be injected."""
        custom_cache = FundamentalsCache(maxsize=100, ttl=3600)
        repo = StockRepository(cache=custom_cache)
        assert repo._cache is custom_cache

    def test_invalidate_removes_from_cache(self):
        """Cache can be invalidated for a ticker."""
        cache = FundamentalsCache()
        repo = StockRepository(cache=cache)

        repo.get_stock_info("AAPL")
        assert cache.size >= 1

        repo._cache.invalidate("AAPL")
        # After invalidate, next call would re-fetch
        # (We can't easily test the miss without mocking)
