# Codebase Structure

**Analysis Date:** 2026-03-25

## Directory Layout

```
/Users/guanjie/Desktop/guanjie/tradingStrategy_test/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── config/                  # Configuration
│   ├── __init__.py
│   └── settings.py          # Config dataclasses
├── src/                     # Core source code
│   ├── __init__.py
│   ├── strategy.py          # Option wheel state machine
│   ├── simulator.py         # Backtest orchestration
│   ├── data_fetcher.py     # Stock + option data fetching
│   ├── ibkr_fetcher.py     # IBKR live data interface
│   ├── option_pricing.py    # Black-Scholes pricing
│   ├── option_schemas.py    # Data models
│   ├── option_storage.py    # DuckDB storage
│   └── reporter.py          # CSV logging
├── tests/                   # Unit tests
│   ├── test_*.py
│   └── test_integration.py
├── scripts/                 # Ad-hoc scripts
│   ├── live_*.py           # Live testing scripts
│   ├── test_*.py           # IBKR API test scripts
│   ├── batch_option_scanner.py
│   └── hk_option_scanner.py
├── data/                    # Data storage (runtime created)
│   ├── options.db          # DuckDB database
│   └── parquet/            # Parquet archives
├── docs/                    # Documentation
└── .planning/              # GSD planning docs
```

## Directory Purposes

**`main.py`:**
- Purpose: Primary entry point for backtest mode
- Contains: CLI argument parsing, mode routing
- Key file for running simulations

**`config/`:**
- Purpose: Centralized configuration management
- Contains: `settings.py` with all config dataclasses
- Key files: `config/settings.py`

**`src/`:**
- Purpose: Core business logic
- Contains: All modules for fetching, pricing, simulation, strategy, storage, reporting
- Key files:
  - `src/simulator.py` - Main simulation orchestrator
  - `src/strategy.py` - Strategy state machine
  - `src/data_fetcher.py` - Data abstraction layer
  - `src/ibkr_fetcher.py` - IBKR API wrapper

**`tests/`:**
- Purpose: Unit and integration tests
- Contains: Test files matching source modules
- Key files: `test_simulator.py`, `test_strategy.py`, `test_integration.py`

**`scripts/`:**
- Purpose: Ad-hoc scripts for live data testing
- Contains: Various `test_*.py` and `live_*.py` scripts
- Note: Not part of main application, used for manual testing

**`data/`:**
- Purpose: Runtime data storage
- Contains: DuckDB database, Parquet exports
- Generated at runtime, not committed to git

**`docs/`:**
- Purpose: Documentation
- Contains: Project docs and superpowers documentation

## Key File Locations

**Entry Points:**
- `main.py`: CLI entry point for backtest mode

**Configuration:**
- `config/settings.py`: All dataclass-based configuration

**Core Logic:**
- `src/simulator.py`: `BacktestSimulator` class
- `src/strategy.py`: `StrategyState`, `Position`, `OptionWheelState`
- `src/data_fetcher.py`: `StockDataFetcher`, `InMemoryOptionData`, `IBKROptionData`
- `src/ibkr_fetcher.py`: `IBKROptionFetcher` (low-level IBKR)

**Pricing:**
- `src/option_pricing.py`: Black-Scholes functions

**Data Models:**
- `src/option_schemas.py`: `OptionSnapshot`, `WatchlistEntry`
- `src/reporter.py`: `OperationRecord`, `OperationLogger`

**Storage:**
- `src/option_storage.py`: `OptionStorage` with DuckDB

## Naming Conventions

**Files:**
- Python modules: `lowercase_with_underscores.py`
- Test files: `test_<module_name>.py`
- Config files: `settings.py`

**Classes:**
- PascalCase: `BacktestSimulator`, `StrategyState`, `IBKROptionFetcher`
- Suffix patterns: `*Fetcher`, `*Storage`, `*Logger`, `*Config`

**Functions:**
- snake_case: `calculate_option_price`, `should_roll`, `check_assignment`
- Helper prefix: `_nan_safe_float`, `_normalize_symbol`

**Dataclasses:**
- PascalCase: `OptionSnapshot`, `OperationRecord`, `Position`

**Enums:**
- PascalCase: `OptionWheelState`

**Constants:**
- UPPER_SNAKE_CASE: `DEFAULT_CONFIG`

## Where to Add New Code

**New Feature:**
- Primary code: `src/<feature_name>.py`
- Tests: `tests/test_<feature_name>.py`

**New IBKR Integration:**
- Implementation: `src/ibkr_fetcher.py` (extend `IBKROptionFetcher`)
- Live testing: `scripts/test_<feature>.py`

**New Strategy Logic:**
- Implementation: `src/strategy.py` (add to state machine)
- Simulation: `src/simulator.py` (add handling in `run()`)

**New Data Source:**
- Implementation: `src/data_fetcher.py` (add new fetcher class)
- Interface: Match existing `get_price()`, `get_available_strikes()` patterns

**New Storage Backend:**
- Implementation: `src/option_storage.py` (add new storage class)
- Maintain DuckDB as primary, add alternative backends if needed

**Configuration Changes:**
- Modify: `config/settings.py`
- Add new dataclass or extend existing `Config`

## Special Directories

**`data/`:**
- Purpose: Runtime data storage
- Generated: Yes (by `OptionStorage`)
- Committed: No (in `.gitignore`)

**`.planning/codebase/`:**
- Purpose: GSD planning documents
- Generated: Yes
- Committed: Yes

**`.omc/`:**
- Purpose: OMC orchestration state
- Generated: Yes
- Committed: No

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-03-25*
