from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_racket_candidate_limit,
    get_recommendation_service,
)
from app.schemas.recommendation import (
    ErrorResponse,
    RacketRecommendationRequest,
    RacketRecommendationResponse,
)
from app.services.recommendation_service import (
    RecommendationService,
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post(
    "/rackets",
    response_model=RacketRecommendationResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "No racket candidate found.",
        },
        502: {
            "model": ErrorResponse,
            "description": "AI recommendation service failed.",
        },
    },
)
def recommend_racket(
    request: RacketRecommendationRequest,
    service: RecommendationService = Depends(
        get_recommendation_service
    ),
    candidate_limit: int = Depends(
        get_racket_candidate_limit
    ),
):

    racket, reason = service.recommend_racket(
        request=request,
        limit=candidate_limit,
    )

    return RacketRecommendationResponse(
        racket=racket,
        reason=reason,
    )