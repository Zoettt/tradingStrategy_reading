# Project Research Summary

**Project:** Financial Report Interpretation System (FRIS)
**Domain:** Financial Data Aggregation + LLM Summarization
**Researched:** 2026-03-25
**Confidence:** MEDIUM (web search unavailable; patterns well-established but implementation details need verification)

## Executive Summary

FRIS is a pipeline-based system that transforms a user topic query (e.g., "AI chips") plus a time period into structured earnings summaries for relevant US stocks. It chains together topic classification, stock screening by financial metrics, earnings data fetching from financial APIs, and LLM-powered summarization. This is fundamentally an ETL + AI pipeline, not a real-time trading system or portfolio tracker.

Experts build this type of system using a linear pipeline architecture where each stage (classify, screen, fetch, summarize) has clear input/output contracts. The recommended stack uses FastAPI for the API layer, yfinance for free stock data access, DuckDB + Polars for analytical storage, and direct OpenAI SDK calls for LLM integration. LangChain and similar heavy abstractions are explicitly avoided as overkill for single-document summarization workflows.

Key risks identified: LLM hallucination on financial facts (prevention requires grounded generation with explicit source attribution), topic-industry classification gaps (GICS classification lags reality for cross-sector companies like NVIDIA), and API rate limit exhaustion (mitigated via caching and circuit breaker patterns). These risks must be addressed in the earliest phases, not bolted on later.

## Key Findings

### Recommended Stack

The system uses an async-first Python stack optimized for rapid development and production readiness. FastAPI with Pydantic v2 provides automatic OpenAPI docs and built-in validation, reducing developer-induced errors. yfinance provides free access to Yahoo Finance data without API keys. DuckDB serves as an embedded analytical database with Parquet support, avoiding operational overhead of PostgreSQL while providing SQL querying capability.

**Core technologies:**
- **FastAPI 0.115.x + uvicorn**: Async API framework with auto-generated docs and Pydantic validation
- **yfinance 1.2.0**: Free stock data (price, fundamentals, financials) - no API key required, 22k+ GitHub stars
- **OpenAI SDK (direct)**: LLM integration without LangChain abstraction - lighter, more stable, sufficient for single-doc summarization
- **DuckDB 1.5.x + Polars**: Embedded analytical storage, Arrow-native, SQL queries against Parquet files
- **SEC EDGAR (via sec-edgar-api)**: Official source for 10-K/10-Q filings with rate limit handling
- **Docker + uvicorn workers**: Containerization and production serving with multi-worker concurrency

### Expected Features

**Must have (table stakes):**
- Topic-to-ticker mapping via keyword matching + GICS classification lookup table
- Financial metric filtering (market cap, PE, PB, price ranges) with explicit NULL handling
- Earnings report fetching (EPS, revenue, guidance) from yfinance/FMP API
- Business summary generation via structured LLM prompt with source attribution
- Stock ticker resolution and result pagination

**Should have (competitive):**
- Estimate vs actual analysis (beat/miss percentages for EPS and revenue)
- Peer benchmarking (company metrics vs sector median)
- Interactive re-filtering without page reload (client-side state)

**Defer (v2+):**
- Earnings comparison (side-by-side diff) - UI complexity, not core use case
- Trend analysis (quarter-over-quarter charts) - requires historical data accumulation
- Sentiment scoring from transcripts - higher API cost, transcript access uncertain
- Non-US markets - doubles GICS/API complexity for marginal gain

### Architecture Approach

FRIS follows a linear pipeline pattern where each stage transforms input to output in sequence: User Query -> TopicClassifier -> StockScreener -> FinancialDataFetcher -> LLMAnalyzer -> EarningsSummary. This minimizes complexity and makes debugging linear. The pipeline is intentionally NOT event-driven or microservices - single queries produce single results, and complexity should stay low.

The system comprises 5 major components with defined boundaries:
1. **TopicClassifier** - Maps user topic to GICS industries (keyword matching first, LLM fallback)
2. **StockScreener** - Filters stocks by market cap, PE, PB, price criteria
3. **FinancialDataFetcher** - Parallel earnings data retrieval with circuit breaker and retry logic
4. **LLMAnalyzer** - Structured summary generation with grounded prompts
5. **APIClient** - HTTP abstraction layer over yfinance/FMP with caching

### Critical Pitfalls

1. **LLM Hallucination on Financial Facts** - LLM generates plausible but fabricated revenue numbers or growth metrics. Prevention: Always retrieve actual financial data before summarizing; force structured JSON output with explicit source attribution; inject uncertainty rather than guessing; cross-check summaries against source data.

2. **Topic-Industry Classification Mismatch** - GICS classification lags reality (NVIDIA classified under Technology, not Semiconductors). Prevention: Query both GICS sector AND keyword match on business description; build topic synonym mapping (EV = Electric Vehicles = Auto Manufacturers); include companies where description contains topic keywords.

3. **Missing Data Cascade** - Stocks with missing PE ratio crash the system or show partial results without explanation. Prevention: Define explicit NULL handling policy per metric; return data quality confidence score per stock; gracefully degrade with "PE not available" annotations.

4. **Real-Time vs Delayed Data Confusion** - Free tier APIs provide 15-20 minute delayed quotes but system does not label them. Prevention: Always show "Data delayed by X minutes"; timestamp all price fields; warn users on first interaction.

5. **API Rate Limit Exhaustion** - System works for small queries but fails at 50+ stocks due to FMP limits (5 req/min free tier). Prevention: Cache financial data with TTL; implement exponential backoff retry; batch requests where API supports it; track request count and pause approaching limits.

## Implications for Roadmap

Based on research, a 4-phase structure is recommended, ordered by dependency criticality and risk mitigation priority:

### Phase 1: Core Infrastructure
**Rationale:** Establish data access layer first. Building business logic on broken data fetching wastes work. This phase also directly addresses the most critical pitfall (rate limit exhaustion) by building caching from the start.

**Delivers:** APIClient with yfinance wrapper, response caching (TTL: 1hr for prices, 24hr for fundamentals), circuit breaker pattern, TopicClassifier with GICS mapping table (keyword matching first).

**Addresses:** Table stakes foundation - topic-to-ticker mapping, API rate limit exhaustion, missing data cascade (explicit NULL handling).

**Avoids:** Building LLM integration before caching is in place (would cause cost explosion).

### Phase 2: Filtering and Data Fetching
**Rationale:** Filtering is a core user requirement. Keep it simple (client-side, in-memory) first before optimizing. Also establishes data consistency patterns before LLM integration.

**Delivers:** FilterCriteria dataclass with explicit NULL semantics, StockScreener with filter application, FinancialDataFetcher for parallel earnings retrieval, data quality scoring per stock.

**Addresses:** Filter logic errors (explicit semantics documented), missing data cascade (graceful degradation), topic-industry classification mismatch (multi-source matching starts here).

**Uses:** APIClient from Phase 1.

### Phase 3: LLM Summarization
**Rationale:** LLM integration is the novel value-add. Build and test prompts with small, controlled data first. Must address hallucination prevention from day one.

**Delivers:** EarningsSummary schema with source attribution fields, LLMAnalyzer with grounded prompts, uncertainty injection ("I don't have exact figure"), cost tracking per query, fact verification layer.

**Addresses:** LLM hallucination (grounded generation with source citation), LLM cost explosion (hierarchical approach: sector-level first, stock-level only for filtered subset), real-time/delayed confusion (timestamp all data).

**Implements:** Terminal pipeline stage.

### Phase 4: Integration and Polish
**Rationale:** Integration last. Verify each component works independently before wiring together. This phase addresses production readiness.

**Delivers:** Pipeline orchestration connecting all stages, partial result handling (some stocks fail gracefully while others succeed), retry logic with backoff, real-time/delayed latency labeling, Docker containerization.

**Addresses:** Remaining moderate pitfalls, production deployment concerns.

### Phase Ordering Rationale

- **Foundation before filtering before LLM** - Each stage depends on the previous. TopicClassifier needs APIClient; StockScreener needs TopicClassifier; LLMAnalyzer needs earnings data.
- **Caching in Phase 1** - Prevents rate limit exhaustion and LLM cost explosion. Adding caching later requires refactoring.
- **Hallucination prevention in Phase 3** - Grounded generation is core to LLMAnalyzer design; retrofitting is harder.
- **Integration last** - Standard practice: verify components independently.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 1:** Yahoo Finance API limits are unofficial and change frequently - need live testing to confirm rate limits and behavior under load
- **Phase 3:** LLM prompt engineering for financial accuracy - no documented best practice for this specific use case; likely need to iterate on prompts after testing

**Phases with standard patterns (skip research-phase):**
- **Phase 2:** Filter logic and data fetching patterns are well-established; no novel research needed
- **Phase 4:** Docker + uvicorn deployment is standard FastAPI pattern

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | FastAPI, yfinance, OpenAI SDK well-documented; DuckDB patterns established |
| Features | MEDIUM | Web search unavailable; domain knowledge and competitive analysis used |
| Architecture | HIGH | Pipeline pattern is standard for ETL+AI systems; components well-defined |
| Pitfalls | MEDIUM | Web search unavailable; based on domain literature and established patterns |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Yahoo Finance API limits**: Unofficial API, limits not documented; need live testing before Phase 1 completion
- **GICS mapping dataset**: No free/open keyword-to-GICS mapping confirmed; may need to build manually or use LLM classification as fallback
- **LLM prompt optimization**: Financial summarization prompts need iteration; Phase 3 should include prompt A/B testing
- **SEC EDGAR rate limits**: Official docs show 10/sec but practical limits may differ; verify before production
- **FMP vs yfinance coverage**: yfinance may insufficient for complex earnings data; FMP paid tier may be needed for premium fundamentals

## Sources

### Primary (HIGH confidence)
- yfinance GitHub (v1.2.0, Feb 2026) - version, API coverage
- FastAPI Documentation - framework best practices
- OpenAI Python SDK - async client, Pydantic response models
- SEC EDGAR Developer Documentation - API documentation, rate limits

### Secondary (MEDIUM confidence)
- FMP official pricing page - rate limits and tier information
- GICS Classification Standards (MSCI) - classification structure and limitations
- Enterprise Integration Patterns (Hohpe & Woolf) - pipeline architecture pattern
- Michael Nygard's Release It! - circuit breaker pattern

### Tertiary (LOW confidence)
- LLM hallucination prevention strategies - based on literature, needs validation
- Yahoo Finance API specific limits - unofficial, changes frequently
- SEC EDGAR practical rate limits - need live testing

---
*Research completed: 2026-03-25*
*Ready for roadmap: yes*
