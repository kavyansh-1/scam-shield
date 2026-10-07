# API router: blocklist (stub; see docs/CONTRACT.md)
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/blocklist", tags=["blocklist"])


def _nyi() -> JSONResponse:
    return JSONResponse({"error": "not implemented", "code": "NOT_IMPLEMENTED"}, status_code=501)


@router.post("/report")
async def blocklist_0():
    return _nyi()
