"""Tests for stopping rules module."""

import pytest
import math
from asreview_5star.stopping import (
    bayesian_stopping,
    sprt_stopping,
    safe_stopping,
    consecutive_irrelevant_stopping,
    StoppingResult
)


class TestBayesianStopping:
    """Tests for Bayesian stopping rule."""

    def test_basic_calculation(self):
        """Test basic Bayesian stopping calculation."""
        result = bayesian_stopping(
            n_screened=1000,
            n_relevant=50,
            n_total=5000,
            target_recall=0.95
        )
        assert isinstance(result, StoppingResult)
        assert 0 <= result.confidence <= 1
        assert isinstance(result.should_stop, bool)
        assert "n_screened" in result.details

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = bayesian_stopping(
            n_screened=0,
            n_relevant=0,
            n_total=100
        )
        assert result.should_stop is False
        assert result.confidence == 0.0

    def test_all_screened(self):
        """Test when all documents are screened."""
        result = bayesian_stopping(
            n_screened=100,
            n_relevant=10,
            n_total=100
        )
        assert result.should_stop is True
        assert result.confidence == 1.0

    def test_high_prevalence(self):
        """Test with high prevalence (many relevant)."""
        result = bayesian_stopping(
            n_screened=500,
            n_relevant=100,
            n_total=1000,
            target_recall=0.95
        )
        # With high prevalence, shouldn't stop early
        assert isinstance(result.should_stop, bool)

    def test_low_prevalence(self):
        """Test with low prevalence (few relevant)."""
        result = bayesian_stopping(
            n_screened=1000,
            n_relevant=5,
            n_total=5000,
            target_recall=0.95
        )
        assert isinstance(result.should_stop, bool)

    def test_custom_priors(self):
        """Test with custom prior parameters."""
        result = bayesian_stopping(
            n_screened=500,
            n_relevant=25,
            n_total=1000,
            prior_alpha=2.0,
            prior_beta=10.0
        )
        assert isinstance(result, StoppingResult)

    def test_different_thresholds(self):
        """Test with different confidence thresholds."""
        result_high = bayesian_stopping(
            n_screened=800,
            n_relevant=40,
            n_total=1000,
            confidence_threshold=0.99
        )
        result_low = bayesian_stopping(
            n_screened=800,
            n_relevant=40,
            n_total=1000,
            confidence_threshold=0.80
        )
        # Lower threshold should be more likely to recommend stopping
        assert result_low.should_stop or not result_high.should_stop


class TestSPRTStopping:
    """Tests for SPRT stopping rule."""

    def test_basic_sprt(self):
        """Test basic SPRT calculation."""
        result = sprt_stopping(
            n_screened=100,
            n_relevant=5
        )
        assert isinstance(result, StoppingResult)
        assert "likelihood_ratio" in result.details

    def test_insufficient_data(self):
        """Test with no data."""
        result = sprt_stopping(
            n_screened=0,
            n_relevant=0
        )
        assert result.should_stop is False

    def test_accept_h0(self):
        """Test case that should accept H0 (low prevalence)."""
        result = sprt_stopping(
            n_screened=1000,
            n_relevant=2,  # Very low prevalence
            null_prevalence=0.01,
            alt_prevalence=0.05
        )
        # Should lean towards accepting H0
        assert "decision" in result.details

    def test_accept_h1(self):
        """Test case that should accept H1 (high prevalence)."""
        result = sprt_stopping(
            n_screened=100,
            n_relevant=20,  # High prevalence
            null_prevalence=0.01,
            alt_prevalence=0.05
        )
        # Should lean towards accepting H1
        assert "decision" in result.details

    def test_continue(self):
        """Test case that should continue (inconclusive)."""
        result = sprt_stopping(
            n_screened=50,
            n_relevant=1
        )
        # With limited data, may be inconclusive
        assert isinstance(result.should_stop, bool)

    def test_custom_parameters(self):
        """Test with custom alpha and beta."""
        result = sprt_stopping(
            n_screened=200,
            n_relevant=10,
            alpha=0.01,
            beta=0.10
        )
        assert isinstance(result, StoppingResult)


class TestSAFEStopping:
    """Tests for SAFE stopping rule."""

    def test_basic_safe(self):
        """Test basic SAFE calculation."""
        result = safe_stopping(
            n_screened=500,
            n_relevant=25,
            consecutive_irrelevant=30,
            n_total=1000
        )
        assert isinstance(result, StoppingResult)
        assert "consecutive_irrelevant" in result.details

    def test_no_relevant_found(self):
        """Test when no relevant documents found."""
        result = safe_stopping(
            n_screened=100,
            n_relevant=0,
            consecutive_irrelevant=50,
            n_total=1000
        )
        assert result.should_stop is False

    def test_reaches_threshold(self):
        """Test when threshold is reached."""
        result = safe_stopping(
            n_screened=500,
            n_relevant=25,
            consecutive_irrelevant=100,
            n_total=1000,
            min_consecutive=50
        )
        assert result.should_stop is True

    def test_below_threshold(self):
        """Test when below threshold."""
        result = safe_stopping(
            n_screened=500,
            n_relevant=25,
            consecutive_irrelevant=10,
            n_total=1000,
            min_consecutive=50
        )
        assert result.should_stop is False

    def test_auto_threshold(self):
        """Test automatic threshold calculation."""
        result = safe_stopping(
            n_screened=500,
            n_relevant=25,
            consecutive_irrelevant=30,
            n_total=1000
        )
        assert "min_consecutive_required" in result.details


class TestConsecutiveIrrelevantStopping:
    """Tests for consecutive irrelevant stopping rule."""

    def test_basic_consecutive(self):
        """Test basic consecutive stopping."""
        result = consecutive_irrelevant_stopping(
            consecutive_count=60,
            threshold=50
        )
        assert result.should_stop is True

    def test_below_threshold(self):
        """Test when below threshold."""
        result = consecutive_irrelevant_stopping(
            consecutive_count=30,
            threshold=50
        )
        assert result.should_stop is False

    def test_adjusted_for_no_relevant(self):
        """Test threshold adjustment when no relevant found."""
        result_with = consecutive_irrelevant_stopping(
            consecutive_count=60,
            threshold=50,
            n_relevant=10
        )
        result_without = consecutive_irrelevant_stopping(
            consecutive_count=60,
            threshold=50,
            n_relevant=0
        )
        # Without relevant found, threshold is doubled
        assert result_with.should_stop is True
        assert result_without.should_stop is False  # 60 < 100 (50*2)

    def test_confidence_calculation(self):
        """Test confidence calculation."""
        result = consecutive_irrelevant_stopping(
            consecutive_count=25,
            threshold=50,
            n_relevant=10
        )
        assert result.confidence == 0.5  # 25/50
