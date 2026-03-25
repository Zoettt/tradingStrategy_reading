# Technology Stack

**Project:** Financial Report Interpretation System
**Researched:** 2026-03-25
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core API Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.115.x | REST API framework | Async-first, auto-generated OpenAPI docs, Pydantic validation built-in, 200-300% faster development. Production-ready with uvicorn. |
| **uvicorn** | (bundled with fastapi[standard]) | ASGI server | Native ASGI support, hot reload in dev, production-grade with workers |
| **Pydantic** | 2.10.x | Data validation | Core to FastAPI, reduces 40% of developer-induced errors, v2 has significant perf improvements |

**NOT Flask/Flask-RESTX** because: synchronous-only by default, requires more boilerplate for validation, no auto-generated docs.

### Financial Data APIs

| Technology | Tier | Purpose | Why |
|------------|------|---------|-----|
| **yfinance** | Free/Tier 1 | Stock data (price, fundamentals, financials) | Version 1.2.0 (Feb 2026), 22k+ stars, 86k projects use it. No API key needed. Covers Yahoo Finance data. |
| **SEC EDGAR** | Free | SEC filings (10-K, 10-Q, 8-K) | Official source, no API key, direct/sec-api library available. 10/sec rate limit. |
| **FMP** | Paid Tier | Premium fundamentals, analyst data | ~$30/mo starter. Worth it if yfinance coverage insufficient. JSON exports, no scraping. |

**NOT Alpha Vantage** because: stricter rate limits (5 req/min free), less Python-friendly, weaker fundamentals data.

**NOT Yahoo Finance unofficial scrapers** because: risk of IP blocks, no stability guarantees, yfinance already wraps this elegantly.

### LLM Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **OpenAI SDK** | latest | Direct API access | `pip install openai`. Async client, streaming support, Pydantic response models. Clean, minimal abstraction. |

**NOT LangChain** because: heavy dependency, rapid churn (frequent breaking changes), over-abstracts for simple use cases like single-document summarization. Use direct SDK for MVP.

**NOT LiteLLM** because: adds unnecessary indirection for single-provider MVP. Defer if multi-provider needed later.

### Data Storage

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **DuckDB** | 1.5.x | Analytical queries, Parquet storage | Embedded, no server, excellent for financial time-series, SQL interface, works with Polars. |
| **Polars** | (latest) | DataFrame ops | Faster than Pandas for large datasets, lazy evaluation, Arrow-native. Use with DuckDB for storage. |

**NOT PostgreSQL** because: overkill for MVP, requires separate server, operational overhead.

**NOT SQLite** because: single-writer limitation, poor analytical query performance, no Arrow integration.

**NOT just file-based (JSON/CSV)** because: no querying capability, no incremental updates, will cause rewrites when data grows.

### Infrastructure

| Technology | Purpose | Why |
|------------|---------|-----|
| **Docker** | Containerization | Reproducible builds, easy deployment |
| **uvicorn workers** | Production serving | Multi-worker for concurrency |
| **python-dotenv** | Config management | Simple .env file handling |

## Installation

```bash
# Core dependencies
pip install "fastapi[standard]">=0.115.0
pip install yfinance>=1.2.0
pip install openai
pip install duckdb>=1.5.0
pip install polars
pip install python-dotenv
pip install sec-edgar-api  # For EDGAR access
pip install httpx  # For async HTTP (used by FastAPI/test client)
```

## Architecture Pattern

```
API Layer (FastAPI + Pydantic)
    │
    ├── Financial Data Fetcher (yfinance, EDGAR)
    │
    ├── LLM Service (OpenAI SDK)
    │
    └── Storage Layer (DuckDB + Polars)
```

## Decision Rationale Summary

| Decision | Choice | Alternative | Why |
|----------|--------|-------------|-----|
| API Framework | FastAPI | Flask | Async-first, auto-docs, built-in validation |
| Stock Data | yfinance | FMP paid | Free, well-maintained, sufficient for MVP |
| LLM SDK | OpenAI direct | LangChain | Lighter, more stable, sufficient for single-doc |
| Storage | DuckDB + Polars | PostgreSQL | Embedded, analytical-first, no server needed |
| SEC Filings | sec-edgar-api | Manual HTTP | Official wrapper, handles rate limits |

## Sources

- [yfinance GitHub](https://github.com/ranaroussi/yfinance) - Version 1.2.0, Feb 2026
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Best practices, deployment options
- [OpenAI Python SDK](https://github.com/openai/openai-python) - Version, async support
- [SEC EDGAR Developer](https://www.sec.gov/developers) - API documentation, rate limits
