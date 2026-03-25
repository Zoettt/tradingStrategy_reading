"""Tests for SummarizationService (FRIS-15 to FRIS-19, FRIS-23 to FRIS-25)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.fris.models import StockInfo, StockSummary, KeyMetricsDetail, EarningsData
from src.fris.summarization_service import SummarizationService
from src.fris.llm_client import LLMClient, LLMProvider


class TestStockSummary:
    """Test StockSummary model."""

    def test_stock_summary_has_required_fields(self):
        """FRIS-17, FRIS-24: StockSummary has ticker, company_name, industry, period, key_metrics."""
        metrics = KeyMetricsDetail(eps_current=5.5)
        summary = StockSummary(
            ticker="AAPL",
            company_name="Apple Inc.",
            industry="Technology",
            reporting_period="Q4 2024",
            summary_text="Test summary",
            key_metrics=metrics,
            data_sources=["yfinance"],
            generated_at="2024-01-01T00:00:00",
            model_used="gpt-4o-mini"
        )

        assert summary.ticker == "AAPL"
        assert summary.company_name == "Apple Inc."
        assert summary.industry == "Technology"
        assert summary.reporting_period == "Q4 2024"
        assert summary.key_metrics.eps_current == 5.5

    def test_stock_summary_to_dict(self):
        """FRIS-23: to_dict() returns serializable dict."""
        metrics = KeyMetricsDetail(revenue=394e9)
        summary = StockSummary(
            ticker="AAPL",
            company_name="Apple Inc.",
            industry="Technology",
            reporting_period="Q4 2024",
            summary_text="Test",
            key_metrics=metrics,
            data_sources=["yfinance"],
            generated_at="2024-01-01T00:00:00",
            model_used="gpt-4o-mini"
        )

        result = summary.to_dict()

        assert isinstance(result, dict)
        assert result["ticker"] == "AAPL"
        assert result["key_metrics"]["revenue"] == 394e9


class TestLLMClient:
    """Test LLMClient."""

    def test_build_financial_context(self):
        """FRIS-18: Context includes all financial data to reduce hallucination."""
        client = LLMClient(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        stock = StockInfo(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000e9,
            pe_ratio=30.0,
        )
        earnings = EarningsData(
            ticker="AAPL",
            eps_current=5.5,
            eps_forward=6.0,
            revenue=394e9,
            revenue_yoy_change=3.2,
            data_source="yfinance",
            fetched_at="2024-01-01T00:00:00"
        )

        context = client._build_financial_context(stock, earnings)

        assert "Apple Inc." in context
        assert "AAPL" in context
        assert "Technology" in context
        assert "$394" in context or "394" in context
        assert "3.2%" in context or "3.2" in context

    def test_llm_client_init(self):
        """LLMClient initializes with correct defaults."""
        client = LLMClient()

        assert client.provider == LLMProvider.OPENAI
        assert client.model == "gpt-4o-mini"

    def test_llm_client_custom_model(self):
        """Custom provider and model can be set."""
        client = LLMClient(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-4-20250514")

        assert client.provider == LLMProvider.ANTHROPIC
        assert client.model == "claude-sonnet-4-20250514"


class TestSummarizationService:
    """Test SummarizationService."""

    def test_determine_reporting_period(self):
        """Reporting period determined from earnings date."""
        service = SummarizationService()
        earnings = EarningsData(
            ticker="AAPL",
            earnings_date="2024-01-15",
            data_source="yfinance"
        )

        period = service._determine_reporting_period(earnings)

        assert "Q1" in period
        assert "2024" in period

    def test_determine_reporting_period_default(self):
        """Default period when no earnings date."""
        service = SummarizationService()
        period = service._determine_reporting_period(None)

        now = datetime.now()
        assert str(now.year) in period

    @patch.object(LLMClient, 'generate')
    def test_summarize_returns_stock_summary(self, mock_generate):
        """FRIS-15, FRIS-17: summarize() returns StockSummary with all fields."""
        mock_generate.return_value = '{"business_model": "Test", "recent_performance": "Test", "competitive_landscape": "Test", "risk_factors": "Test"}'

        service = SummarizationService()
        stock = StockInfo(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000e9,
        )

        summary = service.summarize(stock)

        assert isinstance(summary, StockSummary)
        assert summary.ticker == "AAPL"
        assert summary.company_name == "Apple Inc."
        assert summary.model_used == "gpt-4o-mini"
        assert "yfinance" in summary.data_sources

    @patch.object(LLMClient, 'generate')
    def test_summarize_includes_key_metrics(self, mock_generate):
        """FRIS-24: key_metrics included in summary."""
        mock_generate.return_value = '{"business_model": "Test", "recent_performance": "Test", "competitive_landscape": "Test", "risk_factors": "Test"}'

        service = SummarizationService()
        stock = StockInfo(
            ticker="AAPL",
            company_name="Apple Inc.",
            industry="Tech",
            market_cap=3000e9,
        )

        summary = service.summarize(stock)

        assert summary.key_metrics is not None
        assert hasattr(summary.key_metrics, 'market_cap')

    @patch.object(LLMClient, 'generate')
    def test_summarize_batch_returns_list(self, mock_generate):
        """FRIS-16: summarize_batch() returns list of StockSummary (separate documents)."""
        mock_generate.return_value = '{"business_model": "Test", "recent_performance": "Test", "competitive_landscape": "Test", "risk_factors": "Test"}'

        service = SummarizationService()
        stocks = [
            StockInfo(ticker="AAPL", company_name="Apple"),
            StockInfo(ticker="MSFT", company_name="Microsoft"),
        ]

        summaries = service.summarize_batch(stocks)

        assert len(summaries) == 2
        assert all(isinstance(s, StockSummary) for s in summaries)

    @patch.object(LLMClient, 'generate')
    def test_summarize_cites_data_sources(self, mock_generate):
        """FRIS-19: data_sources cites yfinance."""
        mock_generate.return_value = '{"business_model": "Test", "recent_performance": "Test", "competitive_landscape": "Test", "risk_factors": "Test"}'

        service = SummarizationService()
        stock = StockInfo(ticker="AAPL", company_name="Apple Inc.")

        summary = service.summarize(stock)

        assert "yfinance" in summary.data_sources

    @patch.object(LLMClient, 'generate')
    def test_summarize_has_generated_at(self, mock_generate):
        """FRIS-25: generated_at timestamp present."""
        mock_generate.return_value = '{"business_model": "Test", "recent_performance": "Test", "competitive_landscape": "Test", "risk_factors": "Test"}'

        service = SummarizationService()
        stock = StockInfo(ticker="AAPL", company_name="Apple Inc.")

        summary = service.summarize(stock)

        assert summary.generated_at is not None
        # Verify ISO format
        datetime.fromisoformat(summary.generated_at)

    @patch.object(LLMClient, 'generate')
    def test_summarize_error_handling(self, mock_generate):
        """Error handling when LLM fails."""
        from src.fris.llm_client import LLMError
        mock_generate.side_effect = LLMError("API error")

        service = SummarizationService()
        stock = StockInfo(ticker="AAPL", company_name="Apple Inc.")

        summary = service.summarize(stock)

        # Should still return StockSummary with error message
        assert isinstance(summary, StockSummary)
        assert "failed" in summary.summary_text.lower()
