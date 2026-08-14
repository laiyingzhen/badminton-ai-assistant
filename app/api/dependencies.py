from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.chat_repository import ChatRepository
from app.repositories.racket_repository import RacketRepository
from app.services.chat_prompt import ChatPromptBuilder
from app.services.chat_service import RacketChatService
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
) -> RecommendationService:
    return RecommendationService(
        embedding_service=EmbeddingService(),
        racket_repository=RacketRepository(db),
        gemini_service=GeminiService(),
        prompt_builder=RecommendationPromptBuilder(),
    )


def get_racket_chat_service(
    db: Session = Depends(get_db),
) -> RacketChatService:
    racket_repository = RacketRepository(db)
    gemini_service = GeminiService()

    recommendation_service = RecommendationService(
        embedding_service=EmbeddingService(),
        racket_repository=racket_repository,
        gemini_service=gemini_service,
        prompt_builder=RecommendationPromptBuilder(),
    )

    return RacketChatService(
        chat_repository=ChatRepository(db),
        racket_repository=racket_repository,
        recommendation_service=recommendation_service,
        gemini_service=gemini_service,
        prompt_builder=ChatPromptBuilder(),
    )


def get_racket_candidate_limit() -> int:
    return get_settings().racket_candidate_limit