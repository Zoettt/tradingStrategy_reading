"""Shared fixtures for FRIS tests."""
import pytest


@pytest.fixture
def sample_gics_keywords():
    """Sample GICS keyword mapping for testing."""
    return {
        "Semiconductors": ["chip", "semiconductor", "ai chip", "gpu", "cpu"],
        "Software Infrastructure": ["cloud", "saas", "software", "infrastructure"],
        "Auto Manufacturers": ["electric vehicle", "ev", "automobile", "car"],
        "Financial Services": ["bank", "financial", "fintech", "payment"],
        "Healthcare": ["hospital", "healthcare", "medical", "pharma"],
    }
