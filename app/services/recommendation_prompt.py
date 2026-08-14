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
            candidate.to_prompt_dict()
            for candidate in candidates
        ]

        candidates_json = json.dumps(
            candidate_data,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
你是一位專業的羽球拍推薦顧問。

請根據使用者條件，從候選球拍中選出最適合的一支。

使用者條件：
- 程度：{request.level}
- 打法：{request.playing_style}
- 品牌偏好：{request.brand or "無品牌偏好"}
- 預算上限：NT$ {request.budget}

候選球拍：
{candidates_json}

規則：
1. 只能推薦候選清單中的球拍。
2. recommended_racket_id 必須是候選球拍的 id。
3. 不可虛構球拍型號、價格或規格。
4. 必須符合預算。
5. 如果有品牌偏好，候選球拍都已經過品牌篩選。
6. reason 請使用繁體中文，簡潔說明程度、打法、
   品牌與預算的適合原因。
""".strip()