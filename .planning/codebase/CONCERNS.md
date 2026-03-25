# Codebase Concerns

**Analysis Date:** 2026-03-25

## Tech Debt

**Synthetic Option Data in Backtesting:**
- Issue: Backtest simulation uses `generate_synthetic_option_data()` which creates artificial Black-Scholes prices instead of real market data
- Files: `src/data_fetcher.py` (lines 99-174), `main.py` (lines 37-41)
- Impact: Backtest results are unrealistic - no bid/ask spreads, no liquidity considerations, perfect delta calculations
- Fix approach: Integrate with `OptionStorage` to use historical IBKR option data when available, or mark backtest as synthetic-only

**Hardcoded Configuration Values:**
- Issue: Configuration class has hardcoded defaults in `config/settings.py`
- Files: `config/settings.py` (lines 7-42)
- Impact: Changing stock symbol requires code change, not config change; protective put values are static
- Fix approach: Move to YAML/JSON config file with environment variable overrides

**Duplicate Import in main.py:**
- Issue: `calculate_delta` imported twice (line 14 and line 16)
- Files: `main.py` (lines 14-16)
- Impact: Minor confusion, no runtime error
- Fix approach: Remove duplicate import on line 16

**ibkr_fetcher.py sys.path Manipulation:**
- Issue: Hardcoded absolute path inserted into sys.path at lines 6-7
- Files: `src/ibkr_fetcher.py` (lines 6-7)
- Impact: Code breaks when run from different directories or on different machines
- Fix approach: Use relative imports or package installation (pip install -e .)

**Nepotistic Stock Symbol Throughout Codebase:**
- Issue: Stock symbol "0981.HK" (SMIC) hardcoded in multiple places - config, data_fetcher, live scripts
- Files: `config/settings.py` (line 42), `src/data_fetcher.py` (lines 222-224), `scripts/live_option_scanner.py` (line 18)
- Impact: Cannot backtest different stocks without code changes
- Fix approach: Make stock_symbol a required constructor parameter or environment variable

**DuckDB Connection Not Closed Properly:**
- Issue: `OptionStorage.__init__` creates connection but no context manager or guaranteed close
- Files: `src/option_storage.py` (lines 37-42)
- Impact: Connection leaks, especially in long-running scanner processes
- Fix approach: Add context manager protocol (`__enter__`/`__exit__`) and ensure `close()` is called

**Hong Kong Market Exchange Mismatch:**
- Issue: Scripts mention SEHK exchange but IBKR fetcher uses empty string ("") for futFopExchange, with comment that SEHK returns 0 chains
- Files: `src/ibkr_fetcher.py` (lines 97-105), `scripts/live_option_scanner.py` (lines 222-224)
- Impact: HK stock options may not fetch correctly, code is confusing about correct exchange
- Fix approach: Verify correct exchange for HK options (likely "SEHK" or "HKEX") and document

**Missing IBKR Connection Validation:**
- Issue: `IBKROptionFetcher.connect()` catches all exceptions and returns False with no logging
- Files: `src/ibkr_fetcher.py` (lines 56-65)
- Impact: Connection failures are silent - users cannot diagnose why live mode fails
- Fix approach: Log exception details, provide diagnostic information (port check, TWS running check)

**Unused Ticker Storage in ibkr_fetcher:**
- Issue: `_tickers` and `_contracts` dicts are populated in `subscribe()` but never used; `add_option_chain()` populates result list but not internal state for streaming
- Files: `src/ibkr_fetcher.py` (lines 52-54, 107-131, 222-257)
- Impact: Streaming mode (`start_streaming`) cannot work because contracts are not tracked
- Fix approach: Populate `_contracts` in `add_option()` and `add_option_chain()`, use `_tickers` in polling loop

**Inconsistent Option Type Codes:**
- Issue: `InMemoryOptionData` uses 'c'/'p' but `OptionSnapshot` and most of the codebase uses 'call'/'put'
- Files: `src/data_fetcher.py` (line 68), `src/option_schemas.py` (line 14), `src/ibkr_fetcher.py` (line 127)
- Impact: Silent mismatch when storing/retrieving prices; 'c' won't match 'call'
- Fix approach: Standardize on 'call'/'put' throughout

**No Input Validation on External Data:**
- Issue: `StockDataFetcher.calculate_volatility()` will throw if yfinance returns insufficient data
- Files: `src/data_fetcher.py` (lines 38-49)
- Impact: Crashes on holiday periods or when symbol not found
- Fix approach: Add try/except with fallback or error message

## Known Bugs

**Streaming Mode Non-Functional:**
- Bug: `start_streaming()` in `IBKROptionFetcher` iterates over empty `_tickers` dict
- Files: `src/ibkr_fetcher.py` (lines 297-312)
- Trigger: Call `start_streaming()` after `add_option_chain()`
- Workaround: Use `fetch_quote()` in polling loop instead

**Delta-Based Strike Selection Uses Wrong Time:**
- Bug: In `simulator.find_option_for_delta()`, sigma volatility is calculated once but time to expiry is calculated from simulation start date, not current date
- Files: `src/simulator.py` (lines 287-300)
- Impact: Delta estimates become increasingly inaccurate as simulation progresses
- Workaround: None - backtest results will drift from theoretical

** Protective Put Not Reflected in State:**
- Bug: `AccountConfig.protective_put_strike/premium/expiry` are defined but never used in simulation
- Files: `config/settings.py` (lines 32-34), `src/simulator.py`
- Impact: Strategy claims to include protective put but backtest ignores its cost
- Workaround: Manually adjust cumulative P&L calculation

**Duplicate Option Price Lookup:**
- Bug: `find_option_for_delta()` looks up strike prices from `option_data` but the main loop in `simulator.run()` also calls `_open_new_position()` which calls `find_option_for_delta()` again
- Files: `src/simulator.py` (lines 249-271, 273-365)
- Impact: Redundant computation, potential for state inconsistency if called twice

## Security Considerations

**No Secrets Management:**
- Risk: IBKR connection credentials (host, port, client_id) passed as constructor args with no authentication
- Files: `src/ibkr_fetcher.py` (lines 41-54)
- Current mitigation: Defaults to localhost, client_id is not a secret
- Recommendations: Add TWS API password support, use environment variables for credentials

**DuckDB File Permissions:**
- Risk: Database file created with default permissions may be readable by other users
- Files: `src/option_storage.py` (line 40)
- Current mitigation: Default filesystem permissions
- Recommendations: Set restrictive file permissions (0o600) on database file

**Hardcoded Path in sys.path:**
- Risk: `src/ibkr_fetcher.py` adds `/Users/guanjie/Desktop/guanjie/ibkr/src` to path
- Files: `src/ibkr_fetcher.py` (line 7)
- Current mitigation: None
- Recommendations: Use proper package installation or relative imports

## Performance Bottlenecks

**Option Chain Enumeration:**
- Problem: `add_option_chain()` creates ALL possible option contracts (every expiry/strike/right combination) without pagination
- Files: `src/ibkr_fetcher.py` (lines 107-131)
- Cause: No filtering by moneyness or expiration; fetches entire chain
- Improvement path: Add filters for near-ATM strikes only, limit to nearest N expirations

**Sequential Quote Fetching:**
- Problem: Live scanners fetch quotes one-by-one with 0.3-0.5s sleep between each
- Files: `scripts/live_option_scanner.py` (lines 100-106, 136-142), `scripts/batch_option_scanner.py` (lines 99-106)
- Cause: No parallel fetching, IBKR rate limiting requires delays
- Improvement path: Use IBKR's batch market data request, or async with multiple connections

**DuckDB Insert Performance:**
- Problem: Each `insert_batch()` creates a DataFrame, registers a view, inserts, then drops view
- Files: `src/option_storage.py` (lines 48-77)
- Cause: Inefficient for single-row inserts in polling loop
- Improvement path: Use `COPY` command for bulk loads, or accumulate inserts and batch commit

**Volatility Calculation on Every Option Lookup:**
- Problem: `find_option_for_delta()` calculates volatility once per call but calls `calculate_delta()` for every strike
- Files: `src/simulator.py` (lines 296-300)
- Cause: No caching of delta calculations
- Improvement path: Pre-compute delta table for all strikes at given expiry, reuse

## Fragile Areas

**Black-Scholes Exception Handling:**
- Files: `src/option_pricing.py` (lines 35-38, 60-63)
- Why fragile: Silent `return 0.0` on any exception including NaN inputs, masking real errors
- Safe modification: Add logging for exceptions, distinguish between invalid inputs and calculation failures
- Test coverage: Only happy path tested

**Assignment Check Logic:**
- Files: `src/strategy.py` (lines 84-94)
- Why fragile: Uses simple >/< comparison without considering time value or probability
- Safe modification: Should use intrinsic value only at expiration
- Test coverage: Basic cases tested

**Report Generation in Logger:**
- Files: `src/reporter.py` (lines 69-95)
- Why fragile: `multiplier` parameter has wrong default (line 62), different from config
- Safe modification: Use `config.account.option_multiplier` consistently
- Test coverage: Not tested

## Scaling Limits

**DuckDB Single-File Architecture:**
- Current capacity: Suitable for ~1M rows (tens of MB)
- Limit: Single file, no horizontal scaling, backup complexity
- Scaling path: Partition by symbol and date, or migrate to columnar database (ClickHouse, BigQuery)

**In-Memory Option Data for Backtesting:**
- Current capacity: Limited by available RAM; all prices held in dict
- Limit: Long backtest periods with many strikes/expirations will OOM
- Scaling path: Load option data lazily by date range, use memory-mapped files

**IBKR API Rate Limits:**
- Current capacity: ~50-100 quotes per second with brief sleeps
- Limit: Real-time monitoring of large option chains (>1000 contracts) not feasible
- Scaling path: Multiple client IDs, or use IBKR's native batch requests

## Dependencies at Risk

**ib_insync:**
- Risk: Active but small library; breaking changes possible
- Impact: `src/ibkr_fetcher.py` tightly coupled to ib_insync API
- Migration plan: Abstract fetcher behind interface, swap implementation if needed

**py_vollib:**
- Risk: Package has known numerical stability issues with extreme parameters
- Impact: `src/option_pricing.py` uses it for all BS calculations
- Migration plan: Implement fallback to scipy.stats.norm.cdf directly

**yfinance:**
- Risk: Unofficial API, can break without notice
- Impact: `src/data_fetcher.py` uses it for all stock price fetching
- Migration plan: Abstract fetcher behind interface, use pandas_datareader or official API as fallback

## Missing Critical Features

**Live Mode Not Implemented:**
- Problem: `main.py` line 48 prints "Live mode not yet implemented"
- Blocks: Cannot run strategy against real-time data

**No Position Tracking Between Sessions:**
- Problem: StrategyState has no persistence
- Blocks: Restarting live scanner loses all state

**No Greeks Risk Management:**
- Problem: No gamma/vega/theta limits or monitoring
- Blocks: Cannot manage portfolio-level risk

**No Assignment Probability Calculation:**
- Problem: Assignment check uses deterministic rule, not probability
- Blocks: Cannot distinguish between 90% and 10% ITM probability

**No Transaction Cost Modeling Beyond Commission:**
- Problem: Commission is fixed 22 HKD/contract, no slippage modeling
- Blocks: Backtest accuracy for real-world profitability

## Test Coverage Gaps

**Option Pricing Edge Cases:**
- What's not tested: Negative stock prices, zero volatility, zero time to expiry, extreme strikes
- Files: `src/option_pricing.py`
- Risk: Silent failures (returning 0.0) could propagate to large errors
- Priority: High

**Simulator State Transitions:**
- What's not tested: Full option wheel cycle (call -> put -> call), roll decisions, assignment handling
- Files: `src/simulator.py`
- Risk: State machine bugs could cause wrong position sizing or missing trades
- Priority: High

**IBKR Connection Resilience:**
- What's not tested: Reconnection after disconnect, timeout handling, invalid responses
- Files: `src/ibkr_fetcher.py`
- Risk: Live scanner crashes on network hiccup
- Priority: Medium

**DuckDB Query Edge Cases:**
- What's not tested: Empty result sets, corrupted database, concurrent access
- Files: `src/option_storage.py`
- Risk: Data loss or corruption not detected
- Priority: Medium

---

*Concerns audit: 2026-03-25*
