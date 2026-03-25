"""Stock repository with yfinance primary and FMP fallback.

FRIS-20: Primary data source is Yahoo Finance via yfinance
FRIS-21: FMP available as fallback for coverage gaps
FRIS-03: Returns stock tickers with company names and industries
"""

import time
from enum import Enum
from typing import Optional

import yfinance as yf

from src.fris.models import StockInfo
from src.fris.cache import FundamentalsCache
from src.fris.exceptions import DataSourceError, RateLimitError


class DataSource(Enum):
    """Available data sources in priority order."""
    YAHOO_FINANCE = "yfinance"
    FMP = "fmp"


class StockRepository:
    """Repository for fetching stock information.

    Primary: Yahoo Finance (yfinance) - no API key required
    Fallback: FMP API - rate limited (5 req/min free tier)
    """

    def __init__(self, cache: FundamentalsCache | None = None):
        """
        Args:
            cache: FundamentalsCache instance for caching. Creates new if None.
        """
        self._cache = cache or FundamentalsCache()
        self._fmp_request_count = 0
        self._fmp_last_reset = time.time()
        self._fmp_rate_limit = 5  # requests per minute
        self._fmp_rate_window = 60  # seconds

    def _check_fmp_rate_limit(self) -> None:
        """Check if FMP rate limit is exceeded. Raises RateLimitError if so."""
        current_time = time.time()
        # Reset counter if window has passed
        if current_time - self._fmp_last_reset >= self._fmp_rate_window:
            self._fmp_request_count = 0
            self._fmp_last_reset = current_time

        if self._fmp_request_count >= self._fmp_rate_limit:
            raise RateLimitError(
                "FMP",
                retry_after=int(self._fmp_rate_window - (current_time - self._fmp_last_reset))
            )

    def _fetch_from_yfinance(self, ticker: str) -> Optional[StockInfo]:
        """Fetch stock info from Yahoo Finance.

        Returns None if ticker not found or request fails.
        """
        try:
            info = yf.Ticker(ticker).info
            if not info or info.get("regularMarketPrice") is None:
                return None

            return StockInfo(
                ticker=ticker.upper(),
                company_name=info.get("shortName", "N/A"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                current_price=info.get("regularMarketPrice"),
                pe_ratio=info.get("trailingPE"),
                pb_ratio=info.get("priceToBook"),
                description=info.get("longBusinessSummary"),
            )
        except Exception as e:
            raise DataSourceError("yfinance", ticker, str(e))

    def _fetch_from_fmp(self, ticker: str) -> Optional[StockInfo]:
        """Fetch stock info from FMP API (fallback source).

        Raises RateLimitError if rate limit exceeded.
        Returns None if ticker not found.
        """
        self._check_fmp_rate_limit()
        self._fmp_request_count += 1

        # FMP API call would go here
        # For now, return None to indicate fallback failed
        # Real implementation would use requests.get(f"https://financialmodelingprep.com/api/v3/profile/{ticker}...")
        return None

    def get_stock_info(self, ticker: str, force_refresh: bool = False) -> Optional[StockInfo]:
        """Get StockInfo for a single ticker.

        Uses cache if available and not force_refresh.
        Tries yfinance first, falls back to FMP if needed.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            force_refresh: Skip cache if True

        Returns:
            StockInfo or None if not found
        """
        ticker = ticker.upper()

        # Check cache first
        if not force_refresh:
            cached = self._cache.get(ticker)
            if cached:
                return cached

        # Try yfinance (primary)
        stock_info = self._fetch_from_yfinance(ticker)

        # Fallback to FMP if yfinance failed
        if stock_info is None:
            try:
                stock_info = self._fetch_from_fmp(ticker)
            except RateLimitError:
                # FMP rate limited, return what we have (possibly cached)
                pass

        # Cache result if we have one
        if stock_info:
            self._cache.set(ticker, stock_info)

        return stock_info

    def search_by_industry(self, industry: str, limit: int = 50) -> list[StockInfo]:
        """Find stocks matching a GICS industry.

        Uses yfinance sector/industry classification.
        Note: yfinance doesn't provide direct industry search,
        so this method searches a predefined list of tickers.

        Args:
            industry: GICS industry name (e.g., "Semiconductors")
            limit: Maximum number of results to return

        Returns:
            List of StockInfo for matching stocks
        """
        # Predefined ticker lists by industry for MVP
        # In production, this would query a stock database or use
        # yfinance's sector screener functionality
        INDUSTRY_TICKERS: dict[str, list[str]] = {
            "Semiconductors": [
                "NVDA", "AMD", "INTC", "AVGO", "TSM", "QCOM", "AMAT", "LRCX",
                "MU", "TXN", "NXPI", "ON", "MCHP", "ADI", "SWKS", "MPWR"
            ],
            "Software Infrastructure": [
                "MSFT", "ORCL", "CRM", "NOW", "SQSP", "VEEV", "WDAY", "ZS",
                "NET", "PLTR", "AKAM", "CDN", "FFIV", "MANH", "NEWR", "SMAR"
            ],
            "Auto Manufacturers": [
                "TSLA", "F", "GM", "TM", "RIVN", "LCID", "NIO", "XPEV"
            ],
            "Financial Services": [
                "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "V", "MA",
                "PYPL", "COIN", "HOOD"
            ],
            "Healthcare": [
                "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR",
                "BMY", "LLY", "AMGN", "GILD"
            ],
        }

        # Normalize industry name
        industry_normalized = industry.strip()

        # Get ticker list for industry
        tickers = INDUSTRY_TICKERS.get(industry_normalized, [])

        results = []
        for ticker in tickers[:limit]:
            stock_info = self.get_stock_info(ticker)
            if stock_info:
                results.append(stock_info)

        return results

    def get_tickers_by_sector(self, sector: str) -> list[str]:
        """Get all known tickers for a GICS sector.

        This is a convenience method for building sector-specific lists.

        Args:
            sector: GICS sector name

        Returns:
            List of ticker symbols
        """
        # Expanded ticker lists by sector for better coverage
        SECTOR_TICKERS: dict[str, list[str]] = {
            "Technology": [
                "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "INTC",
                "QCOM", "TXN", "NOW", "MU", "AMAT", "LRCX", "NXPI", "ADI"
            ],
            "Healthcare": [
                "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "LLY"
            ],
            "Financials": [
                "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "V", "MA", "PYPL"
            ],
            "Consumer Discretionary": [
                "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG"
            ],
            "Communication Services": [
                "GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS"
            ],
        }

        return SECTOR_TICKERS.get(sector, [])
