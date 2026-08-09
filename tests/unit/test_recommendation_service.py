from unittest.mock import Mock

import pytest

from app.exceptions.recommendation import (
    NoRacketCandidateError,
)
from app.services.recommendation_service import (
    RecommendationService,
)
from app.schemas.recommendation import (
    RacketFinalRecommendation,
)



def test_recommend_racket_no_candidates():

    # Arrange
    embedding_service = Mock()
    racket_repository = Mock()
    gemini_service = Mock()
    prompt_builder = Mock()

    # 重要：
    # 模擬 PostgreSQL + pgvector 查詢後沒有任何候選球拍
    racket_repository.find_similar.return_value = []

    service = RecommendationService(
        embedding_service=embedding_service,
        racket_repository=racket_repository,
        gemini_service=gemini_service,
        prompt_builder=prompt_builder,
    )

    request = Mock()

    request.level = "intermediate"
    request.playing_style = "offensive"
    request.budget = 1000

    # Act & Assert
    with pytest.raises(
        NoRacketCandidateError
    ):
        service.recommend_racket(
            request=request,
            limit=3,
        )

    # 確認 Embedding Service 有被呼叫
    embedding_service.embed_query.assert_called_once()

    # 確認 Repository 有被呼叫
    racket_repository.find_similar.assert_called_once()

    # Gemini 不應該被呼叫
    gemini_service.generate_structured.assert_not_called()

def test_recommend_racket_success():

    # =========================================================
    # Arrange
    # =========================================================

    embedding_service = Mock()
    racket_repository = Mock()
    gemini_service = Mock()
    prompt_builder = Mock()

    # ---------------------------------------------------------
    # 1. Mock Request
    # ---------------------------------------------------------

    request = Mock()

    request.level = "intermediate"
    request.playing_style = "offensive"
    request.budget = 5000

    # ---------------------------------------------------------
    # 2. Mock EmbeddingService
    # ---------------------------------------------------------

    fake_query_embedding = [0.01, 0.02, 0.03]

    embedding_service.embed_query.return_value = (
        fake_query_embedding
    )

    # ---------------------------------------------------------
    # 3. Mock PostgreSQL + pgvector
    #
    # 模擬 DB 回傳 Top-K：
    #
    # (Racket, cosine_distance)
    # ---------------------------------------------------------

    racket_1 = Mock()

    racket_1.id = 1
    racket_1.brand = "Yonex"
    racket_1.model = "Astrox 7 DG"
    racket_1.price = 2990

    racket_2 = Mock()

    racket_2.id = 2
    racket_2.brand = "Yonex"
    racket_2.model = "Astrox 88D Pro"
    racket_2.price = 4990

    racket_repository.find_similar.return_value = [
        (racket_1, 0.232582),
        (racket_2, 0.241278),
    ]

    # ---------------------------------------------------------
    # 4. Mock PromptBuilder
    # ---------------------------------------------------------

    fake_prompt = """
    請從以下候選球拍中選出最適合使用者的一支。
    """

    prompt_builder.build_racket_prompt.return_value = (
        fake_prompt
    )

    # ---------------------------------------------------------
    # 5. Mock Gemini
    #
    # Gemini 選擇 id=1
    # ---------------------------------------------------------

    gemini_result = Mock()

    gemini_result.recommended_racket_id = 1
    gemini_result.reason = (
        "Astrox 7 DG 適合中階進攻型球友，"
        "價格也符合預算。"
    )

    gemini_service.generate_structured.return_value = (
        gemini_result
    )

    # ---------------------------------------------------------
    # 6. 建立 RecommendationService
    # ---------------------------------------------------------

    service = RecommendationService(
        embedding_service=embedding_service,
        racket_repository=racket_repository,
        gemini_service=gemini_service,
        prompt_builder=prompt_builder,
    )

    # =========================================================
    # Act
    # =========================================================

    selected_racket, reason = (
        service.recommend_racket(
            request=request,
            limit=3,
        )
    )

    # =========================================================
    # Assert
    # =========================================================

    # ---------------------------------------------------------
    # 驗證 EmbeddingService
    # ---------------------------------------------------------

    embedding_service.embed_query.assert_called_once()

    # ---------------------------------------------------------
    # 驗證 Repository
    # ---------------------------------------------------------

    racket_repository.find_similar.assert_called_once_with(
        query_embedding=fake_query_embedding,
        budget=5000,
        limit=3,
    )

    # ---------------------------------------------------------
    # 驗證 PromptBuilder
    # ---------------------------------------------------------

    prompt_builder.build_racket_prompt.assert_called_once()

    prompt_args = (
        prompt_builder
        .build_racket_prompt
        .call_args.kwargs
    )

    assert prompt_args["request"] == request

    candidates = prompt_args["candidates"]

    assert len(candidates) == 2

    assert candidates[0].id == 1
    assert candidates[0].model == "Astrox 7 DG"
    assert candidates[0].price == 2990

    assert candidates[1].id == 2
    assert candidates[1].model == "Astrox 88D Pro"
    assert candidates[1].price == 4990

    # ---------------------------------------------------------
    # 驗證 Gemini
    # ---------------------------------------------------------

    gemini_service.generate_structured.assert_called_once_with(
        prompt=fake_prompt,
        response_schema=RacketFinalRecommendation,
    )

    # ---------------------------------------------------------
    # 驗證最終推薦結果
    # ---------------------------------------------------------

    assert selected_racket.id == 1

    assert selected_racket.brand == "Yonex"

    assert selected_racket.model == "Astrox 7 DG"

    assert selected_racket.price == 2990

    assert selected_racket.distance == 0.232582

    assert selected_racket.similarity == (
        1 - 0.232582
    )

    assert reason == (
        "Astrox 7 DG 適合中階進攻型球友，"
        "價格也符合預算。"
    )

