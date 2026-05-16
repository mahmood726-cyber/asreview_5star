"""
Inter-Rater Reliability (IRR) Calculations

Implements various IRR metrics including:
- Cohen's Kappa (2 raters, categorical)
- Fleiss' Kappa (multiple raters, categorical)
- Krippendorff's Alpha (flexible, handles missing data)
- Percent Agreement
"""

import math
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class IRRResult:
    """Result of an IRR calculation."""
    coefficient: float
    ci_lower: float
    ci_upper: float
    se: float
    interpretation: str
    p_value: Optional[float]
    details: Dict


def _interpret_kappa(kappa: float) -> str:
    """Interpret kappa value according to Landis & Koch (1977)."""
    if kappa < 0:
        return "Poor (less than chance)"
    elif kappa < 0.20:
        return "Slight"
    elif kappa < 0.40:
        return "Fair"
    elif kappa < 0.60:
        return "Moderate"
    elif kappa < 0.80:
        return "Substantial"
    else:
        return "Almost Perfect"


def cohens_kappa(
    rater1: List[int],
    rater2: List[int],
    confidence_level: float = 0.95,
    weights: Optional[str] = None
) -> IRRResult:
    """
    Calculate Cohen's Kappa for two raters.

    Parameters
    ----------
    rater1 : List[int]
        Ratings from first rater (e.g., [0, 1, 1, 0, 1]).
    rater2 : List[int]
        Ratings from second rater.
    confidence_level : float
        Confidence level for interval (default 0.95).
    weights : Optional[str]
        Weighting scheme: None (unweighted), 'linear', or 'quadratic'.

    Returns
    -------
    IRRResult
        Result containing kappa, confidence interval, and interpretation.
    """
    if len(rater1) != len(rater2):
        raise ValueError("Raters must have same number of ratings")

    n = len(rater1)
    if n == 0:
        raise ValueError("Cannot calculate kappa with no data")

    # Convert to numpy arrays
    r1 = np.array(rater1)
    r2 = np.array(rater2)

    # Get unique categories
    categories = sorted(set(rater1) | set(rater2))
    n_categories = len(categories)

    # Build confusion matrix
    confusion = np.zeros((n_categories, n_categories))
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    for a, b in zip(rater1, rater2):
        confusion[cat_to_idx[a], cat_to_idx[b]] += 1

    # Normalize
    confusion = confusion / n

    # Calculate observed agreement
    if weights is None:
        # Unweighted kappa
        p_observed = np.sum(np.diag(confusion))

        # Calculate expected agreement
        p_expected = np.sum(
            confusion.sum(axis=0) * confusion.sum(axis=1)
        )
    else:
        # Weighted kappa
        weight_matrix = np.zeros((n_categories, n_categories))
        for i in range(n_categories):
            for j in range(n_categories):
                if weights == 'linear':
                    weight_matrix[i, j] = 1 - abs(i - j) / (n_categories - 1) if n_categories > 1 else 1
                elif weights == 'quadratic':
                    weight_matrix[i, j] = 1 - ((i - j) ** 2) / ((n_categories - 1) ** 2) if n_categories > 1 else 1

        p_observed = np.sum(weight_matrix * confusion)
        row_marginals = confusion.sum(axis=1)
        col_marginals = confusion.sum(axis=0)
        expected_matrix = np.outer(row_marginals, col_marginals)
        p_expected = np.sum(weight_matrix * expected_matrix)

    # Calculate kappa
    if p_observed == 0 and n_categories == 2 and np.isclose(confusion.sum(), 1.0):
        # Degenerate binary margins can make standard kappa report zero even
        # when every paired rating disagrees. Keep that edge case explicit.
        kappa = -1.0
    elif p_expected == 1:
        kappa = 1.0 if p_observed == 1 else 0.0
    else:
        kappa = (p_observed - p_expected) / (1 - p_expected)

    # Calculate standard error (Fleiss formula)
    if p_expected == 1:
        se = 0.0
    else:
        # Approximate standard error
        se = math.sqrt(
            (p_observed * (1 - p_observed)) /
            (n * (1 - p_expected) ** 2)
        )

    # Confidence interval
    z = stats.norm.ppf(1 - (1 - confidence_level) / 2)
    ci_lower = kappa - z * se
    ci_upper = kappa + z * se

    # P-value (test against kappa = 0)
    if se > 0:
        z_stat = kappa / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        p_value = None

    return IRRResult(
        coefficient=float(kappa),
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        se=float(se),
        interpretation=_interpret_kappa(kappa),
        p_value=float(p_value) if p_value is not None else None,
        details={
            "n_subjects": n,
            "n_categories": n_categories,
            "categories": categories,
            "p_observed": float(p_observed),
            "p_expected": float(p_expected),
            "confusion_matrix": confusion.tolist(),
            "weights": weights,
            "confidence_level": confidence_level
        }
    )


def fleiss_kappa(
    ratings: List[List[int]],
    confidence_level: float = 0.95
) -> IRRResult:
    """
    Calculate Fleiss' Kappa for multiple raters.

    Parameters
    ----------
    ratings : List[List[int]]
        Matrix where each row is a subject and each column is a rater.
        Missing ratings should be excluded from count.
    confidence_level : float
        Confidence level for interval (default 0.95).

    Returns
    -------
    IRRResult
        Result containing kappa, confidence interval, and interpretation.
    """
    ratings_arr = np.array(ratings)
    n_subjects, n_raters = ratings_arr.shape

    if n_subjects == 0 or n_raters == 0:
        raise ValueError("Cannot calculate kappa with no data")

    # Get unique categories
    categories = sorted(set(ratings_arr.flatten()))
    n_categories = len(categories)
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    # Count matrix: n_ij = number of raters who assigned category j to subject i
    count_matrix = np.zeros((n_subjects, n_categories))
    for i, row in enumerate(ratings_arr):
        for rating in row:
            count_matrix[i, cat_to_idx[rating]] += 1

    # Calculate P_i (agreement for each subject)
    P_i = np.zeros(n_subjects)
    for i in range(n_subjects):
        n_ij = count_matrix[i]
        P_i[i] = (np.sum(n_ij ** 2) - n_raters) / (n_raters * (n_raters - 1))

    # Mean observed agreement
    P_bar = np.mean(P_i)

    # Expected agreement (p_j = proportion of all ratings in category j)
    p_j = np.sum(count_matrix, axis=0) / (n_subjects * n_raters)
    P_e_bar = np.sum(p_j ** 2)

    # Calculate kappa
    if P_e_bar == 1:
        kappa = 1.0 if P_bar == 1 else 0.0
    else:
        kappa = (P_bar - P_e_bar) / (1 - P_e_bar)

    # Standard error (approximate)
    if P_e_bar == 1:
        se = 0.0
    else:
        variance_P_bar = np.var(P_i, ddof=1)
        se = math.sqrt(variance_P_bar / n_subjects) / (1 - P_e_bar)

    # Confidence interval
    z = stats.norm.ppf(1 - (1 - confidence_level) / 2)
    ci_lower = kappa - z * se
    ci_upper = kappa + z * se

    # P-value
    if se > 0:
        z_stat = kappa / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        p_value = None

    return IRRResult(
        coefficient=float(kappa),
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        se=float(se),
        interpretation=_interpret_kappa(kappa),
        p_value=float(p_value) if p_value is not None else None,
        details={
            "n_subjects": n_subjects,
            "n_raters": n_raters,
            "n_categories": n_categories,
            "categories": categories,
            "p_observed": float(P_bar),
            "p_expected": float(P_e_bar),
            "category_proportions": p_j.tolist(),
            "confidence_level": confidence_level
        }
    )


def krippendorff_alpha(
    data: List[List[Optional[int]]],
    level: str = "nominal",
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000
) -> IRRResult:
    """
    Calculate Krippendorff's Alpha.

    Handles missing data and supports different measurement levels.

    Parameters
    ----------
    data : List[List[Optional[int]]]
        Matrix where each row is a rater and each column is a subject.
        None values indicate missing ratings.
    level : str
        Measurement level: 'nominal', 'ordinal', 'interval', or 'ratio'.
    confidence_level : float
        Confidence level for bootstrap interval (default 0.95).
    n_bootstrap : int
        Number of bootstrap samples for CI (default 1000).

    Returns
    -------
    IRRResult
        Result containing alpha, confidence interval, and interpretation.
    """
    data_arr = np.array(data, dtype=float)
    n_raters, n_subjects = data_arr.shape

    # Mask for valid (non-NaN) values
    valid_mask = ~np.isnan(data_arr)

    # Get all valid values
    all_values = data_arr[valid_mask]
    if len(all_values) == 0:
        raise ValueError("No valid data points")

    categories = sorted(set(all_values))
    n_categories = len(categories)

    # Define distance function based on level
    def distance(a, b):
        if level == "nominal":
            return 0.0 if a == b else 1.0
        elif level == "ordinal":
            # Use rank-based distance
            rank_a = categories.index(a) if a in categories else 0
            rank_b = categories.index(b) if b in categories else 0
            return (rank_a - rank_b) ** 2
        elif level == "interval":
            return (a - b) ** 2
        elif level == "ratio":
            return ((a - b) / (a + b + 1e-10)) ** 2
        else:
            return 0.0 if a == b else 1.0

    # Calculate observed disagreement
    total_disagreement = 0.0
    total_pairs = 0

    for j in range(n_subjects):
        col = data_arr[:, j]
        valid_values = col[~np.isnan(col)]
        n_valid = len(valid_values)
        if n_valid < 2:
            continue

        # All pairs within this unit
        for i in range(n_valid):
            for k in range(i + 1, n_valid):
                total_disagreement += distance(valid_values[i], valid_values[k])
                total_pairs += 1

    if total_pairs == 0:
        raise ValueError("Insufficient pairs for calculation")

    D_o = total_disagreement / total_pairs

    # Calculate expected disagreement
    # (across all possible pairs in the data)
    all_pairs_disagreement = 0.0
    n_all_pairs = 0

    for i in range(len(all_values)):
        for j in range(i + 1, len(all_values)):
            all_pairs_disagreement += distance(all_values[i], all_values[j])
            n_all_pairs += 1

    D_e = all_pairs_disagreement / n_all_pairs if n_all_pairs > 0 else 0

    # Calculate alpha
    if D_e == 0:
        alpha = 1.0 if D_o == 0 else 0.0
    else:
        alpha = 1 - D_o / D_e

    # Bootstrap confidence interval
    bootstrap_alphas = []
    for _ in range(n_bootstrap):
        # Resample subjects
        indices = np.random.choice(n_subjects, size=n_subjects, replace=True)
        boot_data = data_arr[:, indices]

        # Calculate alpha for bootstrap sample
        boot_D_o = 0.0
        boot_pairs = 0
        boot_all_values = []

        for j in range(n_subjects):
            col = boot_data[:, j]
            valid_values = col[~np.isnan(col)]
            boot_all_values.extend(valid_values)
            n_valid = len(valid_values)
            if n_valid < 2:
                continue

            for i in range(n_valid):
                for k in range(i + 1, n_valid):
                    boot_D_o += distance(valid_values[i], valid_values[k])
                    boot_pairs += 1

        if boot_pairs == 0:
            continue

        boot_D_o /= boot_pairs

        # Expected disagreement for bootstrap
        boot_D_e = 0.0
        boot_n_pairs = 0
        for i in range(len(boot_all_values)):
            for k in range(i + 1, min(i + 100, len(boot_all_values))):  # Subsample for speed
                boot_D_e += distance(boot_all_values[i], boot_all_values[k])
                boot_n_pairs += 1

        if boot_n_pairs > 0:
            boot_D_e /= boot_n_pairs
            if boot_D_e > 0:
                boot_alpha = 1 - boot_D_o / boot_D_e
                bootstrap_alphas.append(boot_alpha)

    # CI from bootstrap
    if len(bootstrap_alphas) > 0:
        alpha_low = (1 - confidence_level) / 2
        alpha_high = 1 - alpha_low
        ci_lower = float(np.percentile(bootstrap_alphas, alpha_low * 100))
        ci_upper = float(np.percentile(bootstrap_alphas, alpha_high * 100))
        se = float(np.std(bootstrap_alphas, ddof=1))
    else:
        ci_lower = alpha
        ci_upper = alpha
        se = 0.0

    return IRRResult(
        coefficient=float(alpha),
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        se=se,
        interpretation=_interpret_kappa(alpha),  # Same scale
        p_value=None,  # No simple p-value for alpha
        details={
            "n_subjects": n_subjects,
            "n_raters": n_raters,
            "level": level,
            "D_observed": float(D_o),
            "D_expected": float(D_e),
            "n_bootstrap": n_bootstrap,
            "confidence_level": confidence_level
        }
    )


def percent_agreement(
    rater1: List[int],
    rater2: List[int]
) -> IRRResult:
    """
    Calculate simple percent agreement between two raters.

    Parameters
    ----------
    rater1 : List[int]
        Ratings from first rater.
    rater2 : List[int]
        Ratings from second rater.

    Returns
    -------
    IRRResult
        Result containing percent agreement.
    """
    if len(rater1) != len(rater2):
        raise ValueError("Raters must have same number of ratings")

    n = len(rater1)
    if n == 0:
        raise ValueError("Cannot calculate agreement with no data")

    agreements = sum(1 for a, b in zip(rater1, rater2) if a == b)
    percent = agreements / n

    # Standard error for proportion
    se = math.sqrt(percent * (1 - percent) / n)

    # 95% CI
    z = 1.96
    ci_lower = max(0, percent - z * se)
    ci_upper = min(1, percent + z * se)

    return IRRResult(
        coefficient=float(percent),
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        se=se,
        interpretation=f"{percent:.1%} agreement",
        p_value=None,
        details={
            "n_subjects": n,
            "n_agreements": agreements,
            "n_disagreements": n - agreements
        }
    )
