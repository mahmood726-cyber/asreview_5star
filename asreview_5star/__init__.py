"""
ASReview 5-Star: Enhanced Systematic Review Tools

A comprehensive Python package for systematic review workflows including:
- Bayesian and SPRT stopping rules
- Inter-rater reliability (IRR) calculations
- Meta-analysis with forest plots
- PRISMA flow diagram statistics
- REST API for integration

Author: ASReview Team
License: MIT
"""

__version__ = "0.1.0"
__author__ = "ASReview Team"

from .stopping import (
    bayesian_stopping,
    sprt_stopping,
    safe_stopping,
    consecutive_irrelevant_stopping,
)
from .irr import (
    cohens_kappa,
    fleiss_kappa,
    krippendorff_alpha,
    percent_agreement,
)
from .meta_analysis import (
    pool_effects,
    eggers_test,
    beggs_test,
    heterogeneity_stats,
    forest_plot_data,
)
from .prisma import (
    prisma_stats,
    prisma_flow_data,
    generate_prisma_svg,
)

# Lazy import for API to avoid requiring fastapi for basic usage
def get_api():
    """Get the FastAPI application for the REST API."""
    from .api import create_app
    return create_app()

__all__ = [
    # Stopping rules
    "bayesian_stopping",
    "sprt_stopping",
    "safe_stopping",
    "consecutive_irrelevant_stopping",
    # IRR
    "cohens_kappa",
    "fleiss_kappa",
    "krippendorff_alpha",
    "percent_agreement",
    # Meta-analysis
    "pool_effects",
    "eggers_test",
    "beggs_test",
    "heterogeneity_stats",
    "forest_plot_data",
    # PRISMA
    "prisma_stats",
    "prisma_flow_data",
    "generate_prisma_svg",
    # API
    "get_api",
]
