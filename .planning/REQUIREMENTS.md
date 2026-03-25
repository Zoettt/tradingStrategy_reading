# Requirements: Financial Report Interpretation System (FRIS)

**Project:** FRIS (Financial Report Interpretation System)
**Version:** 1.0
**Date:** 2026-03-25

---

## v1 Requirements

### Topic Search (FRIS-01)

- [x] **FRIS-01**: User can input a topic (free text, e.g., "AI chips") and time period (quarter/date range)
- [x] **FRIS-02**: System matches topic to GICS sectors/industries using keyword mapping table
- [ ] **FRIS-03**: System returns list of relevant US stock tickers with company names and industries

### Stock Filtering (FRIS-02)

- [ ] **FRIS-04**: Filter by market cap (min/max in USD, or predefined: large/mid/small cap)
- [ ] **FRIS-05**: Filter by P/E ratio (min/max, handle negative earnings as N/A)
- [ ] **FRIS-06**: Filter by P/B ratio (min/max, handle negative book value as N/A)
- [ ] **FRIS-07**: Filter by stock price (min/max in USD)
- [ ] **FRIS-08**: Filters are combinable (AND logic)
- [ ] **FRIS-09**: System returns filtered stock count before full data fetch

### Earnings Data Fetching (FRIS-03)

- [ ] **FRIS-10**: Fetch latest earnings data for each filtered stock (EPS, revenue, earnings date)
- [ ] **FRIS-11**: Fetch company overview data (market cap, P/E, P/B, price, description)
- [ ] **FRIS-12**: Fetch earnings guidance (forward EPS if available)
- [x] **FRIS-13**: Handle missing/incomplete data gracefully (flag as N/A, continue processing)
- [ ] **FRIS-14**: Support quarterly data (Q1, Q2, Q3, Q4) with year

### Business Summary Generation (FRIS-04)

- [ ] **FRIS-15**: Generate structured summary per stock covering:
  - Business model overview (how the company makes money)
  - Recent performance (revenue, profit, YoY growth)
  - Competitive landscape (key competitors, market position)
  - Risk factors (main business risks)
- [ ] **FRIS-16**: Each summary is a separate document (JSON/markdown format)
- [ ] **FRIS-17**: Summary includes: company name, ticker, industry, reporting period, key metrics
- [ ] **FRIS-18**: LLM prompts include financial context to reduce hallucination
- [ ] **FRIS-19**: Summaries cite data sources (API provider)

### Data Source (FRIS-05)

- [ ] **FRIS-20**: Primary data source: Yahoo Finance via yfinance library (free, no API key required)
- [ ] **FRIS-21**: Fallback/supplementary: FMP API (if yfinance coverage gaps)
- [x] **FRIS-22**: Cache financial data locally to reduce API calls

### Output (FRIS-06)

- [ ] **FRIS-23**: Return results as structured JSON (one object per stock)
- [ ] **FRIS-24**: Each result includes: ticker, company_name, industry, period, summary_text, key_metrics
- [ ] **FRIS-25**: Include data freshness timestamp

---

## v2 Requirements (Deferred)

- [ ] Estimate vs actual beat/miss analysis
- [ ] Peer benchmarking (vs sector median)
- [ ] Interactive re-filtering without re-fetch
- [ ] Earnings call transcript summarization
- [ ] Trend analysis (quarter-over-quarter)

---

## Out of Scope

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

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRIS-01: User can input a topic and time period | Phase 1 | Pending |
| FRIS-02: System matches topic to GICS sectors/industries | Phase 1 | Pending |
| FRIS-03: System returns list of US stock tickers with names/industries | Phase 1 | Pending |
| FRIS-04: Filter by market cap | Phase 2 | Pending |
| FRIS-05: Filter by P/E ratio | Phase 2 | Pending |
| FRIS-06: Filter by P/B ratio | Phase 2 | Pending |
| FRIS-07: Filter by stock price | Phase 2 | Pending |
| FRIS-08: Filters are combinable (AND logic) | Phase 2 | Pending |
| FRIS-09: System returns filtered stock count before full fetch | Phase 2 | Pending |
| FRIS-10: Fetch latest earnings data (EPS, revenue, earnings date) | Phase 2 | Pending |
| FRIS-11: Fetch company overview data | Phase 2 | Pending |
| FRIS-12: Fetch earnings guidance (forward EPS) | Phase 2 | Pending |
| FRIS-13: Handle missing/incomplete data gracefully | Phase 1 | Pending |
| FRIS-14: Support quarterly data (Q1-Q4 with year) | Phase 2 | Pending |
| FRIS-15: Generate structured summary per stock | Phase 3 | Pending |
| FRIS-16: Each summary is a separate document (JSON/markdown) | Phase 3 | Pending |
| FRIS-17: Summary includes company name, ticker, industry, period, key metrics | Phase 3 | Pending |
| FRIS-18: LLM prompts include financial context to reduce hallucination | Phase 3 | Pending |
| FRIS-19: Summaries cite data sources | Phase 3 | Pending |
| FRIS-20: Primary data source Yahoo Finance via yfinance | Phase 1 | Pending |
| FRIS-21: Fallback/supplementary FMP API | Phase 1 | Pending |
| FRIS-22: Cache financial data locally | Phase 1 | Pending |
| FRIS-23: Return results as structured JSON | Phase 3 | Pending |
| FRIS-24: Result includes ticker, company_name, industry, period, summary_text, key_metrics | Phase 3 | Pending |
| FRIS-25: Include data freshness timestamp | Phase 3 | Pending |

---

## Notes

- **GICS Mapping:** Static keyword-to-GICS table (e.g., "AI chips" → "Semiconductors"). Need to build initial mapping from research.
- **Financial Data Coverage:** yfinance covers ~99% of US stocks. Coverage gaps expected for very small/micro cap stocks.
- **LLM Provider:** Default to OpenAI GPT-4o mini for cost efficiency. Support Anthropic Claude as alternative.
- **Rate Limits:** yfinance has no rate limit. FMP has 5 req/min on free tier — caching required.
