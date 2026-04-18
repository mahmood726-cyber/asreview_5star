"""
API Routes for ASReview 5-Star.

Defines all HTTP endpoints for the REST API.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .models import (
    # Stopping
    BayesianStoppingRequest,
    SPRTStoppingRequest,
    SAFEStoppingRequest,
    StoppingResponse,
    # IRR
    CohensKappaRequest,
    FleissKappaRequest,
    IRRResponse,
    # Meta-analysis
    PoolEffectsRequest,
    MetaAnalysisResponse,
    BiasTestRequest,
    BiasTestResponse,
    # PRISMA
    PRISMAStatsRequest,
    PRISMAResponse,
    PRISMAFlowResponse,
)

from ..stopping import bayesian_stopping, sprt_stopping, safe_stopping
from ..irr import cohens_kappa, fleiss_kappa
from ..meta_analysis import pool_effects, eggers_test, beggs_test
from ..prisma import prisma_stats, prisma_flow_data


# ============================================================
# Router Setup
# ============================================================

router = APIRouter(prefix="/api/v1", tags=["ASReview 5-Star"])


# ============================================================
# Health Check
# ============================================================

@router.get("/health", tags=["System"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# ============================================================
# Stopping Rules Endpoints
# ============================================================

@router.post("/stopping/bayesian", response_model=StoppingResponse, tags=["Stopping Rules"])
async def api_bayesian_stopping(request: BayesianStoppingRequest) -> StoppingResponse:
    """
    Calculate Bayesian stopping probability.

    Uses a Beta-Binomial model to estimate the probability that
    the target recall has been achieved.
    """
    try:
        result = bayesian_stopping(
            n_screened=request.n_screened,
            n_relevant=request.n_relevant,
            n_total=request.n_total,
            target_recall=request.target_recall,
            prior_alpha=request.prior_alpha,
            prior_beta=request.prior_beta,
            confidence_threshold=request.confidence_threshold
        )
        return StoppingResponse(
            should_stop=result.should_stop,
            confidence=result.confidence,
            message=result.message,
            details=result.details
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stopping/sprt", response_model=StoppingResponse, tags=["Stopping Rules"])
async def api_sprt_stopping(request: SPRTStoppingRequest) -> StoppingResponse:
    """
    Sequential Probability Ratio Test (SPRT) for stopping.

    Tests whether the prevalence is below a null threshold,
    indicating it's safe to stop screening.
    """
    try:
        result = sprt_stopping(
            n_screened=request.n_screened,
            n_relevant=request.n_relevant,
            null_prevalence=request.null_prevalence,
            alt_prevalence=request.alt_prevalence,
            alpha=request.alpha,
            beta=request.beta
        )
        return StoppingResponse(
            should_stop=result.should_stop,
            confidence=result.confidence,
            message=result.message,
            details=result.details
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stopping/safe", response_model=StoppingResponse, tags=["Stopping Rules"])
async def api_safe_stopping(request: SAFEStoppingRequest) -> StoppingResponse:
    """
    SAFE (Stop After First Estimate) stopping rule.

    Determines when to stop based on consecutive irrelevant documents
    and estimated prevalence.
    """
    try:
        result = safe_stopping(
            n_screened=request.n_screened,
            n_relevant=request.n_relevant,
            consecutive_irrelevant=request.consecutive_irrelevant,
            n_total=request.n_total,
            target_recall=request.target_recall,
            min_consecutive=request.min_consecutive
        )
        return StoppingResponse(
            should_stop=result.should_stop,
            confidence=result.confidence,
            message=result.message,
            details=result.details
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# IRR Endpoints
# ============================================================

@router.post("/irr/cohens-kappa", response_model=IRRResponse, tags=["Inter-Rater Reliability"])
async def api_cohens_kappa(request: CohensKappaRequest) -> IRRResponse:
    """
    Calculate Cohen's Kappa for two raters.

    Measures agreement between two raters accounting for chance agreement.
    Supports unweighted, linear, and quadratic weighted kappa.
    """
    try:
        if len(request.rater1) != len(request.rater2):
            raise ValueError("Rater lists must have equal length")

        result = cohens_kappa(
            rater1=request.rater1,
            rater2=request.rater2,
            weights=request.weights
        )
        return IRRResponse(
            coefficient=result.coefficient,
            ci_lower=result.ci_lower,
            ci_upper=result.ci_upper,
            se=result.se,
            interpretation=result.interpretation,
            p_value=result.p_value,
            details=result.details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/irr/fleiss-kappa", response_model=IRRResponse, tags=["Inter-Rater Reliability"])
async def api_fleiss_kappa(request: FleissKappaRequest) -> IRRResponse:
    """
    Calculate Fleiss' Kappa for multiple raters.

    Measures agreement among multiple raters on categorical data.
    """
    try:
        result = fleiss_kappa(ratings=request.ratings)
        return IRRResponse(
            coefficient=result.coefficient,
            ci_lower=result.ci_lower,
            ci_upper=result.ci_upper,
            se=result.se,
            interpretation=result.interpretation,
            p_value=result.p_value,
            details=result.details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Meta-Analysis Endpoints
# ============================================================

@router.post("/meta/pool", response_model=MetaAnalysisResponse, tags=["Meta-Analysis"])
async def api_pool_effects(request: PoolEffectsRequest) -> MetaAnalysisResponse:
    """
    Pool effect sizes using fixed or random effects model.

    Implements inverse-variance weighting and DerSimonian-Laird
    random effects estimation.
    """
    try:
        if len(request.effects) != len(request.standard_errors):
            raise ValueError("Effects and standard errors must have equal length")

        result = pool_effects(
            effects=request.effects,
            standard_errors=request.standard_errors,
            study_names=request.study_names,
            model=request.model,
            confidence_level=request.confidence_level
        )
        return MetaAnalysisResponse(
            pooled_effect=result.pooled_effect,
            ci_lower=result.ci_lower,
            ci_upper=result.ci_upper,
            se=result.se,
            p_value=result.p_value,
            z_score=result.z_score,
            model=result.model,
            heterogeneity=result.heterogeneity,
            studies=result.studies
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meta/eggers-test", response_model=BiasTestResponse, tags=["Meta-Analysis"])
async def api_eggers_test(request: BiasTestRequest) -> BiasTestResponse:
    """
    Egger's test for publication bias.

    Tests for asymmetry in the funnel plot using weighted regression.
    """
    try:
        if len(request.effects) != len(request.standard_errors):
            raise ValueError("Effects and standard errors must have equal length")

        result = eggers_test(
            effects=request.effects,
            standard_errors=request.standard_errors
        )
        return BiasTestResponse(
            test_statistic=result.test_statistic,
            p_value=result.p_value,
            interpretation=result.interpretation,
            details=result.details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meta/beggs-test", response_model=BiasTestResponse, tags=["Meta-Analysis"])
async def api_beggs_test(request: BiasTestRequest) -> BiasTestResponse:
    """
    Begg's test for publication bias.

    Tests for rank correlation between effect sizes and their variances.
    """
    try:
        if len(request.effects) != len(request.standard_errors):
            raise ValueError("Effects and standard errors must have equal length")

        result = beggs_test(
            effects=request.effects,
            standard_errors=request.standard_errors
        )
        return BiasTestResponse(
            test_statistic=result.test_statistic,
            p_value=result.p_value,
            interpretation=result.interpretation,
            details=result.details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# PRISMA Endpoints
# ============================================================

@router.post("/prisma/stats", response_model=PRISMAResponse, tags=["PRISMA"])
async def api_prisma_stats(request: PRISMAStatsRequest) -> PRISMAResponse:
    """
    Calculate PRISMA flow diagram statistics.

    Computes all intermediate values for a PRISMA 2020 flow diagram.
    """
    try:
        result = prisma_stats(
            records_total=request.records_total,
            records_duplicates=request.records_duplicates,
            records_screened=request.records_screened,
            records_excluded_screening=request.records_excluded_screening,
            records_retrieved=request.records_retrieved,
            records_not_retrieved=request.records_not_retrieved,
            records_excluded_fulltext=request.records_excluded_fulltext,
            records_from_databases=request.records_from_databases,
            records_from_registers=request.records_from_registers,
            records_from_other=request.records_from_other,
            exclusion_reasons=request.exclusion_reasons
        )
        return PRISMAResponse(
            records_identified_databases=result.records_identified_databases,
            records_identified_registers=result.records_identified_registers,
            records_identified_other=result.records_identified_other,
            records_removed_duplicates=result.records_removed_duplicates,
            records_screened=result.records_screened,
            records_excluded_screening=result.records_excluded_screening,
            reports_retrieved=result.reports_retrieved,
            reports_not_retrieved=result.reports_not_retrieved,
            reports_assessed=result.reports_assessed,
            reports_excluded=result.reports_excluded,
            studies_included=result.studies_included,
            exclusion_reasons=result.exclusion_reasons
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prisma/flow", response_model=PRISMAFlowResponse, tags=["PRISMA"])
async def api_prisma_flow(request: PRISMAStatsRequest) -> PRISMAFlowResponse:
    """
    Generate PRISMA flow diagram data structure.

    Returns structured data suitable for rendering a PRISMA 2020 flow diagram.
    """
    try:
        stats = prisma_stats(
            records_total=request.records_total,
            records_duplicates=request.records_duplicates,
            records_screened=request.records_screened,
            records_excluded_screening=request.records_excluded_screening,
            records_retrieved=request.records_retrieved,
            records_not_retrieved=request.records_not_retrieved,
            records_excluded_fulltext=request.records_excluded_fulltext,
            records_from_databases=request.records_from_databases,
            records_from_registers=request.records_from_registers,
            records_from_other=request.records_from_other,
            exclusion_reasons=request.exclusion_reasons
        )
        flow_data = prisma_flow_data(stats)
        return PRISMAFlowResponse(**flow_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
