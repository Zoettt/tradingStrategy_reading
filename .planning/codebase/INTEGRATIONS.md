# External Integrations

**Analysis Date:** 2026-03-25

## APIs & External Services

**Market Data - Yahoo Finance:**
- yfinance - Historical stock price data
  - SDK/Client: `yfinance` Python package
  - Auth: None (public API)
  - Usage: `src/data_fetcher.py` - `StockDataFetcher.get_historical_prices()`

**Market Data - Interactive Brokers:**
- IBKR API - Real-time option chain and quote data
  - SDK/Client: `ib_insync` Python package
  - Connection: `IBKROptionFetcher` class in `src/ibkr_fetcher.py`
  - Host: `127.0.0.1` (local TWS/Gateway)
  - Port: `7497` (paper) or `7496` (live)
  - Auth: TWS/Gateway credentials
  - Additional: Uses `ibkr-common` library from sibling directory

**Option Pricing:**
- py_vollib - Black-Scholes model implementation
  - Usage: `src/option_pricing.py` - `calculate_option_price()`, `calculate_delta()`
  - No external API calls (pure Python calculation)

## Data Storage

**Databases:**
- DuckDB (embedded)
  - Connection: Local file path (`data/options.db` by default)
  - Client: `duckdb` Python package
  - Usage: `src/option_storage.py` - `OptionStorage` class
  - Schema: `option_snapshots` table with symbol, expiry, strike, greeks, etc.

**File Storage:**
- Parquet format
  - Location: `data/parquet/{symbol}/{date}.parquet`
  - Client: `pyarrow` Python package
  - Usage: `OptionStorage.export_parquet()`

**Caching:**
- None detected

## Authentication & Identity

**Auth Provider:**
- None (no external auth service)
- IBKR authentication handled by TWS/Gateway application

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Console output via `print()` statements in `main.py`
- CSV output via `OperationLogger` in `src/reporter.py`
- `operations_log.csv` in project root

## CI/CD & Deployment

**Hosting:**
- Local development environment
- No cloud deployment detected

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- None required (all configuration in `config/settings.py`)

**Secrets location:**
- IBKR credentials managed by TWS/Gateway application
- No `.env` file in project

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Key Integration Patterns

**Stock Data Fetching:**
```python
# src/data_fetcher.py - StockDataFetcher
yfinance.download(self.symbol, start=start_date, end=end_date)
```

**IBKR Connection:**
```python
# src/ibkr_fetcher.py - IBKROptionFetcher
from ibkr_common.connection.manager import ConnectionManager
from ibkr_common.config import IBKRConfig
self._ib, _ = self._manager.connect(config)
```

**Option Storage:**
```python
# src/option_storage.py - OptionStorage
self.conn = duckdb.connect(db_path)
df.to_parquet(output_path, index=False)
```

---

*Integration audit: 2026-03-25*
