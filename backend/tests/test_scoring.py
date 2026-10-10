from app.detection.scoring import final_score
from app.detection.taxonomy import verdict_for


def test_blend_and_floor():
    assert final_score(50, None) == 50
    assert final_score(50, 100) == 80
    assert final_score(90, 10, floor=85) == 85  # LLM can never push below the floor
    assert final_score(0, 0) == 0


def test_thresholds():
    assert verdict_for(34) == "SAFE" and verdict_for(35) == "SUSPICIOUS"
    assert verdict_for(69) == "SUSPICIOUS" and verdict_for(70) == "SCAM"
