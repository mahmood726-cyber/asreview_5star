"""
Stopping Rules for Systematic Reviews

Implements various stopping rules including:
- Bayesian stopping (posterior probability)
- SPRT (Sequential Probability Ratio Test)
- SAFE (Stop After First Estimate) procedure
- Consecutive irrelevant threshold
"""

import math
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from scipy import stats
import numpy as np


@dataclass
class StoppingResult:
    """Result of a stopping rule evaluation."""
    should_stop: bool
    confidence: float
    message: str
    details: Dict


def bayesian_stopping(
    n_screened: int,
    n_relevant: int,
    n_total: int,
    target_recall: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    confidence_threshold: float = 0.95
) -> StoppingResult:
    """
    Bayesian stopping rule based on posterior probability of achieving target recall.

    Uses a Beta-Binomial model to estimate the probability that the remaining
    unscreened documents contain no more relevant documents.

    Parameters
    ----------
    n_screened : int
        Number of documents screened so far.
    n_relevant : int
        Number of relevant documents found so far.
    n_total : int
        Total number of documents in the dataset.
    target_recall : float
        Target recall level (default 0.95).
    prior_alpha : float
        Alpha parameter for Beta prior (default 1.0 = uniform).
    prior_beta : float
        Beta parameter for Beta prior (default 1.0 = uniform).
    confidence_threshold : float
        Confidence threshold for stopping (default 0.95).

    Returns
    -------
    StoppingResult
        Result containing whether to stop, confidence level, and details.
    """
    if n_screened <= 0 or n_total <= 0:
        return StoppingResult(
            should_stop=False,
            confidence=0.0,
            message="Insufficient data for stopping decision.",
            details={"n_screened": n_screened, "n_total": n_total}
        )

    if n_screened >= n_total:
        return StoppingResult(
            should_stop=True,
            confidence=1.0,
            message="All documents have been screened.",
            details={"recall": 1.0}
        )

    n_irrelevant = n_screened - n_relevant
    n_remaining = n_total - n_screened

    # Posterior parameters (Beta distribution)
    post_alpha = prior_alpha + n_relevant
    post_beta = prior_beta + n_irrelevant

    # Estimate prevalence
    prevalence = post_alpha / (post_alpha + post_beta)

    # Expected remaining relevant documents
    expected_remaining = n_remaining * prevalence

    # Calculate probability of achieving target recall
    if n_relevant == 0:
        # No relevant documents found yet
        prob_target_recall = 0.0
    else:
        # Use hypergeometric distribution to estimate
        # probability that we've found at least target_recall of all relevant
        total_relevant_estimate = n_relevant / (n_screened / n_total)

        # Monte Carlo estimation of posterior probability
        n_samples = 10000
        samples = np.random.beta(post_alpha, post_beta, n_samples)
        total_relevant_samples = samples * n_total

        # Probability that current recall >= target
        current_recalls = np.where(
            total_relevant_samples > 0,
            n_relevant / total_relevant_samples,
            1.0
        )
        prob_target_recall = np.mean(current_recalls >= target_recall)

    should_stop = bool(prob_target_recall >= confidence_threshold)

    return StoppingResult(
        should_stop=should_stop,
        confidence=float(prob_target_recall),
        message=f"Bayesian posterior probability of {target_recall:.0%} recall: {prob_target_recall:.2%}",
        details={
            "n_screened": n_screened,
            "n_relevant": n_relevant,
            "n_total": n_total,
            "prevalence_estimate": float(prevalence),
            "expected_remaining_relevant": float(expected_remaining),
            "target_recall": target_recall,
            "confidence_threshold": confidence_threshold
        }
    )


def sprt_stopping(
    n_screened: int,
    n_relevant: int,
    null_prevalence: float = 0.01,
    alt_prevalence: float = 0.05,
    alpha: float = 0.05,
    beta: float = 0.20
) -> StoppingResult:
    """
    Sequential Probability Ratio Test (SPRT) for stopping.

    Tests H0: prevalence <= null_prevalence vs H1: prevalence >= alt_prevalence.

    Parameters
    ----------
    n_screened : int
        Number of documents screened so far.
    n_relevant : int
        Number of relevant documents found so far.
    null_prevalence : float
        Prevalence under null hypothesis (default 0.01).
    alt_prevalence : float
        Prevalence under alternative hypothesis (default 0.05).
    alpha : float
        Type I error rate (default 0.05).
    beta : float
        Type II error rate (default 0.20).

    Returns
    -------
    StoppingResult
        Result containing decision (accept H0, accept H1, or continue).
    """
    if n_screened <= 0:
        return StoppingResult(
            should_stop=False,
            confidence=0.0,
            message="Insufficient data for SPRT.",
            details={}
        )

    # Calculate boundaries
    A = (1 - beta) / alpha  # Upper boundary (accept H1)
    B = beta / (1 - alpha)  # Lower boundary (accept H0)

    # Calculate likelihood ratio
    if n_relevant == 0:
        # Avoid log(0)
        log_ratio = n_screened * (math.log(1 - null_prevalence) - math.log(1 - alt_prevalence))
    elif n_relevant == n_screened:
        log_ratio = n_screened * (math.log(null_prevalence) - math.log(alt_prevalence))
    else:
        log_ratio = (
            n_relevant * math.log(alt_prevalence / null_prevalence) +
            (n_screened - n_relevant) * math.log((1 - alt_prevalence) / (1 - null_prevalence))
        )

    likelihood_ratio = math.exp(log_ratio)

    # Decision
    if likelihood_ratio >= A:
        return StoppingResult(
            should_stop=True,
            confidence=1 - alpha,
            message=f"SPRT: Accept H1 (prevalence >= {alt_prevalence:.1%}). Consider continuing screening.",
            details={
                "likelihood_ratio": likelihood_ratio,
                "upper_boundary": A,
                "lower_boundary": B,
                "decision": "accept_h1"
            }
        )
    elif likelihood_ratio <= B:
        return StoppingResult(
            should_stop=True,
            confidence=1 - beta,
            message=f"SPRT: Accept H0 (prevalence <= {null_prevalence:.1%}). Safe to stop screening.",
            details={
                "likelihood_ratio": likelihood_ratio,
                "upper_boundary": A,
                "lower_boundary": B,
                "decision": "accept_h0"
            }
        )
    else:
        return StoppingResult(
            should_stop=False,
            confidence=0.5,
            message="SPRT: Continue screening. Insufficient evidence.",
            details={
                "likelihood_ratio": likelihood_ratio,
                "upper_boundary": A,
                "lower_boundary": B,
                "decision": "continue"
            }
        )


def safe_stopping(
    n_screened: int,
    n_relevant: int,
    consecutive_irrelevant: int,
    n_total: int,
    target_recall: float = 0.95,
    min_consecutive: int = None
) -> StoppingResult:
    """
    SAFE (Stop After First Estimate) stopping rule.

    Based on Boetje & van de Schoot (2024) method for determining
    when to stop screening based on consecutive irrelevant documents.

    Parameters
    ----------
    n_screened : int
        Number of documents screened so far.
    n_relevant : int
        Number of relevant documents found so far.
    consecutive_irrelevant : int
        Current count of consecutive irrelevant documents.
    n_total : int
        Total number of documents in the dataset.
    target_recall : float
        Target recall level (default 0.95).
    min_consecutive : int
        Minimum consecutive irrelevant needed. If None, calculated automatically.

    Returns
    -------
    StoppingResult
        Result containing whether to stop based on SAFE procedure.
    """
    if n_screened <= 0 or n_relevant <= 0:
        return StoppingResult(
            should_stop=False,
            confidence=0.0,
            message="Need at least one relevant document found to apply SAFE.",
            details={}
        )

    # Calculate required consecutive irrelevant documents
    # Based on hypergeometric probability
    if min_consecutive is None:
        # Calculate threshold based on desired confidence
        # P(missing <= (1-target_recall) * total_relevant | consecutive_irrelevant)

        # Estimate total relevant using current prevalence
        prevalence = n_relevant / n_screened
        estimated_total_relevant = max(n_relevant, int(prevalence * n_total))

        # How many can we miss and still achieve target recall?
        allowed_misses = max(0, int((1 - target_recall) * estimated_total_relevant))

        # Conservative threshold based on negative hypergeometric
        # Rule of thumb: need ~log(1 - confidence) / log(1 - remaining_prevalence)
        remaining = n_total - n_screened
        if remaining > 0 and prevalence > 0:
            remaining_prevalence = prevalence  # Assume same prevalence
            min_consecutive = max(
                10,  # Minimum threshold
                int(-math.log(0.05) / (remaining_prevalence + 0.001))
            )
        else:
            min_consecutive = 50  # Default

    should_stop = bool(consecutive_irrelevant >= min_consecutive)
    confidence = min(1.0, consecutive_irrelevant / min_consecutive)

    return StoppingResult(
        should_stop=should_stop,
        confidence=confidence,
        message=f"SAFE: {consecutive_irrelevant}/{min_consecutive} consecutive irrelevant documents.",
        details={
            "consecutive_irrelevant": consecutive_irrelevant,
            "min_consecutive_required": min_consecutive,
            "n_relevant_found": n_relevant,
            "prevalence": n_relevant / n_screened if n_screened > 0 else 0,
            "target_recall": target_recall
        }
    )


def consecutive_irrelevant_stopping(
    consecutive_count: int,
    threshold: int = 50,
    n_relevant: Optional[int] = None
) -> StoppingResult:
    """
    Simple consecutive irrelevant stopping rule.

    Stop screening after a fixed number of consecutive irrelevant documents.

    Parameters
    ----------
    consecutive_count : int
        Current count of consecutive irrelevant documents.
    threshold : int
        Number of consecutive irrelevant documents required to stop (default 50).
    n_relevant : Optional[int]
        Number of relevant documents found. If explicitly zero, the threshold
        is doubled because no relevant studies have been observed.

    Returns
    -------
    StoppingResult
        Result containing whether to stop.
    """
    if n_relevant == 0:
        # If no relevant documents found, be more cautious
        adjusted_threshold = threshold * 2
    else:
        adjusted_threshold = threshold

    should_stop = bool(consecutive_count >= adjusted_threshold)
    confidence = min(1.0, consecutive_count / adjusted_threshold)

    return StoppingResult(
        should_stop=should_stop,
        confidence=confidence,
        message=f"Consecutive irrelevant: {consecutive_count}/{adjusted_threshold}",
        details={
            "consecutive_count": consecutive_count,
            "threshold": adjusted_threshold,
            "original_threshold": threshold,
            "n_relevant": n_relevant
        }
    )
