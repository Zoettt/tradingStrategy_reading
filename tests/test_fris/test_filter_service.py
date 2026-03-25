"""Tests for StockFilterService (FRIS-04 to FRIS-09)."""

import pytest

from src.fris.filter_service import StockFilterService, FilterCriteria, FilterResult
from src.fris.models import StockInfo


# Sample stocks for testing
def make_stock(ticker, market_cap=None, pe_ratio=None, pb_ratio=None, price=None):
    return StockInfo(
        ticker=ticker,
        company_name=f"{ticker} Corp",
        sector="Technology",
        industry="Semiconductors",
        market_cap=market_cap,
        current_price=price,
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
    )


class TestStockFilterService:
    """Test StockFilterService filtering logic."""

    def test_no_filters_returns_all_stocks(self):
        """FRIS-08: No filters returns original list."""
        service = StockFilterService()
        stocks = [
            make_stock("AAPL", market_cap=3000e9, pe_ratio=30, pb_ratio=50, price=180),
            make_stock("NVDA", market_cap=2000e9, pe_ratio=60, pb_ratio=40, price=500),
        ]
        result = service.apply_filters(FilterCriteria(), stocks)

        assert result.filtered_count == 2
        assert result.total_count == 2

    def test_filter_by_market_cap_min(self):
        """FRIS-04: Filter by market_cap_min."""
        service = StockFilterService()
        stocks = [
            make_stock("BIG", market_cap=100e9),   # Pass
            make_stock("MID", market_cap=5e9),     # Pass
            make_stock("SMALL", market_cap=500e6), # Fail
        ]
        criteria = FilterCriteria(market_cap_min=1e9)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2
        assert [s.ticker for s in result.filtered_stocks] == ["BIG", "MID"]

    def test_filter_by_market_cap_max(self):
        """FRIS-04: Filter by market_cap_max."""
        service = StockFilterService()
        stocks = [
            make_stock("BIG", market_cap=100e9),   # Fail
            make_stock("MID", market_cap=5e9),     # Pass
            make_stock("SMALL", market_cap=500e6), # Pass
        ]
        criteria = FilterCriteria(market_cap_max=10e9)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2
        assert [s.ticker for s in result.filtered_stocks] == ["MID", "SMALL"]

    def test_filter_by_market_cap_large_category(self):
        """FRIS-04: Filter by large cap category (>= $10B)."""
        service = StockFilterService()
        stocks = [
            make_stock("LARGE1", market_cap=50e9),  # Pass
            make_stock("LARGE2", market_cap=15e9),  # Pass
            make_stock("MID", market_cap=5e9),       # Fail
        ]
        criteria = FilterCriteria(market_cap_category="large")
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2

    def test_filter_by_market_cap_mid_category(self):
        """FRIS-04: Filter by mid cap category (>= $2B and < $10B)."""
        service = StockFilterService()
        stocks = [
            make_stock("LARGE", market_cap=50e9),   # Fail
            make_stock("MID", market_cap=5e9),       # Pass
            make_stock("SMALL", market_cap=500e6),  # Fail
        ]
        criteria = FilterCriteria(market_cap_category="mid")
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 1
        assert result.filtered_stocks[0].ticker == "MID"

    def test_filter_by_market_cap_small_category(self):
        """FRIS-04: Filter by small cap category (>= $300M and < $2B)."""
        service = StockFilterService()
        stocks = [
            make_stock("LARGE", market_cap=50e9),   # Fail
            make_stock("MID", market_cap=5e9),       # Fail
            make_stock("SMALL", market_cap=500e6),  # Pass
        ]
        criteria = FilterCriteria(market_cap_category="small")
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 1
        assert result.filtered_stocks[0].ticker == "SMALL"

    def test_filter_by_pe_ratio(self):
        """FRIS-05: Filter by P/E ratio."""
        service = StockFilterService()
        stocks = [
            make_stock("LOW_PE", pe_ratio=15),    # Pass
            make_stock("MID_PE", pe_ratio=25),    # Pass
            make_stock("HIGH_PE", pe_ratio=50),   # Fail
        ]
        criteria = FilterCriteria(pe_ratio_max=30)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2

    def test_filter_by_pe_ratio_excludes_negative(self):
        """FRIS-05: Negative P/E stocks excluded when P/E filter active."""
        service = StockFilterService()
        stocks = [
            make_stock("NEG_PE", pe_ratio=-5),   # Fail
            make_stock("POS_PE", pe_ratio=20),    # Pass
        ]
        criteria = FilterCriteria(pe_ratio_min=0)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 1
        assert result.filtered_stocks[0].ticker == "POS_PE"

    def test_filter_by_pe_ratio_excludes_na(self):
        """FRIS-05: N/A (None) P/E stocks excluded when P/E filter active."""
        service = StockFilterService()
        stocks = [
            make_stock("NA_PE", pe_ratio=None),   # Fail
            make_stock("VAL_PE", pe_ratio=20),     # Pass
        ]
        criteria = FilterCriteria(pe_ratio_min=0)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 1
        assert result.filtered_stocks[0].ticker == "VAL_PE"

    def test_filter_by_pb_ratio(self):
        """FRIS-06: Filter by P/B ratio."""
        service = StockFilterService()
        stocks = [
            make_stock("LOW_PB", pb_ratio=2),    # Pass
            make_stock("MID_PB", pb_ratio=5),     # Pass
            make_stock("HIGH_PB", pb_ratio=15),   # Fail
        ]
        criteria = FilterCriteria(pb_ratio_max=10)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2

    def test_filter_by_pb_ratio_excludes_negative(self):
        """FRIS-06: Negative P/B stocks excluded when P/B filter active."""
        service = StockFilterService()
        stocks = [
            make_stock("NEG_PB", pb_ratio=-1),   # Fail
            make_stock("POS_PB", pb_ratio=3),     # Pass
        ]
        criteria = FilterCriteria(pb_ratio_min=0)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 1

    def test_filter_by_price(self):
        """FRIS-07: Filter by stock price."""
        service = StockFilterService()
        stocks = [
            make_stock("CHEAP", price=50),    # Pass
            make_stock("MID_PRICE", price=150),  # Pass
            make_stock("EXPENSIVE", price=500),  # Fail
        ]
        criteria = FilterCriteria(price_min=30, price_max=200)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2

    def test_filter_and_logic_combination(self):
        """FRIS-08: Multiple filters combined with AND logic."""
        service = StockFilterService()
        stocks = [
            make_stock("A", market_cap=50e9, pe_ratio=20, price=100),   # Pass all
            make_stock("B", market_cap=5e9, pe_ratio=20, price=100),    # Fail: market cap
            make_stock("C", market_cap=50e9, pe_ratio=50, price=100),   # Fail: P/E
            make_stock("D", market_cap=50e9, pe_ratio=20, price=300),   # Fail: price
        ]
        criteria = FilterCriteria(
            market_cap_min=10e9,
            pe_ratio_max=30,
            price_max=200
        )
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 1
        assert result.filtered_stocks[0].ticker == "A"

    def test_filtered_count_before_full_fetch(self):
        """FRIS-09: get_filtered_count returns count without full data fetch."""
        service = StockFilterService()
        stocks = [
            make_stock("A", market_cap=50e9, pe_ratio=20, price=100),
            make_stock("B", market_cap=5e9, pe_ratio=20, price=100),
        ]
        criteria = FilterCriteria(market_cap_min=10e9)

        # get_filtered_count should be lightweight
        count = service.get_filtered_count(criteria, stocks)
        assert count == 1

        # Same as applying filters
        result = service.apply_filters(criteria, stocks)
        assert count == result.filtered_count

    def test_empty_result_when_no_match(self):
        """FRIS-08: Empty result when no stocks match."""
        service = StockFilterService()
        stocks = [
            make_stock("A", market_cap=500e6),
            make_stock("B", market_cap=300e6),
        ]
        criteria = FilterCriteria(market_cap_min=1e9)
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 0
        assert result.filtered_stocks == []

    def test_all_filters_none_returns_original(self):
        """FRIS-08: All None filters returns original list."""
        service = StockFilterService()
        stocks = [
            make_stock("A"),
            make_stock("B"),
        ]
        criteria = FilterCriteria()
        result = service.apply_filters(criteria, stocks)

        assert result.filtered_count == 2
        assert result.total_count == 2
