# Coding Conventions

**Analysis Date:** 2026-03-25

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `ibkr_fetcher.py`, `option_pricing.py`)
- Test files: `test_<module>.py` pattern (e.g., `test_ibkr_fetcher.py`)
- Configuration: `settings.py` in `config/` directory

**Classes:**
- PascalCase: `BacktestSimulator`, `IBKROptionFetcher`, `OperationLogger`, `OptionSnapshot`
- Dataclasses: PascalCase with `@dataclass` decorator
- Enums: PascalCase values (`HOLDING_CALL`, `HOLDING_PUT`)

**Functions/Methods:**
- snake_case: `calculate_delta`, `fetch_quote`, `get_historical_prices`
- Private methods: `_ prefixed` (e.g., `_get_volatility`, `_nan_safe_float`)

**Variables:**
- snake_case: `stock_price`, `option_multiplier`, `risk_free_rate`
- Private: `_` prefixed (e.g., `_prices`, `_tickers`, `_contracts`)

**Constants:**
- snake_case with descriptive names: `risk_free_rate`, `option_multiplier`

**Type Hints:**
- Used throughout: `def func(arg: Type) -> ReturnType`
- Union types: `int | None` (Python 3.10+)
- Generic types: `List[float]`, `Dict[str, Any]`

## Code Style

**Formatting:**
- No formatter config detected (no .prettierrc, .ruff.toml, black.toml)
- 4-space indentation
- No strict line length enforcement detected
- Trailing commas in multi-line constructs

**Docstrings:**
- Triple quotes for module/function docstrings
- Chinese comments for domain-specific terms (e.g., `期权净权利金` for net premium)
- English docstrings for public APIs

**Imports:**
```
Standard library (datetime, pathlib, typing)
Third-party (yfinance, ib_insync, pandas, numpy, py_vollib)
Local (from src.module import Class)
```
- `sys.path.insert(0, ...)` used in `src/ibkr_fetcher.py` for local ibkr_common imports

**Code Organization:**
- One class per file preferred
- Related functions grouped in modules (e.g., `option_pricing.py` contains all pricing functions)
- Test files co-located in `tests/` directory

## Error Handling

**Pattern - Try/Except with Fallback:**
```python
# src/option_pricing.py
try:
    return black_scholes(flag, S, K, t, r, sigma)
except Exception:
    return 0.0
```

**Pattern - NaN Handling:**
```python
# src/ibkr_fetcher.py
def _nan_safe_float(value) -> float:
    if value is None:
        return 0.0
    try:
        f = float(value)
        return 0.0 if f != f else f  # NaN check
    except (TypeError, ValueError):
        return 0.0
```

**Pattern - Validation Methods:**
```python
# src/option_schemas.py
@dataclass
class OptionSnapshot:
    def validate(self) -> bool:
        if self.strike < 0:
            return False
        if self.option_type not in ("call", "put"):
            return False
        # ... more checks
        return True
```

**Pattern - Connection Checks:**
```python
# src/ibkr_fetcher.py
if not self._ib:
    raise ConnectionError("Not connected")
```

**Pattern - Early Returns:**
```python
# Common pattern for input validation
if not snapshots:
    return
```

## Data Classes

**Pattern:**
```python
# src/option_schemas.py
@dataclass
class OptionSnapshot:
    symbol: str
    exchange: str
    expiry: date
    strike: float
    option_type: str  # 'call' or 'put'
    bid: float
    # ... many fields
    timestamp: datetime

    def validate(self) -> bool:
        # Instance validation logic

    def mid_price(self) -> float:
        return (self.bid + self.ask) / 2
```

**Configuration Pattern:**
```python
# config/settings.py
@dataclass
class Config:
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    account: AccountConfig = field(default_factory=AccountConfig)
    stock_symbol: str = "0981.HK"
```

## Logging

**No Formal Logging Framework:**
- Uses `print()` for output: `print("Running backtest simulation...")`
- Custom `OperationLogger` class for strategy operations in `src/reporter.py`
- Logs to CSV via `OperationLogger.save_csv()`

## Comments

**Chinese Comments for Domain Logic:**
```python
# src/reporter.py
net_premium_hkd: float  # 期权净权利金
commission: float = 0.0  # 手续费
```

**English Docstrings for APIs:**
```python
def calculate_option_price(flag: str, S: float, K: float, t: float, r: float, sigma: float) -> float:
    """
    Calculate option price using Black-Scholes.
    ...
    """
```

## Function Design

**Small, Focused Functions:**
- Functions typically < 50 lines
- Single responsibility (e.g., `_nan_safe_float` does one conversion)

**Parameter Patterns:**
- Config objects passed to constructors
- Optional parameters with defaults
- Type hints on all parameters

**Return Patterns:**
- Explicit return types
- `None` for "not found" cases
- Empty collections for "no results" cases

## Module Design

**Exports:**
- Direct class/function imports: `from src.simulator import BacktestSimulator`
- No `__all__` exports detected

**Entry Points:**
- `main.py` - CLI entry with argparse
- `scripts/` - Ad-hoc testing scripts

---

*Convention analysis: 2026-03-25*
