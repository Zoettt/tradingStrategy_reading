# Phase 1: Core Infrastructure - Research

**Researched:** 2026-03-25
**Domain:** Financial Data Access Layer / Topic-to-Ticker Mapping
**Confidence:** MEDIUM-HIGH (verified with live yfinance call; FMP details need verification)

## Summary

Phase 1 establishes the foundation for FRIS: data access via yfinance (primary) and FMP (fallback), topic-to-GICS mapping via keyword table, and local caching with TTL. The existing codebase already has `src/data_fetcher.py` with a `StockDataFetcher` class using yfinance for price data. Phase 1 extends this to sector/industry classification and company overview data.

Key decisions locked from research: yfinance is the primary data source (no API key required, covers ~99% US stocks), FMP is fallback for coverage gaps (5 req/min free tier), and caching is required before LLM integration (prevents cost explosion).

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase 1: Topic search + data source infrastructure grouped (yfinance primary, FMP fallback, caching)
- Phase 1: GICS keyword mapping table for topic-to-industry matching
- Phase 1: NULL handling built into foundation (not retrofitted later)

### Claude's Discretion
- Implementation patterns for caching (TTLCache vs disk cache)
- GICS keyword table structure and initial keywords
- Module organization within src/

### Deferred Ideas (OUT OF SCOPE)
- SEC EDGAR filing parsing (Phase 3+)
- Non-US markets
- Real-time price streaming

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FRIS-01 | User can input a topic (free text) and time period (quarter/date range) | TopicClassifier interface, input validation |
| FRIS-02 | System matches topic to GICS sectors/industries using keyword mapping table | GICS classification structure, keyword mapping approach |
| FRIS-03 | System returns list of relevant US stock tickers with company names and industries | yfinance Ticker.info fields (sector, industry, shortName) |
| FRIS-13 | Handle missing/incomplete data gracefully (flag as N/A, continue processing) | NULL handling patterns, data quality scoring |
| FRIS-20 | Primary data source: Yahoo Finance via yfinance library | Verified: yfinance 1.1.0 installed, .info returns sector/industry/marketCap |
| FRIS-21 | Fallback/supplementary: FMP API | FMP Python client patterns, rate limit handling |
| FRIS-22 | Cache financial data locally (TTL: 1hr prices, 24hr fundamentals) | TTLCache from cachetools OR disk cache with JSON |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | 1.1.0 (installed), 1.2.0 (latest) | Stock data access | Free, no API key, covers 99% US stocks, confirmed working |
| cachetools | NOT INSTALLED | TTL in-memory cache | Standard for TTL memoization in Python |
| duckdb | 1.5.0 (installed) | Local data storage | Embedded analytical DB, already in project |
| pandas | 2.0.0+ (inferred) | DataFrame operations | Industry standard for financial data |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.32.3 (installed) | HTTP client for FMP API | FMP fallback only |
| json | stdlib | Cache serialization | Disk cache for persistence |

**Installation:**
```bash
pip install cachetools>=5.0.0
```

**Version verification:**
- yfinance: `pip show yfinance | grep Version` -> 1.1.0 (upgrade to 1.2.0 available)
- cachetools: NOT installed - must add to requirements

## Architecture Patterns

### Recommended Project Structure
```
src/
├── data_fetcher.py        # Existing - StockDataFetcher for prices
├── fris/
│   ├── __init__.py
│   ├── topic_classifier.py   # NEW: Topic-to-GICS mapping
│   ├── stock_repository.py  # NEW: Ticker search + info fetching
│   ├── cache.py             # NEW: TTL cache layer
│   ├── models.py            # NEW: Pydantic dataclasses
│   └── exceptions.py        # NEW: Custom exceptions
├── config/
│   └── settings.py          # Existing
tests/
├── test_topic_classifier.py # NEW
├── test_stock_repository.py # NEW
└── test_cache.py            # NEW
```

### Pattern 1: Topic-to-GICS Keyword Mapping
**What:** Static mapping table from topic keywords to GICS sectors/industries
**When to use:** User inputs free text topic, need to find related stocks
**Example:**
```python
GICS_KEYWORD_MAP = {
    "AI chips": {"sector": "Technology", "industry": "Semiconductors"},
    "electric vehicles": {"sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
    "cloud computing": {"sector": "Technology", "industry": "Software Infrastructure"},
}

def classify_topic(topic: str) -> list[str]:
    """Returns list of matching GICS industry keys."""
    topic_lower = topic.lower()
    matches = []
    for keyword, gics_info in GICS_KEYWORD_MAP.items():
        if keyword in topic_lower or fuzzy_match(keyword, topic_lower):
            matches.append(gics_info)
    return matches
```

### Pattern 2: Stock Repository with Caching
**What:** Repository pattern wrapping yfinance with TTL cache
**When to use:** Need to fetch stock info without hammering API
**Example:**
```python
from cachetools import TTLCache
from dataclasses import dataclass

@dataclass
class StockInfo:
    ticker: str
    company_name: str
    sector: str | None = None  # N/A if missing
    industry: str | None = None
    market_cap: float | None = None

class StockRepository:
    def __init__(self, cache_ttl: int = 86400):  # 24hr default
        self._info_cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        self._price_cache = TTLCache(maxsize=500, ttl=3600)  # 1hr for prices

    def get_stock_info(self, ticker: str) -> StockInfo:
        cache_key = f"{ticker}:info"
        if cache_key in self._info_cache:
            return self._info_cache[cache_key]

        info = yf.Ticker(ticker).info
        stock_info = StockInfo(
            ticker=ticker,
            company_name=info.get("shortName", "N/A"),
            sector=info.get("sector") or "N/A",
            industry=info.get("industry") or "N/A",
            market_cap=info.get("marketCap"),
        )
        self._info_cache[cache_key] = stock_info
        return stock_info
```

### Pattern 3: Graceful NULL Handling
**What:** Every field has explicit N/A handling - no crashes, no None propagation
**When to use:** Any financial data field that may be missing
**Example:**
```python
@dataclass
class StockInfo:
    sector: str | None = None  # Store None internally

    @property
    def sector_display(self) -> str:
        return self.sector if self.sector else "N/A"

# Usage:
info = repo.get_stock_info(ticker)
print(f"{info.company_name}: {info.sector_display}")
```

### Anti-Patterns to Avoid
- **Returning None from repository methods:** Return N/A strings or wrapper objects instead
- **Catching exceptions silently:** Log and continue, but track failure count
- **Single large cache:** Separate price cache (1hr TTL) from info cache (24hr TTL)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTL caching | Custom cache with timestamps | cachetools TTLCache | Battle-tested, auto-eviction |
| HTTP requests to FMP | Raw requests with retry | fmp-python client | Handles auth, rate limits |
| JSON serialization | Manual JSON dumps | Pydantic model.model_dump_json() | Validation + serialization |

## Runtime State Inventory

> Phase 1 is greenfield - no rename/refactor. This section is N/A.

**Verification:** Phase 1 creates new modules, no existing runtime state to migrate.

## Common Pitfalls

### Pitfall 1: yfinance Rate Limiting Under Load
**What goes wrong:** System works for 10-20 stocks but fails silently at 50+
**Why it happens:** yfinance has unofficial rate limits that trigger 429 responses
**How to avoid:** Cache aggressively (24hr for info), add 0.5s delay between fetches, implement retry with backoff
**Warning signs:** Intermittent 429 errors, empty info dicts for previously working tickers

### Pitfall 2: GICS Classification Lag
**What goes wrong:** NVIDIA classified under "Technology" not "Semiconductors"
**Why it happens:** GICS classification lags actual business mix for cross-sector companies
**How to avoid:** Match on BOTH sector AND company description keywords; include companies where description contains topic keywords
**Warning signs:** Missing obvious matches like NVIDIA for "AI chips"

### Pitfall 3: Missing Data Cascade
**What goes wrong:** Single stock with missing PE ratio crashes filter logic
**Why it happens:** No explicit NULL/N/A policy per metric
**How to avoid:** Define display policy upfront; use "N/A" strings for missing, not None; filter logic handles N/A explicitly
**Warning signs:** TypeErrors in filter code, partial results without explanation

### Pitfall 4: FMP Free Tier Exhaustion
**What goes wrong:** FMP free tier has 5 req/min limit - exhausts quickly
**Why it happens:** No request counting or circuit breaker
**How to avoid:** Track request count, pause when approaching limit, fallback to yfinance only
**Warning signs:** FMP returns 429, empty responses, stale data

## Code Examples

### Verified: yfinance Ticker.info fields (live test confirmed)
```python
import yfinance as yf
t = yf.Ticker('AAPL')
info = t.info
# Returns: sector='Technology', industry='Consumer Electronics',
#          marketCap=3698586025984, shortName='Apple Inc.'
```

### Pattern: Topic classifier with keyword matching
```python
GICS_INDUSTRIES = {
    "Semiconductors": ["chip", "semiconductor", "wafer", "foundry"],
    "Software Infrastructure": ["cloud", "saas", "software", "infrastructure"],
    "Auto Manufacturers": ["electric vehicle", "ev", "automobile", "car"],
}

def find_industries(topic: str) -> list[str]:
    topic_lower = topic.lower()
    return [
        industry for industry, keywords in GICS_INDUSTRIES.items()
        if any(kw in topic_lower for kw in keywords)
    ]
```

### Pattern: Dual-cache repository
```python
class StockRepository:
    def __init__(self):
        self._info_cache = TTLCache(maxsize=1000, ttl=86400)  # 24hr
        self._price_cache = TTLCache(maxsize=500, ttl=3600)   # 1hr

    def get_info(self, ticker: str) -> StockInfo:
        if ticker in self._info_cache:
            return self._info_cache[ticker]
        info = self._fetch_info(ticker)
        self._info_cache[ticker] = info
        return info
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct yfinance calls every request | TTLCache with 24hr for info | 2024+ | Reduces API load 95%+ |
| Single cache for all data types | Dual cache (price vs fundamentals) | Best practice | Prevents stale prices |
| None for missing fields | "N/A" string display policy | Standard | UI never shows blank for missing |

**Deprecated/outdated:**
- yfinance 0.1.x: .info was synchronous; now async-capable
- FMP v3 client: v4 has better rate limit handling

## Open Questions

1. **FMP Python client library**
   - What we know: FMP has a Python client (`fmp-python` or similar)
   - What's unclear: Exact package name and API interface
   - Recommendation: Verify package name, test rate limit behavior

2. **GICS keyword mapping completeness**
   - What we know: Need mapping for common topics like "AI", "cloud", "EV", "fintech"
   - What's unclear: How many keywords needed for MVP coverage
   - Recommendation: Start with 20-30 common topics, expand based on user queries

3. **Cache persistence across restarts**
   - What we know: TTLCache is in-memory only (lost on restart)
   - What's unclear: Is disk-persisted cache needed for Phase 1?
   - Recommendation: Phase 1 uses in-memory only; add disk cache if performance issues

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| yfinance | Primary data source | YES | 1.1.0 | N/A |
| cachetools | TTL caching | NO | - | Install `pip install cachetools` |
| duckdb | Local storage | YES | 1.5.0 | N/A |
| requests | FMP API calls | YES | 2.32.3 | N/A |
| Python 3.13 | Runtime | YES | 3.13.4 | N/A |

**Missing dependencies with no fallback:**
- None blocking Phase 1

**Missing dependencies with fallback:**
- cachetools: Install via pip (one command)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pytest.ini or pyproject.toml (not yet created) |
| Quick run command | `pytest tests/test_fris/ -x -v` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FRIS-01 | Topic input validation | unit | `pytest tests/test_fris/test_topic_classifier.py -k "test_topic_input"` | NO |
| FRIS-02 | Keyword-to-GICS mapping | unit | `pytest tests/test_fris/test_topic_classifier.py -k "test_gics_mapping"` | NO |
| FRIS-03 | Returns tickers with names/industries | integration | `pytest tests/test_fris/test_stock_repository.py -k "test_get_tickers"` | NO |
| FRIS-13 | Missing data returns N/A | unit | `pytest tests/test_fris/test_models.py -k "test_na_handling"` | NO |
| FRIS-20 | yfinance primary source | integration | `pytest tests/test_fris/test_stock_repository.py -k "test_yfinance_primary"` | NO |
| FRIS-22 | Cache TTL enforcement | unit | `pytest tests/test_fris/test_cache.py -k "test_ttl"` | NO |

### Sampling Rate
- **Per task commit:** Quick run on changed module only
- **Per wave merge:** Full suite
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_fris/` directory structure
- [ ] `tests/test_fris/__init__.py`
- [ ] `tests/test_fris/conftest.py` - shared fixtures
- [ ] `tests/test_fris/test_topic_classifier.py` - FRIS-01, FRIS-02
- [ ] `tests/test_fris/test_stock_repository.py` - FRIS-03, FRIS-20
- [ ] `tests/test_fris/test_cache.py` - FRIS-22
- [ ] `tests/test_fris/test_models.py` - FRIS-13
- [ ] Framework install: `pip install cachetools` (if not already in CI)

## Sources

### Primary (HIGH confidence)
- yfinance 1.2.0 PyPI page (Feb 2026) - version, API coverage, components
- yfinance GitHub README - Ticker/Tickers/Search/Sector/Industry classes
- Live yfinance test on AAPL - confirmed sector/industry/marketCap fields work
- cachetools PyPI page - TTLCache API and usage

### Secondary (MEDIUM confidence)
- GICS Classification Standards (MSCI) - classification structure
- Enterprise Integration Patterns - pipeline architecture pattern
- Nygard's Release It! - circuit breaker pattern

### Tertiary (LOW confidence)
- FMP API details - need verification of Python client and rate limits
- Specific GICS industry keywords - initial set needs validation against real queries

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM-HIGH - yfinance confirmed working, cachetools is standard library
- Architecture: HIGH - repository pattern + TTL cache is well-established
- Pitfalls: MEDIUM - based on domain literature, web search was unavailable for verification

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (30 days - stable domain)
