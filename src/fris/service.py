"""TopicSearchService - orchestrates topic classification and stock search.

Wires TopicClassifier and StockRepository together to implement
the core FRIS user flow: topic input -> GICS industries -> stock list.

FRIS-01: User inputs topic string and time period
FRIS-02: Topic matched to GICS industries via keyword mapping
FRIS-03: Returns stock tickers with company names and industries
"""

from dataclasses import dataclass
from typing import Optional

from src.fris.topic_classifier import TopicClassifier, IndustryMatch
from src.fris.stock_repository import StockRepository
from src.fris.models import StockSearchResult, StockInfo


@dataclass
class TimePeriod:
    """Time period specification for earnings query.

    Used to filter results by earnings period.
    Phase 1: Accepted but not yet used for filtering.
    """
    period_type: str  # "quarter" or "date_range"
    quarter: Optional[int] = None  # 1-4
    year: Optional[int] = None
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None

    @classmethod
    def current_quarter(cls) -> "TimePeriod":
        """Create TimePeriod for current quarter."""
        from datetime import datetime
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return cls(period_type="quarter", quarter=quarter, year=now.year)

    @classmethod
    def last_n_quarters(cls, n: int) -> "TimePeriod":
        """Create TimePeriod for last N quarters."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        now = datetime.now()
        # Calculate start of N quarters ago
        current_quarter_start = datetime(now.year, ((now.month - 1) // 3) * 3 + 1, 1)
        start_date = current_quarter_start - relativedelta(months=3 * (n - 1))
        return cls(
            period_type="date_range",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d")
        )


class TopicSearchService:
    """Main service for topic-based stock search.

    Orchestrates TopicClassifier and StockRepository to implement:
    1. User inputs topic (e.g., "AI chips") and time period
    2. TopicClassifier maps topic to GICS industries
    3. StockRepository finds stocks in those industries
    4. Returns combined StockSearchResult
    """

    def __init__(
        self,
        classifier: TopicClassifier | None = None,
        repository: StockRepository | None = None
    ):
        """
        Args:
            classifier: TopicClassifier instance. Creates new if None.
            repository: StockRepository instance. Creates new if None.
        """
        self._classifier = classifier or TopicClassifier()
        self._repository = repository or StockRepository()

    def search(
        self,
        topic: str,
        time_period: TimePeriod | None = None,
        limit_per_industry: int = 10
    ) -> StockSearchResult:
        """
        Search for stocks matching a topic.

        Args:
            topic: Free-text topic (e.g., "AI chips", "electric vehicles")
            time_period: Time period for earnings data (Phase 2+)
            limit_per_industry: Max stocks to return per industry

        Returns:
            StockSearchResult with matched stocks and metadata
        """
        # Validate topic
        if not topic or not topic.strip():
            return StockSearchResult(
                stocks=[],
                matched_industries=[],
                search_topic=topic,
                total_count=0
            )

        topic = topic.strip()

        # Classify topic into industries
        industry_matches = self._classifier.classify(topic)

        if not industry_matches:
            return StockSearchResult(
                stocks=[],
                matched_industries=[],
                search_topic=topic,
                total_count=0
            )

        # Get matched industry names
        matched_industries = [m.industry for m in industry_matches]

        # Search for stocks in each matched industry
        all_stocks: list[StockInfo] = []
        seen_tickers: set[str] = set()

        for industry in matched_industries:
            stocks = self._repository.search_by_industry(industry, limit=limit_per_industry)

            for stock in stocks:
                # Deduplicate by ticker
                if stock.ticker not in seen_tickers:
                    seen_tickers.add(stock.ticker)
                    all_stocks.append(stock)

        return StockSearchResult(
            stocks=all_stocks,
            matched_industries=matched_industries,
            search_topic=topic,
            total_count=len(all_stocks)
        )

    def search_single_industry(
        self,
        topic: str,
        industry: str,
        limit: int = 10
    ) -> StockSearchResult:
        """
        Search for stocks in a specific industry.

        Useful when user selects one industry from multiple matches.

        Args:
            topic: Original search topic
            industry: Specific industry to search
            limit: Max stocks to return

        Returns:
            StockSearchResult for the specific industry
        """
        stocks = self._repository.search_by_industry(industry, limit=limit)

        return StockSearchResult(
            stocks=stocks,
            matched_industries=[industry],
            search_topic=topic,
            total_count=len(stocks)
        )
