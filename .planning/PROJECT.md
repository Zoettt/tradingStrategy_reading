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

(None yet — this is a greenfield project)

### Active

**Core Flow:**
- [ ] **Topic Search**: User inputs a topic (e.g., "AI Chips") + time period
- [ ] **Industry Matching**: Match topic to relevant GICS sectors/industries, return list of US stocks in those categories
- [ ] **Stock Filtering**: Filter results by market cap, PE, PB, price
- [ ] **Earnings Summaries**: For each filtered stock, generate structured summary covering:
  - Business model overview (how the company makes money)
  - Recent performance (revenue, profit, growth)
  - Competitive landscape (key competitors, market position)
  - Risk factors (main business risks)

**Data Source:**
- Primary: Structured financial data from FMP / Yahoo Finance API
- Supporting: SEC EDGAR for XBRL fundamentals if needed

**Output:**
- Individual summary per stock (one JSON/markdown document per ticker)
- Each summary includes: company name, ticker, industry, period, business description, key metrics, competitive position, risks

### Out of Scope

- Raw PDF/HTML filing parsing (LLM analysis of unstructured data)
- Non-US markets (A-share, HK stocks)
- Financial ratio calculations from scratch (use pre-calculated from data provider)
- Portfolio management or trading signals
- Real-time data streaming

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Topic→Industry matching via GICS | Standard classification, maps well to financial data | Pending research |
| Individual summaries per stock | Better for comparison and focused analysis | — |
| Filter: market cap, PE, PB, price | Most common screening criteria for retail investors | — |
| Structured data only (no raw PDF parsing) | Fastest path to MVP, reliable data quality | — |

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-25 after initialization*
