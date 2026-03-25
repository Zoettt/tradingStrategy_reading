# Domain Pitfalls: Financial Report Interpretation System

**Project:** FRIS (Financial Report Interpretation System)
**Researched:** 2026-03-25
**Confidence:** MEDIUM (web search unavailable; based on domain literature and established patterns)

## Critical Pitfalls

Mistakes that cause user distrust, incorrect investment decisions, or system rewrites.

---

### Pitfall 1: LLM Hallucination on Financial Facts

**What goes wrong:** The LLM generates plausible-sounding but factually incorrect financial data — wrong revenue numbers, non-existent partnerships, incorrect growth percentages.

**Why it happens:**
- LLMs lack real-time data access; they generate from training distribution
- Financial terminology is ambiguous (EBIT vs EBITDA confusion propagates)
- Model may "fill in" missing data with fabricated but plausible values
- User phrasing "tell me about Company X's margins" invites confabulation

**Consequences:**
- User makes investment decision based on fabricated data
- System loses all credibility for factual queries
- Potential regulatory liability if used for financial advice

**Prevention:**
1. **Grounded generation**: Always retrieve actual financial data before summarizing; LLM must cite specific data points from API responses
2. **Structured output schema**: Force JSON with explicit source attribution per field
3. **Uncertainty injection**: System should say "I don't have the exact figure" rather than guess
4. **Fact verification layer**: Cross-check LLM summary against source data before returning

**Warning signs (detection):**
- LLM generates numbers not present in source data
- Summary contains temporal claims ("increased 30%") without corresponding data
- Vague qualifiers without specifics ("strong growth", "healthy margins")

**Phase mapping:** Core implementation — hallucinations must be prevented at the data fetching + LLM integration layer

---

### Pitfall 2: Topic-Industry Classification Mismatch

**What goes wrong:** User searches "AI Chips" and gets semiconductor stocks correctly, but misses NVIDIA (classified under "Technology" not "Semiconductors") or gets irrelevant "AI" pure-play software companies.

**Why it happens:**
- GICS classification is lagging — NVIDIA is Technology, not Semiconductors
- Topic synonyms not mapped (e.g., "EV" = "Electric Vehicles" = "Auto Manufacturers")
- Multi-industry companies get single classification
- Company business descriptions evolve faster than classification updates

**Consequences:**
- Incomplete coverage — user misses relevant stocks
- False positives — irrelevant stocks included
- User loses confidence in filtering logic

**Prevention:**
1. **Multi-classification search**: Query both GICS sector AND keyword match on business description
2. **Topic ontology**: Build synonym mapping for common investor topics (EV, AI, Cloud, etc.)
3. **Soft matching**: Include companies where business description contains topic keywords, not just GICS code
4. **Manual override list**: Maintain curated lists for broad topics (AI = {NVDA, AMD, INTC, ...})

**Warning signs:**
- User feedback: "missing Company X" for popular topic
- Recall rate < 80% when tested against known relevant stocks
- High variance in result set sizes for similar topics

**Phase mapping:** Topic matching is a core algorithm problem — address in Phase 1 before expanding coverage

---

### Pitfall 3: Missing Data Cascade

**What goes wrong:** Stock passes filter criteria but has missing PE ratio → system crashes, returns error, or shows partial results with no explanation.

**Why it happens:**
- Young companies (IPO < 2 years) often have negative earnings → no PE
- Financial ratios are optional in data providers; some stocks lack PB
- API returns null vs 0 vs "N/A" inconsistently
- Filtering logic doesn't handle NULL gracefully

**Consequences:**
- Crashes on stocks with valid ticker but missing metrics
- Silent failures — user sees incomplete results with no explanation
- Incorrect filtering — null treated as "doesn't match" when it should be "unknown"

**Prevention:**
1. **Explicit NULL handling**: Define behavior for each metric (exclude vs include with annotation)
2. **Data quality scoring**: Return confidence level per stock based on data completeness
3. **Graceful degradation**: If PE is missing, note "PE not available" and still return summary
4. **Schema validation**: Validate required vs optional fields before processing

**Warning signs:**
- API returns error for valid ticker
- Results exclude legitimate stocks with missing optional fields
- Inconsistent null/0/"N/A" handling across different stocks

**Phase mapping:** Data handling — address when integrating financial data APIs

---

### Pitfall 4: Real-Time vs Delayed Data Confusion

**What goes wrong:** User sees "current price" that is 15-20 minutes delayed and makes trading decision on stale data.

**Why it happens:**
- Free tier APIs (Yahoo Finance, FMP free) provide delayed quotes (15-20 min)
- System doesn't explicitly state data latency
- Price shown looks "live" but isn't
- User assumes real-time and acts on it

**Consequences:**
- User trades on stale prices
- Mismatch between displayed data and actual market
- Particular risk for volatile stocks or earnings announcements

**Prevention:**
1. **Explicit latency labeling**: Always show "Data delayed by X minutes" when applicable
2. **Timestamp all prices**: Include `data_timestamp` field on every quote
3. **Upgrade path documentation**: Note when real-time data requires paid tier
4. **User education**: Prompt warns "Prices may be delayed" on first interaction

**Warning signs:**
- Price data lacks timestamp
- User complaints about "wrong" prices during market hours
- No distinction between delayed and real-time tiers

**Phase mapping:** Data display — must be addressed before any user-facing release

---

## Moderate Pitfalls

### Pitfall 5: API Rate Limit Exhaustion

**What goes wrong:** System works for small queries but fails when user requests 50+ stocks — API returns 429 errors or account locked.

**Why it happens:**
- FMP free tier: 5 requests/minute, 250 requests/day
- Yahoo Finance (unofficial): stricter limits, IP-based blocking
- Batch requests not supported → individual calls per stock
- No request queuing or retry with backoff
- Economic events (earnings season) increase demand

**Consequences:**
- System fails during high-value use cases (earnings season)
- User sees cryptic error messages
- Cannot scale to full market scan

**Prevention:**
1. **Request batching**: Use FMP's batch endpoints where available
2. **Caching**: Cache financial data with TTL; don't refetch within 1 hour for same ticker
3. **Rate limit awareness**: Track request count, pause when approaching limits
4. **Exponential backoff**: Implement retry with jitter for 429 responses
5. **Request prioritization**: Fetch high-priority data first (filtered results) before detailed metrics

**Warning signs:**
- 429 errors appearing in logs
- Increasing latency as request count grows
- Free tier limits hit frequently

**Phase mapping:** API integration layer — implement before any production use

---

### Pitfall 6: LLM Cost Explosion

**What goes wrong:** Simple query generates 100+ LLM calls (one per stock), costing $10+ for a single user query.

**Why it happens:**
- Naive approach: one LLM call per stock for summary
- User queries broad topic → 200+ stocks → 200+ LLM calls
- No caching of LLM outputs
- Expensive model (GPT-4) used for simple summarization

**Consequences:**
- Cost per query becomes prohibitive
- Response time unacceptable (>60 seconds)
- Cannot serve many concurrent users

**Prevention:**
1. **Hierarchical summarization**: Summarize sector-level data first, stock-level only for filtered subset
2. **Cheap model for drafts**: Use GPT-3.5-turbo for initial extraction, GPT-4 only for final polish
3. **Batch LLM calls**: Send multiple stocks in single prompt (with careful token limits)
4. **Output caching**: Cache LLM summaries for same ticker + period combination
5. **Cost tracking**: Log cost per query, alert on anomalies

**Warning signs:**
- Cost per query > $0.50
- Response time > 30 seconds for single-stock query
- LLM token usage growing unbounded

**Phase mapping:** LLM integration — address before scaling user base

---

### Pitfall 7: Filter Logic Errors

**What goes wrong:** User sets PE < 20 but gets stocks with PE = N/A (negative earnings); price filter applies to wrong field.

**Why it happens:**
- NULL vs negative vs positive PE semantics confused
- Price field confusion (trailing price vs forward price vs 52-week range)
- Units mismatch (millions vs billions in market cap)
- Boundary conditions (≤20 vs <20) not explicit

**Consequences:**
- User gets unexpected results
- Wrong stocks filtered in/out
- Confusion about what "filter applied" actually means

**Prevention:**
1. **Explicit filter semantics**: Document exactly what each filter does (e.g., "PE < 20 means positive earnings with ratio below 20")
2. **NULL handling policy**: Clearly state whether N/A stocks are included or excluded
3. **Unit display**: Always show units in filter UI and results
4. **Filter summary**: Return "Showing X stocks matching filters (Y excluded due to missing data)"

**Warning signs:**
- User complaints about "wrong" filter results
- N/A stocks appearing where user expects excluded
- Results don't match manual calculation

**Phase mapping:** Filtering implementation — address when building stock screening feature

---

### Pitfall 8: Data Consistency Across Providers

**What goes wrong:** FMP shows different revenue than Yahoo Finance for same stock; system shows inconsistent metrics without explanation.

**Why it happens:**
- Different fiscal year definitions (some companies use non-calendar FY)
- Different accounting standards (US GAAP vs IFRS)
- Different data revision policies
- Unofficial vs official reported numbers
- Acquisitions/divestitures affecting historical comparisons

**Consequences:**
- User loses trust in data
- Cannot compare stocks across providers
- Apparent contradictions in financial picture

**Prevention:**
1. **Single source of truth**: Use one provider per metric, document which
2. **Provider attribution**: Always show which source provided each data point
3. **Fiscal year awareness**: Show fiscal year alongside metric ("FY2025 Revenue" vs "TTM Revenue")
4. **Consistency checks**: Alert when same metric differs >5% across providers

**Warning signs:**
- User reports "wrong" numbers that are actually from different providers
- Large discrepancies between sources for same stock/period
- No source attribution on metrics

**Phase mapping:** Data integration — establish source policy early

---

## Minor Pitfalls

### Pitfall 9: Earnings Report Timing Gaps

**What goes wrong:** User queries "last quarter" but gets results from 6 months ago because company reports annually, not quarterly.

**Why it happens:**
- Not all companies report quarterly (some mid-caps report semi-annually)
- Different fiscal calendars (Apple FY ends Sept, most end Dec)
- Data provider lags in posting latest reports
- "Last quarter" interpreted as calendar quarter, not fiscal quarter

**Prevention:**
1. **Report frequency display**: Show "Quarterly" vs "Annual" reporter badge per stock
2. **Date precision**: Show exact report date, not relative period
3. **Fiscal calendar awareness**: If available, show company's actual fiscal quarter dates

---

### Pitfall 10: Market Cap Classification Drift

**What goes wrong:** Large-cap filter excludes a stock that was mid-cap last quarter due to stock price drop.

**Why it happens:**
- Market cap classifications (large/mid/small) are relative to total market
- Thresholds change as total market value changes
- Daily price fluctuations shift cap within classification bands
- Stale classification data used

**Prevention:**
1. **Use current market cap values**: Don't rely on static classification; calculate from current price × shares outstanding
2. **Show actual cap**: Display "$48.2B" not "Large Cap"
3. **Date context**: Note "Market cap as of [date]"

---

## Phase-Specific Warning Summary

| Phase | Critical Pitfalls | Mitigation Priority |
|-------|-------------------|---------------------|
| **Phase 1: Core Infrastructure** | Rate limits, data consistency, missing data | Build error handling + caching first |
| **Phase 2: LLM Integration** | Hallucination, cost explosion | Grounded generation + cost controls |
| **Phase 3: Topic Matching** | Classification mismatch, filter logic | Multi-source matching + explicit filter semantics |
| **Production Release** | Real-time/delayed confusion | Latency labeling + timestamp all data |

---

## Research Confidence Notes

**HIGH confidence (verified in docs):**
- FMP API rate limits (from official pricing page knowledge)
- GICS classification structure and limitations

**MEDIUM confidence (established patterns):**
- LLM hallucination patterns and prevention strategies (well-documented in literature)
- Rate limit handling best practices (standard industry approach)
- Cost management for LLM APIs (documented by OpenAI, Anthropic)

**LOW confidence (needs validation):**
- Yahoo Finance API specific limits (unofficial, changes frequently)
- SEC EDGAR API exact rate limits (should verify with current docs)

---

## Gaps Needing Further Research

- **Yahoo Finance API limits**: Unofficial API, limits not documented; need live testing
- **FMP API behavior during market hours**: Whether limits tighten during trading
- **GICS 2024 updates**: Classification changes that may affect topic matching
- **LLM provider cost changes**: Prices update frequently; re-verify before production

---

## Sources

*Note: Web search was unavailable during research. Information based on:*
- FMP official documentation (historical knowledge)
- OpenAI/Anthropic LLM grounding literature
- SEC EDGAR API public documentation
- Industry best practices for financial data pipelines
- GICS classification standards documentation
