# Architecture

**Analysis Date:** 2026-03-25

## Pattern Overview

**Overall:** Layered Architecture with State Machine

**Key Characteristics:**
- Clear separation between data fetching, strategy logic, simulation engine, and reporting
- State machine pattern for option wheel strategy transitions
- Dual-mode operation: backtest (synthetic data) and live (IBKR API)
- Configuration-driven design using Python dataclasses

## Layers

**Entry Layer:**
- Purpose: CLI interface and mode selection
- Location: `main.py`
- Contains: Argument parsing, mode routing (backtest/live)
- Depends on: All lower layers
- Used by: CLI invocation

**Simulation Layer:**
- Purpose: Orchestrate backtest execution
- Location: `src/simulator.py`
- Contains: `BacktestSimulator` class
- Depends on: Config, Strategy, Reporter, Option Pricing, Data Fetcher
- Used by: `main.py`

**Strategy Layer:**
- Purpose: Option wheel state machine and position management
- Location: `src/strategy.py`
- Contains: `StrategyState`, `Position`, `OptionWheelState`, decision functions
- Depends on: None (pure logic)
- Used by: `src/simulator.py`

**Data Fetching Layer:**
- Purpose: Fetch stock prices and option data from multiple sources
- Location: `src/data_fetcher.py`, `src/ibkr_fetcher.py`
- Contains: `StockDataFetcher` (yfinance), `InMemoryOptionData`, `IBKROptionFetcher`, `IBKROptionData`
- Depends on: yfinance, ib_insync, ibkr-common
- Used by: `src/simulator.py`

**Pricing Layer:**
- Purpose: Black-Scholes option pricing and Greeks calculation
- Location: `src/option_pricing.py`
- Contains: Price/delta calculation functions using py_vollib
- Depends on: py_vollib, numpy
- Used by: `src/simulator.py`, `src/data_fetcher.py`

**Storage Layer:**
- Purpose: Persist option snapshots to DuckDB and Parquet
- Location: `src/option_storage.py`
- Contains: `OptionStorage` class
- Depends on: duckdb, pandas
- Used by: Live mode scripts

**Reporting Layer:**
- Purpose: Log strategy operations to CSV
- Location: `src/reporter.py`
- Contains: `OperationLogger`, `OperationRecord`, `format_option_name`
- Depends on: csv module
- Used by: `src/simulator.py`

**Configuration Layer:**
- Purpose: Centralized parameter management
- Location: `config/settings.py`
- Contains: `Config`, `StrategyConfig`, `BacktestConfig`, `AccountConfig` dataclasses
- Depends on: None (pure data)
- Used by: All layers

## Data Flow

**Backtest Flow:**

1. `main.py` parses CLI args, creates `BacktestSimulator` with `Config`
2. `BacktestSimulator` fetches historical stock prices via `StockDataFetcher`
3. `generate_synthetic_option_data()` creates synthetic options using Black-Scholes
4. `simulator.run()` iterates through trading days
5. For each day, checks expiration/roll conditions via `should_roll()`, `check_assignment()`
6. `find_option_for_delta()` selects vertical spreads based on target delta
7. `OperationLogger` records each trade with `_handle_assignment()`, `_handle_expiry()`, `_handle_roll()`
8. Final results saved to CSV via `logger.save_csv()`

**Live Flow:**

1. `IBKROptionFetcher.connect()` establishes IBKR TWS connection
2. `add_option_chain()` subscribes to full option chain
3. `start_streaming()` begins polling loop with callback
4. `IBKROptionData` caches snapshots in `_cache`
5. `OptionStorage.insert_batch()` persists to DuckDB

**State Transitions:**

```
HOLDING_CALL --(call assigned)--> HOLDING_PUT
HOLDING_PUT --(put assigned)--> HOLDING_CALL
HOLDING_CALL --(roll)--> HOLDING_CALL (new position)
HOLDING_PUT --(roll)--> HOLDING_PUT (new position)
```

## Key Abstractions

**OptionWheelState (Enum):**
- Purpose: Represents the two states of the wheel strategy
- Location: `src/strategy.py`
- Pattern: Simple enum with two values

**Position (Dataclass):**
- Purpose: Represents an option position with strike, expiry, type, prices
- Location: `src/strategy.py`
- Pattern: Data carrier with optional protective leg

**StrategyState (Dataclass):**
- Purpose: Maintains current state, position, stock holding, cumulative premium
- Location: `src/strategy.py`
- Pattern: Mutable state container

**OptionSnapshot (Dataclass):**
- Purpose: Real-time option data with Greeks
- Location: `src/option_schemas.py`
- Pattern: Immutable data record with validation

**InMemoryOptionData:**
- Purpose: Dictionary-based option price lookup for backtesting
- Location: `src/data_fetcher.py`
- Pattern: Repository interface with get_price(), get_available_strikes()

**IBKROptionData:**
- Purpose: IBKR-backed live option data with caching
- Location: `src/data_fetcher.py`
- Pattern: Repository with connect/disconnect lifecycle

## Entry Points

**`main.py`:**
- Location: `/Users/guanjie/Desktop/guanjie/tradingStrategy_test/main.py`
- Triggers: CLI execution (`python main.py`)
- Responsibilities: Mode selection, config loading, simulator orchestration

**`src/ibkr_fetcher.py` (direct use):**
- Location: `/Users/guanjie/Desktop/guanjie/tradingStrategy_test/src/ibkr_fetcher.py`
- Triggers: Scripts in `scripts/` directory
- Responsibilities: Low-level IBKR API interaction

**Scripts (`scripts/`):**
- Location: `/Users/guanjie/Desktop/guanjie/tradingStrategy_test/scripts/`
- Triggers: Direct Python execution for live testing
- Responsibilities: Ad-hoc live data fetching and verification

## Error Handling

**Strategy:** Graceful degradation with fallback values

**Patterns:**
- Option pricing failures return 0.0 (`calculate_option_price`, `calculate_delta`)
- IBKR connection failures return False (`connect()`)
- Invalid option data returns None (`fetch_quote`, `subscribe`)
- NaN/None values sanitized via `_nan_safe_float()`, `_nan_safe_int()`

## Cross-Cutting Concerns

**Logging:** CSV-based via `OperationLogger`, no structured logging library

**Validation:** `OptionSnapshot.validate()` checks bid/ask/delta bounds

**Configuration:** Dataclass-based config in `config/settings.py`, no external file loading by default

**Data Storage:** DuckDB for querying, Parquet for archival

---

*Architecture analysis: 2026-03-25*
