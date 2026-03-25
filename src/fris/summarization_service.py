"""Summarization service for generating LLM-powered business summaries.

FRIS-15: Generate structured summary covering business model, performance, competitive landscape, risks
FRIS-16: Each summary is a separate document (JSON)
FRIS-17: Includes company name, ticker, industry, period, key metrics
FRIS-18: LLM prompts include financial context to reduce hallucination
FRIS-19: Summaries cite data sources
FRIS-23: Return results as structured JSON
FRIS-24: Each result includes ticker, company_name, industry, period, summary_text, key_metrics
FRIS-25: Include data freshness timestamp
"""

from datetime import datetime
from typing import Optional

from src.fris.models import StockInfo, StockSummary, KeyMetricsDetail, EarningsData
from src.fris.llm_client import LLMClient, LLMProvider, LLMError
from src.fris.earnings_service import EarningsService


class SummarizationService:
    """Service for generating LLM-powered business summaries.

    Takes StockInfo (from Phase 1-2) and generates a structured StockSummary.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        earnings_service: Optional[EarningsService] = None
    ):
        """Initialize SummarizationService.

        Args:
            llm_client: LLMClient instance. Creates GPT-4o-mini client if None.
            earnings_service: EarningsService instance. Creates new if None.
        """
        self._llm = llm_client or LLMClient(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        self._earnings = earnings_service or EarningsService()

    def _determine_reporting_period(self, earnings_data: Optional[EarningsData]) -> str:
        """Determine reporting period from earnings data.

        Args:
            earnings_data: EarningsData instance

        Returns:
            Period string like "Q4 2024" or "FY 2024"
        """
        if earnings_data and earnings_data.earnings_date:
            try:
                dt = datetime.strptime(earnings_data.earnings_date, "%Y-%m-%d")
                month = dt.month
                year = dt.year

                # Determine quarter
                if month <= 3:
                    quarter = "Q1"
                elif month <= 6:
                    quarter = "Q2"
                elif month <= 9:
                    quarter = "Q3"
                else:
                    quarter = "Q4"

                return f"{quarter} {year}"
            except ValueError:
                pass

        # Default to current quarter
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"Q{quarter} {now.year}"

    def _build_summary_prompt(
        self,
        company_name: str,
        industry: str,
        financial_context: str
    ) -> str:
        """Build prompt for LLM to generate business summary.

        Args:
            company_name: Company name
            industry: Industry
            financial_context: Pre-formatted financial data context

        Returns:
            Prompt string for LLM
        """
        return f"""Based on the following financial data for {company_name} ({industry}):

{financial_context}

Generate a structured JSON business summary with the following sections:
{{
  "business_model": "Brief description of how the company makes money",
  "recent_performance": "Summary of recent financial performance including revenue trends and profitability",
  "competitive_landscape": "Key competitors and company's market position",
  "risk_factors": "Main business and financial risks"
}}

Respond ONLY with valid JSON. Do not include any other text."""

    def summarize(self, stock_info: StockInfo) -> StockSummary:
        """Generate business summary for a single stock.

        Args:
            stock_info: StockInfo from Phase 1-2 pipeline

        Returns:
            StockSummary with business intelligence
        """
        ticker = stock_info.ticker.upper()

        # Fetch earnings data
        earnings_data = None
        company_overview = None
        try:
            earnings_data = self._earnings.get_earnings_data(ticker)
            company_overview = self._earnings.get_company_overview(ticker)
        except Exception:
            pass

        # Build financial context for LLM
        financial_context = self._llm._build_financial_context(
            stock_info, earnings_data, company_overview
        )

        # Determine reporting period
        reporting_period = self._determine_reporting_period(earnings_data)

        # Generate summary via LLM
        summary_text = ""
        try:
            prompt = self._build_summary_prompt(
                stock_info.company_name,
                stock_info.industry or "N/A",
                financial_context
            )
            llm_response = self._llm.generate(prompt, structured_output=True)

            # Parse JSON response
            import json
            try:
                summary_json = json.loads(llm_response)
                # Combine sections into single summary text
                sections = []
                for key in ["business_model", "recent_performance", "competitive_landscape", "risk_factors"]:
                    if key in summary_json:
                        sections.append(f"{key.replace('_', ' ').title()}: {summary_json[key]}")
                summary_text = "\n\n".join(sections)
            except json.JSONDecodeError:
                summary_text = llm_response

        except LLMError as e:
            summary_text = f"Summary generation failed: {str(e)}"

        # Build key metrics
        key_metrics = KeyMetricsDetail(
            eps_current=earnings_data.eps_current if earnings_data else None,
            eps_forward=earnings_data.eps_forward if earnings_data else None,
            revenue=earnings_data.revenue if earnings_data else None,
            revenue_yoy_change=earnings_data.revenue_yoy_change if earnings_data else None,
            market_cap=company_overview.get("market_cap") if company_overview else stock_info.market_cap,
            pe_ratio=company_overview.get("pe_ratio") if company_overview else stock_info.pe_ratio,
            pb_ratio=company_overview.get("pb_ratio") if company_overview else stock_info.pb_ratio,
            current_price=company_overview.get("current_price") if company_overview else stock_info.current_price,
        )

        # Build data sources list
        data_sources = ["yfinance"]
        if earnings_data and earnings_data.data_source:
            if earnings_data.data_source not in data_sources:
                data_sources.append(earnings_data.data_source)

        return StockSummary(
            ticker=ticker,
            company_name=stock_info.company_name,
            industry=stock_info.industry or "N/A",
            reporting_period=reporting_period,
            summary_text=summary_text,
            key_metrics=key_metrics,
            data_sources=data_sources,
            generated_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            model_used=self._llm.model,
        )

    def summarize_batch(self, stocks: list[StockInfo]) -> list[StockSummary]:
        """Generate business summaries for multiple stocks.

        Args:
            stocks: List of StockInfo

        Returns:
            List of StockSummary (one per stock, FRIS-16)
        """
        return [self.summarize(stock) for stock in stocks]
