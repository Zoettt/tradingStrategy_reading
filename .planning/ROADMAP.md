# Roadmap: Financial Report Interpretation System (FRIS)

## Overview

A pipeline-based system that transforms a user topic query (e.g., "AI chips") plus a time period into structured earnings summaries for relevant US stocks. The system chains topic classification via GICS, stock screening by financial metrics, earnings data fetching from financial APIs, and LLM-powered summarization. Four phases deliver a production-ready MVP: Core Infrastructure, Filtering & Data Fetching, LLM Summarization & Output, and Integration & Polish.

## Phases

- [ ] **Phase 1: Core Infrastructure** - Topic search, GICS mapping, API client with caching
- [ ] **Phase 2: Filtering & Data Fetching** - Stock filtering, earnings data retrieval
- [ ] **Phase 3: LLM Summarization & Output** - Business summary generation, structured output
- [ ] **Phase 4: Integration & Polish** - Pipeline orchestration, deployment

## Phase Details

### Phase 1: Core Infrastructure
**Goal**: Users can input a topic and receive relevant US stock tickers with data access layer established
**Depends on**: Nothing (first phase)
**Requirements**: FRIS-01, FRIS-02, FRIS-03, FRIS-13, FRIS-20, FRIS-21, FRIS-22
**Success Criteria** (what must be TRUE):
  1. User can input a topic (free text) and time period (quarter/date range) and receive matching US stocks
  2. System matches topic to GICS sectors/industries via keyword mapping table and returns stock tickers with company names and industries
  3. System caches financial data locally (TTL: 1hr prices, 24hr fundamentals) to reduce API calls
  4. System handles missing/incomplete data gracefully (flags as N/A, continues processing)
  5. Primary data source is Yahoo Finance via yfinance; FMP available as fallback
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md -- FRIS foundation: models, exceptions, cache (FRIS-13, FRIS-22)
- [x] 01-02-PLAN.md -- TopicClassifier with GICS keyword mapping (FRIS-01, FRIS-02)
- [x] 01-03-PLAN.md -- StockRepository with yfinance/FMP (FRIS-03, FRIS-20, FRIS-21)
- [x] 01-04-PLAN.md -- TopicSearchService orchestration (FRIS-01, FRIS-02, FRIS-03)

### Phase 2: Filtering & Data Fetching
**Goal**: Users can filter stocks by financial metrics and retrieve earnings data
**Depends on**: Phase 1
**Requirements**: FRIS-04, FRIS-05, FRIS-06, FRIS-07, FRIS-08, FRIS-09, FRIS-10, FRIS-11, FRIS-12, FRIS-14
**Success Criteria** (what must be TRUE):
  1. User can filter by market cap (min/max or predefined large/mid/small cap)
  2. User can filter by P/E ratio (min/max, with N/A for negative earnings)
  3. User can filter by P/B ratio (min/max, with N/A for negative book value)
  4. User can filter by stock price (min/max in USD)
  5. User can combine filters with AND logic; system returns filtered count before full data fetch
  6. System fetches latest earnings data (EPS, revenue, earnings date) and company overview (market cap, P/E, P/B, price, description) for each filtered stock
  7. System fetches earnings guidance (forward EPS) when available and supports quarterly data (Q1-Q4 with year)
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md -- StockFilterService with market cap, P/E, P/B, price filters (FRIS-04 to FRIS-09)
- [x] 02-02-PLAN.md -- EarningsService for earnings data, overview, guidance (FRIS-10 to FRIS-12, FRIS-14)

### Phase 3: LLM Summarization & Output
**Goal**: Users receive structured business summaries in JSON format
**Depends on**: Phase 2
**Requirements**: FRIS-15, FRIS-16, FRIS-17, FRIS-18, FRIS-19, FRIS-23, FRIS-24, FRIS-25
**Success Criteria** (what must be TRUE):
  1. System generates structured summary per stock covering: business model overview, recent performance (revenue, profit, YoY growth), competitive landscape, risk factors
  2. Each summary is a separate document in JSON/markdown format containing company name, ticker, industry, reporting period, and key metrics
  3. LLM prompts include financial context and summaries cite data sources (reducing hallucination)
  4. Results are returned as structured JSON with data freshness timestamp
**Plans**: 1 plan

Plans:
- [x] 03-01-PLAN.md -- LLM SummarizationService with GPT-4o-mini/Claude (FRIS-15 to FRIS-19, FRIS-23 to FRIS-25)

### Phase 4: Integration & Polish
**Goal**: Complete pipeline runs end-to-end with production readiness
**Depends on**: Phase 3
**Requirements**: (pipeline orchestration - all prior requirements)
**Success Criteria** (what must be TRUE):
  1. Complete pipeline executes from topic input to summary output without manual intervention
  2. Pipeline handles partial failures gracefully (some stocks fail while others succeed)
  3. All price data is labeled with data freshness (real-time vs delayed)
  4. System is containerized with Docker and runs via uvicorn workers
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Infrastructure | 4/4 | COMPLETED | 2026-03-25 |
| 2. Filtering & Data Fetching | 2/2 | COMPLETED | 2026-03-25 |
| 3. LLM Summarization & Output | 1/1 | COMPLETED | 2026-03-25 |
| 4. Integration & Polish | 0/N | Not started | - |
