"""Tests for EarningsService (FRIS-10, FRIS-11, FRIS-12, FRIS-14)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.fris.earnings_service import EarningsService
from src.fris.models import EarningsData, QuarterlyData


class TestEarningsService:
    """Test EarningsService data fetching methods."""

    @patch('yfinance.Ticker')
    def test_get_earnings_data_returns_earnings_data(self, mock_ticker):
        """FRIS-10: get_earnings_data returns EarningsData with EPS, revenue, date."""
        # Setup mock
        mock_info = MagicMock()
        mock_info.get.side_effect = lambda k: {
            "earningsTimestamp": 1704067200,
            "epsTrailingTwelveMonths": 5.5,
            "epsForward": 6.0,
            "totalRevenue": 394e9,
        }.get(k)
        mock_ticker.return_value.info = mock_info

        service = EarningsService()
        result = service.get_earnings_data("AAPL")

        assert isinstance(result, EarningsData)
        assert result.ticker == "AAPL"
        assert result.eps_current == 5.5
        assert result.eps_forward == 6.0
        assert result.revenue == 394e9
        assert result.earnings_date is not None
        assert result.data_source == "yfinance"

    @patch('yfinance.Ticker')
    def test_get_earnings_data_handles_missing_fields(self, mock_ticker):
        """FRIS-13: Missing fields return None, not exception."""
        mock_info = MagicMock()
        mock_info.get.return_value = None
        mock_ticker.return_value.info = mock_info

        service = EarningsService()
        result = service.get_earnings_data("INVALID")

        assert isinstance(result, EarningsData)
        assert result.eps_current is None
        assert result.eps_forward is None
        assert result.earnings_date is None

    @patch('yfinance.Ticker')
    def test_get_company_overview(self, mock_ticker):
        """FRIS-11: get_company_overview returns dict with market cap, P/E, P/B, price."""
        mock_info = MagicMock()
        mock_info.get.side_effect = lambda k: {
            "marketCap": 3000e9,
            "regularMarketPrice": 180.0,
            "trailingPE": 30.0,
            "priceToBook": 50.0,
            "longBusinessSummary": "Apple Inc. designs products.",
            "forwardPE": 25.0,
            "epsTrailingTwelveMonths": 5.5,
            "epsForward": 6.0,
        }.get(k)
        mock_ticker.return_value.info = mock_info

        service = EarningsService()
        result = service.get_company_overview("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["market_cap"] == 3000e9
        assert result["current_price"] == 180.0
        assert result["pe_ratio"] == 30.0
        assert result["pb_ratio"] == 50.0
        assert result["description"] == "Apple Inc. designs products."

    @patch('yfinance.Ticker')
    def test_get_earnings_guidance_returns_forward_eps(self, mock_ticker):
        """FRIS-12: get_earnings_guidance returns forward EPS."""
        mock_info = MagicMock()
        mock_info.get.return_value = 6.0
        mock_ticker.return_value.info = mock_info

        service = EarningsService()
        result = service.get_earnings_guidance("AAPL")

        assert result == 6.0

    @patch('yfinance.Ticker')
    def test_get_earnings_guidance_returns_none_when_missing(self, mock_ticker):
        """FRIS-12: Returns None when forward EPS not available."""
        mock_info = MagicMock()
        mock_info.get.return_value = None
        mock_ticker.return_value.info = mock_info

        service = EarningsService()
        result = service.get_earnings_guidance("PRE")

        assert result is None

    @patch('yfinance.Ticker')
    def test_get_quarterly_data_returns_quarterly_data(self, mock_ticker):
        """FRIS-14: get_quarterly_data returns QuarterlyData for Q1-Q4."""
        # Setup mock quarterly_financials
        mock_qf = MagicMock()
        mock_qf.empty = False
        mock_qf.loc = {}
        mock_ticker.return_value.quarterly_financials = mock_qf

        service = EarningsService()
        result = service.get_quarterly_data("AAPL", "Q1", 2024)

        assert isinstance(result, QuarterlyData)
        assert result.ticker == "AAPL"
        assert result.quarter == "Q1"
        assert result.year == 2024
        assert result.data_source == "yfinance"

    def test_quarterly_data_ticker_uppercase(self):
        """Ticker is normalized to uppercase."""
        service = EarningsService()
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.quarterly_financials = MagicMock(empty=True)
            result = service.get_quarterly_data("aapl", "Q2", 2024)
            assert result.ticker == "AAPL"

    def test_earnings_data_ticker_uppercase(self):
        """Ticker is normalized to uppercase."""
        service = EarningsService()
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.info = MagicMock()
            mock_ticker.return_value.info.get.return_value = None
            result = service.get_earnings_data("nvda")
            assert result.ticker == "NVDA"

    def test_fetched_at_timestamp_present(self):
        """FRIS-25: fetched_at timestamp is included."""
        service = EarningsService()
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.info = MagicMock()
            mock_ticker.return_value.info.get.return_value = None
            result = service.get_earnings_data("AAPL")
            assert result.fetched_at is not None
            # Should be valid ISO format
            datetime.fromisoformat(result.fetched_at)


class TestEarningsServiceYoY:
    """Test YoY calculation logic."""

    def test_calculate_yoy_positive(self):
        """YoY calculation for positive growth."""
        service = EarningsService()
        result = service._calculate_yoy(110, 100)
        assert result == 10.0

    def test_calculate_yoy_negative(self):
        """YoY calculation for negative growth."""
        service = EarningsService()
        result = service._calculate_yoy(90, 100)
        assert result == -10.0

    def test_calculate_yoy_zero_prior(self):
        """YoY calculation with zero prior year returns None."""
        service = EarningsService()
        result = service._calculate_yoy(100, 0)
        assert result is None

    def test_calculate_yoy_none_prior(self):
        """YoY calculation with None prior year returns None."""
        service = EarningsService()
        result = service._calculate_yoy(100, None)
        assert result is None
