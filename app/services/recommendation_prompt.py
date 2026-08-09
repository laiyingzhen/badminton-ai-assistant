import json

from app.schemas.recommendation import (
    RacketCandidate,
    RacketRecommendationRequest,
)


class RecommendationPromptBuilder:

    def build_racket_prompt(
        self,
        request: RacketRecommendationRequest,
        candidates: list[RacketCandidate],
    ) -> str:

        candidate_data = [
            {
                "id": candidate.id,
                "brand": candidate.brand,
                "model": candidate.model,
                "price": float(candidate.price),
            }
            for candidate in candidates
        ]

        candidates_json = json.dumps(
            candidate_data,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
你是一位專業的羽球裝備推薦助手。

請根據使用者的程度、打法與預算，
從「候選球拍清單」中選出最適合的一支球拍。

【使用者需求】
- 羽球程度：{request.level}
- 打法：{request.playing_style}
- 預算：NT$ {request.budget}

【候選球拍】
{candidates_json}

【重要規則】
1. 只能從候選球拍清單中選擇。
2. 不可以推薦候選清單以外的球拍。
3. recommended_racket_id 必須是候選清單中的 id。
4. 不可以修改候選球拍的品牌、型號或價格。
5. 請根據使用者的程度、打法與預算判斷最適合的球拍。
6. reason 請簡潔說明推薦理由。
"""