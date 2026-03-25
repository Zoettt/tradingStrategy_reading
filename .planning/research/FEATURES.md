# Feature Landscape: Financial Report Interpretation System

**Domain:** Financial analysis tool (topic-to-earnings-summary pipeline)
**Researched:** 2026-03-25
**Confidence:** MEDIUM (web search unavailable, based on domain knowledge)

## Executive Summary

A Financial Report Interpretation System takes a topic + time period, identifies relevant US stocks, filters by financial metrics, fetches earnings reports, and generates summaries. The market includes established players (Bloomberg Terminal, FactSet, Refinitiv) and newer entrants (Perplexity Finance, AlphaStack, Arc).

This research categorizes features into table stakes (must-have), differentiators (competitive advantage), and anti-features (deliberately avoided).

---

## Table Stakes

Features users expect immediately. Missing these = product is not viable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Topic-to-ticker mapping** | Users enter topics, expect relevant stocks | Medium | Requires NLP/classification layer |
| **Financial metric filtering** | Market cap, PE, PB, price are standard filters | Low | Standard SQL/filter operations |
| **Earnings date filtering** | Users want reports within a time window | Low | Date range query |
| **Earnings report fetching** | Core value proposition | Medium | API integration required |
| **Business summary generation** | Users want digestible output | Medium | LLM call with financial prompt engineering |
| **Stock ticker resolution** | Symbol ambiguity is common | Low | Mapping table or API |
| **Result pagination** | Many stocks can match a topic | Low | Standard UI pattern |

### Detailed Table Stakes Requirements

#### Topic-to-Ticker Mapping
- Input: Free-text topic (e.g., "AI chips", "cloud computing")
- Output: List of relevant stock tickers
- Approaches:
  - Keyword matching to company description/business segment
  - GICS sector/industry classification
  - LLM classification (higher accuracy, higher latency/cost)
- **Minimum viable:** Keyword + GICS mapping table

#### Financial Metric Filtering
- **Market Cap:** Large-cap (>10B), Mid-cap (2-10B), Small-cap (<2B)
- **P/E Ratio:** Numeric range filter, handle negative earnings
- **P/B Ratio:** Numeric range filter, handle negative book value
- **Price:** Numeric range filter
- **Data sources:** Company overview endpoints from financial APIs

#### Earnings Report Fetching
- Must support: Latest earnings date, EPS, revenue, guidance
- Should support: Earnings call transcript (for richer summaries)
- **Data sources:** Alpha Vantage, Financial Modeling Prep, IEX Cloud

#### Business Summary Generation
- Input: Earnings report data (financials + transcript if available)
- Output: 3-5 paragraph business summary with key metrics highlighted
- **Prompt engineering:** Must include financial context, avoid hallucinations
- **Model choice:** GPT-4o mini for cost-efficiency, Claude Haiku for quality

---

## Differentiators

Features that set the product apart. Not expected, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Earnings comparison** | Side-by-side diff of same-quarter companies | High | Diff algorithm + UI |
| **Trend analysis** | Quarter-over-quarter metrics trajectory | Medium | Historical data required |
| **Sentiment scoring** | Bullish/bearish signals from transcript | Medium | Requires LLM + scoring rubric |
| **Estimate vs actual** | Beat/miss analysis for EPS and revenue | Low | Comparison calculation |
| **Peer benchmarking** | Compare metric against sector average | Medium | Requires sector benchmark data |
| **Related news aggregation** | Show relevant news during earnings period | Medium | News API integration |
| **Interactive filtering** | Real-time filter adjustment without re-fetch | Low | Client-side state management |
| **Export capabilities** | PDF/CSV export of summaries | Low | Library integration |

### Detailed Differentiator Requirements

#### Earnings Comparison
- User selects 2+ companies from results
- System shows side-by-side metrics
- Highlight relative performance (who beat estimates by more, higher revenue growth)
- **Complexity driver:** UI for comparison selection, diff algorithm

#### Trend Analysis
- Show 4-quarter or 8-quarter trajectory for key metrics
- Revenue growth rate, EPS trend, margin evolution
- **Data requirement:** Historical earnings data (deeper API calls)

#### Sentiment Scoring
- Score transcript as Bullish / Neutral / Bearish
- Provide per-section scores (guidance section vs risk factors)
- **Approach:** LLM with structured output + confidence score

#### Estimate vs Actual Analysis
- Fetch consensus estimates from API
- Calculate beat/miss percentage
- Flag guidance changes (upgrades/downgrades)

#### Peer Benchmarking
- Show how company metrics compare to sector median
- Requires sector classification + aggregated sector data
- **Data source:** Sector averages from financial APIs or calculated from available data

---

## Anti-Features

Things to deliberately NOT build (unless explicitly requested).

| Anti-Feature | Why Avoid | What To Do Instead |
|--------------|-----------|-------------------|
| **Real-time stock prices** | Not relevant to earnings analysis, adds API cost | Show latest closing price only |
| **Trading signals/buy/sell recommendations** | Regulatory risk, not the product scope | Focus on information, not advice |
| **Technical analysis (charting, indicators)** | Different use case entirely | Keep scope to fundamental analysis |
| **Options/futures data** | Separate market segment | Future product line |
| **Non-US markets (initial launch)** | GICS/API complexity doubles | US-only MVP |
| **Portfolio tracking** | Different product entirely | Links to portfolio tools |
| **Automatic re-ranking of results by "best opportunity"** | Subjective, regulatory risk | Present filters, let user decide |
| **Social sentiment (Twitter, Reddit)** | Unreliable, high noise | Use official guidance/transcripts only |

---

## Feature Dependencies

```
Topic Input
    └── Topic-to-Ticker Mapping
            └── GICS Classification (optional for better accuracy)
                    └── Stock Screener (filter by metrics)
                            └── Earnings Data Fetch
                                    └── Summary Generation
                                            └── (Optional) Comparison Mode
                                            └── (Optional) Trend Analysis
```

**Critical path (MVP):**
1. Topic-to-ticker mapping
2. Financial metric filtering
3. Earnings data fetching
4. Summary generation

**Post-MVP (differentiators):**
5. Estimate vs actual
6. Peer benchmarking
7. Trend analysis
8. Comparison mode

---

## MVP Recommendation

### Phase 1: Core Loop (Table Stakes Only)
Prioritize in order:
1. Topic-to-ticker mapping (keyword matching + GICS lookup table)
2. Financial metric filters (market cap, PE, PB, price)
3. Earnings date filter
4. Earnings data fetch (EPS, revenue, guidance from API)
5. LLM summary generation (structured prompt, 3-5 paragraphs)

**Defer:**
- Sentiment scoring (requires transcript access, higher API cost)
- Trend analysis (requires historical data accumulation)
- Comparison mode (UI complexity, not core use case)

### Phase 2: Differentiators
Add:
- Estimate vs actual beat/miss
- Peer benchmarking
- Interactive re-filtering without page reload

### Phase 3: Advanced
- Earnings comparison (side-by-side diff)
- Trend charts (quarter-over-quarter)
- Sentiment scoring (if transcripts accessible)

---

## Sources

- **Confidence: LOW** (web search unavailable during research)
- **Based on:** Domain knowledge of financial data APIs and competitive analysis of Bloomberg, Alpha Vantage, Perplexity Finance, Arc by Arc Investments
- **Validation needed:** Confirm specific API capabilities and pricing for chosen data providers

### Recommended Data Providers (Need Verification)
| Provider | Strengths | Limitations |
|---------|-----------|-------------|
| Alpha Vantage | Earnings calendar, EPS data, sentiment-enriched transcripts | Rate limits (25-75 req/day on free tier) |
| Financial Modeling Prep | Comprehensive financials, easy API design | Free tier limited |
| IEX Cloud | Real-time-ish prices, good fundamentals | Less focus on earnings |
| SEC EDGAR (free) | Primary source for 10-K/10-Q | No summarization, raw filings |

### GICS Resources
- [GICS Hierarchy](https://www.msci.com/our-solutions/indexes/gics) - Official GICS classification
- 11 sectors, 24 industry groups, 69 industries, 158 sub-industries

---

## Open Questions

1. **Data provider selection:** Which API provides best coverage + cost for earnings data?
2. **Transcript access:** Are earnings call transcripts available via any affordable API?
3. **GICS mapping:** Is there a free/open GICS-to-keyword mapping dataset?
4. **Summary quality:** What prompt structure produces reliable financial summaries without hallucinations?
5. **Latency tolerance:** Users expect earnings summaries quickly — what is acceptable response time?
