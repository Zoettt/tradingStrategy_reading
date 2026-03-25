"""FRIS exceptions."""


class FRISError(Exception):
    """Base exception for FRIS errors."""
    pass


class DataSourceError(FRISError):
    """Error fetching data from a data source."""

    def __init__(self, source: str, ticker: str, details: str):
        self.source = source
        self.ticker = ticker
        self.details = details
        super().__init__(f"{source} error for {ticker}: {details}")


class RateLimitError(FRISError):
    """Rate limit exceeded for a data source."""

    def __init__(self, source: str, retry_after: int = 60):
        self.source = source
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {source}. Retry after {retry_after}s.")


class CacheError(FRISError):
    """Error with the cache."""
    pass


class ValidationError(FRISError):
    """Input validation failed."""
    pass


class TickerNotFoundError(FRISError):
    """Raised when a ticker cannot be found."""
    def __init__(self, ticker: str):
        self.ticker = ticker
        super().__init__(f"Ticker not found: {ticker}")
