from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.racket_repository import (
    RacketRepository,
)
from app.repositories.shoe_repository import (
    ShoeRepository,
)
from app.repositories.string_repository import (
    StringRepository,
)
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.recommendation_prompt import (
    RecommendationPromptBuilder,
)
from app.services.recommendation_service import (
    RecommendationService,
)


def get_recommendation_service(
    db: Session = Depends(get_db),
):

    return RecommendationService(
        embedding_service=EmbeddingService(),
        racket_repository=RacketRepository(db),
        string_repository=StringRepository(db),
        shoe_repository=ShoeRepository(db),
        gemini_service=GeminiService(),
        prompt_builder=RecommendationPromptBuilder(),
    )

def get_racket_candidate_limit() -> int:
    return get_settings().racket_candidate_limit