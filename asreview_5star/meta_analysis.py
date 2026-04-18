"""
Meta-Analysis Functions

Implements meta-analysis methods including:
- Effect size pooling (fixed and random effects)
- Heterogeneity statistics (I², τ², Q, H²)
- Publication bias tests (Egger's, Begg's)
- Forest plot data generation
"""

import math
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class MetaAnalysisResult:
    """Result of a meta-analysis."""
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    se: float
    z_value: float
    p_value: float
    model: str
    heterogeneity: Dict
    studies: List[Dict]


@dataclass
class BiasTestResult:
    """Result of a publication bias test."""
    statistic: float
    p_value: float
    bias_detected: bool
    interpretation: str
    details: Dict


def pool_effects(
    effects: List[float],
    standard_errors: List[float],
    study_names: Optional[List[str]] = None,
    model: str = "random",
    method: str = "DL"
) -> MetaAnalysisResult:
    """
    Pool effect sizes using meta-analysis.

    Parameters
    ----------
    effects : List[float]
        Effect sizes (log-transformed for OR/RR/HR).
    standard_errors : List[float]
        Standard errors of effect sizes.
    study_names : Optional[List[str]]
        Names of studies for reporting.
    model : str
        'fixed' or 'random' effects model.
    method : str
        Method for random effects: 'DL' (DerSimonian-Laird) or 'REML'.

    Returns
    -------
    MetaAnalysisResult
        Pooled effect size with confidence interval and heterogeneity stats.
    """
    if len(effects) != len(standard_errors):
        raise ValueError("Effects and standard errors must have same length")

    n_studies = len(effects)
    if n_studies == 0:
        raise ValueError("No studies provided")

    effects = np.array(effects)
    ses = np.array(standard_errors)

    if study_names is None:
        study_names = [f"Study {i+1}" for i in range(n_studies)]

    # Calculate weights (inverse variance)
    variances = ses ** 2
    weights_fixed = 1 / variances

    # Fixed effects pooled estimate
    pooled_fixed = np.sum(weights_fixed * effects) / np.sum(weights_fixed)
    se_fixed = 1 / math.sqrt(np.sum(weights_fixed))

    # Q statistic for heterogeneity
    Q = np.sum(weights_fixed * (effects - pooled_fixed) ** 2)
    df = n_studies - 1
    Q_pvalue = 1 - stats.chi2.cdf(Q, df) if df > 0 else 1.0

    # I² statistic
    I_squared = max(0, (Q - df) / Q * 100) if Q > 0 else 0

    # H² statistic
    H_squared = Q / df if df > 0 else 1

    # Between-study variance (τ²) using DerSimonian-Laird
    C = np.sum(weights_fixed) - np.sum(weights_fixed ** 2) / np.sum(weights_fixed)
    tau_squared = max(0, (Q - df) / C) if C > 0 and Q > df else 0

    # Random effects weights
    weights_random = 1 / (variances + tau_squared)

    # Select model
    if model == "fixed":
        weights = weights_fixed
        pooled = pooled_fixed
        se_pooled = se_fixed
    else:  # random
        pooled = np.sum(weights_random * effects) / np.sum(weights_random)
        se_pooled = 1 / math.sqrt(np.sum(weights_random))
        weights = weights_random

    # Confidence interval and test
    z_value = pooled / se_pooled if se_pooled > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_value)))
    ci_lower = pooled - 1.96 * se_pooled
    ci_upper = pooled + 1.96 * se_pooled

    # Prediction interval for random effects
    if model == "random" and tau_squared > 0 and n_studies > 2:
        t_crit = stats.t.ppf(0.975, df)
        pi_lower = pooled - t_crit * math.sqrt(tau_squared + se_pooled ** 2)
        pi_upper = pooled + t_crit * math.sqrt(tau_squared + se_pooled ** 2)
    else:
        pi_lower = ci_lower
        pi_upper = ci_upper

    # Individual study data for forest plot
    studies_data = []
    for i in range(n_studies):
        study_ci_lower = effects[i] - 1.96 * ses[i]
        study_ci_upper = effects[i] + 1.96 * ses[i]
        studies_data.append({
            "name": study_names[i],
            "effect": float(effects[i]),
            "se": float(ses[i]),
            "ci_lower": float(study_ci_lower),
            "ci_upper": float(study_ci_upper),
            "weight": float(weights[i] / np.sum(weights) * 100)
        })

    return MetaAnalysisResult(
        pooled_effect=float(pooled),
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        se=float(se_pooled),
        z_value=float(z_value),
        p_value=float(p_value),
        model=model,
        heterogeneity={
            "Q": float(Q),
            "Q_df": df,
            "Q_pvalue": float(Q_pvalue),
            "I_squared": float(I_squared),
            "H_squared": float(H_squared),
            "tau_squared": float(tau_squared),
            "tau": float(math.sqrt(tau_squared)),
            "prediction_interval": {
                "lower": float(pi_lower),
                "upper": float(pi_upper)
            }
        },
        studies=studies_data
    )


def eggers_test(
    effects: List[float],
    standard_errors: List[float]
) -> BiasTestResult:
    """
    Egger's test for publication bias (small-study effects).

    Tests for asymmetry in funnel plot using regression.

    Parameters
    ----------
    effects : List[float]
        Effect sizes.
    standard_errors : List[float]
        Standard errors of effect sizes.

    Returns
    -------
    BiasTestResult
        Test result with p-value and interpretation.
    """
    if len(effects) < 3:
        return BiasTestResult(
            statistic=0.0,
            p_value=1.0,
            bias_detected=False,
            interpretation="Insufficient studies (need >= 3) for Egger's test.",
            details={"n_studies": len(effects)}
        )

    effects = np.array(effects)
    ses = np.array(standard_errors)

    # Standard normal deviate (effect / SE)
    z_scores = effects / ses

    # Precision (1 / SE)
    precision = 1 / ses

    # Weighted regression of z_scores on precision
    # z = a + b * precision + error
    # Under no bias, intercept a should be 0

    n = len(effects)
    weights = 1 / (ses ** 2)

    # Weighted means
    sum_w = np.sum(weights)
    mean_z = np.sum(weights * z_scores) / sum_w
    mean_prec = np.sum(weights * precision) / sum_w

    # Weighted covariance and variance
    cov = np.sum(weights * (z_scores - mean_z) * (precision - mean_prec)) / sum_w
    var_prec = np.sum(weights * (precision - mean_prec) ** 2) / sum_w

    # Slope and intercept
    slope = cov / var_prec if var_prec > 0 else 0
    intercept = mean_z - slope * mean_prec

    # Standard error of intercept
    residuals = z_scores - (intercept + slope * precision)
    mse = np.sum(weights * residuals ** 2) / (n - 2)
    se_intercept = math.sqrt(mse / sum_w * (1 + mean_prec ** 2 / var_prec)) if var_prec > 0 else 0

    # t-statistic and p-value
    if se_intercept > 0:
        t_stat = intercept / se_intercept
        df = n - 2
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    else:
        t_stat = 0.0
        p_value = 1.0

    bias_detected = p_value < 0.10  # Common threshold

    if bias_detected:
        interpretation = f"Egger's test significant (p={p_value:.3f}). Possible publication bias or small-study effects."
    else:
        interpretation = f"Egger's test not significant (p={p_value:.3f}). No strong evidence of publication bias."

    return BiasTestResult(
        statistic=float(t_stat),
        p_value=float(p_value),
        bias_detected=bias_detected,
        interpretation=interpretation,
        details={
            "intercept": float(intercept),
            "se_intercept": float(se_intercept),
            "slope": float(slope),
            "n_studies": n,
            "df": n - 2
        }
    )


def beggs_test(
    effects: List[float],
    standard_errors: List[float]
) -> BiasTestResult:
    """
    Begg's test (rank correlation) for publication bias.

    Tests for correlation between effect sizes and their variances.

    Parameters
    ----------
    effects : List[float]
        Effect sizes.
    standard_errors : List[float]
        Standard errors of effect sizes.

    Returns
    -------
    BiasTestResult
        Test result with p-value and interpretation.
    """
    if len(effects) < 3:
        return BiasTestResult(
            statistic=0.0,
            p_value=1.0,
            bias_detected=False,
            interpretation="Insufficient studies (need >= 3) for Begg's test.",
            details={"n_studies": len(effects)}
        )

    effects = np.array(effects)
    ses = np.array(standard_errors)
    variances = ses ** 2

    # Standardized effect (subtract pooled estimate)
    weights = 1 / variances
    pooled = np.sum(weights * effects) / np.sum(weights)
    standardized = effects - pooled

    # Kendall's tau between standardized effects and variances
    n = len(effects)

    # Count concordant and discordant pairs
    concordant = 0
    discordant = 0
    ties = 0

    for i in range(n):
        for j in range(i + 1, n):
            prod1 = (standardized[i] - standardized[j]) * (variances[i] - variances[j])
            if prod1 > 0:
                concordant += 1
            elif prod1 < 0:
                discordant += 1
            else:
                ties += 1

    tau = (concordant - discordant) / (concordant + discordant + ties) if (concordant + discordant + ties) > 0 else 0

    # Standard error and z-test
    se_tau = math.sqrt((2 * (2 * n + 5)) / (9 * n * (n - 1))) if n > 1 else 0
    z_stat = tau / se_tau if se_tau > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    bias_detected = p_value < 0.10

    if bias_detected:
        interpretation = f"Begg's test significant (p={p_value:.3f}). Possible publication bias."
    else:
        interpretation = f"Begg's test not significant (p={p_value:.3f}). No strong evidence of publication bias."

    return BiasTestResult(
        statistic=float(tau),
        p_value=float(p_value),
        bias_detected=bias_detected,
        interpretation=interpretation,
        details={
            "kendall_tau": float(tau),
            "z_statistic": float(z_stat),
            "se": float(se_tau),
            "n_studies": n,
            "concordant_pairs": concordant,
            "discordant_pairs": discordant
        }
    )


def heterogeneity_stats(
    effects: List[float],
    standard_errors: List[float]
) -> Dict:
    """
    Calculate heterogeneity statistics.

    Parameters
    ----------
    effects : List[float]
        Effect sizes.
    standard_errors : List[float]
        Standard errors.

    Returns
    -------
    Dict
        Dictionary with Q, I², τ², H², and interpretation.
    """
    result = pool_effects(effects, standard_errors, model="random")
    het = result.heterogeneity

    # Interpretation
    if het["I_squared"] < 25:
        i2_interp = "Low heterogeneity"
    elif het["I_squared"] < 50:
        i2_interp = "Moderate heterogeneity"
    elif het["I_squared"] < 75:
        i2_interp = "Substantial heterogeneity"
    else:
        i2_interp = "Considerable heterogeneity"

    return {
        "Q": het["Q"],
        "Q_df": het["Q_df"],
        "Q_pvalue": het["Q_pvalue"],
        "I_squared": het["I_squared"],
        "I_squared_interpretation": i2_interp,
        "tau_squared": het["tau_squared"],
        "tau": het["tau"],
        "H_squared": het["H_squared"],
        "prediction_interval": het["prediction_interval"]
    }


def forest_plot_data(
    effects: List[float],
    standard_errors: List[float],
    study_names: Optional[List[str]] = None,
    model: str = "random",
    exponentiate: bool = True
) -> Dict:
    """
    Generate data for creating a forest plot.

    Parameters
    ----------
    effects : List[float]
        Effect sizes (log scale if exponentiate=True).
    standard_errors : List[float]
        Standard errors.
    study_names : Optional[List[str]]
        Study names.
    model : str
        'fixed' or 'random'.
    exponentiate : bool
        Whether to exponentiate effects (for OR/RR/HR).

    Returns
    -------
    Dict
        Data suitable for creating a forest plot.
    """
    result = pool_effects(effects, standard_errors, study_names, model)

    # Transform if needed
    def transform(x):
        return math.exp(x) if exponentiate else x

    # Study data
    studies = []
    for s in result.studies:
        studies.append({
            "name": s["name"],
            "effect": transform(s["effect"]),
            "ci_lower": transform(s["ci_lower"]),
            "ci_upper": transform(s["ci_upper"]),
            "weight": s["weight"]
        })

    return {
        "studies": studies,
        "pooled": {
            "effect": transform(result.pooled_effect),
            "ci_lower": transform(result.ci_lower),
            "ci_upper": transform(result.ci_upper),
            "model": model
        },
        "heterogeneity": {
            "I_squared": result.heterogeneity["I_squared"],
            "tau_squared": result.heterogeneity["tau_squared"],
            "Q_pvalue": result.heterogeneity["Q_pvalue"]
        },
        "null_line": 1.0 if exponentiate else 0.0,
        "scale": "log" if exponentiate else "linear"
    }
