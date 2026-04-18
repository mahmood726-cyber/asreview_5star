"""Tests for ASReview 5-Star REST API."""

import pytest
import math
from fastapi.testclient import TestClient
from asreview_5star.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ASReview 5-Star API"
        assert "endpoints" in data


class TestStoppingEndpoints:
    """Tests for stopping rule endpoints."""

    def test_bayesian_stopping(self, client):
        """Test Bayesian stopping endpoint."""
        response = client.post("/api/v1/stopping/bayesian", json={
            "n_screened": 500,
            "n_relevant": 25,
            "n_total": 5000,
            "target_recall": 0.95
        })
        assert response.status_code == 200
        data = response.json()
        assert "should_stop" in data
        assert "confidence" in data
        assert "message" in data
        assert 0 <= data["confidence"] <= 1

    def test_bayesian_stopping_invalid(self, client):
        """Test Bayesian stopping with invalid data."""
        response = client.post("/api/v1/stopping/bayesian", json={
            "n_screened": -1,
            "n_relevant": 25,
            "n_total": 5000
        })
        assert response.status_code == 422  # Validation error

    def test_sprt_stopping(self, client):
        """Test SPRT stopping endpoint."""
        response = client.post("/api/v1/stopping/sprt", json={
            "n_screened": 500,
            "n_relevant": 10,
            "null_prevalence": 0.01,
            "alt_prevalence": 0.05
        })
        assert response.status_code == 200
        data = response.json()
        assert "should_stop" in data
        assert "details" in data

    def test_safe_stopping(self, client):
        """Test SAFE stopping endpoint."""
        response = client.post("/api/v1/stopping/safe", json={
            "n_screened": 500,
            "n_relevant": 25,
            "consecutive_irrelevant": 50,
            "n_total": 5000,
            "target_recall": 0.95
        })
        assert response.status_code == 200
        data = response.json()
        assert "should_stop" in data


class TestIRREndpoints:
    """Tests for IRR endpoints."""

    def test_cohens_kappa(self, client):
        """Test Cohen's Kappa endpoint."""
        response = client.post("/api/v1/irr/cohens-kappa", json={
            "rater1": [1, 1, 0, 0, 1, 0, 1, 0],
            "rater2": [1, 0, 0, 0, 1, 0, 1, 0]
        })
        assert response.status_code == 200
        data = response.json()
        assert "coefficient" in data
        assert "interpretation" in data
        assert -1 <= data["coefficient"] <= 1

    def test_cohens_kappa_perfect_agreement(self, client):
        """Test Cohen's Kappa with perfect agreement."""
        response = client.post("/api/v1/irr/cohens-kappa", json={
            "rater1": [1, 1, 0, 0, 1],
            "rater2": [1, 1, 0, 0, 1]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["coefficient"] == 1.0

    def test_cohens_kappa_weighted(self, client):
        """Test weighted Cohen's Kappa."""
        response = client.post("/api/v1/irr/cohens-kappa", json={
            "rater1": [0, 1, 2, 0, 1, 2],
            "rater2": [0, 1, 2, 1, 1, 1],
            "weights": "linear"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["details"]["weights"] == "linear"

    def test_cohens_kappa_unequal_length(self, client):
        """Test Cohen's Kappa with unequal lengths."""
        response = client.post("/api/v1/irr/cohens-kappa", json={
            "rater1": [1, 1, 0],
            "rater2": [1, 0]
        })
        assert response.status_code == 400

    def test_fleiss_kappa(self, client):
        """Test Fleiss' Kappa endpoint."""
        response = client.post("/api/v1/irr/fleiss-kappa", json={
            "ratings": [
                [1, 1, 0],
                [0, 0, 0],
                [1, 1, 1],
                [0, 1, 0]
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "coefficient" in data
        assert "interpretation" in data


class TestMetaAnalysisEndpoints:
    """Tests for meta-analysis endpoints."""

    def test_pool_effects_random(self, client):
        """Test effect pooling with random effects."""
        response = client.post("/api/v1/meta/pool", json={
            "effects": [math.log(0.8), math.log(0.75), math.log(0.85)],
            "standard_errors": [0.1, 0.12, 0.11],
            "model": "random"
        })
        assert response.status_code == 200
        data = response.json()
        assert "pooled_effect" in data
        assert data["model"] == "random"
        assert "heterogeneity" in data

    def test_pool_effects_fixed(self, client):
        """Test effect pooling with fixed effects."""
        response = client.post("/api/v1/meta/pool", json={
            "effects": [math.log(0.8), math.log(0.75), math.log(0.85)],
            "standard_errors": [0.1, 0.12, 0.11],
            "model": "fixed"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "fixed"

    def test_pool_effects_with_names(self, client):
        """Test effect pooling with study names."""
        response = client.post("/api/v1/meta/pool", json={
            "effects": [math.log(0.8), math.log(0.75)],
            "standard_errors": [0.1, 0.12],
            "study_names": ["Study A", "Study B"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["studies"][0]["name"] == "Study A"

    def test_eggers_test(self, client):
        """Test Egger's test endpoint."""
        response = client.post("/api/v1/meta/eggers-test", json={
            "effects": [math.log(0.8), math.log(0.75), math.log(0.85), math.log(0.7)],
            "standard_errors": [0.1, 0.12, 0.11, 0.15]
        })
        assert response.status_code == 200
        data = response.json()
        assert "p_value" in data
        assert "interpretation" in data

    def test_beggs_test(self, client):
        """Test Begg's test endpoint."""
        response = client.post("/api/v1/meta/beggs-test", json={
            "effects": [math.log(0.8), math.log(0.75), math.log(0.85), math.log(0.7)],
            "standard_errors": [0.1, 0.12, 0.11, 0.15]
        })
        assert response.status_code == 200
        data = response.json()
        assert "p_value" in data
        assert "details" in data


class TestPRISMAEndpoints:
    """Tests for PRISMA endpoints."""

    def test_prisma_stats(self, client):
        """Test PRISMA statistics endpoint."""
        response = client.post("/api/v1/prisma/stats", json={
            "records_total": 1500,
            "records_duplicates": 300,
            "records_screened": 1200,
            "records_excluded_screening": 1050,
            "records_retrieved": 150,
            "records_not_retrieved": 10,
            "records_excluded_fulltext": 90
        })
        assert response.status_code == 200
        data = response.json()
        assert data["records_identified_databases"] == 1500
        assert data["studies_included"] == 50

    def test_prisma_stats_with_sources(self, client):
        """Test PRISMA statistics with different sources."""
        response = client.post("/api/v1/prisma/stats", json={
            "records_total": 1500,
            "records_duplicates": 300,
            "records_screened": 1200,
            "records_excluded_screening": 1050,
            "records_retrieved": 150,
            "records_not_retrieved": 10,
            "records_excluded_fulltext": 90,
            "records_from_databases": 1200,
            "records_from_registers": 200,
            "records_from_other": 100
        })
        assert response.status_code == 200
        data = response.json()
        assert data["records_identified_databases"] == 1200
        assert data["records_identified_registers"] == 200

    def test_prisma_flow(self, client):
        """Test PRISMA flow data endpoint."""
        response = client.post("/api/v1/prisma/flow", json={
            "records_total": 1000,
            "records_duplicates": 100,
            "records_screened": 900,
            "records_excluded_screening": 800,
            "records_retrieved": 100,
            "records_not_retrieved": 5,
            "records_excluded_fulltext": 75
        })
        assert response.status_code == 200
        data = response.json()
        assert "identification" in data
        assert "screening" in data
        assert "eligibility" in data
        assert "included" in data
        assert "summary" in data

    def test_prisma_with_exclusion_reasons(self, client):
        """Test PRISMA with exclusion reasons."""
        response = client.post("/api/v1/prisma/stats", json={
            "records_total": 1000,
            "records_duplicates": 100,
            "records_screened": 900,
            "records_excluded_screening": 800,
            "records_retrieved": 100,
            "records_not_retrieved": 5,
            "records_excluded_fulltext": 75,
            "exclusion_reasons": {
                "Wrong population": 30,
                "Wrong intervention": 25,
                "Wrong outcome": 20
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["exclusion_reasons"]["Wrong population"] == 30


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # CORS preflight should be handled
        assert response.status_code in [200, 204]


class TestOpenAPI:
    """Tests for OpenAPI documentation."""

    def test_openapi_json(self, client):
        """Test OpenAPI JSON is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_docs_page(self, client):
        """Test Swagger docs page is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
