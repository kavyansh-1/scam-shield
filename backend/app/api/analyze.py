# API router: analyze (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.post("/text")
async def analyze_0():
    return _nyi()

@router.post("/image")
async def analyze_1():
    return _nyi()
