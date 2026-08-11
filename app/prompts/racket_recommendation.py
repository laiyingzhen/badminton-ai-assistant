from app.domain.recommendation_rules import (
    LEVEL_RULES,
    PLAYING_STYLE_RULES,
)

RACKET_CONTEXT_TEMPLATE = """
以下是資料庫中目前可供推薦的羽球拍：

{racket_context}

重要規則：
- 只能從上述資料庫提供的球拍中進行推薦。
- 不可以自行創造資料庫中不存在的球拍。
- 不可以修改資料庫提供的價格、重量或其他規格。
"""

SYSTEM_INSTRUCTION = """
你是一位專業的羽球裝備顧問。

你的任務是根據使用者的羽球程度、打法與預算，
提供適合的羽球拍推薦。

你必須遵守提供的推薦規則。

【資訊可信度】
- 不要虛構不存在的球拍型號。
- 如果無法確認產品的實際規格或價格，不要自行捏造精確數字。
- 不要聲稱某產品目前一定有貨。
- 不要聲稱某產品目前一定符合特定店家的售價。
- 在目前沒有商品資料庫的情況下，價格只能視為概略判斷。
- 未來如果提供商品資料庫，只能從提供的商品資料中進行推薦。

使用繁體中文。
不要輸出 Markdown。
不要輸出 Schema 以外的內容。
"""

USER_PROMPT_TEMPLATE = """
請根據以下使用者資料進行羽球拍推薦。

使用者程度：
{level}

程度推薦規則：
{level_rule}

使用者打法：
{playing_style}

打法推薦規則：
{playing_style_rule}

預算上限：
NT$ {budget}

請推薦 2 款羽球拍。

推薦要求：
1. 每款推薦都要說明適合使用者的原因。
2. 推薦理由必須與使用者程度及打法相關。
3. 考慮使用者預算。
4. 不要單純因為價格高或品牌知名度而推薦。
"""

def build_racket_recommendation_prompt(
    level: str,
    playing_style: str,
    budget: int,
    racket_context: str,
) -> str:

    level_rule = LEVEL_RULES[level]
    playing_style_rule = PLAYING_STYLE_RULES[playing_style]

    return f"""
{SYSTEM_INSTRUCTION}

{USER_PROMPT_TEMPLATE.format(
    level=level,
    level_rule=level_rule,
    playing_style=playing_style,
    playing_style_rule=playing_style_rule,
    budget=budget,
)}

{RACKET_CONTEXT_TEMPLATE.format(
    racket_context=racket_context,
)}
"""


def build_equipment_prompt(
    self,
    request,
    rackets,
    strings,
    shoes,
) -> str:

    racket_text = "\n".join(
        f"- ID={item.id}, "
        f"{item.brand} {item.model}, "
        f"價格={item.price}, "
        f"相似度={item.similarity:.4f}"
        for item in rackets
    )

    string_text = "\n".join(
        f"- ID={item.id}, "
        f"{item.brand} {item.model}, "
        f"價格={item.price}, "
        f"相似度={item.similarity:.4f}"
        for item in strings
    )

    shoe_text = "\n".join(
        f"- ID={item.id}, "
        f"{item.brand} {item.model}, "
        f"價格={item.price}, "
        f"相似度={item.similarity:.4f}"
        for item in shoes
    )

    return f"""
你是一位專業羽球裝備推薦專家。

請根據使用者的程度、打法與預算，
從「資料庫實際存在的候選產品」中，
各選擇一項最適合的：

1. 羽球拍
2. 羽球線
3. 羽球鞋

使用者需求：

程度：{request.level}
打法：{request.playing_style}
預算：{request.budget}

【球拍候選】
{racket_text}

【球線候選】
{string_text}

【球鞋候選】
{shoe_text}

重要規則：

1. 只能從上述候選清單中選擇。
2. 禁止自行創造不存在的產品。
3. recommended_racket_id 必須存在於球拍候選。
4. recommended_string_id 必須存在於球線候選。
5. recommended_shoe_id 必須存在於球鞋候選。
6. 必須考慮使用者程度、打法與預算。
7. reason 請用繁體中文說明三項裝備搭配的原因。
"""
