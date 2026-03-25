# Testing Patterns

**Analysis Date:** 2026-03-25

## Test Framework

**Runner:**
- pytest 8.0.0+
- No pytest.ini or pyproject.toml test config detected

**Assertion Library:**
- pytest built-in assertions

**Mocking:**
- unittest.mock (MagicMock, Mock, patch)

## Test File Organization

**Location:**
- Tests in `tests/` directory (co-located with `src/`)
- Structure mirrors src layout:
  ```
  tests/
  ├── test_ibkr_fetcher.py
  ├── test_option_pricing.py
  ├── test_reporter.py
  ├── test_simulator.py
  ├── test_integration.py
  ├── test_option_schemas.py
  ├── test_data_fetcher.py
  ├── test_strategy.py
  └── test_option_storage.py
  ```

**Naming:**
- `test_<module>.py` pattern
- Test functions: `test_<description>`

## Test Structure

**Pattern - Basic Unit Test:**
```python
# tests/test_option_pricing.py
def test_calculate_time_to_expiry():
    """Test days to expiration calculation."""
    from datetime import date
    expiry = date(2025, 6, 20)
    today = date(2025, 5, 20)
    t = calculate_time_to_expiry(expiry, today)
    assert abs(t - 31/365) < 0.001
```

**Pattern - Initialization Test:**
```python
# tests/test_reporter.py
def test_operation_logger_init():
    """Logger should initialize with empty records."""
    logger = OperationLogger()
    assert len(logger.records) == 0
```

**Pattern - Data Validation Test:**
```python
# tests/test_option_schemas.py
def test_option_snapshot_invalid_bid_ask():
    """Bid > Ask should fail validation."""
    snap = OptionSnapshot(...)
    assert snap.validate() is False
```

## Mocking Patterns

**Pattern - MagicMock for Objects:**
```python
# tests/test_ibkr_fetcher.py
mock_ib = MagicMock()
mock_contract = MagicMock()
mock_contract.conId = 12345
mock_contract.symbol = "AAPL"
mock_ib.qualifyContracts = MagicMock()
mock_ib.reqMktData = MagicMock(return_value=mock_ticker)
```

**Pattern - patch Decorator:**
```python
# tests/test_ibkr_fetcher.py
with patch("ib_insync.IB", return_value=mock_ib):
    fetcher = IBKROptionFetcher()
    fetcher._ib = mock_ib
    snap = fetcher.fetch_quote(...)
```

**Pattern - Mock Ticker with Greeks:**
```python
mock_ticker.bid = 5.0
mock_ticker.ask = 5.2
mock_ticker.last = 5.1
mock_ticker.bidGreeks = MagicMock(delta=0.5, gamma=0.03, vega=0.15, theta=-0.05, impliedVol=0.25)
mock_ticker.volume = 1000
mock_ticker.openInterest = 5000
```

## Fixtures and Test Data

**Pattern - tmp_path Fixture:**
```python
# tests/test_reporter.py
def test_save_csv(tmp_path):
    """Should save to CSV file."""
    csv_path = tmp_path / "test_log.csv"
    logger.save_csv(csv_path)
    assert csv_path.exists()
```

**Pattern - Manual Test Data:**
```python
# tests/test_option_schemas.py
snap = OptionSnapshot(
    symbol="AAPL",
    exchange="SMART",
    expiry=date(2025, 6, 20),
    strike=185.0,
    option_type="call",
    bid=5.0,
    ask=5.2,
    # ... full object construction
)
```

**Pattern - Synthetic Data Generation:**
```python
# tests/test_integration.py
from src.data_fetcher import generate_synthetic_option_data
option_data = generate_synthetic_option_data("0981.HK", start, end, prices)
```

## Test Categories

**Unit Tests:**
- Individual function tests (e.g., `test_calculate_delta_call`)
- Dataclass validation tests (e.g., `test_option_snapshot_validate`)
- Strategy logic tests (e.g., `test_should_roll_check_weekly`)

**Integration Tests:**
- `tests/test_integration.py` - End-to-end simulator tests
- `tests/test_simulator.py` - Simulator initialization and state tests

**Not Detected:**
- No E2E tests
- No performance/benchmark tests
- No property-based tests

## Coverage

**No Coverage Enforcement:**
- No .coveragerc or coverage configuration detected
- No coverage reporting in CI/CD

## Common Patterns

**Async/Blocking Patterns:**
```python
# src/ibkr_fetcher.py uses blocking sleep
self._ib.sleep(1.5)  # Wait for market data
```

**Edge Case Testing:**
```python
# tests/test_option_schemas.py
def test_option_snapshot_negative_gamma():
    """Negative gamma should fail validation."""
    snap = OptionSnapshot(gamma=-0.03, ...)
    assert snap.validate() is False
```

**State Machine Tests:**
```python
# tests/test_strategy.py
def test_state_transition_on_call_assignment():
    """Call assignment should transition to HOLDING_PUT."""
    state = StrategyState()
    state.record_call_assigned()
    assert state.current == OptionWheelState.HOLDING_PUT
```

## Run Commands

```bash
pytest                    # Run all tests
pytest tests/             # Run specific directory
pytest -v                # Verbose output
pytest --tb=short         # Shorter tracebacks
```

---

*Testing analysis: 2026-03-25*
