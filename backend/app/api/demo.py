import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter

router = APIRouter(prefix="/api/demo", tags=["demo"])
_DIR = Path(__file__).parent.parent / "data"


@router.get("/call")
async def call(variant: Literal["hinglish", "english", "benign"] = "hinglish"):
    return json.loads((_DIR / f"demo_{variant}.json").read_text(encoding="utf-8"))
