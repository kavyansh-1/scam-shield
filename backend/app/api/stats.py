# API router: stats (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.get("")
async def stats_0():
    return _nyi()
