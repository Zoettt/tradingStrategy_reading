"""Earnings data fetching service for FRIS.

FRIS-10: Fetch latest earnings data (EPS, revenue, earnings date)
FRIS-11: Fetch company overview (market cap, P/E, P/B, price, description)
FRIS-12: Fetch earnings guidance (forward EPS)
FRIS-14: Support quarterly data (Q1-Q4 with year)
"""

from datetime import datetime
from typing import Optional

import yfinance as yf

from src.fris.models import EarningsData, QuarterlyData
from src.fris.cache import FundamentalsCache


class EarningsService:
    """Service for fetching earnings data, company overview, and guidance.

    Uses Yahoo Finance (yfinance) as primary data source.
    Caches results using FundamentalsCache (24hr TTL).
    """

    def __init__(self, cache: FundamentalsCache | None = None):
        """Initialize EarningsService.

        Args:
            cache: FundamentalsCache instance. Creates new if None.
        """
        self._cache = cache or FundamentalsCache()

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def _calculate_yoy(self, current: float, prior: float) -> Optional[float]:
        """Calculate year-over-year change percentage."""
        if prior is None or prior == 0:
            return None
        return ((current - prior) / prior) * 100

    def get_earnings_data(self, ticker: str) -> EarningsData:
        """Fetch latest earnings data for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            EarningsData with EPS, revenue, earnings date, YoY change
        """
        ticker = ticker.upper()
        fetched_at = self._now_iso()

        # Check cache first
        cached = self._cache.get(f"{ticker}_earnings")
        if cached:
            return cached

        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info

            # Extract earnings date
            earnings_date = None
            if info.get("earningsTimestamp"):
                earnings_date = datetime.fromtimestamp(
                    info["earningsTimestamp"]
                ).strftime("%Y-%m-%d")

            # Extract EPS
            eps_current = info.get("epsTrailingTwelveMonths")
            eps_forward = info.get("epsForward")

            # Extract revenue
            revenue = info.get("totalRevenue")

            # Calculate revenue YoY (requires comparing to prior year)
            revenue_yoy_change = None
            try:
                income_stmt = yf_ticker.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    # Get revenue for current and prior year
                    years = list(income_stmt.columns)
                    if len(years) >= 2:
                        current_rev = income_stmt.loc["Total Revenue", years[0]]
                        prior_rev = income_stmt.loc["Total Revenue", years[1]]
                        if current_rev and prior_rev:
                            revenue_yoy_change = self._calculate_yoy(
                                float(current_rev), float(prior_rev)
                            )
            except Exception:
                pass  # YoY calculation is best-effort

            earnings_data = EarningsData(
                ticker=ticker,
                earnings_date=earnings_date,
                eps_current=eps_current,
                eps_forward=eps_forward,
                revenue=revenue,
                revenue_yoy_change=revenue_yoy_change,
                earnings_surprise=None,  # yfinance doesn't provide this easily
                data_source="yfinance",
                fetched_at=fetched_at
            )

            # Cache the result
            self._cache.set(f"{ticker}_earnings", earnings_data)

            return earnings_data

        except Exception as e:
            # Return empty EarningsData on failure
            return EarningsData(
                ticker=ticker,
                data_source="yfinance",
                fetched_at=fetched_at
            )

    def get_company_overview(self, ticker: str) -> dict:
        """Fetch company overview data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with market_cap, current_price, pe_ratio, pb_ratio, description
        """
        ticker = ticker.upper()

        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info

            return {
                "ticker": ticker,
                "market_cap": info.get("marketCap"),
                "current_price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "description": info.get("longBusinessSummary"),
                "forward_pe": info.get("forwardPE"),
                "eps_trailing": info.get("epsTrailingTwelveMonths"),
                "eps_forward": info.get("epsForward"),
            }

        except Exception:
            return {
                "ticker": ticker,
                "market_cap": None,
                "current_price": None,
                "pe_ratio": None,
                "pb_ratio": None,
                "description": None,
            }

    def get_earnings_guidance(self, ticker: str) -> Optional[float]:
        """Fetch earnings guidance (forward EPS).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Forward EPS or None if not available
        """
        ticker = ticker.upper()

        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            return info.get("epsForward")
        except Exception:
            return None

    def get_quarterly_data(self, ticker: str, quarter: str, year: int) -> QuarterlyData:
        """Fetch quarterly financial data.

        Args:
            ticker: Stock ticker symbol
            quarter: Quarter string ("Q1", "Q2", "Q3", "Q4")
            year: Year (e.g., 2024)

        Returns:
            QuarterlyData with EPS, revenue, YoY change
        """
        ticker = ticker.upper()
        fetched_at = self._now_iso()

        # Check cache first
        cache_key = f"{ticker}_{quarter}_{year}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            yf_ticker = yf.Ticker(ticker)
            quarterly_financials = yf_ticker.quarterly_financials

            if quarterly_financials is None or quarterly_financials.empty:
                return QuarterlyData(
                    ticker=ticker,
                    quarter=quarter,
                    year=year,
                    data_source="yfinance",
                    fetched_at=fetched_at
                )

            # Find the right quarter column in quarterly_financials
            # yfinance columns are typically datetime objects
            quarter_num = int(quarter[1])  # "Q1" -> 1
            quarter_start_month = (quarter_num - 1) * 3 + 1  # Q1 -> 1, Q2 -> 4, etc.

            eps = None
            revenue = None
            report_date = None

            for col in quarterly_financials.columns:
                if hasattr(col, 'month') and hasattr(col, 'year'):
                    if col.year == year and col.month >= quarter_start_month and col.month < quarter_start_month + 3:
                        # Found the right quarter
                        if "Basic EPS" in quarterly_financials.index:
                            eps = quarterly_financials.loc["Basic EPS", col]
                        if "Total Revenue" in quarterly_financials.index:
                            revenue = quarterly_financials.loc["Total Revenue", col]
                        report_date = col.strftime("%Y-%m-%d")
                        break

            # Calculate YoY revenue change
            revenue_yoy_change = None
            if revenue and year > 1:
                try:
                    # Get prior year same quarter
                    prior_year = year - 1
                    prior_quarter_start_month = quarter_start_month

                    for col in quarterly_financials.columns:
                        if hasattr(col, 'month') and hasattr(col, 'year'):
                            if col.year == prior_year and col.month >= prior_quarter_start_month and col.month < prior_quarter_start_month + 3:
                                if "Total Revenue" in quarterly_financials.index:
                                    prior_revenue = quarterly_financials.loc["Total Revenue", col]
                                    if prior_revenue:
                                        revenue_yoy_change = self._calculate_yoy(
                                            float(revenue), float(prior_revenue)
                                        )
                                break
                except Exception:
                    pass

            quarterly_data = QuarterlyData(
                ticker=ticker,
                quarter=quarter,
                year=year,
                eps=float(eps) if eps else None,
                revenue=float(revenue) if revenue else None,
                revenue_yoy_change=revenue_yoy_change,
                report_date=report_date,
                data_source="yfinance",
                fetched_at=fetched_at
            )

            # Cache the result
            self._cache.set(cache_key, quarterly_data)

            return quarterly_data

        except Exception as e:
            return QuarterlyData(
                ticker=ticker,
                quarter=quarter,
                year=year,
                data_source="yfinance",
                fetched_at=fetched_at
            )
