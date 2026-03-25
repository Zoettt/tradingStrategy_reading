# Technology Stack

**Analysis Date:** 2026-03-25

## Languages

**Primary:**
- Python 3.13.4 - All application code

## Runtime

**Environment:**
- CPython (homebrew installation at `/opt/homebrew/bin/python3`)

**Package Manager:**
- pip (inferred from `requirements.txt`)

## Frameworks

**Core:**
- None - Pure Python application

**Data Processing:**
- pandas>=2.0.0 - DataFrame operations, time series
- numpy>=1.26.0 - Numerical computations

**Testing:**
- pytest>=8.0.0 - Unit testing framework

**Financial Calculations:**
- py_vollib>=1.0.1 - Black-Scholes option pricing and Greeks

## Key Dependencies

**Critical:**
- `yfinance>=0.2.40` - Historical stock price fetching
- `ib_insync>=0.9.86` - Interactive Brokers API client for live option data
- `duckdb>=1.0.0` - Embedded analytical database for option storage
- `pyarrow>=14.0.0` - Parquet file format support

**Infrastructure:**
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.26.0` - Numerical operations
- `py_vollib>=1.0.1` - Option pricing models

## Configuration

**Environment:**
- No `.env` file detected
- Configuration via Python dataclasses in `config/settings.py`
- Config class hierarchy: `Config` > `StrategyConfig`, `BacktestConfig`, `AccountConfig`

**Build:**
- No build system detected (pure Python)
- No `pyproject.toml`, `setup.py`, or `setup.cfg`

## Platform Requirements

**Development:**
- Python 3.13+ recommended
- pip for dependency installation

**Production:**
- Standard Python 3 runtime
- IBKR TWS/Gateway running locally for live trading features

---

*Stack analysis: 2026-03-25*
