"""LLM client for FRIS summarization.

FRIS-18: LLM prompts include financial context to reduce hallucination
Supports OpenAI GPT-4o-mini and Anthropic Claude.
"""

import os
import json
from enum import Enum
from typing import Optional

from src.fris.models import StockInfo, EarningsData, KeyMetricsDetail


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """Client for LLM API calls with structured output support.

    Default: OpenAI GPT-4o-mini (cost efficient)
    Alternative: Anthropic Claude
    """

    SYSTEM_PROMPT = """You are a financial analyst assistant. Generate concise, accurate business summaries based on the provided financial data.

IMPORTANT RULES:
1. Only state facts that appear in the provided data
2. Always cite specific numbers from the data (e.g., "revenue of $394B" not "high revenue")
3. If data is unavailable for a claim, state "Data not available"
4. Do not speculate or add information not in the data
5. Structure your response as valid JSON in the format specified

Data source: Yahoo Finance (yfinance)
"""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None
    ):
        """Initialize LLM client.

        Args:
            provider: LLM provider (OPENAI or ANTHROPIC)
            model: Model name (e.g., "gpt-4o-mini" for OpenAI, "claude-sonnet-4-20250514" for Anthropic)
            api_key: API key. Reads from environment if not provided.
        """
        self.provider = provider
        self.model = model
        self._api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or None (for testing)."""
        if self.provider == LLMProvider.OPENAI:
            return os.environ.get("OPENAI_API_KEY")
        elif self.provider == LLMProvider.ANTHROPIC:
            return os.environ.get("ANTHROPIC_API_KEY")
        return None

    def _build_financial_context(
        self,
        stock_info: StockInfo,
        earnings_data: Optional[EarningsData] = None,
        overview: Optional[dict] = None
    ) -> str:
        """Build rich context string with financial data.

        This context is injected into prompts to reduce hallucination (FRIS-18).

        Args:
            stock_info: Basic stock information
            earnings_data: Earnings data from EarningsService
            overview: Company overview dict from EarningsService

        Returns:
            Formatted context string with all available financial data
        """
        context_parts = []

        # Company basic info
        context_parts.append(f"Company: {stock_info.company_name} ({stock_info.ticker})")
        context_parts.append(f"Sector: {stock_info.sector or 'N/A'}")
        context_parts.append(f"Industry: {stock_info.industry or 'N/A'}")

        if stock_info.description:
            desc = stock_info.description[:500] + "..." if len(stock_info.description) > 500 else stock_info.description
            context_parts.append(f"Business Description: {desc}")

        # Market data
        if overview:
            if overview.get("market_cap"):
                context_parts.append(f"Market Cap: ${overview['market_cap']:,.0f}")
            if overview.get("current_price"):
                context_parts.append(f"Current Price: ${overview['current_price']:.2f}")
            if overview.get("pe_ratio"):
                context_parts.append(f"P/E Ratio: {overview['pe_ratio']:.2f}")
            if overview.get("pb_ratio"):
                context_parts.append(f"P/B Ratio: {overview['pb_ratio']:.2f}")

        # Earnings data
        if earnings_data:
            context_parts.append(f"Data Source: {earnings_data.data_source}")
            context_parts.append(f"Data Fetched At: {earnings_data.fetched_at or 'N/A'}")

            if earnings_data.eps_current:
                context_parts.append(f"Trailing EPS (TTM): ${earnings_data.eps_current:.2f}")
            if earnings_data.eps_forward:
                context_parts.append(f"Forward EPS: ${earnings_data.eps_forward:.2f}")
            if earnings_data.revenue:
                context_parts.append(f"Revenue: ${earnings_data.revenue:,.0f}")
            if earnings_data.revenue_yoy_change is not None:
                context_parts.append(f"Revenue YoY Change: {earnings_data.revenue_yoy_change:.1f}%")
            if earnings_data.earnings_date:
                context_parts.append(f"Last Earnings Date: {earnings_data.earnings_date}")

        return "\n".join(context_parts)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        structured_output: bool = True
    ) -> str:
        """Generate text from LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt. Uses default if not provided.
            structured_output: If True, request JSON output

        Returns:
            Generated text from LLM

        Raises:
            LLMError: If API call fails
        """
        if self.provider == LLMProvider.OPENAI:
            return self._generate_openai(prompt, system_prompt or self.SYSTEM_PROMPT, structured_output)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, system_prompt or self.SYSTEM_PROMPT, structured_output)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: str,
        structured_output: bool
    ) -> str:
        """Generate using OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise LLMError("openai package not installed. Run: pip install openai")

        if not self._api_key:
            raise LLMError("OPENAI_API_KEY not set in environment")

        client = OpenAI(api_key=self._api_key)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # Lower temp for more consistent output
        }

        if structured_output:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: str,
        structured_output: bool
    ) -> str:
        """Generate using Anthropic API."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise LLMError("anthropic package not installed. Run: pip install anthropic")

        if not self._api_key:
            raise LLMError("ANTHROPIC_API_KEY not set in environment")

        client = Anthropic(api_key=self._api_key)

        # Anthropic uses system parameter
        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
            "system": system_prompt,
        }

        if structured_output:
            # Anthropic supports JSON mode
            kwargs["thinking"] = {"type": "disabled"}

        response = client.messages.create(**kwargs)
        return response.content[0].text


class LLMError(Exception):
    """LLM-related errors."""
    pass
