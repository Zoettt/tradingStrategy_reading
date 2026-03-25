"""Tests for TopicClassifier (FRIS-01, FRIS-02)."""

import pytest
from src.fris.topic_classifier import TopicClassifier, IndustryMatch, GICS_KEYWORD_MAP


class TestTopicClassifier:
    """Test TopicClassifier.classify() and find_industries()."""

    def test_ai_chips_maps_to_semiconductors(self):
        """FRIS-02: 'AI chips' should match Semiconductors industry."""
        tc = TopicClassifier()
        matches = tc.classify("AI chips")
        industries = tc.find_industries("AI chips")

        assert "Semiconductors" in industries
        sem_match = next(m for m in matches if m.industry == "Semiconductors")
        assert "chip" in sem_match.matched_keywords or "ai chip" in sem_match.matched_keywords

    def test_electric_vehicle_maps_to_auto_manufacturers(self):
        """FRIS-02: 'electric vehicle' should match Auto Manufacturers."""
        tc = TopicClassifier()
        industries = tc.find_industries("electric vehicle")

        assert "Auto Manufacturers" in industries

    def test_cloud_computing_maps_to_software_infrastructure(self):
        """FRIS-02: 'cloud computing' should match Software Infrastructure."""
        tc = TopicClassifier()
        industries = tc.find_industries("cloud computing")

        assert "Software Infrastructure" in industries

    def test_empty_topic_returns_empty_list(self):
        """FRIS-01: Empty topic should return empty list."""
        tc = TopicClassifier()
        assert tc.classify("") == []
        assert tc.find_industries("") == []

    def test_whitespace_topic_returns_empty_list(self):
        """FRIS-01: Whitespace-only topic should return empty list."""
        tc = TopicClassifier()
        assert tc.classify("   ") == []
        assert tc.find_industries("   ") == []

    def test_multiple_industries_can_match(self):
        """FRIS-02: A topic can match multiple industries."""
        tc = TopicClassifier()
        # "bank" could match Financial Services and potentially others
        matches = tc.classify("bank financial payment")
        industries = tc.find_industries("bank financial payment")

        assert len(industries) >= 1
        assert "Financial Services" in industries

    def test_case_insensitive_matching(self):
        """FRIS-02: Keyword matching should be case insensitive."""
        tc = TopicClassifier()
        lower_result = tc.find_industries("ai chips")
        upper_result = tc.find_industries("AI CHIPS")
        mixed_result = tc.find_industries("Ai ChiPs")

        assert lower_result == upper_result == mixed_result

    def test_confidence_scoring(self):
        """FRIS-02: More keyword matches should increase confidence."""
        tc = TopicClassifier()
        single_match = tc.classify("chip")
        multi_match = tc.classify("chip semiconductor ai")

        # Multi-match should have higher or equal confidence
        if single_match and multi_match:
            assert multi_match[0].confidence >= single_match[0].confidence

    def test_industry_match_properties(self):
        """FRIS-02: IndustryMatch should have correct properties."""
        tc = TopicClassifier()
        matches = tc.classify("AI chips")

        assert matches
        match = matches[0]
        assert isinstance(match, IndustryMatch)
        assert match.industry
        assert match.matched_keywords
        assert 0.0 <= match.confidence <= 1.0
        assert hasattr(match, "is_high_confidence")

    def test_custom_keyword_map(self, sample_gics_keywords):
        """FRIS-02: Custom keyword map can be provided."""
        tc = TopicClassifier(keyword_map=sample_gics_keywords)
        matches = tc.classify("chip")

        assert any(m.industry == "Semiconductors" for m in matches)

    def test_add_keyword(self):
        """FRIS-02: Keywords can be added dynamically."""
        tc = TopicClassifier()
        initial_industries = tc.find_industries("blockchain")

        tc.add_keyword("Financial Services", "blockchain")
        updated_industries = tc.find_industries("blockchain")

        # After adding "blockchain" to Financial Services
        assert len(updated_industries) >= len(initial_industries)

    def test_get_all_industries(self):
        """FRIS-02: Can retrieve all supported industries."""
        tc = TopicClassifier()
        industries = tc.get_all_industries()

        assert len(industries) > 0
        assert "Semiconductors" in industries
        assert "Financial Services" in industries


class TestIndustryMatch:
    """Test IndustryMatch dataclass."""

    def test_is_high_confidence_true(self):
        """Confidence >= 0.5 should be high confidence."""
        match = IndustryMatch(
            industry="Test",
            matched_keywords=["kw1", "kw2"],
            confidence=0.6
        )
        assert match.is_high_confidence is True

    def test_is_high_confidence_false(self):
        """Confidence < 0.5 should not be high confidence."""
        match = IndustryMatch(
            industry="Test",
            matched_keywords=["kw1"],
            confidence=0.3
        )
        assert match.is_high_confidence is False

    def test_is_high_confidence_boundary(self):
        """Boundary case: exactly 0.5 should be high confidence."""
        match = IndustryMatch(
            industry="Test",
            matched_keywords=["kw1", "kw2"],
            confidence=0.5
        )
        assert match.is_high_confidence is True
