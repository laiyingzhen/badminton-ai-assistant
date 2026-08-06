from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.racket_repository import RacketRepository
from app.schemas.recommendation import (
    RacketRecommendationRequest,
    RacketRecommendationResponse,
)
from app.services.gemini_service import GeminiService
from app.services.recommendation_service import RecommendationService


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post(
    "/rackets",
    response_model=RacketRecommendationResponse,
)
def recommend_rackets(
    request: RacketRecommendationRequest,
    db: Session = Depends(get_db),
):

    gemini_service = GeminiService()

    racket_repository = RacketRepository(
        db=db
    )

    recommendation_service = RecommendationService(
        gemini_service=gemini_service,
        racket_repository=racket_repository,
    )

    return recommendation_service.recommend_rackets(
        request
    )