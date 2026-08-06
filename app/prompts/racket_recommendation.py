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
