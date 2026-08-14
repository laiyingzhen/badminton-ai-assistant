import json

from app.models.chat import ChatSession
from app.models.racket import Racket


FIELD_LABELS = {
    "playing_style": "偏好的打法",
    "level": "能力／程度",
    "budget": "預算",
}


class ChatPromptBuilder:

    def build_extraction_prompt(
        self,
        session: ChatSession,
        user_message: str,
    ) -> str:
        current_criteria = {
            "playing_style": session.playing_style,
            "brand": session.brand,
            "level": session.level,
            "budget": (
                float(session.budget)
                if session.budget is not None
                else None
            ),
        }

        criteria_json = json.dumps(
            current_criteria,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
你負責從羽球拍推薦對話中抽取查詢條件。

目前已保存的條件：
{criteria_json}

使用者最新訊息：
{user_message}

請只從最新訊息抽取使用者這次明確提供或修改的條件。

欄位規則：
- playing_style：
  - 進攻、殺球、重殺、後場進攻 → offensive
  - 防守、接殺、速度、平抽擋 → defensive
  - 攻守兼備、平均、全能 → all_round
- brand：只允許 YONEX、VICTOR、LI-NING、JNICE。
- level：
  - 新手、初學、剛開始 → beginner
  - 中階、有一些經驗 → intermediate
  - 高階、進階、選手 → advanced
- budget：大於 0 的數字，代表新台幣預算上限。
- 沒提到的欄位回傳 null。
- 不可猜測使用者未提供的資料。
- 如果使用者明確說不限品牌、沒有品牌偏好，
  clear_brand 必須回傳 true。
- 「五千」「5k」「5000元」都應轉換成 5000。
""".strip()

    def build_guidance_prompt(
        self,
        session: ChatSession,
        missing_fields: list[str],
        candidates: list[Racket],
    ) -> str:
        known_criteria = {
            "playing_style": session.playing_style,
            "brand": session.brand,
            "level": session.level,
            "budget": (
                float(session.budget)
                if session.budget is not None
                else None
            ),
        }

        candidate_data = [
            {
                "brand": racket.brand,
                "model": racket.model,
                "price": float(racket.price),
                "playing_style": racket.playing_style,
                "level": racket.suitable_level,
            }
            for racket in candidates
        ]

        missing_labels = [
            FIELD_LABELS[field]
            for field in missing_fields
        ]

        return f"""
你是專業且親切的羽球拍推薦聊天助手。

目前已知條件：
{json.dumps(known_criteria, ensure_ascii=False, indent=2)}

仍缺少的必填條件：
{json.dumps(missing_labels, ensure_ascii=False)}

依部分條件從資料庫找到的參考球拍：
{json.dumps(candidate_data, ensure_ascii=False, indent=2)}

請產生一段簡短繁體中文回覆：
1. 先確認目前已理解的條件。
2. 若有參考球拍，可簡短說明目前資料庫中的價格或方向，
   但不要說這是最終推薦。
3. 一次清楚詢問缺少的必填資料。
4. 提供合法選項：
   打法為進攻、防守、全能；
   程度為初學、中階、進階；
   預算必須大於 0。
5. 品牌是選填，不得要求使用者一定提供。
6. 不可虛構資料庫不存在的球拍。
""".strip()