"""
Pydantic models for API request/response validation.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================
# Stopping Rules Models
# ============================================================

class BayesianStoppingRequest(BaseModel):
    """Request model for Bayesian stopping rule."""
    n_screened: int = Field(..., gt=0, description="Number of documents screened")
    n_relevant: int = Field(..., ge=0, description="Number of relevant documents found")
    n_total: int = Field(..., gt=0, description="Total number of documents")
    target_recall: float = Field(0.95, gt=0, le=1, description="Target recall level")
    prior_alpha: float = Field(1.0, gt=0, description="Beta prior alpha parameter")
    prior_beta: float = Field(1.0, gt=0, description="Beta prior beta parameter")
    confidence_threshold: float = Field(0.95, gt=0, le=1, description="Confidence threshold")


class SPRTStoppingRequest(BaseModel):
    """Request model for SPRT stopping rule."""
    n_screened: int = Field(..., gt=0, description="Number of documents screened")
    n_relevant: int = Field(..., ge=0, description="Number of relevant documents found")
    null_prevalence: float = Field(0.01, gt=0, lt=1, description="Null hypothesis prevalence")
    alt_prevalence: float = Field(0.05, gt=0, lt=1, description="Alternative hypothesis prevalence")
    alpha: float = Field(0.05, gt=0, lt=1, description="Type I error rate")
    beta: float = Field(0.20, gt=0, lt=1, description="Type II error rate")


class SAFEStoppingRequest(BaseModel):
    """Request model for SAFE stopping rule."""
    n_screened: int = Field(..., gt=0, description="Number of documents screened")
    n_relevant: int = Field(..., ge=0, description="Number of relevant documents found")
    consecutive_irrelevant: int = Field(..., ge=0, description="Consecutive irrelevant count")
    n_total: int = Field(..., gt=0, description="Total number of documents")
    target_recall: float = Field(0.95, gt=0, le=1, description="Target recall level")
    min_consecutive: Optional[int] = Field(None, gt=0, description="Minimum consecutive required")


class StoppingResponse(BaseModel):
    """Response model for stopping rules."""
    should_stop: bool
    confidence: float
    message: str
    details: Dict[str, Any]


# ============================================================
# IRR Models
# ============================================================

class CohensKappaRequest(BaseModel):
    """Request model for Cohen's Kappa."""
    rater1: List[int] = Field(..., min_length=1, description="Ratings from rater 1")
    rater2: List[int] = Field(..., min_length=1, description="Ratings from rater 2")
    weights: Optional[str] = Field(None, description="Weight type: 'linear' or 'quadratic'")


class FleissKappaRequest(BaseModel):
    """Request model for Fleiss' Kappa."""
    ratings: List[List[int]] = Field(
        ...,
        min_length=1,
        description="Matrix of ratings [subjects x raters]"
    )


class IRRResponse(BaseModel):
    """Response model for IRR calculations."""
    coefficient: float
    ci_lower: float
    ci_upper: float
    se: float
    interpretation: str
    p_value: Optional[float]
    details: Dict[str, Any]


# ============================================================
# Meta-Analysis Models
# ============================================================

class PoolEffectsRequest(BaseModel):
    """Request model for pooling effects."""
    effects: List[float] = Field(..., min_length=1, description="Effect sizes")
    standard_errors: List[float] = Field(..., min_length=1, description="Standard errors")
    study_names: Optional[List[str]] = Field(None, description="Study names")
    model: str = Field("random", description="Model type: 'fixed' or 'random'")
    confidence_level: float = Field(0.95, gt=0, lt=1, description="Confidence level")


class MetaAnalysisResponse(BaseModel):
    """Response model for meta-analysis."""
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    se: float
    p_value: float
    z_score: float
    model: str
    heterogeneity: Dict[str, Any]
    studies: List[Dict[str, Any]]


class BiasTestRequest(BaseModel):
    """Request model for publication bias tests."""
    effects: List[float] = Field(..., min_length=3, description="Effect sizes")
    standard_errors: List[float] = Field(..., min_length=3, description="Standard errors")


class BiasTestResponse(BaseModel):
    """Response model for bias tests."""
    test_statistic: float
    p_value: float
    interpretation: str
    details: Dict[str, Any]


# ============================================================
# PRISMA Models
# ============================================================

class PRISMAStatsRequest(BaseModel):
    """Request model for PRISMA statistics."""
    records_total: int = Field(..., gt=0, description="Total records identified")
    records_duplicates: int = Field(..., ge=0, description="Duplicates removed")
    records_screened: int = Field(..., gt=0, description="Records screened")
    records_excluded_screening: int = Field(..., ge=0, description="Excluded at screening")
    records_retrieved: int = Field(..., ge=0, description="Full-text retrieved")
    records_not_retrieved: int = Field(0, ge=0, description="Full-text not retrieved")
    records_excluded_fulltext: int = Field(..., ge=0, description="Excluded at full-text")
    records_from_databases: Optional[int] = Field(None, description="Records from databases")
    records_from_registers: Optional[int] = Field(None, description="Records from registers")
    records_from_other: Optional[int] = Field(None, description="Records from other sources")
    exclusion_reasons: Optional[Dict[str, int]] = Field(None, description="Exclusion reasons")


class PRISMAResponse(BaseModel):
    """Response model for PRISMA statistics."""
    records_identified_databases: int
    records_identified_registers: int
    records_identified_other: int
    records_removed_duplicates: int
    records_screened: int
    records_excluded_screening: int
    reports_retrieved: int
    reports_not_retrieved: int
    reports_assessed: int
    reports_excluded: int
    studies_included: int
    exclusion_reasons: Optional[Dict[str, int]]


class PRISMAFlowResponse(BaseModel):
    """Response model for PRISMA flow data."""
    identification: Dict[str, Any]
    screening: Dict[str, Any]
    eligibility: Dict[str, Any]
    included: Dict[str, Any]
    summary: Dict[str, Any]


# ============================================================
# Error Models
# ============================================================

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str
    status_code: int
