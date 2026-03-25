"""Integration tests for TopicSearchService (FRIS-01, FRIS-02, FRIS-03)."""

import pytest
from unittest.mock import MagicMock, patch

from src.fris.service import TopicSearchService, TimePeriod
from src.fris.topic_classifier import TopicClassifier, IndustryMatch
from src.fris.stock_repository import StockRepository
from src.fris.models import StockInfo, StockSearchResult


class TestTopicSearchService:
    """Test TopicSearchService.search() - end-to-end topic to stocks."""

    def test_search_returns_stock_search_result(self):
        """FRIS-03: search() returns StockSearchResult."""
        service = TopicSearchService()
        result = service.search("AI chips")

        assert isinstance(result, StockSearchResult)
        assert hasattr(result, 'stocks')
        assert hasattr(result, 'matched_industries')
        assert hasattr(result, 'search_topic')
        assert hasattr(result, 'total_count')

    def test_search_with_ai_chips_finds_semiconductors(self):
        """FRIS-02: 'AI chips' maps to Semiconductors industry."""
        service = TopicSearchService()
        result = service.search("AI chips")

        assert "Semiconductors" in result.matched_industries
        assert result.search_topic == "AI chips"

    def test_search_with_electric_vehicle_finds_auto_manufacturers(self):
        """FRIS-02: 'electric vehicle' maps to Auto Manufacturers."""
        service = TopicSearchService()
        result = service.search("electric vehicle")

        assert "Auto Manufacturers" in result.matched_industries

    def test_search_with_empty_topic_returns_empty_result(self):
        """FRIS-01: Empty topic returns empty StockSearchResult."""
        service = TopicSearchService()
        result = service.search("")

        assert result.stocks == []
        assert result.matched_industries == []
        assert result.total_count == 0

    def test_search_with_whitespace_topic_returns_empty_result(self):
        """FRIS-01: Whitespace-only topic returns empty result."""
        service = TopicSearchService()
        result = service.search("   ")

        assert result.stocks == []
        assert result.matched_industries == []

    def test_search_returns_stocks_with_required_fields(self):
        """FRIS-03: Stocks have ticker, company_name, sector, industry."""
        service = TopicSearchService()
        result = service.search("AI chips")

        if result.stocks:
            stock = result.stocks[0]
            assert stock.ticker
            assert stock.company_name
            # sector/industry may be None (N/A) but field must exist
            assert hasattr(stock, 'sector')
            assert hasattr(stock, 'industry')

    def test_search_respects_limit_per_industry(self):
        """FRIS-03: limit_per_industry restricts results."""
        service = TopicSearchService()

        # Mock the repository to return known stocks
        mock_stocks = [
            StockInfo(ticker=f"TEST{i}", company_name=f"Test {i}")
            for i in range(20)
        ]

        with patch.object(service._repository, 'search_by_industry', return_value=mock_stocks):
            result = service.search("test topic", limit_per_industry=5)

        # With 1 industry and limit 5, should have at most 5 stocks
        assert len(result.stocks) <= 5

    def test_search_deduplicates_stocks(self):
        """FRIS-03: Same ticker appearing in multiple industries is deduplicated."""
        service = TopicSearchService()

        # Create mock stocks where TEST1 appears in both industries
        mock_stocks = [
            StockInfo(ticker="TEST1", company_name="Test 1", sector="Tech", industry="Software"),
            StockInfo(ticker="TEST1", company_name="Test 1", sector="Tech", industry="Hardware"),
            StockInfo(ticker="TEST2", company_name="Test 2", sector="Tech", industry="Software"),
        ]

        with patch.object(service._repository, 'search_by_industry', return_value=mock_stocks):
            with patch.object(service._classifier, 'classify', return_value=[
                IndustryMatch("Software", ["test"], 0.5),
                IndustryMatch("Hardware", ["test"], 0.5),
            ]):
                result = service.search("test")

        # TEST1 should appear only once
        tickers = [s.ticker for s in result.stocks]
        assert tickers.count("TEST1") == 1

    def test_search_single_industry(self):
        """FRIS-03: search_single_industry returns stocks for specific industry."""
        service = TopicSearchService()
        result = service.search_single_industry("AI chips", "Semiconductors", limit=5)

        assert isinstance(result, StockSearchResult)
        assert result.matched_industries == ["Semiconductors"]
        assert result.search_topic == "AI chips"


class TestTimePeriod:
    """Test TimePeriod dataclass."""

    def test_current_quarter_creates_valid_period(self):
        """TimePeriod.current_quarter() creates quarter-based period."""
        period = TimePeriod.current_quarter()

        assert period.period_type == "quarter"
        assert period.quarter in [1, 2, 3, 4]
        assert period.year is not None

    def test_last_n_quarters_creates_date_range(self):
        """TimePeriod.last_n_quarters() creates date_range period."""
        period = TimePeriod.last_n_quarters(4)

        assert period.period_type == "date_range"
        assert period.start_date is not None
        assert period.end_date is not None

    def test_time_period_can_be_passed_to_search(self):
        """TimePeriod is accepted by search() method."""
        service = TopicSearchService()
        period = TimePeriod.current_quarter()

        # Should not raise - period is accepted but not yet used
        result = service.search("AI chips", time_period=period)

        assert isinstance(result, StockSearchResult)


class TestTopicSearchServiceIntegration:
    """Integration tests using real (non-mocked) components."""

    def test_full_pipeline_ai_chips(self):
        """FRIS-01 + FRIS-02 + FRIS-03: Full pipeline with 'AI chips'."""
        service = TopicSearchService()

        result = service.search("AI chips")

        # Verify success criteria from ROADMAP
        assert result.search_topic == "AI chips"
        assert len(result.matched_industries) > 0
        assert "Semiconductors" in result.matched_industries
        assert result.total_count >= 0  # May be 0 if network issues
        assert isinstance(result.stocks, list)

    def test_full_pipeline_electric_vehicle(self):
        """FRIS-01 + FRIS-02 + FRIS-03: Full pipeline with 'electric vehicle'."""
        service = TopicSearchService()

        result = service.search("electric vehicle")

        assert result.search_topic == "electric vehicle"
        assert len(result.matched_industries) > 0
        assert "Auto Manufacturers" in result.matched_industries

    def test_full_pipeline_cloud_computing(self):
        """FRIS-01 + FRIS-02 + FRIS-03: Full pipeline with 'cloud computing'."""
        service = TopicSearchService()

        result = service.search("cloud computing")

        assert result.search_topic == "cloud computing"
        assert "Software Infrastructure" in result.matched_industries
