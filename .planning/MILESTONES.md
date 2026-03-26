# Milestones

## v1.0 — MVP (2026-03-26)

**Phases:** 1-4 | **Plans:** 8 | **Status:** SHIPPED

### Accomplishments

- FRIS package foundation: StockInfo with N/A handling, dual TTL cache (PriceCache 1hr, FundamentalsCache 24hr)
- TopicClassifier with GICS keyword mapping (13 industries, 20-30 keywords each, confidence scoring)
- StockRepository with yfinance primary + FMP fallback, rate limit handling
- TopicSearchService orchestrating classifier + repository
- StockFilterService: market cap/P/E/P/B/price filters with AND logic
- EarningsService: EPS, revenue, earnings date, company overview, forward EPS, quarterly data
- LLM SummarizationService: GPT-4o-mini/Claude, structured JSON, financial context, data source citations
- FRISPipeline orchestrator, FastAPI + uvicorn, Docker deployment
- ~3100 LOC Python, all 25 FRIS requirements delivered

### Git Range

`d4bdd09` → `4d67475`

### Archive

- [milestones/v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md)
- [milestones/v1.0-REQUIREMENTS.md](./milestones/v1.0-REQUIREMENTS.md)
