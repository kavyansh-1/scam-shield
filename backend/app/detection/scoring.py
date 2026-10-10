from typing import Optional

from .taxonomy import verdict_for


def final_score(rules_score: int, llm_score: Optional[int], floor: int = 0) -> int:
    s = rules_score if llm_score is None else round(0.4 * rules_score + 0.6 * llm_score)
    return max(0, min(100, max(s, floor)))


__all__ = ["final_score", "verdict_for"]
