from app.prompts.racket_recommendation import (
    build_racket_recommendation_prompt,
)


def test_racket_prompt_contains_user_context():

    racket_context = """
    1. Yonex Astrox 7 DG
       Price: 2990
       Distance: 0.232582
       Similarity: 0.767418

    2. Yonex Astrox 88D Pro
       Price: 4990
       Distance: 0.241278
       Similarity: 0.758722
    """

    prompt = build_racket_recommendation_prompt(
        level="intermediate",
        playing_style="offensive",
        budget=5000,
        racket_context=racket_context,
    )

    assert "intermediate" in prompt
    assert "offensive" in prompt
    assert "5000" in prompt

    # 確認實際候選球拍有進入 Prompt
    assert "Astrox 7 DG" in prompt
    assert "Astrox 88D Pro" in prompt
    assert "2990" in prompt
    assert "4990" in prompt


def test_beginner_defensive_prompt():

    racket_context = """
    1. Yonex Astrox 7 DG
       Price: 2990
       Distance: 0.232582
       Similarity: 0.767418
    """

    prompt = build_racket_recommendation_prompt(
        level="beginner",
        playing_style="defensive",
        budget=3000,
        racket_context=racket_context,
    )

    assert "beginner" in prompt
    assert "defensive" in prompt
    assert "3000" in prompt

    assert "容錯性" in prompt
    assert "防守" in prompt

    # 確認候選球拍有被加入 Prompt
    assert "Astrox 7 DG" in prompt
    assert "2990" in prompt

