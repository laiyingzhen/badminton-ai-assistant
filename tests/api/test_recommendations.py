from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_recommendation_service
from app.exceptions.recommendation import (
    NoRacketCandidateError,
    DatabaseServiceError,
    GeminiServiceError,
)
from app.schemas.recommendation import RacketCandidate
from decimal import Decimal
client = TestClient(app)


# ============================================================
# Helpers
# ============================================================

def create_mock_service():
    return Mock()


def override_recommendation_service(mock_service):
    app.dependency_overrides[
        get_recommendation_service
    ] = lambda: mock_service


def clear_dependency_overrides():
    app.dependency_overrides.clear()


# ============================================================
# 1. Success - 200
# ============================================================

def test_recommendation_success():

    mock_service = create_mock_service()

    # mock_service.recommend_racket.return_value = (
    #     Mock(
    #         id=1,
    #         brand="Yonex",
    #         model="Astrox 7 DG",
    #         price=2990,
    #         distance=0.232582,
    #         similarity=0.767418,
    #     ),
    #     "適合中階進攻型球友，價格符合預算。",
    # )
    candidate = RacketCandidate(
        id=1,
        brand="Yonex",
        model="Astrox 7 DG",
        price=2990,
        distance=0.232582,
        similarity=0.767418,
    )

    mock_service.recommend_racket.return_value = (
        candidate,
        "適合中階進攻型球友，價格符合預算。",
    )    

    override_recommendation_service(
        mock_service
    )

    try:
        response = client.post(
            "/api/v1/recommendations/rackets",
            json={
                "level": "intermediate",
                "playing_style": "offensive",
                "budget": 5000,
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["racket"]["id"] == 1
        assert body["racket"]["brand"] == "Yonex"
        assert body["racket"]["model"] == "Astrox 7 DG"
        #assert body["racket"]["price"] == 2990
        assert Decimal(body["racket"]["price"]) == Decimal("2990")        

        assert body["racket"]["distance"] == 0.232582

        assert body["reason"] == (
            "適合中階進攻型球友，價格符合預算。"
        )

        mock_service.recommend_racket.assert_called_once()

    finally:
        clear_dependency_overrides()


# ============================================================
# 2. No Candidate - 404
# ============================================================

def test_recommendation_no_candidates():

    mock_service = create_mock_service()

    mock_service.recommend_racket.side_effect = (
        NoRacketCandidateError(
            budget=3000
        )
    )

    override_recommendation_service(
        mock_service
    )

    try:
        response = client.post(
            "/api/v1/recommendations/rackets",
            json={
                "level": "beginner",
                "playing_style": "defensive",
                "budget": 3000,
            },
        )

        assert response.status_code == 404

        body = response.json()

        assert body["error"]["code"] == (
            "NO_RACKET_CANDIDATE"
        )

    finally:
        clear_dependency_overrides()


# ============================================================
# 3. Gemini Failure - 502
# ============================================================

def test_recommendation_gemini_failure():

    mock_service = create_mock_service()

    mock_service.recommend_racket.side_effect = (
        GeminiServiceError(
            "Gemini service failed."
        )
    )

    override_recommendation_service(
        mock_service
    )

    try:
        response = client.post(
            "/api/v1/recommendations/rackets",
            json={
                "level": "intermediate",
                "playing_style": "offensive",
                "budget": 5000,
            },
        )

        assert response.status_code == 502

        body = response.json()

        assert body["error"]["code"] == (
            "GEMINI_SERVICE_ERROR"
        )

    finally:
        clear_dependency_overrides()


# ============================================================
# 4. Database Failure - 503
# ============================================================

def test_recommendation_database_failure():

    mock_service = create_mock_service()

    mock_service.recommend_racket.side_effect = (
        DatabaseServiceError(
            "Database service failed."
        )
    )

    override_recommendation_service(
        mock_service
    )

    try:
        response = client.post(
            "/api/v1/recommendations/rackets",
            json={
                "level": "intermediate",
                "playing_style": "offensive",
                "budget": 5000,
            },
        )

        assert response.status_code == 503

        body = response.json()

        assert body["error"]["code"] == (
            "DATABASE_SERVICE_ERROR"
        )

    finally:
        clear_dependency_overrides()


# ============================================================
# 5. Request Validation - 422
# ============================================================

def test_recommendation_invalid_request():

    mock_service = create_mock_service()

    override_recommendation_service(
        mock_service
    )

    try:
        response = client.post(
            "/api/v1/recommendations/rackets",
            json={
                "level": "intermediate",
                "playing_style": "offensive",
                "budget": -100,
            },
        )

        assert response.status_code == 422

        body = response.json()

        assert "error" in body

        mock_service.recommend_racket.assert_not_called()

    finally:
        clear_dependency_overrides()

def test_recommendation_missing_budget():

    mock_service = create_mock_service()

    override_recommendation_service(
        mock_service
    )

    try:
        response = client.post(
            "/api/v1/recommendations/rackets",
            json={
                "level": "intermediate",
                "playing_style": "offensive",
            },
        )

        assert response.status_code == 422

        body = response.json()

        assert body["error"]["code"] == (
            "VALIDATION_ERROR"
        )

        assert body["error"]["message"] == (
            "Request validation failed."
        )

        assert any(
            detail["field"] == "budget"
            for detail in body["error"]["details"]
        )

        mock_service.recommend_racket.assert_not_called()

    finally:
        clear_dependency_overrides()
