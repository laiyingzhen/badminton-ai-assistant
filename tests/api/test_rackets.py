from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_racket_service
from app.exceptions.recommendation import DatabaseServiceError
from app.main import app
from app.models.racket import Racket


client = TestClient(app)


@pytest.fixture
def mock_racket_service():
    service = Mock()

    app.dependency_overrides[
        get_racket_service
    ] = lambda: service

    yield service

    app.dependency_overrides.clear()


def create_racket() -> Racket:
    return Racket(
        id=1,
        brand="YONEX",
        model="ASTROX 88 D PRO",
        price=Decimal("4890.00"),
        weight="4U",
        balance="head_heavy",
        flexibility="stiff",
        suitable_level="advanced",
        playing_style="offensive",
        description="適合後場進攻型選手。",
        image_url=(
            "https://storage.googleapis.com/"
            "badminton-rackets/astrox-88-d-pro.jpg"
        ),
        affiliate_url=(
            "https://example.com/rackets/"
            "astrox-88-d-pro?ref=badminton"
        ),
        embedding=[0.1] * 768,
        is_active=True,
    )


def test_query_rackets_success(
    mock_racket_service,
):
    mock_racket_service.query_rackets.return_value = (
        [create_racket()],
        1,
    )

    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "5000",
            "playing_style": "offensive",
            "brand": "YONEX",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["data"] == [{
        "id": 1,
        "brand": "YONEX",
        "model": "ASTROX 88 D PRO",
        "price": "4890.00",
        "weight": "4U",
        "balance": "head_heavy",
        "flexibility": "stiff",
        "suitable_level": "advanced",
        "playing_style": "offensive",
        "description": "適合後場進攻型選手。",
        "image_url": (
            "https://storage.googleapis.com/"
            "badminton-rackets/astrox-88-d-pro.jpg"
        ),
        "affiliate_url": (
            "https://example.com/rackets/"
            "astrox-88-d-pro?ref=badminton"
        ),
        "is_active": True,
    }]

    assert body["pagination"] == {
        "page": 1,
        "pageSize": 10,
        "totalItems": 1,
        "totalPages": 1,
    }
    assert "embedding" not in body["data"][0]

    mock_racket_service.query_rackets.assert_called_once_with(
        budget=Decimal("5000"),
        playing_style="offensive",
        brand="YONEX",
        page=1,
        page_size=10,
    )


def test_query_rackets_without_brand(
    mock_racket_service,
):
    mock_racket_service.query_rackets.return_value = ([], 0)

    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "3000",
            "playing_style": "defensive",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": [],
        "pagination": {
            "page": 1,
            "pageSize": 10,
            "totalItems": 0,
            "totalPages": 0,
        },
    }

    mock_racket_service.query_rackets.assert_called_once_with(
        budget=Decimal("3000"),
        playing_style="defensive",
        brand=None,
        page=1,
        page_size=10,
    )


def test_get_racket_success(mock_racket_service):
    mock_racket_service.get_racket.return_value = create_racket()

    response = client.get("/api/v1/rackets/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["brand"] == "YONEX"
    assert response.json()["model"] == "ASTROX 88 D PRO"
    assert "embedding" not in response.json()

    mock_racket_service.get_racket.assert_called_once_with(1)


def test_get_racket_not_found(mock_racket_service):
    mock_racket_service.get_racket.return_value = None

    response = client.get("/api/v1/rackets/999")

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "code": "RACKET_NOT_FOUND",
        "message": "Racket 999 was not found.",
    }

    mock_racket_service.get_racket.assert_called_once_with(999)


def test_query_rackets_missing_budget(
    mock_racket_service,
):
    response = client.get(
        "/api/v1/rackets",
        params={
            "playing_style": "offensive",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    mock_racket_service.query_rackets.assert_not_called()


def test_query_rackets_missing_playing_style(
    mock_racket_service,
):
    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "5000",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    mock_racket_service.query_rackets.assert_not_called()


def test_query_rackets_invalid_budget(
    mock_racket_service,
):
    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "0",
            "playing_style": "offensive",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    mock_racket_service.query_rackets.assert_not_called()


def test_query_rackets_invalid_playing_style(
    mock_racket_service,
):
    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "5000",
            "playing_style": "invalid",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    mock_racket_service.query_rackets.assert_not_called()


def test_query_rackets_database_failure(
    mock_racket_service,
):
    mock_racket_service.query_rackets.side_effect = (
        DatabaseServiceError(
            "Unable to query racket database."
        )
    )

    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "5000",
            "playing_style": "offensive",
        },
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == (
        "DATABASE_SERVICE_ERROR"
    )
