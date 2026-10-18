"""Count-accounting software fixtures, not review or clinical findings."""
import pytest

from asreview_5star.prisma import prisma_stats


def counts(**changes):
    values = dict(records_total=20, records_duplicates=2, records_screened=18,
                  records_excluded_screening=10, records_retrieved=8,
                  records_not_retrieved=1, records_excluded_fulltext=3)
    values.update(changes)
    return values


@pytest.mark.parametrize("field", list(counts()) + ["records_from_databases", "records_from_registers", "records_from_other"])
@pytest.mark.parametrize("value", [-1, 0.5, True])
def test_counts_must_be_nonnegative_integers(field, value):
    with pytest.raises(ValueError):
        prisma_stats(**counts(**{field: value}))


@pytest.mark.parametrize("changes", [
    {"records_duplicates": 21}, {"records_screened": 19},
    {"records_excluded_screening": 19}, {"records_not_retrieved": 9},
    {"records_excluded_fulltext": 8}, {"records_from_registers": 21},
    {"records_from_databases": 19}, {"exclusion_reasons": {"fixture": -1}},
    {"exclusion_reasons": {"fixture": 2}},
])
def test_impossible_stage_counts_are_rejected(changes):
    with pytest.raises(ValueError):
        prisma_stats(**counts(**changes))


def test_zero_counts_are_valid_and_input_reasons_are_copied():
    empty = {name: 0 for name in counts()}
    assert prisma_stats(**empty).studies_included == 0
    reasons = {"software fixture": 3}
    result = prisma_stats(**counts(exclusion_reasons=reasons))
    reasons["software fixture"] = 99
    assert result.exclusion_reasons == {"software fixture": 3}


@pytest.mark.parametrize("endpoint", ["stats", "flow"])
def test_api_rejects_negative_derived_results(endpoint):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from asreview_5star.api.app import create_app
    with TestClient(create_app()) as client:
        response = client.post(f"/api/v1/prisma/{endpoint}", json=counts(records_not_retrieved=9))
    assert response.status_code == 400
    assert "not_retrieved" in response.json()["detail"]


@pytest.mark.parametrize("value", [True, 1.5, "18"])
def test_api_does_not_coerce_invalid_counts(value):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from asreview_5star.api.app import create_app
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/prisma/stats", json=counts(records_screened=value))
    assert response.status_code == 422


def test_api_accepts_an_empty_review():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from asreview_5star.api.app import create_app
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/prisma/stats", json={name: 0 for name in counts()})
    assert response.status_code == 200
    assert response.json()["studies_included"] == 0
