"""FRIS Pipeline - End-to-end orchestration of all FRIS services.

Integrates Phase 1-3 services into a single pipeline:
1. TopicSearchService.search(topic) -> stocks
2. StockFilterService.apply_filters(criteria) -> filtered stocks
3. SummarizationService.summarize(stock) -> StockSummary
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.fris.service import TopicSearchService, TimePeriod
from src.fris.filter_service import StockFilterService, FilterCriteria
from src.fris.summarization_service import SummarizationService
from src.fris.models import StockSummary


logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of running the FRIS pipeline.

    Attributes:
        summaries: List of successful StockSummary results
        failed_tickers: List of tickers that failed with error messages
        total_count: Total stocks processed
        success_count: Number of successful summaries
        error_count: Number of failed stocks
    """
    summaries: list[StockSummary] = field(default_factory=list)
    failed_tickers: list[dict] = field(default_factory=list)
    total_count: int = 0
    success_count: int = 0
    error_count: int = 0


class FRISPipeline:
    """End-to-end FRIS pipeline orchestrator.

    Combines TopicSearchService, StockFilterService, and SummarizationService
    into a single run() method. Handles partial failures gracefully.

    Success criteria:
    - Pipeline executes end-to-end from topic input to StockSummary output
    - Single stock failure does not stop pipeline (other stocks still processed)
    - Data freshness via generated_at/fetched_at timestamps
    """

    def __init__(
        self,
        topic_service: Optional[TopicSearchService] = None,
        filter_service: Optional[StockFilterService] = None,
        summarization_service: Optional[SummarizationService] = None
    ):
        """Initialize FRISPipeline with services.

        Args:
            topic_service: TopicSearchService instance. Creates new if None.
            filter_service: StockFilterService instance. Creates new if None.
            summarization_service: SummarizationService instance. Creates new if None.
        """
        self._topic_service = topic_service or TopicSearchService()
        self._filter_service = filter_service or StockFilterService()
        self._summarization_service = summarization_service or SummarizationService()

    def run(
        self,
        topic: str,
        time_period: Optional[TimePeriod] = None,
        criteria: Optional[FilterCriteria] = None,
        limit_per_industry: int = 10
    ) -> PipelineResult:
        """Run the full FRIS pipeline.

        Pipeline steps:
        1. Search for stocks by topic (TopicSearchService)
        2. Filter stocks by criteria (StockFilterService)
        3. Generate summaries for each stock (SummarizationService)

        Partial failure handling: If a single stock fails to summarize,
        the error is logged and the pipeline continues with other stocks.

        Args:
            topic: Search topic (e.g., "AI chips", "electric vehicles")
            time_period: Time period for earnings query (optional)
            criteria: Filter criteria for filtering stocks (optional)
            limit_per_industry: Max stocks per industry in search

        Returns:
            PipelineResult with summaries, failed_tickers, and counts
        """
        result = PipelineResult()

        # Step 1: Search for stocks by topic
        search_result = self._topic_service.search(
            topic=topic,
            time_period=time_period,
            limit_per_industry=limit_per_industry
        )

        if not search_result.stocks:
            logger.info(f"No stocks found for topic: {topic}")
            return result

        # Step 2: Filter stocks if criteria provided
        stocks_to_process = search_result.stocks
        if criteria:
            filter_result = self._filter_service.apply_filters(criteria, stocks_to_process)
            stocks_to_process = filter_result.filtered_stocks
            logger.info(f"Filtered {filter_result.total_count} stocks to {filter_result.filtered_count}")

        if not stocks_to_process:
            logger.info("No stocks passed filters")
            return result

        result.total_count = len(stocks_to_process)

        # Step 3: Generate summaries for each stock
        for stock in stocks_to_process:
            try:
                summary = self._summarization_service.summarize(stock)
                result.summaries.append(summary)
                result.success_count += 1
            except Exception as e:
                logger.warning(f"Failed to summarize {stock.ticker}: {str(e)}")
                result.failed_tickers.append({
                    "ticker": stock.ticker,
                    "error": str(e)
                })
                result.error_count += 1

        logger.info(
            f"Pipeline complete: {result.success_count} succeeded, "
            f"{result.error_count} failed out of {result.total_count}"
        )

        return result

    def run_batch(
        self,
        topic: str,
        time_period: Optional[TimePeriod] = None,
        criteria_list: Optional[list[FilterCriteria]] = None
    ) -> list[PipelineResult]:
        """Run pipeline with multiple filter criteria.

        Args:
            topic: Search topic
            time_period: Time period for earnings query
            criteria_list: List of FilterCriteria to apply

        Returns:
            List of PipelineResult, one per criteria
        """
        if not criteria_list:
            # If no criteria list, run once with None
            return [self.run(topic, time_period, None)]

        results = []
        for criteria in criteria_list:
            result = self.run(topic, time_period, criteria)
            results.append(result)

        return results
