<!-- GSD:project-start source:PROJECT.md -->
## Project

**Financial Report Interpretation System (FRIS)**

A system that takes a **topic + time period** and returns **individual earnings report summaries** for all topic-related US stocks. Users can filter by market cap, PE, PB, and price to narrow results.

**Core Value:** **Fast, structured business intelligence from public financial data.** Quickly understand what a company does, how it performs, who it competes with, and what risks it faces — without reading raw SEC filings.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.13.4 - All application code
## Runtime
- CPython (homebrew installation at `/opt/homebrew/bin/python3`)
- pip (inferred from `requirements.txt`)
## Frameworks
- None - Pure Python application
- pandas>=2.0.0 - DataFrame operations, time series
- numpy>=1.26.0 - Numerical computations
- pytest>=8.0.0 - Unit testing framework
- py_vollib>=1.0.1 - Black-Scholes option pricing and Greeks
## Key Dependencies
- `yfinance>=0.2.40` - Historical stock price fetching
- `ib_insync>=0.9.86` - Interactive Brokers API client for live option data
- `duckdb>=1.0.0` - Embedded analytical database for option storage
- `pyarrow>=14.0.0` - Parquet file format support
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.26.0` - Numerical operations
- `py_vollib>=1.0.1` - Option pricing models
## Configuration
- No `.env` file detected
- Configuration via Python dataclasses in `config/settings.py`
- Config class hierarchy: `Config` > `StrategyConfig`, `BacktestConfig`, `AccountConfig`
- No build system detected (pure Python)
- No `pyproject.toml`, `setup.py`, or `setup.cfg`
## Platform Requirements
- Python 3.13+ recommended
- pip for dependency installation
- Standard Python 3 runtime
- IBKR TWS/Gateway running locally for live trading features
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Python modules: `snake_case.py` (e.g., `ibkr_fetcher.py`, `option_pricing.py`)
- Test files: `test_<module>.py` pattern (e.g., `test_ibkr_fetcher.py`)
- Configuration: `settings.py` in `config/` directory
- PascalCase: `BacktestSimulator`, `IBKROptionFetcher`, `OperationLogger`, `OptionSnapshot`
- Dataclasses: PascalCase with `@dataclass` decorator
- Enums: PascalCase values (`HOLDING_CALL`, `HOLDING_PUT`)
- snake_case: `calculate_delta`, `fetch_quote`, `get_historical_prices`
- Private methods: `_ prefixed` (e.g., `_get_volatility`, `_nan_safe_float`)
- snake_case: `stock_price`, `option_multiplier`, `risk_free_rate`
- Private: `_` prefixed (e.g., `_prices`, `_tickers`, `_contracts`)
- snake_case with descriptive names: `risk_free_rate`, `option_multiplier`
- Used throughout: `def func(arg: Type) -> ReturnType`
- Union types: `int | None` (Python 3.10+)
- Generic types: `List[float]`, `Dict[str, Any]`
## Code Style
- No formatter config detected (no .prettierrc, .ruff.toml, black.toml)
- 4-space indentation
- No strict line length enforcement detected
- Trailing commas in multi-line constructs
- Triple quotes for module/function docstrings
- Chinese comments for domain-specific terms (e.g., `期权净权利金` for net premium)
- English docstrings for public APIs
- `sys.path.insert(0, ...)` used in `src/ibkr_fetcher.py` for local ibkr_common imports
- One class per file preferred
- Related functions grouped in modules (e.g., `option_pricing.py` contains all pricing functions)
- Test files co-located in `tests/` directory
## Error Handling
## Data Classes
## Logging
- Uses `print()` for output: `print("Running backtest simulation...")`
- Custom `OperationLogger` class for strategy operations in `src/reporter.py`
- Logs to CSV via `OperationLogger.save_csv()`
## Comments
## Function Design
- Functions typically < 50 lines
- Single responsibility (e.g., `_nan_safe_float` does one conversion)
- Config objects passed to constructors
- Optional parameters with defaults
- Type hints on all parameters
- Explicit return types
- `None` for "not found" cases
- Empty collections for "no results" cases
## Module Design
- Direct class/function imports: `from src.simulator import BacktestSimulator`
- No `__all__` exports detected
- `main.py` - CLI entry with argparse
- `scripts/` - Ad-hoc testing scripts
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Clear separation between data fetching, strategy logic, simulation engine, and reporting
- State machine pattern for option wheel strategy transitions
- Dual-mode operation: backtest (synthetic data) and live (IBKR API)
- Configuration-driven design using Python dataclasses
## Layers
- Purpose: CLI interface and mode selection
- Location: `main.py`
- Contains: Argument parsing, mode routing (backtest/live)
- Depends on: All lower layers
- Used by: CLI invocation
- Purpose: Orchestrate backtest execution
- Location: `src/simulator.py`
- Contains: `BacktestSimulator` class
- Depends on: Config, Strategy, Reporter, Option Pricing, Data Fetcher
- Used by: `main.py`
- Purpose: Option wheel state machine and position management
- Location: `src/strategy.py`
- Contains: `StrategyState`, `Position`, `OptionWheelState`, decision functions
- Depends on: None (pure logic)
- Used by: `src/simulator.py`
- Purpose: Fetch stock prices and option data from multiple sources
- Location: `src/data_fetcher.py`, `src/ibkr_fetcher.py`
- Contains: `StockDataFetcher` (yfinance), `InMemoryOptionData`, `IBKROptionFetcher`, `IBKROptionData`
- Depends on: yfinance, ib_insync, ibkr-common
- Used by: `src/simulator.py`
- Purpose: Black-Scholes option pricing and Greeks calculation
- Location: `src/option_pricing.py`
- Contains: Price/delta calculation functions using py_vollib
- Depends on: py_vollib, numpy
- Used by: `src/simulator.py`, `src/data_fetcher.py`
- Purpose: Persist option snapshots to DuckDB and Parquet
- Location: `src/option_storage.py`
- Contains: `OptionStorage` class
- Depends on: duckdb, pandas
- Used by: Live mode scripts
- Purpose: Log strategy operations to CSV
- Location: `src/reporter.py`
- Contains: `OperationLogger`, `OperationRecord`, `format_option_name`
- Depends on: csv module
- Used by: `src/simulator.py`
- Purpose: Centralized parameter management
- Location: `config/settings.py`
- Contains: `Config`, `StrategyConfig`, `BacktestConfig`, `AccountConfig` dataclasses
- Depends on: None (pure data)
- Used by: All layers
## Data Flow
```
```
## Key Abstractions
- Purpose: Represents the two states of the wheel strategy
- Location: `src/strategy.py`
- Pattern: Simple enum with two values
- Purpose: Represents an option position with strike, expiry, type, prices
- Location: `src/strategy.py`
- Pattern: Data carrier with optional protective leg
- Purpose: Maintains current state, position, stock holding, cumulative premium
- Location: `src/strategy.py`
- Pattern: Mutable state container
- Purpose: Real-time option data with Greeks
- Location: `src/option_schemas.py`
- Pattern: Immutable data record with validation
- Purpose: Dictionary-based option price lookup for backtesting
- Location: `src/data_fetcher.py`
- Pattern: Repository interface with get_price(), get_available_strikes()
- Purpose: IBKR-backed live option data with caching
- Location: `src/data_fetcher.py`
- Pattern: Repository with connect/disconnect lifecycle
## Entry Points
- Location: `/Users/guanjie/Desktop/guanjie/tradingStrategy_test/main.py`
- Triggers: CLI execution (`python main.py`)
- Responsibilities: Mode selection, config loading, simulator orchestration
- Location: `/Users/guanjie/Desktop/guanjie/tradingStrategy_test/src/ibkr_fetcher.py`
- Triggers: Scripts in `scripts/` directory
- Responsibilities: Low-level IBKR API interaction
- Location: `/Users/guanjie/Desktop/guanjie/tradingStrategy_test/scripts/`
- Triggers: Direct Python execution for live testing
- Responsibilities: Ad-hoc live data fetching and verification
## Error Handling
- Option pricing failures return 0.0 (`calculate_option_price`, `calculate_delta`)
- IBKR connection failures return False (`connect()`)
- Invalid option data returns None (`fetch_quote`, `subscribe`)
- NaN/None values sanitized via `_nan_safe_float()`, `_nan_safe_int()`
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
