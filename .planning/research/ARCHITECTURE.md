# Architecture: Financial Report Interpretation System (FRIS)

**Domain:** Financial Data Aggregation + LLM Summarization
**Researched:** 2026-03-25
**Confidence:** MEDIUM (patterns well-established; implementation details depend on chosen data providers)

---

## System Overview

The system transforms a user query (topic + time period) into individual earnings summaries for relevant US stocks. This requires a pipeline pattern where each stage refines and enriches the data.

```
User Query → Topic Classification → Stock Screening → Financial Data Fetch → LLM Summarization → Output
```

**Key architectural insight:** This is a **pipeline architecture** (not event-driven or microservices). Each stage has a clear input/output contract and depends only on the previous stage. This minimizes complexity and makes debugging linear.

---

## Component Boundaries

| Component | Responsibility | Input | Output | Talks To |
|-----------|---------------|-------|--------|----------|
| **TopicClassifier** | Map user topic to GICS industries | `topic: str, time_period: str` | `List[GICSIndustry]` | StockScreener |
| **StockScreener** | Filter stocks by market cap, PE, PB, price | `industries: List[GICSIndustry], filters: FilterCriteria` | `List[Stock]` | FinancialDataFetcher, TopicClassifier |
| **FinancialDataFetcher** | Retrieve earnings data from API | `stocks: List[Stock], period: str` | `List[EarningsData]` | LLMAnalyzer |
| **LLMAnalyzer** | Generate structured summaries | `earnings_data: EarningsData, company_info: CompanyInfo` | `EarningsSummary` | None (terminal) |
| **APIClient** | HTTP wrapper for FMP/Yahoo | `endpoint: str, params: dict` | `dict \| list` | FinancialDataFetcher |

---

## Data Flow

### Primary Flow (Linear Pipeline)

```
1. User Query
   topic: "AI Chips"
   time_period: "Q3 2024"

2. TopicClassifier.classify()
   Input:  topic="AI Chips", period="Q3 2024"
   Action: Map to GICS: "Semiconductors", "Semiconductor Equipment"
   Output: industries=[GICSIndustry("Technology", "Semiconductons"), ...]

3. StockScreener.screen()
   Input:  industries=[...], filters={market_cap_min: 1e9, pe_max: 50, ...}
   Action: Fetch all US stocks in industries, apply filters
   Output: stocks=[Stock(ticker="NVDA", ...), Stock(ticker="AMD", ...), ...]

4. FinancialDataFetcher.fetch_earnings()
   Input:  stocks=[NVDA, AMD, ...], period="Q3 2024"
   Action: Parallel API calls to FMP/Yahoo for each stock
   Output: earnings_data=[EarningsData(ticker="NVDA", revenue=..., profit=...), ...]

5. LLMAnalyzer.summarize()
   Input:  earnings_data for each stock
   Action: Construct prompt, call LLM API
   Output: EarningsSummary(ticker="NVDA", business_model=..., risks=..., ...)

6. Return list of EarningsSummary objects
```

### Data Flow Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────────────┐
│ User Query  │────▶│  TopicClassifier │────▶│ StockScreener   │────▶│ FinancialDataFetch │
│ (topic+     │     │  (GICS mapping)  │     │  (filter+sort)  │     │  (parallel API)    │
│  period)    │     └──────────────────┘     └─────────────────┘     └────────────────────┘
└─────────────┘                                                               │
                                                                              ▼
                                                                        ┌────────────┐
                                                                        │  LLM       │
                                                                        │  Analyzer  │
                                                                        └────────────┘
                                                                              │
                                                                              ▼
                                                                   ┌──────────────────┐
                                                                   │ EarningsSummary  │
                                                                   │ (per stock)      │
                                                                   └──────────────────┘
```

---

## Component Specifications

### TopicClassifier

**Purpose:** Translate natural language topic to financial classification

**Design:**
- Maintain a topic-to-GICS mapping table (seeded with common topics)
- Use keyword matching first, LLM fallback for unknown topics
- Cache classifications to avoid repeated API calls

**Interface:**
```python
class TopicClassifier:
    def classify(self, topic: str, period: str) -> List[GICSIndustry]:
        """Returns GICS industries matching the topic."""

    def expand_topic(self, topic: str) -> List[str]:
        """Returns related search terms for topic expansion."""
```

### StockScreener

**Purpose:** Filter stocks by financial criteria

**Design:**
- Fetch stock universe from FMP/Yahoo screener API
- Apply filters in-memory (client-side)
- Support pagination for large result sets
- Cache stock lists per industry to reduce API calls

**Interface:**
```python
@dataclass
class FilterCriteria:
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    pe_max: Optional[float] = None
    pe_min: Optional[float] = None
    pb_max: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None

class StockScreener:
    def screen(self, industries: List[GICSIndustry], filters: FilterCriteria) -> List[Stock]:
        """Returns filtered stocks matching criteria."""

    def get_stock_universe(self, industries: List[GICSIndustry]) -> List[Stock]:
        """Fetches all stocks in given industries (uncached)."""
```

### FinancialDataFetcher

**Purpose:** Retrieve earnings and company data

**Design:**
- Parallel fetching with asyncio/aiohttp for performance
- Circuit breaker pattern for API resilience
- Exponential backoff retry logic
- Batch requests where API supports it

**Interface:**
```python
@dataclass
class EarningsData:
    ticker: str
    period: str
    revenue: float
    net_income: float
    eps: float
    revenue_growth: Optional[float]
    earnings_date: datetime

class FinancialDataFetcher:
    def fetch_earnings(self, stocks: List[Stock], period: str) -> List[EarningsData]:
        """Fetches earnings data for all stocks in parallel."""

    def fetch_company_info(self, ticker: str) -> CompanyInfo:
        """Fetches business description, competitors, sector."""
```

### LLMAnalyzer

**Purpose:** Generate structured earnings summaries

**Design:**
- Prompt engineering with structured output (JSON mode)
- System prompt defines summary template
- Few-shot examples for consistency
- Rate limiting to respect API quotas
- Retry with exponential backoff

**Interface:**
```python
@dataclass
class EarningsSummary:
    ticker: str
    company_name: str
    industry: str
    period: str
    business_model: str
    revenue_highlight: str
    profit_highlight: str
    competitive_position: str
    key_risks: List[str]
    confidence_score: float  # LLM confidence in summary

class LLMAnalyzer:
    def summarize(self, earnings: EarningsData, company_info: CompanyInfo) -> EarningsSummary:
        """Generates structured summary for single stock."""

    def summarize_batch(self, batch: List[Tuple[EarningsData, CompanyInfo]]) -> List[EarningsSummary]:
        """Generates summaries with batch LLM calls where supported."""
```

### APIClient

**Purpose:** HTTP abstraction for financial data providers

**Design:**
- Single class wrapping httpx/requests
- Provider abstraction layer (FMP vs Yahoo)
- Response caching with TTL
- Error classification (rate limit vs server error vs client error)

**Interface:**
```python
class APIClient:
    def __init__(self, provider: FinancialDataProvider, cache_ttl: int = 3600):
        ...

    async def get(self, endpoint: str, params: dict) -> dict | list:
        ...

    async def post(self, endpoint: str, data: dict) -> dict:
        ...
```

---

## Architecture Patterns to Follow

### Pipeline Pattern
**What:** Linear flow where each stage transforms input to output
**When:** Primary use case is a single query producing a single result
**Why:** Minimal complexity, easy debugging, clear data contract

### Repository Pattern
**What:** Abstraction over data access (stocks, earnings, summaries)
**When:** Multiple data sources or need for caching
**Why:** Decouples business logic from data retrieval

### Circuit Breaker Pattern
**What:** Fail fast when external API is degraded
**When:** Calling third-party financial APIs
**Why:** Prevents cascade failures, allows graceful degradation

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic LLM Prompt
**What:** stuffing all stock data into one massive LLM call
**Why bad:** Token limits, cost explosion, poor error recovery
**Instead:** Individual summaries per stock, parallelize LLM calls

### Anti-Pattern 2: Synchronous Sequential API Calls
**What:** Fetch stock A, wait, fetch stock B, wait...
**Why bad:** 100 stocks = 100 * latency = unacceptable response time
**Instead:** asyncio parallel fetching with controlled concurrency

### Anti-Pattern 3: No Caching
**What:** Every query hits external APIs
**Why bad:** Rate limits, costs, latency for repeated queries
**Instead:** Cache stock universe, earnings data (TTL: 1 hour for prices, 24 hours for fundamentals)

---

## Scalability Considerations

| Concern | At 10 stocks | At 100 stocks | At 1000 stocks |
|---------|--------------|---------------|----------------|
| **API calls** | 10 parallel | 100 parallel (batch) | Paginated, 10 batches |
| **LLM calls** | 10 sequential | 10 parallel batches | 100 parallel batches |
| **Latency target** | < 5 seconds | < 15 seconds | < 60 seconds |
| **Cost** | $0.10 | $1.00 | $10.00 |
| **Rate limiting** | No issue | FMP premium needed | Requires caching + queuing |

---

## Suggested Build Order

### Phase 1: Foundation
1. **APIClient** - HTTP wrapper with caching
2. **TopicClassifier** - GICS mapping (static first, LLM fallback later)
3. **Basic StockScreener** - Fetch stocks by industry, no filters

**Why:** Establishes data access layer. No point building business logic on broken data fetching.

### Phase 2: Filtering
4. **FilterCriteria dataclass**
5. **StockScreener with filters** - Client-side filtering
6. **FinancialDataFetcher** - Earnings retrieval

**Why:** Filtering is a core user requirement. Keep it simple (in-memory) first.

### Phase 3: Summarization
7. **LLMAnalyzer** - Single-stock summary generation
8. **EarningsSummary schema** - Structured output definition
9. **Prompt templates** - System prompt, few-shot examples

**Why:** LLM integration is the novel part. Build and test prompts with small data first.

### Phase 4: Integration & Polish
10. **Pipeline orchestration** - Connect all stages
11. **Error handling** - Partial results, retry logic
12. **Caching layer** - Reduce API costs

**Why:** Integration last. Verify each component works independently before wiring together.

---

## Data Schema

### Input
```python
@dataclass
class UserQuery:
    topic: str                    # "AI Chips"
    time_period: str              # "Q3 2024" or "FY 2024"
    filters: FilterCriteria       # Optional filtering criteria
```

### Internal
```python
@dataclass
class GICSIndustry:
    sector: str                   # "Technology"
    industry: str                 # "Semiconductors"

@dataclass
class Stock:
    ticker: str
    company_name: str
    industry: GICSIndustry
    market_cap: float
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    price: float
```

### Output
```python
@dataclass
class EarningsSummary:
    ticker: str
    company_name: str
    industry: str
    period: str
    business_model: str
    revenue_highlight: str
    profit_highlight: str
    competitive_position: str
    key_risks: List[str]
    confidence_score: float
```

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Pipeline architecture | HIGH | Standard pattern for ETL + AI systems |
| Component boundaries | HIGH | Clear separation of concerns |
| Data flow | HIGH | Linear flow well-suited for this use case |
| Build order | MEDIUM | Phases are logical but may need adjustment based on MVP scope |
| Scalability estimates | MEDIUM | Based on FMP API limits; actual limits need verification |

---

## Sources

- **Pipeline pattern:** Enterprise Integration Patterns (Hohpe & Woolf)
- **LLM structured output:** OpenAI API best practices, Anthropic function calling
- **Financial API patterns:** FMP API documentation (needs verification)
- **Circuit breaker:** Michael Nygard's Release It!

---

*Architecture research: 2026-03-25*
