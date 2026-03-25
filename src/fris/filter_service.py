"""Stock filtering service for financial metric-based screening.

FRIS-04: Filter by market cap (min/max or predefined large/mid/small)
FRIS-05: Filter by P/E ratio (min/max, N/A for negative earnings)
FRIS-06: Filter by P/B ratio (min/max, N/A for negative book value)
FRIS-07: Filter by stock price (min/max in USD)
FRIS-08: Filters combinable with AND logic
FRIS-09: System returns filtered count before full data fetch
"""

from dataclasses import dataclass
from typing import Optional, Literal

from src.fris.models import StockInfo


# Market cap predefined thresholds (USD)
MARKET_CAP_THRESHOLDS = {
    "large": 10e9,   # >= $10B
    "mid": 2e9,      # >= $2B and < $10B
    "small": 300e6,  # >= $300M and < $2B
}


@dataclass
class FilterCriteria:
    """Filter criteria for stock screening.

    All fields are optional. A stock passes a filter criterion only if:
    - The criterion is None (not specified), OR
    - The stock's value meets the criterion
    """
    # Market cap filters (USD)
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    market_cap_category: Optional[Literal["large", "mid", "small"]] = None

    # P/E ratio filters
    pe_ratio_min: Optional[float] = None
    pe_ratio_max: Optional[float] = None

    # P/B ratio filters
    pb_ratio_min: Optional[float] = None
    pb_ratio_max: Optional[float] = None

    # Stock price filters (USD)
    price_min: Optional[float] = None
    price_max: Optional[float] = None


@dataclass
class FilterResult:
    """Result of applying filters to a stock list."""
    filtered_stocks: list[StockInfo]
    total_count: int
    filtered_count: int


class StockFilterService:
    """Service for filtering stocks by financial metrics.

    Applies AND logic: a stock must pass ALL specified criteria to be included.
    """

    def __init__(self):
        """Initialize StockFilterService."""
        pass

    def _get_market_cap_min(self, criteria: FilterCriteria) -> Optional[float]:
        """Get effective market cap minimum considering category."""
        if criteria.market_cap_category:
            return MARKET_CAP_THRESHOLDS.get(criteria.market_cap_category)
        return criteria.market_cap_min

    def _get_market_cap_max(self, criteria: FilterCriteria) -> Optional[float]:
        """Get effective market cap maximum considering category."""
        if criteria.market_cap_category:
            category = criteria.market_cap_category
            if category == "large":
                return None  # No upper limit for large cap
            elif category == "mid":
                return MARKET_CAP_THRESHOLDS["large"]
            elif category == "small":
                return MARKET_CAP_THRESHOLDS["mid"]
        return criteria.market_cap_max

    def _stock_passes_market_cap(self, stock: StockInfo, criteria: FilterCriteria) -> bool:
        """Check if stock passes market cap filter."""
        if stock.market_cap is None:
            # If market cap is N/A and we have a market cap filter, exclude
            if criteria.market_cap_min is not None or criteria.market_cap_max is not None or criteria.market_cap_category:
                return False
            return True

        cap_min = self._get_market_cap_min(criteria)
        cap_max = self._get_market_cap_max(criteria)

        if cap_min is not None and stock.market_cap < cap_min:
            return False
        if cap_max is not None and stock.market_cap >= cap_max:
            return False

        return True

    def _stock_passes_pe_ratio(self, stock: StockInfo, criteria: FilterCriteria) -> bool:
        """Check if stock passes P/E ratio filter."""
        if criteria.pe_ratio_min is None and criteria.pe_ratio_max is None:
            return True

        # N/A handling: exclude stocks with None or negative P/E when filter is active
        if stock.pe_ratio is None or stock.pe_ratio <= 0:
            return False

        if criteria.pe_ratio_min is not None and stock.pe_ratio < criteria.pe_ratio_min:
            return False
        if criteria.pe_ratio_max is not None and stock.pe_ratio > criteria.pe_ratio_max:
            return False

        return True

    def _stock_passes_pb_ratio(self, stock: StockInfo, criteria: FilterCriteria) -> bool:
        """Check if stock passes P/B ratio filter."""
        if criteria.pb_ratio_min is None and criteria.pb_ratio_max is None:
            return True

        # N/A handling: exclude stocks with None or negative P/B when filter is active
        if stock.pb_ratio is None or stock.pb_ratio <= 0:
            return False

        if criteria.pb_ratio_min is not None and stock.pb_ratio < criteria.pb_ratio_min:
            return False
        if criteria.pb_ratio_max is not None and stock.pb_ratio > criteria.pb_ratio_max:
            return False

        return True

    def _stock_passes_price(self, stock: StockInfo, criteria: FilterCriteria) -> bool:
        """Check if stock passes price filter."""
        if criteria.price_min is None and criteria.price_max is None:
            return True

        if stock.current_price is None:
            return False

        if criteria.price_min is not None and stock.current_price < criteria.price_min:
            return False
        if criteria.price_max is not None and stock.current_price > criteria.price_max:
            return False

        return True

    def _stock_passes_filters(self, stock: StockInfo, criteria: FilterCriteria) -> bool:
        """Check if stock passes all active filters (AND logic)."""
        return (
            self._stock_passes_market_cap(stock, criteria)
            and self._stock_passes_pe_ratio(stock, criteria)
            and self._stock_passes_pb_ratio(stock, criteria)
            and self._stock_passes_price(stock, criteria)
        )

    def apply_filters(self, criteria: FilterCriteria, stocks: list[StockInfo]) -> FilterResult:
        """Apply filters to stock list.

        Args:
            criteria: FilterCriteria with optional min/max values
            stocks: List of StockInfo to filter

        Returns:
            FilterResult with filtered_stocks, filtered_count, and total_count
        """
        total_count = len(stocks)

        filtered_stocks = [
            stock for stock in stocks
            if self._stock_passes_filters(stock, criteria)
        ]

        filtered_count = len(filtered_stocks)

        return FilterResult(
            filtered_stocks=filtered_stocks,
            total_count=total_count,
            filtered_count=filtered_count
        )

    def get_filtered_count(self, criteria: FilterCriteria, stocks: list[StockInfo]) -> int:
        """Get count of stocks that would pass filters (lightweight, no data fetching).

        Args:
            criteria: FilterCriteria with optional min/max values
            stocks: List of StockInfo to filter

        Returns:
            Number of stocks that would pass the filters
        """
        return sum(1 for stock in stocks if self._stock_passes_filters(stock, criteria))
