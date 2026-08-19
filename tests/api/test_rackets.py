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
    mock_racket_service.query_rackets.return_value = [
        create_racket()
    ]

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

    assert len(body) == 1
    assert body[0] == {
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
    }

    assert "id" not in body[0]
    assert "embedding" not in body[0]

    mock_racket_service.query_rackets.assert_called_once_with(
        budget=Decimal("5000"),
        playing_style="offensive",
        brand="YONEX",
    )


def test_query_rackets_without_brand(
    mock_racket_service,
):
    mock_racket_service.query_rackets.return_value = []

    response = client.get(
        "/api/v1/rackets",
        params={
            "budget": "3000",
            "playing_style": "defensive",
        },
    )

    assert response.status_code == 200
    assert response.json() == []

    mock_racket_service.query_rackets.assert_called_once_with(
        budget=Decimal("3000"),
        playing_style="defensive",
        brand=None,
    )


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