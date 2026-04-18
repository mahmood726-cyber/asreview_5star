"""Tests for Inter-Rater Reliability (IRR) module."""

import pytest
import math
from asreview_5star.irr import (
    cohens_kappa,
    fleiss_kappa,
    krippendorff_alpha,
    percent_agreement,
    IRRResult
)


class TestCohensKappa:
    """Tests for Cohen's Kappa."""

    def test_perfect_agreement(self):
        """Test perfect agreement gives kappa = 1."""
        rater1 = [1, 1, 0, 0, 1, 0, 1, 0]
        rater2 = [1, 1, 0, 0, 1, 0, 1, 0]
        result = cohens_kappa(rater1, rater2)
        assert result.coefficient == 1.0
        assert result.interpretation == "Almost Perfect"

    def test_complete_disagreement(self):
        """Test complete disagreement."""
        rater1 = [1, 1, 1, 1]
        rater2 = [0, 0, 0, 0]
        result = cohens_kappa(rater1, rater2)
        assert result.coefficient < 0

    def test_moderate_agreement(self):
        """Test moderate agreement."""
        rater1 = [1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
        rater2 = [1, 0, 0, 0, 1, 1, 1, 0, 0, 1]
        result = cohens_kappa(rater1, rater2)
        assert -1 <= result.coefficient <= 1

    def test_confidence_interval(self):
        """Test confidence interval calculation."""
        rater1 = [1, 1, 0, 0, 1, 0, 1, 0, 1, 1] * 10
        rater2 = [1, 0, 0, 0, 1, 1, 1, 0, 0, 1] * 10
        result = cohens_kappa(rater1, rater2)
        assert result.ci_lower <= result.coefficient <= result.ci_upper

    def test_weighted_kappa_linear(self):
        """Test linear weighted kappa."""
        rater1 = [0, 1, 2, 0, 1, 2, 0, 1, 2]
        rater2 = [0, 1, 2, 1, 1, 1, 0, 2, 2]
        result = cohens_kappa(rater1, rater2, weights='linear')
        assert isinstance(result, IRRResult)
        assert result.details["weights"] == "linear"

    def test_weighted_kappa_quadratic(self):
        """Test quadratic weighted kappa."""
        rater1 = [0, 1, 2, 0, 1, 2, 0, 1, 2]
        rater2 = [0, 1, 2, 1, 1, 1, 0, 2, 2]
        result = cohens_kappa(rater1, rater2, weights='quadratic')
        assert isinstance(result, IRRResult)
        assert result.details["weights"] == "quadratic"

    def test_unequal_lengths_raises(self):
        """Test that unequal lengths raise an error."""
        with pytest.raises(ValueError):
            cohens_kappa([1, 0, 1], [1, 0])

    def test_empty_data_raises(self):
        """Test that empty data raises an error."""
        with pytest.raises(ValueError):
            cohens_kappa([], [])

    def test_p_value(self):
        """Test p-value calculation."""
        rater1 = [1, 1, 0, 0, 1, 0, 1, 0] * 5
        rater2 = [1, 0, 0, 0, 1, 0, 1, 0] * 5
        result = cohens_kappa(rater1, rater2)
        assert result.p_value is not None
        assert 0 <= result.p_value <= 1


class TestFleissKappa:
    """Tests for Fleiss' Kappa."""

    def test_perfect_agreement(self):
        """Test perfect agreement among multiple raters."""
        ratings = [
            [1, 1, 1],
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 0],
        ]
        result = fleiss_kappa(ratings)
        assert result.coefficient == 1.0

    def test_moderate_agreement(self):
        """Test moderate agreement among multiple raters."""
        ratings = [
            [1, 1, 0],
            [0, 0, 0],
            [1, 1, 1],
            [0, 1, 0],
            [1, 1, 1],
        ]
        result = fleiss_kappa(ratings)
        assert -1 <= result.coefficient <= 1

    def test_confidence_interval(self):
        """Test confidence interval for Fleiss' kappa."""
        ratings = [[1, 1, 0], [0, 0, 0], [1, 1, 1], [0, 1, 0]] * 10
        result = fleiss_kappa(ratings)
        assert result.ci_lower <= result.coefficient <= result.ci_upper

    def test_many_raters(self):
        """Test with many raters."""
        ratings = [
            [1, 1, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1],
        ]
        result = fleiss_kappa(ratings)
        assert result.details["n_raters"] == 5


class TestKrippendorffAlpha:
    """Tests for Krippendorff's Alpha."""

    def test_perfect_agreement(self):
        """Test perfect agreement gives alpha = 1."""
        data = [
            [1, 0, 1, 0],
            [1, 0, 1, 0],
            [1, 0, 1, 0],
        ]
        result = krippendorff_alpha(data)
        assert result.coefficient == 1.0

    def test_nominal_level(self):
        """Test nominal measurement level."""
        data = [
            [1, 0, 1, 0, 1],
            [1, 1, 1, 0, 1],
            [1, 0, 0, 0, 1],
        ]
        result = krippendorff_alpha(data, level="nominal")
        assert result.details["level"] == "nominal"

    def test_ordinal_level(self):
        """Test ordinal measurement level."""
        data = [
            [1, 2, 3, 1, 2],
            [1, 2, 3, 2, 2],
            [1, 3, 3, 1, 2],
        ]
        result = krippendorff_alpha(data, level="ordinal")
        assert result.details["level"] == "ordinal"

    def test_interval_level(self):
        """Test interval measurement level."""
        data = [
            [1.0, 2.5, 3.0, 1.5, 2.0],
            [1.0, 2.0, 3.0, 2.0, 2.0],
            [1.0, 3.0, 3.0, 1.0, 2.0],
        ]
        result = krippendorff_alpha(data, level="interval")
        assert result.details["level"] == "interval"

    def test_with_missing_data(self):
        """Test handling of missing data (NaN)."""
        import numpy as np
        data = [
            [1, 0, 1, np.nan],
            [1, 0, np.nan, 0],
            [1, 0, 1, 0],
        ]
        result = krippendorff_alpha(data)
        assert isinstance(result, IRRResult)

    def test_bootstrap_ci(self):
        """Test bootstrap confidence interval."""
        data = [
            [1, 0, 1, 0, 1, 0, 1, 0],
            [1, 1, 1, 0, 1, 0, 0, 0],
            [1, 0, 0, 0, 1, 0, 1, 0],
        ]
        result = krippendorff_alpha(data, n_bootstrap=100)
        assert result.ci_lower <= result.coefficient <= result.ci_upper


class TestPercentAgreement:
    """Tests for percent agreement."""

    def test_perfect_agreement(self):
        """Test 100% agreement."""
        rater1 = [1, 1, 0, 0, 1]
        rater2 = [1, 1, 0, 0, 1]
        result = percent_agreement(rater1, rater2)
        assert result.coefficient == 1.0

    def test_no_agreement(self):
        """Test 0% agreement."""
        rater1 = [1, 1, 1, 1]
        rater2 = [0, 0, 0, 0]
        result = percent_agreement(rater1, rater2)
        assert result.coefficient == 0.0

    def test_partial_agreement(self):
        """Test partial agreement."""
        rater1 = [1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
        rater2 = [1, 0, 0, 0, 1, 1, 1, 0, 0, 1]
        result = percent_agreement(rater1, rater2)
        # 7 out of 10 agree
        assert result.coefficient == 0.7

    def test_confidence_interval(self):
        """Test confidence interval calculation."""
        rater1 = [1, 1, 0, 0, 1, 0, 1, 0] * 10
        rater2 = [1, 0, 0, 0, 1, 0, 1, 0] * 10
        result = percent_agreement(rater1, rater2)
        assert result.ci_lower <= result.coefficient <= result.ci_upper

    def test_unequal_lengths_raises(self):
        """Test that unequal lengths raise an error."""
        with pytest.raises(ValueError):
            percent_agreement([1, 0, 1], [1, 0])

    def test_empty_data_raises(self):
        """Test that empty data raises an error."""
        with pytest.raises(ValueError):
            percent_agreement([], [])
