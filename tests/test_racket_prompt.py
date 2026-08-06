from app.prompts.racket_recommendation import (
    build_racket_recommendation_prompt,
)


def test_racket_prompt_contains_user_context():
    prompt = build_racket_recommendation_prompt(
        level="intermediate",
        playing_style="offensive",
        budget=5000,
    )

    assert "intermediate" in prompt
    assert "offensive" in prompt
    assert "5000" in prompt

def test_beginner_defensive_prompt():
    prompt = build_racket_recommendation_prompt(
        level="beginner",
        playing_style="defensive",
        budget=3000,
    )

    assert "beginner" in prompt
    assert "defensive" in prompt
    assert "3000" in prompt
    assert "容錯性" in prompt
    assert "防守" in prompt    