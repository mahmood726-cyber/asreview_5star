"""
ASReview 5-Star REST API

Provides HTTP endpoints for:
- Stopping rules (Bayesian, SPRT, SAFE)
- Inter-rater reliability (Cohen's Kappa, Fleiss' Kappa)
- Meta-analysis (effect pooling, bias tests)
- PRISMA statistics
"""

from .app import create_app

__all__ = ["create_app"]
