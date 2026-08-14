from uuid import UUID

from app.exceptions.recommendation import NoRacketCandidateError
from app.models.chat import ChatSession
from app.repositories.chat_repository import ChatRepository
from app.repositories.racket_repository import RacketRepository
from app.schemas.chat import (
    ChatGuidanceResult,
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatResponse,
    CriteriaExtractionResult,
    ExtractedRacketCriteria,
)
from app.schemas.recommendation import (
    RacketCandidate,
    RacketRecommendationRequest,
)
from app.services.chat_prompt import ChatPromptBuilder
from app.services.gemini_service import GeminiService
from app.services.recommendation_service import (
    RecommendationService,
)


class ChatSessionNotFoundError(Exception):

    def __init__(self, session_id: UUID):
        self.session_id = session_id

        super().__init__(
            f"Chat session {session_id} was not found."
        )


class RacketChatService:

    REQUIRED_FIELDS = (
        "playing_style",
        "level",
        "budget",
    )

    def __init__(
        self,
        chat_repository: ChatRepository,
        racket_repository: RacketRepository,
        recommendation_service: RecommendationService,
        gemini_service: GeminiService,
        prompt_builder: ChatPromptBuilder,
    ):
        self.chat_repository = chat_repository
        self.racket_repository = racket_repository
        self.recommendation_service = recommendation_service
        self.gemini_service = gemini_service
        self.prompt_builder = prompt_builder

    def chat(
        self,
        message: str,
        session_id: UUID | None,
        candidate_limit: int,
    ) -> ChatResponse:
        session = self._get_or_create_session(session_id)

        try:
            self.chat_repository.add_message(
                session=session,
                role="user",
                content=message,
            )

            extraction = self._extract_criteria(
                session=session,
                user_message=message,
            )

            self._merge_criteria(
                session=session,
                extraction=extraction,
            )

            missing_fields = self._missing_fields(session)

            if missing_fields:
                response = self._build_collecting_response(
                    session=session,
                    missing_fields=missing_fields,
                    candidate_limit=candidate_limit,
                )
            else:
                response = self._build_recommendation_response(
                    session=session,
                    candidate_limit=candidate_limit,
                )

            self.chat_repository.add_message(
                session=session,
                role="assistant",
                content=response.message,
            )

            self.chat_repository.save()

            return response

        except Exception:
            self.chat_repository.rollback()
            raise

    def get_history(
        self,
        session_id: UUID,
    ) -> ChatHistoryResponse:
        session = (
            self.chat_repository.get_session_with_messages(
                session_id
            )
        )

        if session is None:
            raise ChatSessionNotFoundError(session_id)

        return ChatHistoryResponse(
            session_id=session.id,
            criteria=self._criteria_response(session),
            messages=[
                ChatMessageResponse(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                )
                for message in session.messages
            ],
        )

    def _get_or_create_session(
        self,
        session_id: UUID | None,
    ) -> ChatSession:
        if session_id is None:
            return self.chat_repository.create_session()

        session = self.chat_repository.get_session(
            session_id
        )

        if session is None:
            raise ChatSessionNotFoundError(session_id)

        return session

    def _extract_criteria(
        self,
        session: ChatSession,
        user_message: str,
    ) -> CriteriaExtractionResult:
        prompt = self.prompt_builder.build_extraction_prompt(
            session=session,
            user_message=user_message,
        )

        return self.gemini_service.generate_structured(
            prompt=prompt,
            response_schema=CriteriaExtractionResult,
        )

    def _merge_criteria(
        self,
        session: ChatSession,
        extraction: CriteriaExtractionResult,
    ) -> None:
        if extraction.playing_style is not None:
            session.playing_style = extraction.playing_style

        if extraction.level is not None:
            session.level = extraction.level

        if extraction.budget is not None:
            session.budget = extraction.budget

        if extraction.clear_brand:
            session.brand = None
        elif extraction.brand is not None:
            session.brand = extraction.brand

    def _missing_fields(
        self,
        session: ChatSession,
    ) -> list[str]:
        return [
            field
            for field in self.REQUIRED_FIELDS
            if getattr(session, field) is None
        ]

    def _build_collecting_response(
        self,
        session: ChatSession,
        missing_fields: list[str],
        candidate_limit: int,
    ) -> ChatResponse:
        candidates = (
            self.racket_repository.find_by_partial_conditions(
                playing_style=session.playing_style,
                level=session.level,
                budget=session.budget,
                brand=session.brand,
                limit=candidate_limit,
            )
        )

        prompt = self.prompt_builder.build_guidance_prompt(
            session=session,
            missing_fields=missing_fields,
            candidates=candidates,
        )

        guidance = self.gemini_service.generate_structured(
            prompt=prompt,
            response_schema=ChatGuidanceResult,
        )

        return ChatResponse(
            session_id=session.id,
            status="collecting",
            message=guidance.message,
            criteria=self._criteria_response(session),
            missing_fields=missing_fields,
            recommendation=None,
        )

    def _build_recommendation_response(
        self,
        session: ChatSession,
        candidate_limit: int,
    ) -> ChatResponse:
        request = RacketRecommendationRequest(
            playing_style=session.playing_style,
            brand=session.brand,
            level=session.level,
            budget=session.budget,
        )

        try:
            racket, reason = (
                self.recommendation_service.recommend_racket(
                    request=request,
                    limit=candidate_limit,
                )
            )

        except NoRacketCandidateError:
            brand_text = (
                f"{session.brand}、"
                if session.brand
                else ""
            )

            message = (
                f"目前找不到符合{brand_text}"
                f"預算 NT$ {session.budget} 的球拍。"
                "你可以提高預算、取消品牌限制，"
                "或告訴我新的條件，我會再幫你查詢。"
            )

            return ChatResponse(
                session_id=session.id,
                status="no_match",
                message=message,
                criteria=self._criteria_response(session),
                missing_fields=[],
                recommendation=None,
            )

        message = (
            f"推薦你選擇 {racket.brand} {racket.model}，"
            f"價格約 NT$ {racket.price}。{reason}"
        )

        return ChatResponse(
            session_id=session.id,
            status="recommended",
            message=message,
            criteria=self._criteria_response(session),
            missing_fields=[],
            recommendation=racket,
        )

    @staticmethod
    def _criteria_response(
        session: ChatSession,
    ) -> ExtractedRacketCriteria:
        return ExtractedRacketCriteria(
            playing_style=session.playing_style,
            brand=session.brand,
            level=session.level,
            budget=session.budget,
        )