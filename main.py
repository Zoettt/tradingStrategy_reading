"""FRIS FastAPI Application.

Entry point for the FRIS API service.
Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
"""

from typing import Optional
from dataclasses import dataclass

from fastapi import FastAPI
from pydantic import BaseModel

from src.fris.pipeline import FRISPipeline, PipelineResult
from src.fris.service import TimePeriod
from src.fris.filter_service import FilterCriteria


app = FastAPI(
    title="FRIS API",
    description="Financial Report Interpretation System - AI-powered business summaries",
    version="1.0.0"
)


# Request/Response models
class TimePeriodRequest(BaseModel):
    """Time period specification for earnings query."""
    period_type: str  # "quarter" or "date_range"
    quarter: Optional[int] = None
    year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class FilterCriteriaRequest(BaseModel):
    """Filter criteria for stock screening."""
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    market_cap_category: Optional[str] = None
    pe_ratio_min: Optional[float] = None
    pe_ratio_max: Optional[float] = None
    pb_ratio_min: Optional[float] = None
    pb_ratio_max: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None


class AnalyzeRequest(BaseModel):
    """Request body for /analyze endpoint."""
    topic: str
    time_period: Optional[TimePeriodRequest] = None
    criteria: Optional[FilterCriteriaRequest] = None
    limit_per_industry: int = 10


class AnalyzeResponse(BaseModel):
    """Response from /analyze endpoint."""
    summaries: list[dict]
    failed_tickers: list[dict]
    total_count: int
    success_count: int
    error_count: int


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "FRIS"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run FRIS pipeline to analyze stocks by topic.

    Takes a topic (e.g., "AI chips"), searches for related stocks,
    optionally filters them, and generates AI-powered business summaries.

    Args:
        request: AnalyzeRequest with topic, optional time_period and criteria

    Returns:
        AnalyzeResponse with summaries, failed_tickers, and counts
    """
    # Convert request to pipeline inputs
    time_period = None
    if request.time_period:
        time_period = TimePeriod(
            period_type=request.time_period.period_type,
            quarter=request.time_period.quarter,
            year=request.time_period.year,
            start_date=request.time_period.start_date,
            end_date=request.time_period.end_date
        )

    criteria = None
    if request.criteria:
        criteria = FilterCriteria(
            market_cap_min=request.criteria.market_cap_min,
            market_cap_max=request.criteria.market_cap_max,
            market_cap_category=request.criteria.market_cap_category,
            pe_ratio_min=request.criteria.pe_ratio_min,
            pe_ratio_max=request.criteria.pe_ratio_max,
            pb_ratio_min=request.criteria.pb_ratio_min,
            pb_ratio_max=request.criteria.pb_ratio_max,
            price_min=request.criteria.price_min,
            price_max=request.criteria.price_max
        )

    # Run pipeline
    pipeline = FRISPipeline()
    result = pipeline.run(
        topic=request.topic,
        time_period=time_period,
        criteria=criteria,
        limit_per_industry=request.limit_per_industry
    )

    # Convert to response
    return AnalyzeResponse(
        summaries=[s.to_dict() for s in result.summaries],
        failed_tickers=result.failed_tickers,
        total_count=result.total_count,
        success_count=result.success_count,
        error_count=result.error_count
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
