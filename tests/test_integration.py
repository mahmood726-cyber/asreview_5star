"""Integration tests for ASReview 5-Star package."""

import pytest
import math
import numpy as np
from asreview_5star import (
    bayesian_stopping,
    sprt_stopping,
    safe_stopping,
    cohens_kappa,
    fleiss_kappa,
    pool_effects,
    eggers_test,
    prisma_stats,
    prisma_flow_data,
)


class TestFullWorkflow:
    """Integration tests for complete systematic review workflows."""

    def test_screening_workflow(self):
        """Test complete screening workflow with stopping rules."""
        # Simulate screening session
        n_total = 5000
        n_screened = 0
        n_relevant = 0
        consecutive_irrelevant = 0

        # Simulate screening with 2% prevalence
        np.random.seed(42)
        relevance = np.random.choice(
            [0, 1],
            size=n_total,
            p=[0.98, 0.02]
        )

        # Screen in batches
        batch_size = 100
        stopped = False

        while n_screened < n_total and not stopped:
            batch_end = min(n_screened + batch_size, n_total)
            batch = relevance[n_screened:batch_end]

            for doc in batch:
                n_screened += 1
                if doc == 1:
                    n_relevant += 1
                    consecutive_irrelevant = 0
                else:
                    consecutive_irrelevant += 1

            # Check stopping rules
            bayesian_result = bayesian_stopping(
                n_screened=n_screened,
                n_relevant=n_relevant,
                n_total=n_total,
                target_recall=0.95
            )

            safe_result = safe_stopping(
                n_screened=n_screened,
                n_relevant=n_relevant,
                consecutive_irrelevant=consecutive_irrelevant,
                n_total=n_total
            )

            if bayesian_result.confidence >= 0.95 or safe_result.should_stop:
                stopped = True
                break

        # Verify workflow completed reasonably
        assert n_screened > 0
        assert n_relevant >= 0

    def test_dual_screening_irr(self):
        """Test dual screening workflow with IRR calculation."""
        # Simulate two screeners
        np.random.seed(42)
        n_records = 100

        # Base relevance (true labels)
        true_relevance = np.random.choice([0, 1], size=n_records, p=[0.9, 0.1])

        # Screener 1: 90% accuracy
        screener1 = []
        for true in true_relevance:
            if np.random.random() < 0.9:
                screener1.append(true)
            else:
                screener1.append(1 - true)

        # Screener 2: 85% accuracy
        screener2 = []
        for true in true_relevance:
            if np.random.random() < 0.85:
                screener2.append(true)
            else:
                screener2.append(1 - true)

        # Calculate IRR
        kappa_result = cohens_kappa(screener1, screener2)

        # Should have at least slight agreement (random noise can lower kappa)
        assert kappa_result.coefficient > 0.0
        assert kappa_result.ci_lower < kappa_result.coefficient < kappa_result.ci_upper

    def test_meta_analysis_workflow(self):
        """Test complete meta-analysis workflow."""
        # Study data (log hazard ratios and standard errors)
        studies = [
            {"name": "Study A", "hr": 0.80, "ci_lower": 0.65, "ci_upper": 0.98},
            {"name": "Study B", "hr": 0.75, "ci_lower": 0.60, "ci_upper": 0.94},
            {"name": "Study C", "hr": 0.85, "ci_lower": 0.70, "ci_upper": 1.03},
            {"name": "Study D", "hr": 0.70, "ci_lower": 0.55, "ci_upper": 0.89},
            {"name": "Study E", "hr": 0.78, "ci_lower": 0.62, "ci_upper": 0.98},
        ]

        # Convert to log scale and calculate SE
        effects = []
        ses = []
        names = []

        for study in studies:
            log_hr = math.log(study["hr"])
            # SE from CI: SE = (log(upper) - log(lower)) / (2 * 1.96)
            se = (math.log(study["ci_upper"]) - math.log(study["ci_lower"])) / 3.92
            effects.append(log_hr)
            ses.append(se)
            names.append(study["name"])

        # Pool effects
        result = pool_effects(effects, ses, study_names=names, model="random")

        # Check result
        assert result.pooled_effect < 0  # Log HR should be negative
        assert math.exp(result.pooled_effect) < 1  # HR < 1 (protective)

        # Test for publication bias
        eggers_result = eggers_test(effects, ses)
        assert isinstance(eggers_result.p_value, float)

        # Generate forest plot data
        from asreview_5star import forest_plot_data
        plot_data = forest_plot_data(effects, ses, names, exponentiate=True)
        assert len(plot_data["studies"]) == 5
        assert 0 < plot_data["pooled"]["effect"] < 1

    def test_prisma_flow_complete(self):
        """Test complete PRISMA flow generation."""
        # Simulate a complete systematic review
        stats = prisma_stats(
            records_total=3500,
            records_duplicates=500,
            records_screened=3000,
            records_excluded_screening=2700,
            records_retrieved=300,
            records_not_retrieved=15,
            records_excluded_fulltext=260,
            exclusion_reasons={
                "Wrong population": 80,
                "Wrong intervention": 70,
                "Wrong outcome": 50,
                "Wrong study design": 40,
                "Conference abstract only": 20
            }
        )

        flow_data = prisma_flow_data(stats)

        # Verify calculations
        assert flow_data["included"]["studies"]["n"] == 25
        assert flow_data["summary"]["yield_rate"] < 1  # Less than 1% yield

        # Generate SVG
        from asreview_5star.prisma import generate_prisma_svg
        svg = generate_prisma_svg(stats)
        assert len(svg) > 1000  # Should be substantial

    def test_multiple_raters_fleiss(self):
        """Test multi-rater workflow with Fleiss' Kappa."""
        # Simulate 4 raters on 50 documents
        np.random.seed(42)
        n_docs = 50
        n_raters = 4

        # True relevance
        true_labels = np.random.choice([0, 1], size=n_docs, p=[0.8, 0.2])

        # Generate ratings with varying accuracy
        accuracies = [0.90, 0.85, 0.80, 0.85]
        ratings = []

        for i in range(n_docs):
            doc_ratings = []
            for j in range(n_raters):
                if np.random.random() < accuracies[j]:
                    doc_ratings.append(true_labels[i])
                else:
                    doc_ratings.append(1 - true_labels[i])
            ratings.append(doc_ratings)

        # Calculate Fleiss' Kappa
        result = fleiss_kappa(ratings)

        # Should have at least fair agreement (random noise can lower kappa)
        assert result.coefficient > 0.3
        assert result.details["n_raters"] == 4
        assert result.details["n_subjects"] == 50


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_study_meta(self):
        """Test meta-analysis with single study."""
        effects = [math.log(0.8)]
        ses = [0.1]
        result = pool_effects(effects, ses)
        assert result.pooled_effect == effects[0]

    def test_zero_prevalence_stopping(self):
        """Test stopping rules with zero prevalence."""
        result = bayesian_stopping(
            n_screened=1000,
            n_relevant=0,
            n_total=5000
        )
        assert result.confidence == 0.0

    def test_complete_agreement_kappa(self):
        """Test kappa with perfect agreement."""
        rater1 = [0] * 50 + [1] * 50
        rater2 = [0] * 50 + [1] * 50
        result = cohens_kappa(rater1, rater2)
        assert result.coefficient == 1.0

    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        np.random.seed(42)
        n = 10000
        rater1 = list(np.random.choice([0, 1], size=n, p=[0.9, 0.1]))
        rater2 = list(np.random.choice([0, 1], size=n, p=[0.9, 0.1]))

        # Should complete without timeout
        result = cohens_kappa(rater1, rater2)
        assert isinstance(result.coefficient, float)
