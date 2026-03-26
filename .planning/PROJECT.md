# Financial Report Interpretation System (FRIS)

## What This Is

A system that takes a **topic + time period** and returns **individual earnings report summaries** for all topic-related US stocks. Users can filter by market cap, PE, PB, and price to narrow results.

## Core Value

**Fast, structured business intelligence from public financial data.** Quickly understand what a company does, how it performs, who it competes with, and what risks it faces — without reading raw SEC filings.

## Target Users

- Individual investors researching US stocks
- Financial analysts doing sector/thematic research
- Anyone wanting plain-English business summaries from public filings

---

## Requirements

### Validated

- ✓ **Topic Search** — TopicClassifier maps free-text topics to GICS industries with confidence scoring — v1.0
- ✓ **Stock Filtering** — StockFilterService with market cap/P/E/P/B/price AND logic filters — v1.0
- ✓ **Earnings Data** — EarningsService fetches EPS, revenue, guidance, quarterly data — v1.0
- ✓ **LLM Summaries** — SummarizationService generates structured JSON summaries via GPT-4o-mini/Claude — v1.0
- ✓ **Data Source** — yfinance primary, FMP fallback, dual TTL cache — v1.0
- ✓ **Pipeline** — FRISPipeline orchestrator, FastAPI + uvicorn, Docker — v1.0

### Active

**Potential v1.1 improvements (not yet planned):**
- [ ] Estimate vs actual earnings beat/miss analysis
- [ ] Peer benchmarking (vs sector median)
- [ ] Interactive re-filtering without re-fetch
- [ ] Earnings call transcript summarization
- [ ] Trend analysis (quarter-over-quarter)

### Out of Scope

| Item | Reason |
|------|--------|
| Raw PDF/HTML filing parsing | Complexity too high for MVP; structured data sufficient |
| Non-US markets (A-share, HK stocks) | API complexity and GICS mapping would double scope |
| Real-time price streaming | Not relevant to earnings analysis; adds API cost |
| Trading signals/recommendations | Regulatory risk; outside product scope |
| Portfolio tracking | Separate product category |
| Technical analysis/charts | Different use case; fundamental analysis only |
| Social sentiment from Twitter/Reddit | Unreliable, high noise |

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Topic→Industry matching via GICS | Standard classification, maps well to financial data | ✓ Confirmed — works well for MVP |
| Individual summaries per stock | Better for comparison and focused analysis | ✓ Confirmed — enables granular analysis |
| Filter: market cap, PE, PB, price | Most common screening criteria for retail investors | ✓ Confirmed — sufficient for MVP |
| Structured data only (no raw PDF parsing) | Fastest path to MVP, reliable data quality | ✓ Confirmed |
| Dual TTL cache (1hr prices, 24hr fundamentals) | Different data freshness requirements | ✓ Confirmed — works well |
| yfinance primary, FMP fallback | yfinance ~99% coverage, FMP fills gaps | ✓ Confirmed |
| GPT-4o-mini default, Claude alternative | Cost efficiency + flexibility | ✓ Confirmed |
| Substring matching for keywords (no fuzzy) | MVP scope, good enough accuracy | ✓ Confirmed |

---

## Context

**Shipped:** v1.0 MVP (2026-03-26) — all 25 requirements delivered
**Code:** ~3100 LOC Python
**Stack:** Python, FastAPI, uvicorn, Docker, yfinance, GPT-4o-mini/Claude
**Repository:** https://github.com/Zoettt/tradingStrategy_reading
**Git tag:** v1.0

---

*Last updated: 2026-03-26 after v1.0 milestone*
