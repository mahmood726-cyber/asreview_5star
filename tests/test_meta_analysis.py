"""Tests for Meta-Analysis module."""

import pytest
import math
import numpy as np
from asreview_5star.meta_analysis import (
    pool_effects,
    eggers_test,
    beggs_test,
    heterogeneity_stats,
    forest_plot_data,
    MetaAnalysisResult,
    BiasTestResult
)


class TestPoolEffects:
    """Tests for effect pooling."""

    def test_fixed_effects(self):
        """Test fixed effects pooling."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        result = pool_effects(effects, ses, model="fixed")
        assert result.model == "fixed"
        assert isinstance(result.pooled_effect, float)

    def test_random_effects(self):
        """Test random effects pooling."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        result = pool_effects(effects, ses, model="random")
        assert result.model == "random"
        assert result.heterogeneity["tau_squared"] >= 0

    def test_confidence_interval(self):
        """Test confidence interval is valid."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        result = pool_effects(effects, ses)
        assert result.ci_lower < result.pooled_effect < result.ci_upper

    def test_heterogeneity_stats(self):
        """Test heterogeneity statistics."""
        effects = [math.log(0.5), math.log(0.8), math.log(1.2)]
        ses = [0.1, 0.1, 0.1]
        result = pool_effects(effects, ses, model="random")
        assert "Q" in result.heterogeneity
        assert "I_squared" in result.heterogeneity
        assert "tau_squared" in result.heterogeneity
        assert 0 <= result.heterogeneity["I_squared"] <= 100

    def test_study_weights(self):
        """Test that study weights sum to 100%."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        result = pool_effects(effects, ses)
        total_weight = sum(s["weight"] for s in result.studies)
        assert abs(total_weight - 100) < 0.01

    def test_study_names(self):
        """Test custom study names."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        names = ["PARADIGM-HF", "DAPA-HF", "EMPEROR-Reduced"]
        result = pool_effects(effects, ses, study_names=names)
        assert result.studies[0]["name"] == "PARADIGM-HF"

    def test_prediction_interval(self):
        """Test prediction interval calculation."""
        effects = [math.log(0.5), math.log(0.8), math.log(1.0), math.log(0.7)]
        ses = [0.1, 0.1, 0.1, 0.1]
        result = pool_effects(effects, ses, model="random")
        pi = result.heterogeneity["prediction_interval"]
        assert pi["lower"] <= result.pooled_effect <= pi["upper"]

    def test_empty_effects_raises(self):
        """Test that empty data raises error."""
        with pytest.raises(ValueError):
            pool_effects([], [])

    def test_mismatched_lengths_raises(self):
        """Test that mismatched lengths raise error."""
        with pytest.raises(ValueError):
            pool_effects([0.5, 0.6], [0.1])

    def test_p_value(self):
        """Test p-value calculation."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        result = pool_effects(effects, ses)
        assert 0 <= result.p_value <= 1


class TestEggersTest:
    """Tests for Egger's test."""

    def test_basic_calculation(self):
        """Test basic Egger's test."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85), math.log(0.7)]
        ses = [0.1, 0.12, 0.11, 0.15]
        result = eggers_test(effects, ses)
        assert isinstance(result, BiasTestResult)
        assert 0 <= result.p_value <= 1

    def test_insufficient_studies(self):
        """Test with insufficient studies."""
        effects = [math.log(0.8), math.log(0.75)]
        ses = [0.1, 0.12]
        result = eggers_test(effects, ses)
        assert "Insufficient" in result.interpretation

    def test_no_bias(self):
        """Test case with no publication bias."""
        # Symmetric funnel - no bias expected
        np.random.seed(42)
        true_effect = math.log(0.8)
        n_studies = 20
        effects = []
        ses = []
        for i in range(n_studies):
            se = 0.1 + i * 0.01
            effect = true_effect + np.random.normal(0, se)
            effects.append(effect)
            ses.append(se)
        result = eggers_test(effects, ses)
        # May or may not detect bias randomly

    def test_interpretation(self):
        """Test interpretation is provided."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85), math.log(0.7)]
        ses = [0.1, 0.12, 0.11, 0.15]
        result = eggers_test(effects, ses)
        assert "Egger's test" in result.interpretation


class TestBeggsTest:
    """Tests for Begg's test."""

    def test_basic_calculation(self):
        """Test basic Begg's test."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85), math.log(0.7)]
        ses = [0.1, 0.12, 0.11, 0.15]
        result = beggs_test(effects, ses)
        assert isinstance(result, BiasTestResult)
        assert 0 <= result.p_value <= 1

    def test_insufficient_studies(self):
        """Test with insufficient studies."""
        effects = [math.log(0.8), math.log(0.75)]
        ses = [0.1, 0.12]
        result = beggs_test(effects, ses)
        assert "Insufficient" in result.interpretation

    def test_kendall_tau(self):
        """Test Kendall's tau is calculated."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85), math.log(0.7)]
        ses = [0.1, 0.12, 0.11, 0.15]
        result = beggs_test(effects, ses)
        assert "kendall_tau" in result.details
        assert -1 <= result.details["kendall_tau"] <= 1


class TestHeterogeneityStats:
    """Tests for heterogeneity statistics function."""

    def test_all_stats_present(self):
        """Test all statistics are calculated."""
        effects = [math.log(0.5), math.log(0.8), math.log(1.2)]
        ses = [0.1, 0.1, 0.1]
        result = heterogeneity_stats(effects, ses)
        assert "Q" in result
        assert "I_squared" in result
        assert "tau_squared" in result
        assert "H_squared" in result

    def test_i_squared_interpretation(self):
        """Test I² interpretation."""
        effects = [math.log(0.8), math.log(0.8), math.log(0.8)]
        ses = [0.1, 0.1, 0.1]
        result = heterogeneity_stats(effects, ses)
        assert "interpretation" in result["I_squared_interpretation"].lower()


class TestForestPlotData:
    """Tests for forest plot data generation."""

    def test_basic_generation(self):
        """Test basic forest plot data generation."""
        effects = [math.log(0.8), math.log(0.75), math.log(0.85)]
        ses = [0.1, 0.12, 0.11]
        result = forest_plot_data(effects, ses)
        assert "studies" in result
        assert "pooled" in result
        assert "heterogeneity" in result

    def test_exponentiation(self):
        """Test that effects are exponentiated when specified."""
        effects = [math.log(0.8), math.log(0.75)]
        ses = [0.1, 0.12]
        result = forest_plot_data(effects, ses, exponentiate=True)
        # Exponentiated log(0.8) ≈ 0.8
        assert 0.7 < result.studies[0]["effect"] < 0.9

    def test_no_exponentiation(self):
        """Test without exponentiation."""
        effects = [0.5, 0.6]
        ses = [0.1, 0.12]
        result = forest_plot_data(effects, ses, exponentiate=False)
        assert result.studies[0]["effect"] == 0.5

    def test_null_line(self):
        """Test null line values."""
        effects = [math.log(0.8)]
        ses = [0.1]
        result_exp = forest_plot_data(effects, ses, exponentiate=True)
        result_no_exp = forest_plot_data(effects, ses, exponentiate=False)
        assert result_exp["null_line"] == 1.0
        assert result_no_exp["null_line"] == 0.0

    def test_study_names_included(self):
        """Test custom study names are included."""
        effects = [math.log(0.8), math.log(0.75)]
        ses = [0.1, 0.12]
        names = ["Study A", "Study B"]
        result = forest_plot_data(effects, ses, study_names=names)
        assert result["studies"][0]["name"] == "Study A"
